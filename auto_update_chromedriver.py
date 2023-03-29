import os
import stat
import win32api
import config
import requests
import zipfile


def get_version_via_com(file_name):
    try:
        info = win32api.GetFileVersionInfo(file_name, os.sep)
        ms = info['FileVersionMS']
        ls = info['FileVersionLS']
        version = '%d.%d.%d.%d' % (win32api.HIWORD(ms), win32api.LOWORD(ms), win32api.HIWORD(ls), win32api.LOWORD(ls))
        return version
    except:
        return ''


def get_chrome_version(is_windows=True):
    if is_windows:

        # path = os.environ['LOCALAPPDATA']+r'\Google\Chrome\Application\chrome.exe'
        path1 = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        path2 = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
        plist = [ path1, path2]
        for p in plist:
            v = get_version_via_com(p)
            if v:
                return '.'.join(v.split('.')[:-1])
        return ''
    else:
        version = os.popen("google-chrome-stable --version").read()
        version_num = ".".join(str(version.split(' ')[2]).split('.')[:-1])
        return version_num


def get_driver_version(driver_path: str):
    """
        获取driver_version
    :return:
    """
    if not os.path.exists(driver_path):
        os.makedirs(os.sep.join(driver_path.split(os.sep)[:-1]), exist_ok=True)
        return "0.0.0"
    try:
        if not driver_path.endswith('exe'):
            """linux 系统更改文件权限"""
            os.chmod(driver_path, stat.S_IXGRP)

        outstd = os.popen('{} --version'.format(driver_path)).read()
        # print(outstd)
        version = outstd.split(' ')[1]
        version = ".".join(version.split(".")[:-1])
        return version
    except Exception as e:
        return "0.0.0"


def download_driver(chrome_version: str, driver_dir: str, is_windows: bool):
    """
        下载与chrome 匹配的driver
        
    :param chrome_version:
    :param driver_dir:
    :param is_windows:
    :return: bool
    """
    base_url = 'http://npm.taobao.org/mirrors/chromedriver/'
    url = "{}LATEST_RELEASE_{}".format(base_url, chrome_version)
    last_version = requests.get(url).text
    # 下载chromedriver
    if is_windows:
        download_url = "{}{}/chromedriver_win32.zip".format(base_url, last_version)
    else:
        download_url = "{}{}/chromedriver_linux64.zip".format(base_url, last_version)
    file = requests.get(download_url)
    chromedriver_zip_path = os.path.join(driver_dir, 'chromedriver.zip')

    # 保存zip
    with open(chromedriver_zip_path, 'wb') as zip_file:
        zip_file.write(file.content)

    # 解压
    with zipfile.ZipFile(chromedriver_zip_path, 'r') as f:
        for file in f.namelist():
            f.extract(file, driver_dir)
    # print(chromedriver_zip_path)
    os.remove(chromedriver_zip_path)
    if not is_windows:
        chromeDriver = os.path.join(driver_dir, 'chromedriver')
        os.chmod(chromeDriver, stat.S_IXGRP)
