#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-03-03 4:08 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : tasks.py.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""
import logging
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from public.tasks.sync_aws import SyncAws

# 配置日志
logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3, default_retry_delay=60)
def sync_aws_data(self):
    """
    Celery 任务：同步 AWS 资源数据
    1. EC2 实例
    2. VPC
    3. 子网
    4. 路由表
    5. 安全组及规则
    自动重试 3 次，每次间隔 60 秒
    """
    sync_aws = SyncAws()

    try:
        logger.info("Starting AWS EC2 sync...")
        sync_aws.sync_ec2()
        logger.info("AWS EC2 sync complete.")

        logger.info("Starting AWS VPC sync...")
        sync_aws.sync_vpcs()
        logger.info("AWS VPC sync complete.")

        logger.info("Starting AWS Subnets sync...")
        sync_aws.sync_subnets()
        logger.info("AWS Subnets sync complete.")

        logger.info("Starting AWS Route Tables sync...")
        sync_aws.sync_route_table()
        logger.info("AWS Route Tables sync complete.")

        logger.info("Starting AWS Security Groups sync...")
        sync_aws.security_group_rules()
        logger.info("AWS Security Groups sync complete.")

        logger.info("Starting AWS Elastic IP sync...")
        sync_aws.sync_elastic_ips()  # 新增同步 EIP
        logger.info("AWS Elastic IP sync complete.")

        logger.info("Starting AWS Endpoint sync...")
        sync_aws.sync_vpc_endpoints()  # 新增同步 EIP
        logger.info("AWS Endpoint sync complete.")

        logger.info("Starting AWS route53 sync...")
        sync_aws.sync_route53_records()  # 新增同步 route53
        logger.info("AWS route53 sync complete.")

    except MaxRetriesExceededError:
        logger.error("Max retries reached for sync_aws_data task.", exc_info=True)
    except Exception as e:
        logger.error(f"Error in sync_aws_data task: {e}", exc_info=True)
        self.retry(exc=e)  # 触发重试
