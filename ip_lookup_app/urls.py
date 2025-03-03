#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-02-13 3:37 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : urls.py.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""
from django.urls import path
from .views import aws_sg_data

from .views import (
    index_page,
    IPLookupView,
    AWSDataView,
    AzureDataView,
    ip_lookup_page,
    aws_page,
    azure_page,
    aws_sg_data,
    aws_sg_detail,
)

urlpatterns = [
    # 主页面：显示 indexbak.html
    path('', index_page, name='index'),

    # IP 查询相关
    # path('ip-lookup/', ip_lookup_page, name='ip-lookup-page'),       # 返回 IP 查询页面
    # path('api/ip-lookup/', IPLookupView.as_view(), name='ip-lookup'),# IP 查询API
    # 独立页面：返回 ip_lookup.html
    path('ip-lookup/', ip_lookup_page, name='ip-lookup-page'),
    # API：返回 JSON
    path('api/ip-lookup/', IPLookupView.as_view(), name='ip-lookup'),

    # AWS/Azure 数据API
    path('api/aws/<str:table>/', AWSDataView.as_view(), name='aws-data'),
    path('api/aws/security-group/', aws_sg_data, name='aws-sg'),
    path('api/aws/security-group/<str:group_id>/', aws_sg_detail, name='aws-sg-detail'),
    path('api/azure/<str:table>/', AzureDataView.as_view(), name='azure-data'),

    # AWS/Azure 页面占位
    path('aws/', aws_page, name='aws-page'),
    path('azure/', azure_page, name='azure-page'),
]