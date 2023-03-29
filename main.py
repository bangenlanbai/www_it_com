# -*- coding:utf-8  -*-
# @Time     : 2022/4/12 0:12
# @Author   : BGLB
# @Software : PyCharm
import os
import time
from threading import Thread
from config import brower_count, BASE_DIR, DRIVER_PATH
from logger import BaseLog
from utils import file_utils
import shutil
from spider import TiSpider

logger = BaseLog('main')


def open_remote_brower(remote_port):
    """
        打开 远程调试浏览器
    """

    user_data_path = os.path.join(BASE_DIR, 'remote_user_data', f'{remote_port}')
    os.makedirs(user_data_path, exist_ok=True)
    logger.info(f'开启本地浏览器:【{remote_port}】')
    os.popen(f'chrome --remote-debugging-port={remote_port} --user-data-dir="{user_data_path}"')


def task_start(remote_port, product):
    def take_over_brower():
        """
            接管浏览器
        """
        open_remote_brower(remote_port)
        remote_url = f'127.0.0.1:{remote_port}'
        spider = TiSpider(DRIVER_PATH, {}, remote_url)
        spider.run_test(product)
    t = Thread(target=take_over_brower)
    t.start()


def main(product: list):
    clear_user_data()
    remote_port = 9221
    group = len(product)//brower_count
    for i in range(brower_count):

        if i+1 == brower_count:
            product_item = product[group*i: -1]
        else:
            product_item = product[group*i: group*(i+1)]
        logger.info(f'第{i}组: {product_item}')
        task_start(remote_port+i, product_item)
        time.sleep(2)


def clear_user_data():
    logger.info('清理用户数据')
    remote_user_data = os.path.join(BASE_DIR, 'remote_user_data')
    if os.path.exists(remote_user_data):
        shutil.rmtree(remote_user_data)
    os.makedirs(remote_user_data, exist_ok=True)


if __name__ == '__main__':
    product_file = os.path.join(BASE_DIR, 'product.csv')
    product = file_utils.get_content(product_file)
    main(product)
