# coding=utf-8
# python 3.7
import asyncio
import pyppeteer
import time
import warnings
from random import randint
from util.preload import *
from util.settings import *

__author__ = 'icedrunkard'
# 控制并发度
semaphore = asyncio.Semaphore(CONCURRENT_TASKS_OR_FUTURES)


class BaseClient(object):

    def __init__(self, tp_acc_id: int, username: str, password: str, mobile: str = None,
                 email: str = None, email_pwd: str = None, proxies=None):
        assert isinstance(username, str)
        assert isinstance(password, str)
        assert len(username) and len(password)
        self.tp_acc_id = tp_acc_id
        self.username = username
        self.password = password
        self.mobile = mobile
        self.email = email
        self.email_pwd = email_pwd
        self.proxies = proxies
        self.engine = PYPPETEER_ENGINE
        self.use_userdata = USE_USERDATA
        self.options = self.handled_options()

    def handled_options(self):
        args = [
            '--window-size=1200,800',
            "--disable-popup-blocking",
            '--safebrowsing-disable-download-protection',
            '--no-sandbox',
            '--disable-gpu'
        ]

        if isinstance(self.proxies, dict) and self.proxies.get('http'):
            proxy = "--proxy-server={}".format(self.proxies['http'])
            args.append(proxy)
        elif self.proxies is None:
            pass
        else:
            raise ValueError('proxies type should be dict or str')

        options = {
            'headless': True,
            'dumpio': True,
            "args": args,
            'logLevel': 'ERROR',
            'ignoreHTTPSErrors': True
        }
        if self.engine == BROWSERLESS_ENGINE:
            options['browserWSEndpoint'] = BROWSERLESS_ENGINE
        elif self.engine == LOCAL_ENGINE:
            options['executablePath'] = CHROME_EXEC_PATH
            options['headless'] = HEADLESS if 'windows' in PLATFORM else True
        else:
            raise ValueError('chrome engine err, should be ws or local')

        if self.use_userdata:
            options['userDataDir'] = CHROME_USER_DATA
        return options

    @classmethod
    async def res_from_instance(cls, username, password, email, email_pwd, proxies=None):
        instance = cls(username, password, email, email_pwd, proxies=proxies)
        res = await instance.start()
        print(res)
        return res

    async def get_browser(self):
        print(self.options)
        if self.options.get('executablePath'):
            self.browser = await pyppeteer.launch(self.options)
        elif self.options.get('browserWSEndpoint'):
            self.browser = await pyppeteer.connect(self.options)
        else:
            raise ValueError('launch options ERR')
        print(self.browser.wsEndpoint)
        self.targets = self.browser.targets()
        print(self.targets)
        # resp= await self.browser._connection.send('Network.getAllCookies', {})
        # cookiesld = resp.get('cookies', {})
        # print(cookiesld)

    async def get_page(self, page_name='page', interception=False):
        _page = await self.browser.newPage()
        exec('self.{} = _page'.format(page_name))
        page = getattr(self, page_name)

        if page_name == 'page':
            self.page = page
            for _p in await self.browser.pages():
                if _p != page:
                    await _p.close()
        await injectjs(page)
        print('is_mobile: ', IS_MOBILE)
        print(USER_AGENT)
        if interception:
            await page.setRequestInterception(True)
            page.on('request', self.request_handler)

    async def quit(self, quit_after=0):
        print('browser will be closed')
        await asyncio.sleep(quit_after)
        for p in await self.browser.pages():
            await p.close()
        if self.options.get('executablePath'):
            await self.browser.close()
            self.browser.process.terminate()
        else:
            await self.browser.disconnect()

    async def request_handler(self, *args):
        req = args[0]
        raise NotImplementedError('please specify request handler for: {}'.format(req.url))

    async def mouse_click_with_trace(self, start_coor: tuple, end_coor: tuple, start_click=False, page=None):
        """
        模拟将鼠标坐标从起点坐标移动到终点坐标
        :param start_coor:
        :param end_coor: 终点坐标会单击
        :param start_click: 起始坐标处是否要单击
        :param page: pyppeteer.page.Page
        :return:
        """
        if not page:
            page = self.page
        now_x = start_coor[0]
        now_y = start_coor[1]
        mouse_x = end_coor[0]
        mouse_y = end_coor[1]
        if start_click:
            await page.mouse.click(now_x, now_y)

        k = (mouse_y - now_y) / (mouse_x - now_x) if mouse_x != now_x else None
        b = now_y - k * now_x if k is not None else None
        steps = 100
        if k is None:  # 斜率无穷大
            dy = (mouse_y - now_y) / steps
            t0 = time.time()
            now_x = mouse_x
            while abs(now_y + dy - mouse_y) > 1 and time.time() - t0 < 5:
                now_y = int(now_y + dy)
                await page.mouse.move(now_x, now_y)
        else:
            dx = (mouse_x - now_x) / steps
            t0 = time.time()
            while abs(now_x + dx - mouse_x) > 1 and time.time() - t0 < 5:
                now_x = int(now_x + dx)
                now_y = int(k * (now_x + dx) + b)
                await page.mouse.move(now_x, now_y)
        await page.mouse.click(mouse_x, mouse_y)

    async def gen_all_cookies(self):
        try:
            resp = await self.page._client.send('Network.getAllCookies', {})
            cookiesld = resp.get('cookies', {})
            # print(cookiesld)
            return cookiesld
        except Exception as e:
            print(type(e), e)

    async def sleep(self, t):
        # 此方法阻塞，不可使用
        time.sleep(t)

    async def start(self):
        await self.get_browser()
        await self.get_page()
        pass

    def run(self):
        """实例启动"""
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(self.start())
        loop.run_until_complete(task)


async def injectjs(page):
    await page.setBypassCSP(True)
    page.setDefaultNavigationTimeout(60000)
    await page.setViewport(viewport={'width': 1200, 'height': 800, 'isMobile': IS_MOBILE})
    # webdriver
    await page.evaluateOnNewDocument(js0)
    # permission
    await page.evaluateOnNewDocument(js1)
    # language
    await page.evaluateOnNewDocument(js4)
    # languages
    await page.evaluateOnNewDocument(js5)
    # plugins
    await page.evaluateOnNewDocument(js7)
    # useragent
    await page.setUserAgent(USER_AGENT)

    if IS_MOBILE:
        # platform
        await page.evaluateOnNewDocument(js2)
        # appVersion
        await page.evaluateOnNewDocument(js3)
    else:
        # platform
        await page.evaluateOnNewDocument(js2_pc)
        # appVersion
        await page.evaluateOnNewDocument(js3_pc)


if __name__ == '__main__':
    client = BaseClient(username='1', password='2')
    client.run()
