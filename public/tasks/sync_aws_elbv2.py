#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-03-17 3:08 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : sync_aws_elbv2.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""

import logging
from django.db import transaction
from public.tasks.init_aws_conn import InitAws
from ip_lookup_app.models import (
    AWSLoadBalancer,
    AWSListenerAndRule,
    AWSTargetGroup,
    AWSTarget
)

logger = logging.getLogger(__name__)


class SyncAwsElbv2:
    """
    Sync elbv2 rule groups and other rules
    """

    def __init__(self):
        # 创建 InitAws 实例，从而获取 elbv2 客户端
        self.elb_conn = InitAws()
        # config.py 里的 AWS_REGIONS
        self.regions = self.elb_conn.regions


    def sync_load_balancing(self):
        """同步 AWS Load Balancing 数据"""
        for region in self.regions:
            elbv2 = self.elb_conn.get_elbv2_client(region)
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