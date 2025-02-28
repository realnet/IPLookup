#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-02-28 3:10 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : disable_trace_track.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""
from django.http import HttpResponseNotAllowed

def disable_trace_track_middleware(get_response):
    def middleware(request):
        print("HTTP method =>", request.method)  # Debug
        if request.method in ('TRACE','TRACK','PATCH','OPTIONS'):
            from django.http import HttpResponseNotAllowed
            return HttpResponseNotAllowed(['GET','POST','PUT','DELETE'])
        return get_response(request)
    return middleware

