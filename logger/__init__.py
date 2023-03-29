# -*- coding:utf-8  -*-
# @Time     : 2021-02-21 01:26
# @Author   : BGLB
# @Software : PyCharm

# 日志模块
import sys

from logger.base_log import BaseLog

i = __import__('logger.base_log')
sys.modules['logger.base_log'] = None
