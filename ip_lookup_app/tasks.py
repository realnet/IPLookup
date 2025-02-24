#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-02-13 3:38 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : tasks.py.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""
import boto3
import logging
from celery import shared_task
from django.db import connection
from django.db import transaction
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from .models import AWSVPC, AWSEC2Instance, AWSSubnet, AWSSecurityGroup, AWSSecurityGroupRule, AWSRouteTable, AWSRoute, AzureVirtualNetwork, AzureVnet, AzureSubnet, AzureRouteTable
from config import aws_session_token,aws_access_key_id,aws_secret_access_key,AWS_REGIONS

# 配置日志
logging.basicConfig(level=logging.ERROR)


@shared_task
def sync_aws_data():
    for region in AWS_REGIONS:
        ec2_client = boto3.client(
            'ec2',
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )

        # # ==================== 同步 EC2 实例数据 ====================
        try:
            instances = ec2_client.describe_instances()
        except Exception as e:
            logging.error(f"Failed to fetch EC2 instances for {region}: {e}", exc_info=True)
            continue

        with transaction.atomic():
            for reservation in instances.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    try:
                        instance_id = instance.get('InstanceId', '')
                        vpc_id = instance.get('VpcId', '')
                        subnet_id = instance.get('SubnetId', '')
                        state = instance.get('State', {}).get('Name', 'unknown')
                        instance_type = instance.get('InstanceType', '')

                        # 获取 Name Tag
                        name_tag = next(
                            (tag['Value'] for tag in instance.get("Tags", []) if tag['Key'] == 'Name'),
                            instance_id
                        )

                        # 获取 Private IPs
                        private_ips = [
                            eni.get('PrivateIpAddress')
                            for eni in instance.get('NetworkInterfaces', [])
                            if 'PrivateIpAddress' in eni
                        ]

                        # 获取 Public IPs
                        public_ips = [
                            eni['Association']['PublicIp']
                            for eni in instance.get('NetworkInterfaces', [])
                            if 'Association' in eni and 'PublicIp' in eni['Association']
                        ]

                        # 获取 Security Groups
                        security_group_ids = [
                            sg['GroupId']
                            for sg in instance.get('SecurityGroups', [])
                        ]

                        # 更新或创建 EC2 实例记录
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
                            },
                        )

                        # 处理 Security Groups（ManyToMany 关联）
                        sg_instances = [
                            AWSSecurityGroup.objects.get_or_create(group_id=sg_id)[0]
                            for sg_id in security_group_ids
                        ]
                        ec2_instance.security_groups.set(sg_instances)  # 直接更新 ManyToMany 关联

                        print(f"Synced EC2 instance: {instance_id} ({name_tag})")

                    except Exception as e:
                        logging.error(f"Error syncing EC2 instance {instance_id}: {e}", exc_info=True)
        #
        # ==================== 同步 VPC 数据 ====================
        vpcs = ec2_client.describe_vpcs()
        for vpc in vpcs['Vpcs']:
            try:
                vpc_id = vpc['VpcId']
                vpc_name = next((tag["Value"] for tag in vpc.get("Tags", []) if tag["Key"] == "Name"), "")
                ipv4_cidr = vpc["CidrBlock"]
                owner_id = vpc.get("OwnerId", "")

                # 获取主路由表 ID
                main_route_table_id = ''
                route_tables = ec2_client.describe_route_tables(Filters=[
                    {'Name': 'vpc-id', 'Values': [vpc_id]},
                    {'Name': 'association.main', 'Values': ['true']}
                ])
                if route_tables['RouteTables']:
                    main_route_table_id = route_tables['RouteTables'][0]['RouteTableId']

                # 获取主网络 ACL ID
                main_network_acl_id = ''
                network_acls = ec2_client.describe_network_acls(Filters=[
                    {'Name': 'vpc-id', 'Values': [vpc_id]}
                ])
                for network_acl in network_acls.get('NetworkAcls', []):
                    if network_acl.get('IsDefault', False):
                        main_network_acl_id = network_acl['NetworkAclId']
                        break

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

            except Exception as e:
                logging.error(f"Error syncing VPC {vpc_id}: {e}", exc_info=True)

        # ==================== 同步子网数据 ====================
        subnets = ec2_client.describe_subnets()
        for subnet in subnets['Subnets']:
            subnet_name = next((tag["Value"] for tag in subnet.get("Tags", []) if tag["Key"] == "Name"), "")
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

        # ==================== 同步路由表数据 ====================
        route_tables = ec2_client.describe_route_tables()
        for route_table in route_tables['RouteTables']:
            try:
                route_table_name = next((tag["Value"] for tag in route_table.get("Tags", []) if tag["Key"] == "Name"), "N/A")
                new_route_table, _ = AWSRouteTable.objects.update_or_create(
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
                        route_table=new_route_table,
                        destination_cidr_block=route.get('DestinationCidrBlock', 'N/A'),
                        defaults={
                            'target': route.get('GatewayId', route.get('NatGatewayId', 'N/A')),
                            'status': route.get('State', 'N/A'),
                            'region': region
                        }
                    )
            except Exception as e:
                logging.error(f"Error syncing route table {route_table['RouteTableId']} in region {region}: {e}", exc_info=True)

        # ==================== 同步安全组 + 规则 ====================
        try:
            security_groups = ec2_client.describe_security_groups()
            for sg_data in security_groups['SecurityGroups']:
                group_id = sg_data.get('GroupId', '')
                group_name = sg_data.get('GroupName', '')
                vpc_id = sg_data.get('VpcId', '')
                description = sg_data.get('Description', '')
                owner_id = sg_data.get('OwnerId', '')

                # Name 字段可以从Tag里获取，也可直接存 group_name
                name_tag = next(
                    (tag["Value"] for tag in sg_data.get("Tags", []) if tag["Key"] == "Name"),
                    ""
                )

                inbound_count = len(sg_data.get('IpPermissions', []))
                outbound_count = len(sg_data.get('IpPermissionsEgress', []))

                # 更新或创建安全组记录
                sg_obj, _ = AWSSecurityGroup.objects.update_or_create(
                    group_id=group_id,
                    defaults={
                        'name': name_tag,  # 也可直接用 group_name
                        'group_name': group_name,
                        'vpc_id': vpc_id,
                        'description': description,
                        'owner': owner_id,
                        'inbound_rules_count': inbound_count,
                        'outbound_rules_count': outbound_count,
                    }
                )

                # ---- 同步Inbound/Outbound规则 ----
                # 先清除旧规则，避免重复累加
                sg_obj.rules.all().delete()

                # 处理 Inbound (IpPermissions)
                for perm in sg_data.get('IpPermissions', []):
                    ip_protocol = perm.get('IpProtocol', '')
                    from_port = perm.get('FromPort', None)
                    to_port = perm.get('ToPort', None)

                    # 可能存在多个 IPv4 / IPv6 范围
                    for ipv4_range in perm.get('IpRanges', []):
                        cidr_ipv4 = ipv4_range.get('CidrIp', '')
                        # "Description" 字段可用来存到 rule_description
                        range_desc = ipv4_range.get('Description', '')

                        # 你可以自行推断 "Type" (rule_type) 或留空
                        # 下面示例：若 ip_protocol='-1' => "All Traffic"
                        rule_type = ''
                        if ip_protocol == '-1':
                            rule_type = "All Traffic"
                        elif ip_protocol == 'tcp' and from_port == 22 and to_port == 22:
                            rule_type = "SSH"
                        # 可再加更多逻辑判断

                        AWSSecurityGroupRule.objects.create(
                            security_group=sg_obj,
                            direction='inbound',
                            ip_protocol=ip_protocol,
                            from_port=from_port,
                            to_port=to_port,
                            cidr_ipv4=cidr_ipv4,
                            # 三个新字段
                            rule_type=rule_type,
                            rule_description=range_desc  # 来自 ip_range['Description']
                        )

                    for ipv6_range in perm.get('Ipv6Ranges', []):
                        cidr_ipv6 = ipv6_range.get('CidrIpv6', '')
                        range_desc = ipv6_range.get('Description', '')

                        rule_type = ''
                        if ip_protocol == '-1':
                            rule_type = "All Traffic"

                        AWSSecurityGroupRule.objects.create(
                            security_group=sg_obj,
                            direction='inbound',
                            ip_protocol=ip_protocol,
                            from_port=from_port,
                            to_port=to_port,
                            cidr_ipv6=cidr_ipv6,
                            rule_type=rule_type,
                            rule_description=range_desc
                        )

                # 处理 Outbound (IpPermissionsEgress)
                for perm_egress in sg_data.get('IpPermissionsEgress', []):
                    ip_protocol = perm_egress.get('IpProtocol', '')
                    from_port = perm_egress.get('FromPort', None)
                    to_port = perm_egress.get('ToPort', None)

                    for ipv4_range in perm_egress.get('IpRanges', []):
                        cidr_ipv4 = ipv4_range.get('CidrIp', '')
                        range_desc = ipv4_range.get('Description', '')

                        rule_type = ''
                        if ip_protocol == '-1':
                            rule_type = "All Traffic"

                        AWSSecurityGroupRule.objects.create(
                            security_group=sg_obj,
                            direction='outbound',
                            ip_protocol=ip_protocol,
                            from_port=from_port,
                            to_port=to_port,
                            cidr_ipv4=cidr_ipv4,
                            rule_type=rule_type,
                            rule_description=range_desc
                        )

                    for ipv6_range in perm_egress.get('Ipv6Ranges', []):
                        cidr_ipv6 = ipv6_range.get('CidrIpv6', '')
                        range_desc = ipv6_range.get('Description', '')

                        rule_type = ''
                        if ip_protocol == '-1':
                            rule_type = "All Traffic"

                        AWSSecurityGroupRule.objects.create(
                            security_group=sg_obj,
                            direction='outbound',
                            ip_protocol=ip_protocol,
                            from_port=from_port,
                            to_port=to_port,
                            cidr_ipv6=cidr_ipv6,
                            rule_type=rule_type,
                            rule_description=range_desc
                        )

            print(f"Synced Security Groups & rules for region: {region}")

        except Exception as e:
            logging.error(f"Error syncing Security Groups in region {region}: {e}", exc_info=True)



