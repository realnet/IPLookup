#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-02-28 3:13 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : firewall.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""
# pseudo code
from ipaddress import ip_address, ip_network
from django.http import HttpResponseForbidden

WHITELIST = [ip_network('10.41.0.0/16'), ip_network('127.0.0.1/32')]

def ip_whitelist_middleware(get_response):
    def middleware(request):
        remote_ip = request.META.get('REMOTE_ADDR')
        if remote_ip:
            addr = ip_address(remote_ip)
            # 检查是否在任何一个白名单网段
            if not any(addr in net for net in WHITELIST):
                return HttpResponseForbidden("Forbidden")
        return get_response(request)
    return middleware
