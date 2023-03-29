import os

DEBUG = True
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVER_PATH = os.path.join(BASE_DIR, 'lib', 'chromedriver.exe')
BROWSER_PRE_START_JS = os.path.join(BASE_DIR, 'lib', 'stealth.min.js')
brower_count = 1
