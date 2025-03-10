#!/bin/env python
# -*- coding:utf-8 -*-
"""
#---------------------------
# @Time    :2025-03-06 1:52 PM
# @Author  : realnet
# @Email   : zhangxiongganghx@gmail.com
# @Company ：Kyndryl
# @File    : redis_utils.py.py
# @Porject : core
# @Software: PyCharm
#---------------------------
"""
# ip_lookup_app/redis_utils.py
import json
import redis

REDIS_URL = 'redis://10.36.120.110:6379/0'
r = redis.Redis.from_url(REDIS_URL)

TASK_LIST_KEY = 'route53:tasks'  # 存放所有任务的列表

def create_task_in_redis(task_id, old_data, new_data):
    """
    将任务写入Redis, 初始状态pending
    """
    task_data = {
        'task_id': task_id,
        'status': 'pending',
        'old_data': old_data,
        'new_data': new_data
    }
    # 将具体任务数据存为一个key
    task_key = f"route53:task:{task_id}"
    r.set(task_key, json.dumps(task_data))
    # 把任务ID放到列表里方便遍历
    r.lpush(TASK_LIST_KEY, task_key)

def get_all_tasks():
    """
    获取所有任务信息
    """
    task_keys = r.lrange(TASK_LIST_KEY, 0, -1)
    tasks = []
    for tk in task_keys:
        data = r.get(tk)
        if data:
            tasks.append(json.loads(data))
    return tasks

def get_task(task_id):
    """
    根据task_id获取单个任务
    """
    task_key = f"route53:task:{task_id}"
    data = r.get(task_key)
    if data:
        return json.loads(data)
    return None

def update_task_status(task_id, status):
    """
    更新任务状态
    """
    task_key = f"route53:task:{task_id}"
    data = r.get(task_key)
    if not data:
        return
    task_data = json.loads(data)
    task_data['status'] = status
    r.set(task_key, json.dumps(task_data))
