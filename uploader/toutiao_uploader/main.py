# -*- coding: utf-8 -*-
"""头条号登录与 Cookie 管理。

提供 toutiao_cookie_gen（扫码登录）、cookie_auth（校验）、toutiao_setup（统一入口）。
"""

import asyncio
import os

from patchright.async_api import async_playwright

from utils.base_social_media import set_init_script
from utils.log import toutiao_logger

TOUTIAO_LOGIN_URL = "https://mp.toutiao.com"
TOUTIAO_HOME_URL = "https://mp.toutiao.com"


async def toutiao_cookie_gen(account_file, headless: bool = False):
    """打开头条号登录页，等待用户扫码完成登录后保存 cookie。"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=headless,
            args=["--lang=zh-CN", "--no-sandbox"],
        )
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto(TOUTIAO_LOGIN_URL)
        toutiao_logger.info("已打开头条号首页，请在页面上手动登录（或扫码登录）")
        toutiao_logger.info("登录完成后会自动保存 cookie...")

        # 等待用户登录完成：检测 URL 离开登录/auth 页面
        try:
            for _ in range(150):  # 最多等 5 分钟
                await asyncio.sleep(2)
                url = page.url
                if "login" not in url.lower() and "auth" not in url.lower() and "passport" not in url.lower():
                    toutiao_logger.success(f"检测到登录成功，当前页面: {url[:60]}")
                    break
            else:
                toutiao_logger.warning("等待超时，尝试通过 pause 等待手动确认")
                await page.pause()
        except Exception:
            toutiao_logger.warning("等待异常，尝试通过 pause 等待手动确认")
            await page.pause()

        await asyncio.sleep(2)
        account_path = os.path.dirname(account_file)
        os.makedirs(account_path, exist_ok=True)
        await context.storage_state(path=account_file)
        toutiao_logger.success(f"cookie 已保存到: {account_file}")
        await context.close()
        await browser.close()


async def cookie_auth(account_file):
    """校验头条号 cookie 是否有效。"""
    if not os.path.exists(account_file):
        return False

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            context = await browser.new_context(storage_state=account_file)
            context = await set_init_script(context)
            page = await context.new_page()
            await page.goto(TOUTIAO_HOME_URL)
            await page.wait_for_timeout(5000)

            # 检测是否被重定向到登录页
            if "login" in page.url.lower() or "auth" in page.url.lower() or "passport" in page.url.lower():
                toutiao_logger.error("cookie 已失效，被重定向到登录页")
                return False

            toutiao_logger.success("cookie 有效")
            return True
        except Exception as exc:
            toutiao_logger.warning(f"cookie 校验出错: {exc}")
            return False
        finally:
            await browser.close()


async def toutiao_setup(account_file, handle=False):
    """统一的登录准备入口：检查 cookie，失效时根据 handle 决定是否重新登录。"""
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        toutiao_logger.info("cookie 不存在或已失效，准备打开浏览器重新登录...")
        await toutiao_cookie_gen(account_file)
    return True
