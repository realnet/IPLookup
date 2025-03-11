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
from .models import AWSVPC, AWSSubnet,AWSEC2Instance,AWSLoadBalancer,AWSTargetGroup,AWSListenerAndRule, AWSTarget,Route53Record,AWSSecurityGroup, AWSElasticIP, AWSRouteTable, VPCEndpoint,AzureVirtualNetwork, AzureVnet, AzureSubnet, AzureRouteTable

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

class AWSElasticIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = AWSElasticIP
        fields = '__all__'

class AWSVpcEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = VPCEndpoint
        fields = '__all__'

class AWSRoute53RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route53Record
        fields = '__all__'

class AWSLoadBalancerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AWSLoadBalancer
        fields = '__all__'

class AWSTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AWSTarget
        fields = ['ip_address', 'port', 'availability_zone', 'health_status', 'health_status_details']

class AWSTargetGroupSerializer(serializers.ModelSerializer):
    load_balancer_name = serializers.CharField(source='load_balancer.name', read_only=True)
    class Meta:
        model = AWSTargetGroup
        fields = ['name', 'port', 'protocol', 'target_type', 'vpc_id','load_balancer_name']

class AWSListenerAndRuleSerializer(serializers.ModelSerializer):
    load_balancer_name = serializers.CharField(source='load_balancer.name', read_only=True)

    class Meta:
        model = AWSListenerAndRule
        fields = ['id', 'protocol_port', 'forward_target_group', 'load_balancer_name', 'response_code', 'response_body', 'response_content_type', 'security_policy', 'default_ssl_tls']


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