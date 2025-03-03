#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-03-03 2:10 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : sync_aws.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""
import boto3
import logging
from django.db import transaction
from config import AWS_REGIONS, aws_access_key_id, aws_secret_access_key, aws_session_token
from ip_lookup_app.models import (
    AWSEC2Instance,
    AWSVPC,
    AWSSubnet,
    AWSRouteTable,
    AWSRoute,
    AWSSecurityGroup,
    AWSSecurityGroupRule
)

class SyncAws:
    def __init__(self):
        self.regions = AWS_REGIONS
        self.clients = {}

    def _get_ec2_client(self, region):
        """获取区域EC2客户端（带缓存）"""
        if region not in self.clients:
            self.clients[region] = boto3.client(
                'ec2',
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token
            )
        return self.clients[region]

    def _get_resource_name(self, tags, default=""):
        """从标签获取资源名称"""
        return next(
            (tag['Value'] for tag in tags if tag['Key'] == 'Name'),
            default
        )

    def sync_ec2(self):
        """同步EC2实例数据"""
        for region in self.regions:
            ec2 = self._get_ec2_client(region)
            try:
                instances = ec2.describe_instances()
            except Exception as e:
                logging.error(f"Failed to fetch EC2 instances for {region}: {e}", exc_info=True)
                continue

            with transaction.atomic():
                for reservation in instances.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        try:
                            self._process_ec2_instance(region, instance)
                        except Exception as e:
                            logging.error(f"Error processing instance {instance.get('InstanceId')}: {e}", exc_info=True)

    def _process_ec2_instance(self, region, instance):
        """处理单个EC2实例"""
        instance_id = instance.get('InstanceId', '')
        vpc_id = instance.get('VpcId', '')
        subnet_id = instance.get('SubnetId', '')
        state = instance.get('State', {}).get('Name', 'unknown')
        instance_type = instance.get('InstanceType', '')

        # 提取标签信息
        name_tag = self._get_resource_name(instance.get("Tags", []), instance_id)

        # 提取网络信息
        private_ips = [
            eni.get('PrivateIpAddress')
            for eni in instance.get('NetworkInterfaces', [])
            if 'PrivateIpAddress' in eni
        ]
        public_ips = [
            eni['Association']['PublicIp']
            for eni in instance.get('NetworkInterfaces', [])
            if 'Association' in eni and 'PublicIp' in eni['Association']
        ]
        security_group_ids = [sg['GroupId'] for sg in instance.get('SecurityGroups', [])]

        # 更新或创建实例
        ec2_instance, _ = AWSEC2Instance.objects.update_or_create(
            instance_id=instance_id,
            defaults={
                "name": name_tag,
                "private_ips": private_ips,
                "public_ips": public_ips,
                "vpc_id": vpc_id,
                "subnet_id": subnet_id,
                "instance_type": instance_type,
                "state": state,
                "region": region,
            }
        )

        # 更新安全组关联
        sg_instances = [
            AWSSecurityGroup.objects.get_or_create(group_id=sg_id)[0]
            for sg_id in security_group_ids
        ]
        ec2_instance.security_groups.set(sg_instances)
        print(f"Synced EC2 instance: {instance_id} ({name_tag})")

    def sync_vpcs(self):
        """同步VPC数据"""
        for region in self.regions:
            ec2 = self._get_ec2_client(region)
            try:
                vpcs = ec2.describe_vpcs()
                for vpc in vpcs['Vpcs']:
                    with transaction.atomic():
                        self._process_vpc(region, ec2, vpc)
            except Exception as e:
                logging.error(f"Failed to sync VPCs in {region}: {e}", exc_info=True)

    def _process_vpc(self, region, ec2_client, vpc):
        """处理单个VPC"""
        vpc_id = vpc['VpcId']
        vpc_name = self._get_resource_name(vpc.get("Tags", []), "")
        ipv4_cidr = vpc["CidrBlock"]
        owner_id = vpc.get("OwnerId", "")

        # 获取关联资源
        main_route_table_id = self._get_main_route_table(ec2_client, vpc_id)
        main_network_acl_id = self._get_main_network_acl(ec2_client, vpc_id)

        AWSVPC.objects.update_or_create(
            vpc_id=vpc_id,
            defaults={
                'name': vpc_name,
                'ipv4_cidr': ipv4_cidr,
                'owner_id': owner_id,
                'main_route_table': main_route_table_id,
                'main_network_acl': main_network_acl_id,
                'region': region
            }
        )
        print(f"Synced VPC: {vpc_id} ({vpc_name})")

    def _get_main_route_table(self, ec2_client, vpc_id):
        """获取主路由表ID"""
        response = ec2_client.describe_route_tables(Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]},
            {'Name': 'association.main', 'Values': ['true']}
        ])
        return response['RouteTables'][0]['RouteTableId'] if response['RouteTables'] else ''

    def _get_main_network_acl(self, ec2_client, vpc_id):
        """获取主网络ACL ID"""
        response = ec2_client.describe_network_acls(Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]}
        ])
        for acl in response.get('NetworkAcls', []):
            if acl.get('IsDefault', False):
                return acl['NetworkAclId']
        return ''

    def sync_subnets(self):
        """同步子网数据"""
        for region in self.regions:
            ec2 = self._get_ec2_client(region)
            try:
                subnets = ec2.describe_subnets()
                for subnet in subnets['Subnets']:
                    with transaction.atomic():
                        self._process_subnet(region, subnet)
            except Exception as e:
                logging.error(f"Failed to sync subnets in {region}: {e}", exc_info=True)

    def _process_subnet(self, region, subnet):
        """处理单个子网"""
        subnet_name = self._get_resource_name(subnet.get("Tags", []), "")
        AWSSubnet.objects.update_or_create(
            subnet_id=subnet['SubnetId'],
            defaults={
                'name': subnet_name,
                'vpc_id': subnet['VpcId'],
                'ipv4_cidr': subnet['CidrBlock'],
                'available_ipv4_address': subnet['AvailableIpAddressCount'],
                'region': region
            }
        )
        print(f"Synced subnet: {subnet_name} ({subnet['VpcId']})")

    def sync_route_table(self):
        """同步路由表数据"""
        for region in self.regions:
            ec2 = self._get_ec2_client(region)
            try:
                route_tables = ec2.describe_route_tables()
                for rt in route_tables['RouteTables']:
                    with transaction.atomic():
                        self._process_route_table(region, rt)
            except Exception as e:
                logging.error(f"Failed to sync route tables in {region}: {e}", exc_info=True)

    def _process_route_table(self, region, route_table):
        """处理单个路由表"""
        route_table_name = self._get_resource_name(route_table.get("Tags", []), "N/A")
        rt_obj, _ = AWSRouteTable.objects.update_or_create(
            route_table_id=route_table['RouteTableId'],
            defaults={
                'name': route_table_name,
                'vpc_id': route_table['VpcId'],
                'region': region
            }
        )

        # 处理路由条目
        for route in route_table.get('Routes', []):
            AWSRoute.objects.update_or_create(
                route_table=rt_obj,
                destination_cidr_block=route.get('DestinationCidrBlock', 'N/A'),
                defaults={
                    'target': route.get('GatewayId', route.get('NatGatewayId', 'N/A')),
                    'status': route.get('State', 'N/A'),
                    'region': region
                }
            )
            print(f"Synced route table: {route_table_name} ")

    def security_group_rules(self):
        """同步安全组及规则"""
        for region in self.regions:
            ec2 = self._get_ec2_client(region)
            try:
                security_groups = ec2.describe_security_groups()
                for sg in security_groups['SecurityGroups']:
                    with transaction.atomic():
                        self._process_security_group(sg)
            except Exception as e:
                logging.error(f"Failed to sync security groups in {region}: {e}", exc_info=True)

    def _process_security_group(self, sg_data):
        """处理单个安全组"""
        group_id = sg_data['GroupId']
        sg_obj, _ = AWSSecurityGroup.objects.update_or_create(
            group_id=group_id,
            defaults={
                'name': self._get_resource_name(sg_data.get("Tags", []), ""),
                'group_name': sg_data.get('GroupName', ''),
                'vpc_id': sg_data.get('VpcId', ''),
                'description': sg_data.get('Description', ''),
                'owner': sg_data.get('OwnerId', ''),
                'inbound_rules_count': len(sg_data.get('IpPermissions', [])),
                'outbound_rules_count': len(sg_data.get('IpPermissionsEgress', []))
            }
        )

        # 清除旧规则
        sg_obj.rules.all().delete()

        # 处理入站规则
        for perm in sg_data.get('IpPermissions', []):
            self._process_rules(sg_obj, perm, 'inbound')

        # 处理出站规则
        for perm in sg_data.get('IpPermissionsEgress', []):
            self._process_rules(sg_obj, perm, 'outbound')

    def _process_rules(self, sg_obj, permission, direction):
        """处理安全组规则"""
        ip_protocol = permission.get('IpProtocol', '')
        from_port = permission.get('FromPort')
        to_port = permission.get('ToPort')

        # IPv4规则
        for ip_range in permission.get('IpRanges', []):
            self._create_rule(
                sg_obj, direction, ip_protocol,
                from_port, to_port,
                cidr_ipv4=ip_range.get('CidrIp'),
                description=ip_range.get('Description')
            )

        # IPv6规则
        for ipv6_range in permission.get('Ipv6Ranges', []):
            self._create_rule(
                sg_obj, direction, ip_protocol,
                from_port, to_port,
                cidr_ipv6=ipv6_range.get('CidrIpv6'),
                description=ipv6_range.get('Description')
            )

    def _create_rule(self, sg_obj, direction, protocol, from_port, to_port, description, **kwargs):
        """创建规则记录"""
        rule_type = self._infer_rule_type(protocol, from_port, to_port)
        AWSSecurityGroupRule.objects.create(
            security_group=sg_obj,
            direction=direction,
            ip_protocol=protocol,
            from_port=from_port,
            to_port=to_port,
            rule_type=rule_type,
            rule_description = description,
            **kwargs
        )
        print(f"Synced security group: {sg_obj} ")

    def _infer_rule_type(self, protocol, from_port, to_port):
        """推断规则类型"""
        if protocol == '-1':
            return "All Traffic"
        if protocol == 'tcp':
            if from_port == 22 and to_port == 22:
                return "SSH"
            if from_port == 80 and to_port == 80:
                return "HTTP"
            if from_port == 443 and to_port == 443:
                return "HTTPS"
        return "Custom"
