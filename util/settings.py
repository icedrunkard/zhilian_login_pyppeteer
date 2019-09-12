# coding=utf-8
# chrome
from platform import platform
from os import environ as oenviron, makedirs
from os.path import exists, abspath, dirname, join as osjoin

PLATFORM = platform().lower()
PROJECT_DIR = dirname(dirname(abspath(__file__)))

if 'windows' in PLATFORM:
    if exists(oenviron['LOCALAPPDATA'] + r'\Google\Chrome\Application\chrome.exe'):
        CHROME_EXEC_PATH = oenviron['LOCALAPPDATA'] + r'\Google\Chrome\Application\chrome.exe'
    else:
        CHROME_EXEC_PATH = r'c:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    CHROME_USER_DATA = oenviron['LOCALAPPDATA'] + r"/Google/Chrome/User Data"
    if exists(r'c:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe'):
        CHROMEDRIVER_EXEC_PATH = r'c:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe'
    else:
        CHROMEDRIVER_EXEC_PATH = oenviron['LOCALAPPDATA'] + r'\Google\Chrome\Application\chromedriver.exe'
elif 'linux' in PLATFORM:
    CHROME_EXEC_PATH = '/opt/google/chrome/google-chrome'
    CHROME_USER_DATA = osjoin(PROJECT_DIR, 'userdata')
    CHROMEDRIVER_EXEC_PATH = 'chromedriver'
else:
    raise SystemError('platform should be windows or linux')

CHROME_COOKIES_PATH = osjoin(CHROME_USER_DATA, "Default/Cookies")
ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1 (KHTML, like Gecko) CriOS/74.0.3729.169 Mobile/13B143 Safari/601.1.46'

ua_pc = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"

# 此配置只在windows中有用，linux中永远是True
# windows 中 headless 为True 时，才可以打印pdf
HEADLESS = False
BROWSERLESS_ENGINE = 'ws://browserless:3000' if 'linux' in PLATFORM else 'ws://localhost:4001'
LOCAL_ENGINE = 'local'
# PYPPETEER_ENGINE 是表示浏览器如何连接的选项，docker里browserless/chrome,本地的local
PYPPETEER_ENGINE = LOCAL_ENGINE
CONCURRENT_TASKS_OR_FUTURES = 5

USE_USERDATA = False
# IS_MOBILE 表示浏览器是模拟电脑版还是手机版
IS_MOBILE = False
# PROXY_TYPE 表示浏览器所用代理是何种类型，local表示无代理，remote表示使用代理
PROXY_TYPE = 'local'
USE_MITMPROXY = False
USER_AGENT = ua if IS_MOBILE else ua_pc

# LOG_DIR = osjoin(PROJECT_DIR,'logs')
LOG_DIR = osjoin(dirname(PROJECT_DIR), r'logs')
if not exists(LOG_DIR): makedirs(LOG_DIR)

if __name__ == '__main__':
    from os.path import exists

    if not exists(CHROME_EXEC_PATH):
        print('failed', CHROME_EXEC_PATH)
    if not exists(CHROME_COOKIES_PATH):
        print('failed', CHROME_COOKIES_PATH)
    if not exists(CHROMEDRIVER_EXEC_PATH):
        print('failed', CHROMEDRIVER_EXEC_PATH)