@shared_task
def sync_azure_data():
    # Azure 数据同步
    credential = DefaultAzureCredential()
    subscription_id = "YOUR_AZURE_SUBSCRIPTION_ID"  # 替换为你的 Azure 订阅 ID
    network_client = NetworkManagementClient(credential, subscription_id)

    # 同步虚拟网络数据
    virtual_networks = network_client.virtual_networks.list_all()
    for virtual_network in virtual_networks:
        AzureVirtualNetwork.objects.update_or_create(
            name=virtual_network.name,
            defaults={
                'resource_group': virtual_network.id.split('/')[4],
                'location': virtual_network.location,
                'subscription': subscription_id
            }
        )

    # 同步 Vnet 数据
    vnets = network_client.virtual_networks.list_all()
    for vnet in vnets:
        address_space = ','.join(vnet.address_space.address_prefixes) if vnet.address_space else ''
        subnets = ','.join([subnet.name for subnet in vnet.subnets]) if vnet.subnets else ''
        peerings = ','.join([peering.name for peering in vnet.virtual_network_peerings]) if vnet.virtual_network_peerings else ''
        AzureVnet.objects.update_or_create(
            name=vnet.name,
            defaults={
                'address_space': address_space,
                'subnets': subnets,
                'peerings': peerings
            }
        )

    # 同步子网数据
    subnets = network_client.subnets.list_all()
    for subnet in subnets:
        route_table_name = subnet.route_table.name if subnet.route_table else ''
        secret_group = ''  # 需要根据实际情况获取安全组信息
        AzureSubnet.objects.update_or_create(
            name=subnet.name,
            defaults={
                'ipv4': subnet.address_prefix,
                'available_ips': 0,  # 需要根据实际情况计算可用 IP 数量
                'secret_group': secret_group,
                'route_table': route_table_name
            }
        )

    # 同步路由表数据
    route_tables = network_client.route_tables.list_all()
    for route_table in route_tables:
        for route in route_table.routes:
            AzureRouteTable.objects.update_or_create(
                address_prefix=route.address_prefix,
                defaults={
                    'next_hop_type': route.next_hop_type
                }
            )

