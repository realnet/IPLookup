import os
#
import django
# # Create your tests here.
# # 设置 DJANGO_SETTINGS_MODULE 环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ip_lookup_project.settings')
# # 配置 Django 设置
django.setup()
#
# import unittest
# from django.test import TestCase
from public.tasks.sync_aws import SyncAws
# from config import AWS_REGIONS
# from ip_lookup_app.models import AWSVPC, AWSSubnet, AWSRouteTable,AWSEC2Instance,AWSRoute,AWSSecurityGroup,AWSSecurityGroupRule

# AWSRouteTable.objects.all().delete()
# AWSRoute.objects.all().delete()
# AWSVPC.objects.all().delete()
# AWSSubnet.objects.all().delete()
# AWSRoute.objects.all().delete()
#
#



if __name__ == '__main__':
    # AWSEC2Instance.objects.all().delete()
    # AWSVPC.objects.all().delete()
    # AWSSubnet.objects.all().delete()
    # AWSRoute.objects.all().delete()
    # AWSSecurityGroup.objects.all().delete()
    # AWSSecurityGroupRule.objects.all().delete()
    # AWSRouteTable.objects.all().delete()
    syncer = SyncAws()
    # # syncer.sync_ec2()  # 单独同步EC2
    # # syncer.sync_vpcs()  # 单独同步VPC
    # # syncer.sync_subnets() # 单独同步subnets
    # # syncer.sync_route_table() # 单独同步route_table
    # # syncer.security_group_rules() # 单独同步安全组及安全组规则
    # # syncer.sync_elastic_ips()
    # syncer.sync_vpc_endpoints()
    syncer.sync_load_balancing()



    # for region in AWS_REGIONS:
    #     sync_manager = AWSSyncManager(region)
    #     sync_manager.sync_all()
# #
# # # #



# print(AWSVPC.objects.count())  # 检查 VPC 表中的数据量
# #
# for vpc in AWSVPC.objects.all():
#     print(vpc.vpc_id, vpc.name)  # 打印所有 VPC 记录，看看是否真的插入了
#
# print(AWSVPC.objects.all().values("vpc_id", "name"))  # 直接查询数据库内容

# from django.db import connections
#
# print(connections['default'].settings_dict)  # 打印 Django 连接的数据库信息


# from django.db import connection
#
# # 事务提交
# connection.commit()


#在 sync_aws_data() 里，打印数据库配置信息：
# from django.conf import settings
# import json
#
# print("Database settings:", json.dumps(settings.DATABASES, indent=4))


# print(AWSVPC.objects.all())  # 看看数据库里是否真的没有数据
#
# from django.conf import settings
#
# print("Celery DB Engine:", settings.DATABASES['default']['ENGINE'])


# # 手动创建一个 VPC 实例
# vpc = AWSVPC(
#     name='Test VPC',
#     vpc_id='vpc-12345678',
#     ipv4_cidr='10.0.0.0/16',
#     main_route_table='rtb-12345678',
#     main_network_acl='acl-12345678',
#     owner_id='123456789012'
# )
# vpc.save()
#
# print(AWSVPC.objects.all())


#
# from ip_lookup_app.models import AWSSubnet, AzureSubnet
# import ipaddress
#
# # 检查 tasks 子网的 CIDR 格式
# for subnet in AWSSubnet.objects.all():
#     try:
#         ipaddress.ip_network(subnet.ipv4_cidr, strict=False)
#     except ValueError:
#         print(f"Invalid CIDR in AWSSubnet: {subnet.ipv4_cidr}")

# # 检查 Azure 子网的 CIDR 格式
# for subnet in AzureSubnet.objects.all():
#     try:
#         ipaddress.ip_network(subnet.ipv4, strict=False)
#     except ValueError:
#         print(f"Invalid CIDR in AzureSubnet: {subnet.ipv4}")