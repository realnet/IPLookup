#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-02-13 3:36 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : routers.py.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""
class DatabaseRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'ip_lookup_app':
            if 'azure' in model._meta.db_table:
                return 'azure'
            else:
                return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'ip_lookup_app':
            if 'azure' in model._meta.db_table:
                return 'azure'
            else:
                return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'ip_lookup_app' and obj2._meta.app_label == 'ip_lookup_app':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'ip_lookup_app':
            if 'azure' in model_name:
                return db == 'azure'
            else:
                return db == 'default'
        return None