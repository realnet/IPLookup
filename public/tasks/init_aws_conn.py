#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-03-17 11:02 AM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : init_aws_conn.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""

import boto3
from config import AWS_REGIONS, aws_access_key_id, aws_secret_access_key, aws_session_token

class InitAws:
    def __init__(self):
        self.regions = AWS_REGIONS
        self.clients = {}

    def get_ec2_client(self, region):
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

    def get_route53_client(self):
        """获取 Route 53 客户端（带缓存）"""
        if not hasattr(self, 'route53_client'):
            self.route53_client = boto3.client(
                'route53',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token
            )
        return self.route53_client

    def get_elbv2_client(self, region):
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

    def get_wafv2_client(self, region):
        """获取 ELBv2 客户端（带缓存）"""
        if region not in self.clients:
            self.clients[region] = boto3.client(
                'wafv2',
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token
            )
        return self.clients[region]

    def get_resource_name(self, tags, default=""):
        """从标签获取资源名称"""
        return next(
            (tag['Value'] for tag in tags if tag['Key'] == 'Name'),
            default
        )