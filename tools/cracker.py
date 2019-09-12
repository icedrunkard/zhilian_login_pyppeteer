# coding=utf-8
import asyncio
import re
from io import BytesIO
from PIL import Image
from util.loggers import Logger

logger = Logger()


class Cracker:

    def __init__(self, page, query,browser=None,targets=None):
        self.page = page
        self.query = query
        self.browser = browser
        self.targets = targets

    @classmethod
    def from_handler(cls, page, query):
        return cls(page, query)

    async def get_image(self):
        """
        获取验证码图片
        :return: 验证码图片
        """
        img_selector = 'div.geetest_widget > div > a > div.geetest_canvas_img.geetest_absolute'
        img = await self.page.waitForSelector(img_selector)
        _screenshot = await img.screenshot()
        return _screenshot

    async def delete_style(self):
        """
        删除无缺口图片的style属性，执行js脚本，屏幕显示无缺口图片
        :return: None
        """
        # for i in range(4):
        #     js = 'document.querySelectorAll("canvas")[%d].style'%i
        #     try:
        #          style = await self.page.evaluate(js)
        #          if style:
        #              js = 'document.querySelectorAll("canvas")[%d].style=""' % i
        #              await self.page.evaluate(js)
        #     except:
        #         pass
        js = 'document.querySelector("div.geetest_canvas_img.geetest_absolute > canvas").style=""'
        await self.page.evaluate(js)
        await asyncio.sleep(1)

    async def get_slider(self):
        """
        获取滑块
        :return:滑块对象
        """
        slider = await self.page.querySelector('div.geetest_slider_button')
        return slider

    def is_pixel_equal(self, img_1, img_2, x, y):
        """
        判断两个像素是否相同
        :param img_1: 带缺口图片
        :param img_2: 不带缺口图片
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pix_1 = img_1.load()[x, y]
        pix_2 = img_2.load()[x, y]
        threshold = 60  # 阀值
        if abs(pix_1[0] - pix_2[0]) < threshold \
                and abs(pix_1[1] - pix_2[1]) < threshold \
                and abs(pix_1[2] - pix_2[2]) < threshold:
            return True
        else:
            return False

    def get_gap(self, img_1, img_2):
        """
        获取缺口偏移量
        :param img_1: 带缺口图片
        :param img_2: 不带缺口图片
        :return: 缺口位置
        """
        distance = 60
        for i in range(distance, img_2.size[0]):
            for j in range(img_2.size[1]):
                if not self.is_pixel_equal(img_1, img_2, i, j):
                    distance = i
                    return distance
        print(img_2.size[0], img_2.size[1])
        return distance

    def get_tracks(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        over_move_distance = 11  # 滑超过的一段距离
        tracks = []  # 移动轨迹
        current = 0  # 当前位移
        mid = distance * 4 / 5  # 减速阀值
        t = 0.2  # 计算间隔
        v = 0  # 初速度
        distance += over_move_distance  # 滑超过一段距离

        while current <= distance:
            if current < mid:
                a = 1.3  # 加速度为正
            else:
                a = -0.5  # 加速度为负
            v0 = v  # 初速度v0
            v = v0 + a * t  # 当前速度v
            move = int(v0 * t + 1 / 2 * a * t * t)  # 移动距离 move
            current += move  # 当前位移
            tracks.append(move)
        tracks.append(1)
        return tracks

    async def move_to_gap(self, slider, tracks):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param tracks: 轨迹
        :return:
        """
        back_tracks = [-1, -2, -3, -2, -2, -1]  # -11
        location = await slider.boundingBox()
        slider_x = int(location['x'] + location['width'] / 2)
        slider_y = int(location['y'] + location['height'] / 2)
        await self.page.mouse.move(slider_x, slider_y)
        await self.page.mouse.down()
        for x in tracks:  # 正向
            await self.page.mouse.move(slider_x + x, slider_y)
            slider_x = slider_x + x
        await asyncio.sleep(0.5)
        for x in back_tracks:  # 逆向
            await self.page.mouse.move(slider_x + x, slider_y)
            slider_x = slider_x + x
        await self.page.mouse.move(slider_x, slider_y + 1)
        await self.page.mouse.move(slider_x, slider_y - 2)
        await self.page.mouse.up()

    async def crack(self):
        await asyncio.sleep(1)
        img_1 = await self.get_image()
        await asyncio.sleep(0.5)
        await self.delete_style()
        await asyncio.sleep(0.5)
        img_2 = await self.get_image()
        img_1 = Image.open(BytesIO(img_1))
        img_2 = Image.open(BytesIO(img_2))

        distance = self.get_gap(img_1, img_2) - 8  # 计算需要滑动的距离
        track = self.get_tracks(distance)  # 计算轨迹
        slider = await self.get_slider()  # 捕捉滑块
        await self.move_to_gap(slider, track)  # 拖动滑块至缺口处
        await asyncio.sleep(3)

    async def is_page_ok(self):
        await asyncio.sleep(3)
        res = await self.page.waitForResponse(lambda r: 'api.geetest.com/ajax.php?' in r.url, {'timeout': 30e3})
        text = await res.text()
        print('page status:', text)

        status_reg = re.search(r'"message"[\s]*:[\s]*"(.*?)"', text)
        if status_reg:
            return 'success' == status_reg.group(1)
        else:
            raise ValueError('no result')

    async def try_one(self):
        # print('retry', i)
        tasks = [
            self.crack(),
            self.is_page_ok()
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for each in pending:
            each.cancel()
        for each in done:
            # print(each._coro.__name__)
            if not each.exception() and each.result():
                print('发送验证码成功...')
                await asyncio.sleep(3)

                print(await self.page.cookies())  # crashed here
                return True

    async def start(self):
        for i in range(1):
            try:
                r = await self.try_one()
                if r:
                    return r
            except Exception as e:
                logger.log(type(e), e)
