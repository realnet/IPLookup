#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-02-13 3:36 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : serializers.py.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""
from rest_framework import serializers
from .models import AWSVPC, AWSSubnet,AWSEC2Instance, AWSSecurityGroup, AWSRouteTable, AzureVirtualNetwork, AzureVnet, AzureSubnet, AzureRouteTable

class AWSEC2InstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AWSEC2Instance
        fields = '__all__'

class AWSSecurityGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AWSSecurityGroup
        fields = '__all__'

class AWSVPCSerializer(serializers.ModelSerializer):
    class Meta:
        model = AWSVPC
        fields = '__all__'

class AWSSubnetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AWSSubnet
        fields = '__all__'

class AWSRouteTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = AWSRouteTable
        fields = '__all__'

class AzureVirtualNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AzureVirtualNetwork
        fields = '__all__'

class AzureVnetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AzureVnet
        fields = '__all__'

class AzureSubnetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AzureSubnet
        fields = '__all__'

class AzureRouteTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = AzureRouteTable
        fields = '__all__'