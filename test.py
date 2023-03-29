# -*- coding:utf-8  -*-
# @Time     : 2022/4/14 1:12
# @Author   : BGLB
# @Software : PyCharm
import traceback

import requests
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    while True:
        proxy = get_proxy()
        print(proxy)
        browser = playwright.chromium.launch(headless=False, proxy=proxy)
        context = browser.new_context()
        # Open new page
        page = context.new_page()
        try:
            page.goto("https://ip138.com/")
            real_ip = page.evaluate('return document.querySelector("body > p:nth-child(1) > a").text')
            if real_ip in proxy:
                print('可用代理： > {}'.format(real_ip))
            else:
                delete_proxy(proxy.get('server'))

        except Exception:
            print(traceback.format_exc())
            delete_proxy(proxy.get('server'))
        context.close()
        browser.close()


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


def get_proxy():
    """

    :return:
    """
    proxy = requests.get("http://127.0.0.1:5010/get/?type=https").json()
    print(proxy)
    return {'server': proxy.get('proxy', '')}


with sync_playwright() as playwright:
    run(playwright)
