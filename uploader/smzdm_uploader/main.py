# -*- coding: utf-8 -*-
"""什么值得买登录与 Cookie 管理。

提供 smzdm_cookie_gen（扫码登录）、cookie_auth（校验）、smzdm_setup（统一入口）。
"""

import os

from patchright.async_api import async_playwright

from conf import LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import smzdm_logger

SMZDM_LOGIN_URL = "https://www.smzdm.com"
SMZDM_EDITOR_URL = "https://post.smzdm.com/edit/a70658o9"
SMZDM_HOME_URL = "https://www.smzdm.com"


async def smzdm_cookie_gen(account_file, headless: bool = False):
    """打开什么值得买登录页，等待用户扫码完成登录后保存 cookie。"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=headless,
            args=["--lang=zh-CN", "--no-sandbox"],
        )
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto(SMZDM_LOGIN_URL)
        smzdm_logger.info("已打开什么值得买首页，请在页面上手动登录（或扫码登录）")
        smzdm_logger.info("登录完成后会自动保存 cookie...")

        # 等待用户登录完成：检测用户头像或用户名出现
        try:
            await page.wait_for_selector(
                "a.nickname, a[href*='hai'], .J_user_info, .user-bar a",
                timeout=300000,
            )
            smzdm_logger.success("检测到登录成功")
        except Exception:
            smzdm_logger.warning("未检测到登录标识（等待超时），继续尝试保存 cookie...")

        # 验证能否访问发帖页
        await page.goto(SMZDM_EDITOR_URL)
        await page.wait_for_timeout(3000)
        if "login" in page.url.lower() or "passport" in page.url.lower():
            smzdm_logger.error("登录可能未成功，被重定向到登录页")

        account_path = os.path.dirname(account_file)
        os.makedirs(account_path, exist_ok=True)
        await context.storage_state(path=account_file)
        smzdm_logger.success(f"cookie 已保存到: {account_file}")
        await context.close()
        await browser.close()


async def cookie_auth(account_file):
    """校验什么值得买 cookie 是否有效。"""
    if not os.path.exists(account_file):
        return False

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            context = await browser.new_context(storage_state=account_file)
            context = await set_init_script(context)
            page = await context.new_page()
            await page.goto(SMZDM_HOME_URL)
            await page.wait_for_timeout(5000)

            # 检测是否被重定向到登录页或显示登录按钮
            if "login" in page.url.lower() or "passport" in page.url.lower():
                smzdm_logger.error("cookie 已失效，被重定向到登录页")
                return False

            # 检测用户标识
            user_indicator = await page.query_selector_all(
                "a.nickname, a[href*='hai'], .J_user_info, .user-bar a"
            )
            if not user_indicator:
                smzdm_logger.error("cookie 已失效，未检测到用户标识")
                return False

            smzdm_logger.success("cookie 有效")
            return True
        except Exception as exc:
            smzdm_logger.warning(f"cookie 校验出错: {exc}")
            return False
        finally:
            await browser.close()


async def smzdm_setup(account_file, handle=False):
    """统一的登录准备入口：检查 cookie，失效时根据 handle 决定是否重新登录。"""
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        smzdm_logger.info("cookie 不存在或已失效，准备打开浏览器重新登录...")
        await smzdm_cookie_gen(account_file)
    return True
