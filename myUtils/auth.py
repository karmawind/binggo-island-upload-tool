import asyncio
import configparser
import os

from playwright.async_api import async_playwright
from xhs import XhsClient

from conf import BASE_DIR, LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.log import tencent_logger, kuaishou_logger, douyin_logger
from pathlib import Path
from uploader.xhs_uploader.main import sign_local
from uploader.baijiahao_uploader.main import cookie_auth as baijiahao_cookie_auth
from uploader.smzdm_uploader.main import cookie_auth as smzdm_cookie_auth
from uploader.toutiao_uploader.main import cookie_auth as toutiao_cookie_auth
from uploader.ctrip_uploader.main import cookie_auth as ctrip_cookie_auth
from uploader.sohu_uploader.main import cookie_auth as sohu_cookie_auth
from uploader.weibo_uploader.main import cookie_auth as weibo_cookie_auth


def _get_browser_options():
    """获取浏览器启动配置，优先使用本地 Chrome。"""
    options = {
        'headless': LOCAL_CHROME_HEADLESS,
        'args': [
            '--disable-blink-features=AutomationControlled',
            '--lang=zh-CN',
            '--disable-infobars',
            '--start-maximized'
        ]
    }
    if LOCAL_CHROME_PATH:
        options['executable_path'] = LOCAL_CHROME_PATH
    return options


async def cookie_auth_douyin(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**_get_browser_options())
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
            # 2024.06.17 抖音创作者中心改版
            # 判断
            # 等待“扫码登录”元素出现，超时 5 秒（如果 5 秒没出现，说明 cookie 有效）
            try:
                await page.get_by_text("扫码登录").wait_for(timeout=5000)
                douyin_logger.error("[+] cookie 失效，需要扫码登录")
                return False
            except:
                douyin_logger.success("[+]  cookie 有效")
                return True
        except:
            douyin_logger.error("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False


async def cookie_auth_tencent(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**_get_browser_options())
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://channels.weixin.qq.com/platform/post/create")
        try:
            await page.wait_for_selector('div.title-name:has-text("微信小店")', timeout=5000)  # 等待5秒
            tencent_logger.error("[+] 等待5秒 cookie 失效")
            return False
        except:
            tencent_logger.success("[+] cookie 有效")
            return True


async def cookie_auth_ks(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**_get_browser_options())
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://cp.kuaishou.com/article/publish/video")
        try:
            await page.wait_for_selector("div.names div.container div.name:text('机构服务')", timeout=5000)  # 等待5秒

            kuaishou_logger.info("[+] 等待5秒 cookie 失效")
            return False
        except:
            kuaishou_logger.success("[+] cookie 有效")
            return True


async def cookie_auth_xhs(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**_get_browser_options())
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.xiaohongshu.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.xiaohongshu.com/creator-micro/content/upload", timeout=5000)
        except:
            print("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            print("[+] 等待5秒 cookie 失效")
            return False
        else:
            print("[+] cookie 有效")
            return True


async def check_cookie(type, file_path):
    cookie_path = Path(BASE_DIR / "cookiesFile" / file_path)
    match type:
        # 小红书
        case 1:
            return await cookie_auth_xhs(cookie_path)
        # 视频号
        case 2:
            return await cookie_auth_tencent(cookie_path)
        # 抖音
        case 3:
            return await cookie_auth_douyin(cookie_path)
        # 快手
        case 4:
            return await cookie_auth_ks(cookie_path)
        # 百家号
        case 5:
            return await baijiahao_cookie_auth(str(cookie_path))
        # 什么值得买
        case 6:
            return await smzdm_cookie_auth(str(cookie_path))
        # 头条号
        case 7:
            return await toutiao_cookie_auth(str(cookie_path))
        # 携程
        case 8:
            return await ctrip_cookie_auth(str(cookie_path))
        # 搜狐号
        case 9:
            return await sohu_cookie_auth(str(cookie_path))
        # 微博
        case 10:
            return await weibo_cookie_auth(str(cookie_path))
        case _:
            return False

# a = asyncio.run(check_cookie(1,"3a6cfdc0-3d51-11f0-8507-44e51723d63c.json"))
# print(a)
