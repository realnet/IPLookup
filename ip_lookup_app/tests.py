import os
import django
# Create your tests here.
# 设置 DJANGO_SETTINGS_MODULE 环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ip_lookup_project.settings')
# 配置 Django 设置
django.setup()

import unittest
from django.test import TestCase
from ip_lookup_app.tasks import sync_aws_data
from ip_lookup_app.models import AWSVPC, AWSSubnet, AWSRouteTable,AWSEC2Instance,AWSRoute,AWSSecurityGroup,AWSSecurityGroupRule

# AWSRouteTable.objects.all().delete()
# AWSRoute.objects.all().delete()
# AWSVPC.objects.all().delete()
# AWSSubnet.objects.all().delete()
# AWSRoute.objects.all().delete()
#
#
# class AWSSyncTestCase(TestCase):
#     def test_aws_sync(self):
#         # 记录同步前数据库中的 VPC 数量
#         # initial_vpc_count = AWSVPC.objects.count()
#         # # 记录同步前数据库中的子网数量
#         # initial_subnet_count = AWSSubnet.objects.count()
#         # print(f"initial_subnet_count ok{initial_subnet_count}")
#         # # 记录同步前数据库中的路由表数量
#         # initial_route_table_count = AWSRouteTable.objects.count()
#         # print(f"initial_route_table_count{initial_route_table_count}")
#
#         # 调用同步函数
#         sync_aws_data()
#         print("complete sync")
#         # 记录同步后数据库中的 VPC 数量
#         # final_vpc_count = AWSVPC.objects.count()
#         # # 记录同步后数据库中的子网数量
#         # final_subnet_count = AWSSubnet.objects.count()
#         # print(f'final_subnet_count{final_subnet_count}')
#         # # 记录同步后数据库中的路由表数量
#         # final_route_table_count = AWSRouteTable.objects.count()
#         # print(f'final_route_table_count{final_route_table_count}')
#
#         # 验证同步后 VPC 数量是否增加
#         # self.assertTrue(final_vpc_count >= initial_vpc_count, "VPC count did not increase after sync")
#         # # 验证同步后子网数量是否增加
#         # self.assertTrue(final_subnet_count >= initial_subnet_count, "Subnet count did not increase after sync")
#         # # 验证同步后路由表数量是否增加
#         # self.assertTrue(final_route_table_count >= initial_route_table_count, "Route table count did not increase after sync")
#
# #
if __name__ == '__main__':
    AWSEC2Instance.objects.all().delete()
    AWSSecurityGroup.objects.all().delete()
    AWSSecurityGroupRule.objects.all().delete()

    print("delete done")
    import time
    time.sleep(4)
    sync_aws_data()
    print("complete sync")
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
# # 检查 AWS 子网的 CIDR 格式
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