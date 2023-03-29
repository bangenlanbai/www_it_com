# -*- coding:utf-8  -*-
# @Time     : 2021-02-21 02:32
# @Author   : BGLB
# @Software : PyCharm

import logging
import os
import re
import sys
import threading
from logging.handlers import TimedRotatingFileHandler

import colorlog
from config import BASE_DIR, DEBUG

"""
    日志记录
    ./log/[crawer]/[spyider]/[lever.log]
    ./log/[saver]/[spyider]/[lever]

    每个模块一个日志  log - models:[crawler] - spider
    日志分级 -【爬虫脚本，数据存储，】
"""


LOG_CONFIG = {
    'LOG_COLOR_CONFIG': {
        'DEBUG': 'white',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
    },
    'LOG_ROOT_DIR': os.path.join(BASE_DIR, 'log')
}

lock = threading.Lock()


class BaseLog(object):
    LOG_CONFIG['LOG_ROOT_DIR'] = LOG_CONFIG['LOG_ROOT_DIR']
    LOG_CONFIG['LOG_COLOR_CONFIG'] = LOG_CONFIG['LOG_COLOR_CONFIG']

    def __init__(self, _module, spider=''):

        self.__log_dir = os.path.join(LOG_CONFIG['LOG_ROOT_DIR'], _module, spider)
        self.__log_name = '_'.join([_module, spider])
        self.backup_count = 20
        os.makedirs(self.__log_dir, exist_ok=True)
        if spider:
            log_format_console = '%(log_color)s%(asctime)s [p:%(process)d t:%(thread)d] [{}] [{}] [%(levelname)s] %(' \
                                 'reset)s%(blue)s%(message)s'.format(
                _module, spider)

            log_format_file = '%(asctime)s [p:%(process)d t:%(thread)d] [{}] [{}] [%(levelname)s] %(message)s'.format(
                _module, spider)

        else:
            log_format_console = '%(log_color)s%(asctime)s [p:%(process)d t:%(thread)d] [{}] [%(levelname)s] %(' \
                                 'reset)s%(blue)s%(message)s'.format(
                _module)

            log_format_file = '%(asctime)s [p:%(process)d t:%(thread)d] [{}] [%(levelname)s] %(message)s'.format(
                _module, spider)

        self.__formatter_console = colorlog.ColoredFormatter(log_format_console, log_colors=LOG_CONFIG[
            'LOG_COLOR_CONFIG'])

        self.__formatter_file = logging.Formatter(log_format_file)

        # 记录起来，用于回收
        self.__stream_console_handler = None
        self.__file_handler_dict = {}

        # 一个logger对应多个handler
        self.__logger = logging.getLogger(self.__log_name)
        if DEBUG:
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)
        self.__add_handler()

    def log_path(self, level):
        return os.path.join(self.__log_dir, logging.getLevelName(level).lower()+'.log')

    def get_logger(self):
        return self.__logger

    def __del__(self):
        try:
            self.__delete_logger_handlers()
        except Exception as e:
            raise e

    def __add_handler(self):
        """
        给logger绑定多个文件handler对应不同日志等级和一个console handler
        :return:
        """

        # 首先清空掉logger的handles，否则可能遇到日志重复的问题
        for h in self.__logger.handlers:
            self.__logger.removeHandler(h)
        self.__logger.handlers = []

        self.__add_handler_stream()

        # 每个等级一个日志文件
        for level in [logging.DEBUG, logging.INFO, logging.ERROR]:
            self.__add_handler_timed_rotate(level)

    def __delete_logger_handlers(self):
        try:
            logging.Logger.manager.loggerDict.pop(self.__log_name)
            self.__logger.removeHandler(self.__stream_console_handler)
            for h in self.__file_handler_dict:
                self.__logger.removeHandler(h)
            self.__logger.handlers = []
        except Exception as e:
            print(e)

    def __add_handler_stream(self):
        """
        :return:
        """
        self.__stream_console_handler = logging.StreamHandler(stream=sys.stdout)
        if DEBUG:
            self.__stream_console_handler.setLevel(logging.DEBUG)
        else:
            self.__stream_console_handler.setLevel(logging.INFO)
        self.__stream_console_handler.setFormatter(self.__formatter_console)

        self.__logger.addHandler(self.__stream_console_handler)

    def __add_handler_timed_rotate(self, level):
        """
        记录日志，并实现定期删除日志功能
        :return:
        """
        log_file_path = os.path.join(self.__log_dir, logging.getLevelName(level).lower()+'.log')
        handler = TimedRotatingFileHandler(filename=log_file_path, encoding='utf-8', when='D', interval=1,
                                           backupCount=self.backup_count)
        handler.suffix = '%Y%m%d.bak'
        handler.extMatch = re.compile(r'^\d{8}.log$')
        handler.setFormatter(self.__formatter_file)
        handler.setLevel(level)

        self.__logger.addHandler(handler)
        self.__file_handler_dict[level] = handler

    def __log(self, message, lever, **kwargs):
        """

        :param message:
        :param lever:
        :param kwargs:
        :return:
        """
        LEVER = {
            'CRITICAL': 50,
            'FATAL': 50,
            'ERROR': 40,
            'WARN': 30,
            'WARNING': 30,
            'INFO': 20,
            'DEBUG': 10,
            'NOTSET': 0,
        }
        lock.acquire(timeout=.5)
        self.__logger.log(LEVER[lever.upper()], message)
        if lock.locked():
            lock.release()

    def debug(self, message, module='', lineno=0, **kwargs):
        """
        :param message:
        :param module: sys._getframe().f_code.co_name
        :param lineno: sys._getframe().f_lineno
        :return:
        """
        msg = self.__format_msg(message, module, lineno)
        self.__log(msg, 'DEBUG', **kwargs)

    def info(self, message, module='', lineno=0, **kwargs):
        msg = self.__format_msg(message, module, lineno)
        self.__log(msg, 'INFO', **kwargs)

    def warn(self, message, module='', lineno=0, **kwargs):
        msg = self.__format_msg(message, module, lineno)
        self.__log(msg, 'WARNING', **kwargs)

    def warning(self, message, module='', lineno=0, **kwargs):
        self.warn(message, module='', lineno=0, **kwargs)

    def error(self, message, module='', lineno=0, **kwargs):
        msg = self.__format_msg(message, module, lineno)
        self.__log(msg, 'ERROR', **kwargs)

    def __format_msg(self, message, module, lineno):
        message = str(message)
        if module:
            msg = '{}[line:{}] {}'.format(module, lineno, message)
        else:
            msg = '{}'.format(message)
        return msg
