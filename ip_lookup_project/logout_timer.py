#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-03-10 10:32 AM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : logout_timer.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout, get_user
from django.utils.timezone import now

class AutoLogoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not hasattr(request, 'session'):
            return  # 避免 AttributeError

        request.user = get_user(request)  # 确保 request.user 存在

        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity', now().timestamp())

            # 30分钟超时（1800秒）
            if now().timestamp() - last_activity > 1800:
                logout(request)
                request.session.flush()

            request.session['last_activity'] = now().timestamp()

