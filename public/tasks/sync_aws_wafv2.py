#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-03-17 11:00 AM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : sync_aws_wafv2.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""

import boto3
import logging
import json

from botocore.exceptions import ClientError
from django.utils.timezone import now
from django.db import transaction
from public.tasks.init_aws_conn import InitAws
from ip_lookup_app.models import (
    AWSWAFRule,
    AWSWAFRuleGroup
)
logger = logging.getLogger(__name__)


class SyncAwsWafv2:
    """
    Sync Wafv2 rule groups and other rules
    """

    def __init__(self):
        # 创建 InitAws 实例，从而获取 wafv2 客户端
        self.waf_conn = InitAws()
        # config.py 里的 AWS_REGIONS
        self.regions = self.waf_conn.regions


    def sync_waf_rule_groups(self):
        """
        main program, 遍历region，list_rule_groups，再调用 get_rule_group
        :return:
        """
        for region in self.regions:
            # init wafv2 client
            wafv2 = self.waf_conn.get_wafv2_client(region)
            # 如果你要同步CLOUDFRONT的WAF，需要 region='us-east-1' + scope='CLOUDFRONT'
            # 这里示例REGIONAL
            scope = "REGIONAL"
            logger.info(f"Start syncing WAF Rule Groups in region={region}, scope={scope}")
            try:
                marker = None
                while True:
                    if marker:
                        response = wafv2.list_rule_groups(Scope=scope, NextMarker=marker)
                    else:
                        response = wafv2.list_rule_groups(Scope=scope)

                    rule_groups = response.get('RuleGroups', [])
                    for rg_summary in rule_groups:
                        self._process_rule_group(region, scope, wafv2, rg_summary)

                    marker = response.get('NextMarker')
                    if not marker:
                        break

            except ClientError as e:
                logger.error(f"Failed to list WAF Rule Groups for {region}: {e}", exc_info=True)
                continue

    @transaction.atomic
    def _process_rule_group(self, region, scope, wafv2, rg_summary):
        """
        获取单个 Rule Group 的详细信息并存储
        rg_summary 包含 Name, Id, Description, ARN
        """
        name = rg_summary.get('Name')
        rg_id = rg_summary.get('Id')
        description = rg_summary.get('Description', '')
        arn = rg_summary.get('ARN')

        try:
            detail_resp = wafv2.get_rule_group(Name=name, Scope=scope, Id=rg_id)
            rg_detail = detail_resp.get('RuleGroup', {})
        except ClientError as e:
            logger.error(f"Failed to get WAF Rule Group detail: {name}/{rg_id} in {region}. Error: {e}", exc_info=True)
            return

        capacity = rg_detail.get('Capacity', None)
        rules = rg_detail.get('Rules', [])  # list of dict
        # 你还可拿 rg_detail.get('VisibilityConfig'), 'LabelNamespace' 等

        # 更新或创建 AWSWAFRuleGroup
        rg_obj, created = AWSWAFRuleGroup.objects.update_or_create(
            rule_group_id=rg_id,
            defaults={
                'name': name,
                'description': description,
                'capacity': capacity,
                'scope': scope,
                'region': region,
            }
        )
        logger.info(f"{'Created' if created else 'Updated'} WAF Rule Group: {name} (ID={rg_id})")

        # 如果你想先清除旧rule再插入新的，可以这样：
        rg_obj.rules.all().delete()

        # 遍历 Rules
        for rule_dict in rules:
            self._process_single_rule(rg_obj, rule_dict)

        logger.info(f"Synced {len(rules)} rules for WAF Rule Group {name} in {region}")

    def _process_single_rule(self, rg_obj, rule_dict):
        rule_name = rule_dict.get('Name', '')
        priority = rule_dict.get('Priority', 0)
        action_dict = rule_dict.get('Action', {})
        if 'Allow' in action_dict:
            action_str = 'ALLOW'
        elif 'Block' in action_dict:
            action_str = 'BLOCK'
        elif 'Count' in action_dict:
            action_str = 'COUNT'
        else:
            action_str = 'UNKNOWN'

        statement_json = rule_dict.get('Statement', {})

        # 递归将 bytes 转成字符串
        statement_json = self._convert_bytes_in_dict(statement_json)

        AWSWAFRule.objects.create(
            rule_group=rg_obj,
            name=rule_name,
            priority=priority,
            action=action_str,
            statement_json=statement_json,
        )

    def _convert_bytes_in_dict(self, obj):
        """
        递归地将对象(可能是dict/list/bytes/...)中的所有 bytes
        转换为可序列化的字符串(如 UTF-8)。
        """
        if isinstance(obj, dict):
            return {k: self._convert_bytes_in_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_bytes_in_dict(elem) for elem in obj]
        elif isinstance(obj, bytes):
            # 方式1: 尝试用utf-8解码
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                # 如果解码失败，可以转 base64 或简单地使用repr
                import base64
                return base64.b64encode(obj).decode('ascii')
        else:
            return obj
