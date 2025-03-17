#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-03-17 3:19 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : sync_aws_route53.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""

import logging
import json

from django.utils.timezone import now
from public.tasks.init_aws_conn import InitAws
from ip_lookup_app.models import (
    Route53Record
)

logger = logging.getLogger(__name__)


class SyncAwsRoute53:
    """
    Sync Route53 rule groups and other rules
    """

    def __init__(self):
        # 创建 InitAws 实例，从而获取 route53 客户端
        self.dns_conn = InitAws()
        # config.py 里的 AWS_REGIONS
        self.regions = self.dns_conn.regions

    def sync_route53_records(self):
        """同步 AWS Route 53 DNS 记录"""
        try:
            route53 = self.dns_conn.get_route53_client()
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