import os
import time
import traceback

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from auto_update_chromedriver import download_driver, get_chrome_version, get_driver_version
import config
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from utils import file_utils
from logger import BaseLog



class TiSpider(object):
    """
        www.ti.com
    """

    driver: webdriver = None

    def __init__(self, driver_path, user_info: dict, driver_url: str=None) -> None:
        self.driver_path = driver_path
        self.login_id = user_info.get('login_id', '')
        self.password = user_info.get('password', '')
        self.remote_driver_url = driver_url
        self.log = BaseLog(self.remote_driver_url.replace(':', '_'))
        self.retry_count = 3

    def driver_init(self, proxy: dict = None, is_phone=False):
        """

        :param proxy:
        :param is_phone:
        :return:
        """
        if self.driver:
            return
        options = webdriver.ChromeOptions()
        pres = {'credentials_enable_service': False, 'profile.password_manager_enabled': False}
        options.add_argument('--disable-gpu')
        options.add_argument("--disable-blink-features=AutomationControlled")  # 88版本过检测
        options.add_argument('lang=zh_CN.UTF-8')  # 设置语言
        options.add_argument('--disable-infobars')  # 除去“正受到自动测试软件的控制”
        # options.add_argument("--auto-open-devtools-for-tabs") # 相当于 F12
        # options.add_extension('')  # 添加插件
        if is_phone:
            options.add_experimental_option('mobileEmulation', {'deviceName': 'iPhone X'})  # 模拟iPhone X浏览
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])  # 过检测
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('prefs', pres)  # 禁用保存密码弹框

        # 添加代理
        if proxy:
            options.add_argument("--proxy-server=http://{}:{}".format(proxy['ip'], proxy['port']))

        if not self.driver_path.endswith('exe'):
            # options.add_argument('--headless')  # 浏览器不提供可视化页面. 无界面 linux 下如果系统不支持可视化不加这条会启动失败
            options.add_argument('--no-sandbox')

        self.log.info(f'driver_path: {self.driver_path}')

        self.driver = webdriver.Chrome(service=Service(executable_path=self.driver_path), options=options)
        self.log.info('执行相关js')
        # 屏蔽浏览器中的window.navigator.webdriver = true
        with open(config.BROWSER_PRE_START_JS) as f:
            source_js = f.read()
        # self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
        #                             {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"})
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": source_js
        })
        self.driver.maximize_window()

    def remote_driver(self):
        """
            接管本地浏览器
        """
        options = webdriver.ChromeOptions()
        self.log.info(self.remote_driver_url)
        options.add_experimental_option("debuggerAddress", self.remote_driver_url)
        with open(config.BROWSER_PRE_START_JS) as f:
            source_js = f.read()
        self.driver = webdriver.Chrome(service=Service(executable_path=self.driver_path), options=options)
        time.sleep(2)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": source_js
        })

    def check_update_driver(self) -> bool:
        """
            检查升级driver
        :return:
        """
        is_windows = self.driver_path.endswith('exe')
        chrome_version = get_chrome_version(is_windows)

        driver_version = get_driver_version(self.driver_path)
        self.log.info('chrome_version:{}, driver_version:{}'.format(chrome_version, driver_version))
        if chrome_version == driver_version:
            # self.log.info('无需升级')
            return True
        try:
            driver_dir = os.sep.join(self.driver_path.split(os.sep)[:-1])

            self.log.info('开始升级chromedriver: 【{} -> {}】'.format(driver_version, chrome_version))
            download_driver(chrome_version, driver_dir, is_windows)
            driver_version = get_driver_version(self.driver_path)
            self.log.info('chromedriver下载安装成功,当前版本【{}】'.format(driver_version))
            if driver_version == chrome_version:
                return True
            else:
                return False
        except Exception as e:
            self.log.info('chromedriver:【{}】下载失败: {}'.format(chrome_version, e))
            return False

    def login(self, login_id, password) -> bool:
        """
            网站登录        
        """

        self.driver.get("https://www.ti.com/secure-link-forward/?gotoUrl=https%3A%2F%2Fwww.ti.com%2F")
        time.sleep(3)
        self.driver.find_element(by=By.XPATH, value='//*[@id="username-screen"]/div[2]/input').send_keys(login_id)
        time.sleep(2)
        self.driver.find_element(by=By.XPATH, value='//*[@id="nextbutton"]').click()
        time.sleep(1)
        self.driver.find_element(by=By.XPATH, value='//*[@id="password"]/input').send_keys(password)
        time.sleep(1)
        self.driver.find_element(by=By.XPATH, value='//*[@id="loginbutton"]').click()
        time.sleep(2)

        if 'The email address and/or password you' in self.driver.page_source:
            self.log.info('密码错误')
            return False

        return True

    def search(self, shop_name):
        """
            搜索 
        """
        pass

    def search_item(self, shop_name):
        """
            搜索每一项
            暂时用不到
        """
        search_input = (By.XPATH, '//*[@id="searchboxheader"]/div[1]/div/div/div[1]/input')
        try:
            search_input_ele = self.driver.find_element(*search_input)
            if search_input_ele:
                search_input_ele.send_keys(shop_name)
        except NoSuchElementException:
            self.log.info('未找到 搜索框')

        try:
            ele_options = (By.XPATH, '//*[@class="search-query-snapshots"]')

            ele = WebDriverWait(self.driver, 3, 0.5).until(EC.presence_of_element_located(ele_options))

            search_result = ele.find_elements(by=By.XPATH, value='//*[@id="coveo-list-layout CoveoResult"]')

            if len(search_result) > 0:
                self.log.info("获取搜索结果成功：".format(len(search_result)))
                return search_result

        except TimeoutException:
            time.sleep(1)

    def open_new_page(self, url):
        """
            打开新标签页
        :param url:
        :return:
        """
        js_code = "window.open('{}','_blank');"
        self.driver.execute_script(js_code.format(url))
        time.sleep(2)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        time.sleep(3)

    def get_item_shop_stock(self, shop_name):
        """
            获取商品库存
        """
        url = f'https://www.ti.com/store/ti/en/p/product/?p={shop_name}'
        self.open_new_page(url)

        if 'It looks like we’ve encountered some resistance' in self.driver.page_source:
            self.log.error(f'{shop_name} 产品页面错误')
            return False

        if 'Access Denied' in self.driver.page_source:
            self.log.info('请求被拒')
            current_count = 0
            while 'Access Denied' in self.driver.page_source:
                self.log.info('等待 10s 后刷新')
                current_count += 1
                time.sleep(10)
                self.log.info(f"第{current_count}次刷新")
                self.driver.refresh()
        # try:
        #     ele = (By.XPATH, '/html/body/main/div[2]/div[6]/div/div')
        #     self.log.info('开始检测弹出框')
        #     wait = WebDriverWait(self.driver, 3, 1).until(EC.visibility_of_element_located(ele))
        #
        #     self.log.info('wait 结束')
        #     alert_ele = self.driver.find_element(*ele)
        #
        #     js_code = 'document.querySelector("#target-modal-cart-page-empty-shipto-notification > div").style.display = "none";document.querySelector("body > div.modal-backdrop.fade.in").className = "";'
        #     if EC.visibility_of_element_located(ele):
        #         self.log.info('js 去除弹出框')
        #         self.driver.execute_script(js_code)
        # except Exception as e:
        #     self.log.info(f"{e}")
        #     self.log.info('弹出框 检测超时')
        try:
            get_product_status = """return document.querySelector("#addToCartForm > div:nth-child(5) > span.out_of_stock_pdp > div.statusLine.u-margin-bottom-s > div").textContent;"""
            while True:
                try:
                    product_status = self.driver.execute_script(get_product_status)
                except Exception:
                    product_status = ''
                if not product_status:
                    time.sleep(2)
                    continue
                if 'Out of stock' in product_status:
                    self.log.info(f'【{shop_name}】 缺货')
                    return False
                else:
                    self.log.info(f'【{shop_name}】{product_status}')
                    return True

        except Exception:
            self.log.error(f"{traceback.format_exc()}")
            return False

    def buy_shop(self, shop_name):
        self.log.info(f"进行购买: {shop_name}")
        pass

    def is_login(self):
        """

        """

        self.driver.get("https://www.ti.com/secure-link-forward/?gotoUrl=https%3A%2F%2Fwww.ti.com%2F")
        time.sleep(2)
        if 'login-check' in self.driver.current_url:
            return True
        else:
            return False

    def run(self, shop_list):
        """
            爬虫主程序
        """
        try:
            self.check_update_driver()

            if not self.driver:
                self.log.info('开始接管远程浏览器 driver ')
                self.remote_driver()
            shop_list_count = len(shop_list)
            for i, item in enumerate(shop_list):
                self.log.info(f"第 {i}/{shop_list_count} 个 shop: {item}")
                result = self.get_item_shop_stock(item['name'])
                self.log.info(result)
                if result:
                    self.log.info('{} 有货 可以购买了'.format(item['name']))
                    self.logger_can_buy_shop(item['name'])
        except Exception:
            self.log.error(traceback.format_exc())
        finally:
            self.close_some_server()

    def run_test(self, shop_list):
        """

        :param shop_list:
        :return:
        """
        self.check_update_driver()

        if not self.driver:
            self.log.info('开始接管远程浏览器 driver ')
            self.remote_driver()
        shop_list_count = len(shop_list)
        for i, item in enumerate(shop_list):
            self.log.info(f"第 {i}/{shop_list_count} 个 shop: {item}")
            url = 'https://www.ti.com/store/ti/en/p/product/?p={}'.format(item['name'])
            self.open_new_page(url)

    def close_some_server(self):
        """
            关闭浏览器
        :return:
        """
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                self.log.error('close driver 失败')

    def change_proxy(self):
        """
            切换代理

        """
        proxy = self.get_proxy().get("proxy")

        pass

    def get_proxy(self):
        return requests.get("http://127.0.0.1:5010/pop/").json()

    def pop_proxy(self):
        return requests.get("http://127.0.0.1:5010/pop/").json()

    def logger_can_buy_shop(self, shop_name):
        """
            记录可以买的商品
        """
        with open(self.remote_driver_url.replace(':', '_'), mode='w', encoding='utf8') as f:
            f.write(shop_name)



if __name__ == '__main__':
    user_info = {
        "login_id": "zhanghongwei@pandawm.com",
        "password": "SZpanda@0o.o0wm"
    }

    product_file = os.path.join(config.BASE_DIR, 'product.csv')
    product = file_utils.get_content(product_file)
    spider = TiSpider(config.DRIVER_PATH, user_info, '127.0.0.1:9221')
    spider.run_test(product)
