#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-03-06 1:57 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : aws.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""

import boto3
from config import AWS_REGIONS, aws_access_key_id, aws_secret_access_key, aws_session_token

# 用于缓存 EC2 客户端
ec2_clients = {}
# 用于缓存 Route 53 客户端
route53_client = None


def get_ec2_client(region):
    """获取区域 EC2 客户端（带缓存）"""
    global ec2_clients
    if region not in ec2_clients:
        ec2_clients[region] = boto3.client(
            'ec2',
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )
    return ec2_clients[region]


def get_route53_client():
    """获取 Route 53 客户端（带缓存）"""
    global route53_client
    if route53_client is None:
        route53_client = boto3.client(
            'route53',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )
    return route53_client


def _get_resource_name(tags, default=""):
    """从标签获取资源名称"""
    return next(
        (tag['Value'] for tag in tags if tag['Key'] == 'Name'),
        default
    )
