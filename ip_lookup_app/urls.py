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
from .views import user_login, user_logout
from django.contrib.auth.views import LogoutView



from .views import (
    index_page,
    IPLookupView,
    AWSDataView,
    AzureDataView,
    ip_lookup_page,
    WAFRuleGroupView,
    aws_page,
    azure_page,
    aws_sg_data,
    aws_sg_detail,
    get_target_groups,
    get_target_group_detail
)



urlpatterns = [
    # 主页面：显示 index.html
    path('', index_page, name='index'),

    # API：返回 JSON
    path('api/ip-lookup/', IPLookupView.as_view(), name='ip-lookup'),

    # 让target group的查询比AWSDataView更早
    path('api/aws/target-groups/<int:pk>/', get_target_group_detail, name='target_group_detail'),
    path('api/aws/target-groups/', get_target_groups, name='target_groups'),

    # ---------------------------
    # 新增：WAF路由
    # ---------------------------
    path('api/aws/waf-rule-groups/', WAFRuleGroupView.as_view(), name='waf-rule-groups'),

    # tasks/Azure 数据API
    path('api/aws/<str:table>/', AWSDataView.as_view(), name='aws-data'),
    path('api/aws/security-group/', aws_sg_data, name='aws-sg'),
    path('api/aws/security-group/<str:group_id>/', aws_sg_detail, name='aws-sg-detail'),
    path('api/azure/<str:table>/', AzureDataView.as_view(), name='azure-data'),

    # tasks/Azure 页面占位
    path('aws/', aws_page, name='aws-page'),
    path('azure/', azure_page, name='azure-page'),


    #登录配置
    path("login/", user_login, name="login"),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),



]
