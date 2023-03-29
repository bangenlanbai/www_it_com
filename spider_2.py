# -*- coding:utf-8  -*-
# @Time     : 2022/4/13 23:14
# @Author   : BGLB
# @Software : PyCharm
import os
import time
import traceback

import requests
from playwright.sync_api import Playwright, sync_playwright, expect

import config
from logger import BaseLog
from utils import file_utils


class TiSpiderWithPlaywright(object):
    """
        TiSpiderWithPlaywright
    """
    def __init__(self):
        """

        """
        self.browser = None
        self.context = None
        self.log = BaseLog('play')

    def init_context(self, playwright: Playwright) -> None:
        self.browser = playwright.chromium.launch(headless=False, proxy=self.get_proxy(), )
        self.context = self.browser.new_context()
        self.context.add_init_script(config.BROWSER_PRE_START_JS)

    def open_url(self, url):
        """
            打开url
        :return:
        """
        page = self.context.new_page()
        # Go to https://www.ti.com/store/ti/en/p/product/?p=BQ24092DGQR
        page.goto(url)
        # Click text=Ship to and currency selection
        page.locator("text=Ship to and currency selection").click()
        # Press Escape
        page.locator(
            "div[role=\"dialog\"]:has-text(\"Ship to and currency selection Please select your region and currency to update \")").press(
            "Escape")
        page.goto("https://www.ti.com/store/ti/en/p/product/?p=BQ24297RGER")
        # Click text=Ship to and currency selection
        page.locator("text=Ship to and currency selection").click()
        # Press Escape
        page.locator(
            "div[role=\"dialog\"]:has-text(\"Ship to and currency selection Please select your region and currency to update \")").press(
            "Escape")

    def is_can_buy(self, page):
        """
            判断是否能购买

        :return:
            -1 错误
             0 可以购买
             1 缺货
        """
        try:
            get_product_status = """return document.querySelector("#addToCartForm > div:nth-child(5) > span.out_of_stock_pdp > div.statusLine.u-margin-bottom-s > div").textContent;"""
            while True:
                try:
                    product_status = page.eavlvalue(get_product_status)
                except Exception:
                    product_status = ''
                if not product_status:
                    time.sleep(2)
                    continue
                if 'Out of stock' in product_status:
                    return 1
                else:
                    return 0

        except Exception:
            self.log.error({traceback.format_exc()})
            return -1

    def get_proxy(self):
        """

        :return:
        """
        proxy = requests.get("http://127.0.0.1:5010/get/?type=https").json().get('proxy', '')

        return {'server': proxy}

    def main(self, prodcut:list, browser_count=1, browser_page_count=10, ) -> None:
        for i in range(browser_count):
            with sync_playwright() as playwright:
                self.init_context(playwright)
                for item in prodcut:
                    url = f'https://www.ti.com/store/ti/en/p/product/?p{item["name"]}'
                    self.open_url(url)


if __name__ == '__main__':
    product_file = os.path.join(config.BASE_DIR, 'product.csv')
    product = file_utils.get_content(product_file)
    browser_page_count: int = 10
    browser_count: int = 5
    spider = TiSpiderWithPlaywright()
    spider.main(product[:10], )
