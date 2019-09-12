# coding=utf-8
import asyncio
import pyppeteer

from util.client import BaseClient
from util.loggers import Logger
from tools.cracker import Cracker

logger = Logger()


class Zhilian(BaseClient):
    url = 'https://passport.zhaopin.com/org/login'

    # url = 'https://passport.bilibili.com/login'
    async def prepare_handlers(self):
        self.query={'id':self.tp_acc_id}

    async def open(self):
        await self.page.goto(self.url)
        # await self.page.waitForSelector('#login-username')
        await self.page.waitForSelector('#login__message > div > div > button')
        await self.page.click('div.k-tabs__header > div > div > a:nth-child(2)')
        await asyncio.sleep(0.5)
        get_sms_tab_class_js = 'document.querySelector("div.k-tabs__header > div > div > a:nth-child(2)").className'
        tab_class_name = await self.page.evaluate(get_sms_tab_class_js)
        assert 'is-active' in tab_class_name

    async def input_mobile(self):
        await self.page.type('div.zp-passport-widget-b-login-sms__number-box > input', self.username)
        # await self.page.type('#login-username', self.username)

    async def generate_sms(self):
        await self.page.click('button.zp-passport-widget-b-login-sms__send-code')

    async def input_sms(self, sms):
        print(self.page.url)
        input_box = await self.page.waitForSelector('div.zp-passport-widget-b-login-sms__code-box > input')
        print(input_box)

        await input_box.type(sms)
        print('input finished')
        # await self.page.type('#login-passwd',self.password)

    async def press_login(self):
        print('ready click to start')
        await self.page.waitFor(1e3)
        await self.page.click('#login__message > div > div > button')
        # await self.page.click('#geetest-wrap > ul > li.btn-box > a.btn.btn-login')

    async def crack_verify_if_needed(self):
        try:
            await self.page.waitForRequest(lambda r: 'passport.zhaopin.com/jsonp/sendSms' in r.url, {'timeout': 5})
            return True
        except pyppeteer.errors.TimeoutError:
            # js 飞一会
            cracker = Cracker(self.page,self.query,self.browser,targets=self.targets)
            # self.page = cracker.page
            return await cracker.start()

    async def start(self):
        await self.prepare_handlers()
        await self.get_browser()
        await self.get_page()
        await self.open()
        await self.input_mobile()
        await self.generate_sms()
        if not await self.crack_verify_if_needed():
            await self.quit()
            return False
        print('checkcode pass')
        sms = '222222'  # input('ready input sms')
        logger.log('sms to be loaded:', sms)
        await self.input_sms(sms)
        res = await self.press_login()
        await asyncio.sleep(10)
        print(self.page.url)
        return True

