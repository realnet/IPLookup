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
import json
from django.utils.timezone import now
from django.db import transaction
from config import AWS_REGIONS, aws_access_key_id, aws_secret_access_key, aws_session_token
from ip_lookup_app.models import (
    AWSEC2Instance,
    AWSVPC,
    AWSSubnet,
    AWSRouteTable,
    AWSRoute,
    AWSSecurityGroup,
    AWSSecurityGroupRule,
    AWSElasticIP,
    VPCEndpoint,
    Route53Record,
    AWSLoadBalancer,
    AWSListenerAndRule,
    AWSTargetGroup,
    AWSTarget
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

    def _get_route53_client(self):
        """获取 Route 53 客户端（带缓存）"""
        if not hasattr(self, 'route53_client'):
            self.route53_client = boto3.client(
                'route53',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token
            )
        return self.route53_client

    def _get_elbv2_client(self, region):
        """获取 ELBv2 客户端（带缓存）"""
        if region not in self.clients:
            self.clients[region] = boto3.client(
                'elbv2',
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

    def sync_elastic_ips(self):
        """同步 AWS VPC 下的弹性 IP（Elastic IP）"""
        for region in self.regions:
            ec2 = self._get_ec2_client(region)
            try:
                response = ec2.describe_addresses()
            except Exception as e:
                logging.error(f"Failed to fetch Elastic IPs for {region}: {e}", exc_info=True)
                continue

            with transaction.atomic():
                for address in response.get('Addresses', []):
                    try:
                        name_tag = self._get_resource_name(address.get("Tags", []))
                        AWSElasticIP.objects.update_or_create(
                            allocation_id=address.get("AllocationId"),
                            defaults={
                                "name": name_tag,
                                "allocated_ipv4_address": address.get("PublicIp"),
                                "ip_type": address.get("Domain"),
                                "reverse_dns_record": address.get("PublicIpv4Pool"),
                                "associated_instance_id": address.get("InstanceId"),
                                "private_ip_address": address.get("PrivateIpAddress"),
                                "association_id": address.get("AssociationId"),
                                "network_interface_owner_account_id": address.get("NetworkInterfaceOwnerId"),
                                "network_border_group": address.get("NetworkBorderGroup"),
                            }
                        )
                        logging.info(f"Synced Elastic IP: {address.get('PublicIp')}")
                    except Exception as e:
                        logging.error(f"Error processing Elastic IP {address.get('PublicIp')}: {e}", exc_info=True)


    def sync_vpc_endpoints(self):
        """同步 VPC 终端节点数据"""
        for region in self.regions:
            ec2 = self._get_ec2_client(region)
            try:
                endpoints = ec2.describe_vpc_endpoints().get('VpcEndpoints', [])
            except Exception as e:
                logging.error(f"Get {region} VPC Endpoints failure: {e}", exc_info=True)
                continue

            with transaction.atomic():
                for endpoint in endpoints:
                    try:
                        self._process_vpc_endpoint(region, endpoint)
                    except Exception as e:
                        logging.error(f"Action VPC Endpoint {endpoint.get('VpcEndpointId')} failure: {e}", exc_info=True)

    def _process_vpc_endpoint(self, region, endpoint):
        """处理单个 VPC 终端节点"""
        endpoint_id = endpoint.get("VpcEndpointId", "")
        vpc_id = endpoint.get("VpcId", "")
        service_name = endpoint.get("ServiceName", "")
        endpoint_type = endpoint.get("VpcEndpointType", "")
        status = endpoint.get("State", "")
        creation_time = endpoint.get("CreationTimestamp", None)

        # 提取标签信息
        name_tag = self._get_resource_name(endpoint.get("Tags", []), endpoint_id)

        # 获取关联的子网和网络接口
        subnet_ids = endpoint.get("SubnetIds", [])
        network_interfaces = endpoint.get("NetworkInterfaceIds", [])

        # 更新或创建 VPC Endpoint 记录
        VPCEndpoint.objects.update_or_create(
            endpoint_id=endpoint_id,
            defaults={
                "name": name_tag,
                "vpc_id": vpc_id,
                "service_name": service_name,
                "endpoint_type": endpoint_type,
                "status": status,
                "creation_time": creation_time,
                "region": region,
                "subnets": subnet_ids,
                "network_interfaces": network_interfaces
            }
        )

        logging.info(f"Sync VPC Endpoint{endpoint_id}")

    def sync_route53_records(self):
        """同步 AWS Route 53 DNS 记录"""
        try:
            route53 = self._get_route53_client()
            hosted_zones = route53.list_hosted_zones()["HostedZones"]
            for zone in hosted_zones:
                hosted_zone_id = zone["Id"].split("/")[-1]
                hosted_zone_name = zone["Name"]

                records = route53.list_resource_record_sets(HostedZoneId=hosted_zone_id)["ResourceRecordSets"]
                for record in records:
                    record_name = record["Name"]
                    record_type = record["Type"]
                    ttl = record.get("TTL")
                    alias_target = record.get("AliasTarget")
                    alias = alias_target is not None

                    # 处理 value（非别名记录）
                    values = [r["Value"] for r in record.get("ResourceRecords", [])]

                    # 处理 Routing Policy
                    if "GeoLocation" in record:
                        routing_policy = "Geolocation"
                    elif "Weight" in record:
                        routing_policy = "Weighted"
                    elif "Failover" in record:
                        routing_policy = "Failover"
                    elif "MultiValueAnswer" in record:
                        routing_policy = "MultiValue"
                    else:
                        routing_policy = "Simple"

                    Route53Record.objects.update_or_create(
                        record_name=record_name,
                        record_type=record_type,
                        hosted_zone_id=hosted_zone_id,
                        defaults={
                            "routing_policy": routing_policy,
                            "alias": alias,
                            "value": json.dumps(values),
                            "ttl": ttl,
                            "hosted_zone_name": hosted_zone_name,
                            "last_updated": now(),
                        },
                    )
            print("✅ Route 53 sync complete")
        except Exception as e:
            print(f"❌ Route 53 record sync failure: {e}")


    def sync_load_balancing(self):
        """同步 AWS Load Balancing 数据"""
        for region in self.regions:
            elbv2 = self._get_elbv2_client(region)
            try:
                load_balancers = elbv2.describe_load_balancers()
                print("connect ok")
            except Exception as e:
                logging.error(f"Failed to fetch Load Balancers for {region}: {e}", exc_info=True)
                continue

            with transaction.atomic():
                for lb in load_balancers['LoadBalancers']:
                    try:
                        self._process_load_balancer(region, elbv2, lb)
                    except Exception as e:
                        logging.error(f"Error processing Load Balancer {lb.get('LoadBalancerName')}: {e}",
                                      exc_info=True)

    def _process_load_balancer(self, region, elbv2, lb):
        """处理单个 Load Balancer"""
        lb_name = lb['LoadBalancerName']
        dns_name = lb['DNSName']
        state = lb['State']['Code']
        vpc_id = lb['VpcId']
        availability_zone = ', '.join([az['ZoneName'] for az in lb['AvailabilityZones']])
        lb_type = lb['Type']

        # 更新或创建 Load Balancer
        lb_obj, _ = AWSLoadBalancer.objects.update_or_create(
            name=lb_name,
            defaults={
                'dns_name': dns_name,
                'state': state,
                'vpc_id': vpc_id,
                'availability_zone': availability_zone,
                'type': lb_type,
                'region': region
            }
        )

        # 同步 Listener and Rules
        listeners = elbv2.describe_listeners(LoadBalancerArn=lb['LoadBalancerArn'])
        for listener in listeners['Listeners']:
            self._process_listener_and_rule(lb_obj, listener)

        # 同步 Target Groups
        target_groups = elbv2.describe_target_groups(LoadBalancerArn=lb['LoadBalancerArn'])
        for tg in target_groups['TargetGroups']:
            self._process_target_group(lb_obj, tg,elbv2)

        print(f"Synced Load Balancer: {lb_name}")

    def _process_listener_and_rule(self, lb_obj, listener):
        """处理单个 Listener and Rule"""
        protocol_port = f"{listener['Protocol']}:{listener['Port']}"
        security_policy = listener.get('SslPolicy', '')
        default_ssl_tls = listener.get('Certificates', [{}])[0].get('CertificateArn', '')

        # 初始化数据
        forward_target_group = None
        response_code = None
        response_body = None
        response_content_type = None

        for action in listener['DefaultActions']:
            action_type = action['Type']
            if action_type == "forward":
                target_group_arns = action.get("TargetGroupArn", "")
                if not target_group_arns:
                    target_groups = action.get("ForwardConfig", {}).get("TargetGroups", [])
                    if target_groups:
                        target_group_arns = target_groups[0].get("TargetGroupArn", "")

                # 获取 Target Group 名称
                target_group_obj = AWSTargetGroup.objects.filter(arn=target_group_arns).first()
                forward_target_group = target_group_obj.name if target_group_obj else "Unknown"

            elif action_type == "fixed-response":
                resp = action.get("FixedResponseConfig", {})
                response_code = resp.get("StatusCode", "N/A")
                response_body = resp.get("MessageBody", "No body")
                response_content_type = resp.get("ContentType", "text/plain")

        # 更新或创建 Listener and Rule
        AWSListenerAndRule.objects.update_or_create(
            load_balancer=lb_obj,
            protocol_port=protocol_port,
            defaults={
                'forward_target_group': forward_target_group,
                'response_code': response_code,
                'response_body': response_body,
                'response_content_type': response_content_type,
                'security_policy': security_policy,
                'default_ssl_tls': default_ssl_tls
            }
        )
        print('update listener ok')

    def _process_target_group(self, lb_obj, tg, elbv2):
        """处理单个 Target Group"""
        tg_name = tg['TargetGroupName']
        arn = tg['TargetGroupArn']
        port = tg['Port']
        protocol = tg['Protocol']
        target_type = tg['TargetType']
        vpc_id = tg['VpcId']

        # 更新或创建 Target Group
        tg_obj, _ = AWSTargetGroup.objects.update_or_create(
            name=tg_name,
            defaults={
                'arn': arn,
                'port': port,
                'protocol': protocol,
                'target_type': target_type,
                'load_balancer': lb_obj,
                'vpc_id': vpc_id
            }
        )
        print(f"Target Group {tg_name} synced")

        # 获取 Target Group 中的 Targets 状态
        target_health = elbv2.describe_target_health(TargetGroupArn=arn)
        for target in target_health['TargetHealthDescriptions']:
            ip_address = target['Target']['Id']
            port = target['Target']['Port']

            # 直接获取 AvailabilityZone
            availability_zone = target['Target'].get('AvailabilityZone', 'N/A')

            # 获取健康状态
            health_status = target.get('TargetHealth', {}).get('State', 'N/A')

            # 获取详细健康状态信息
            health_status_details = ""
            if health_status != "healthy":
                health_status_details = target.get('TargetHealth', {}).get('Description', '')

            # 保存 Target 数据
            AWSTarget.objects.update_or_create(
                target_group=tg_obj,
                ip_address=ip_address,
                port=port,
                defaults={
                    'availability_zone': availability_zone,
                    'health_status': health_status,
                    'health_status_details': health_status_details
                }
            )

        print(f"Synced Targets for Target Group: {tg_name}")
