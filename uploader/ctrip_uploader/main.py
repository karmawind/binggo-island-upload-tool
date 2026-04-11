# -*- coding: utf-8 -*-
"""携程内容中心登录与 Cookie 管理。

提供 ctrip_cookie_gen（扫码登录）、cookie_auth（校验）、ctrip_setup（统一入口）。
"""

import asyncio
import os

from patchright.async_api import async_playwright

from utils.base_social_media import set_init_script
from utils.log import ctrip_logger

CTRIP_LOGIN_URL = "https://we.ctrip.com/?accountsource=c"
CTRIP_HOME_URL = "https://we.ctrip.com/"


async def ctrip_cookie_gen(account_file, headless: bool = False):
    """打开携程内容中心登录页，等待用户登录后保存 cookie。"""
    async with async_playwright() as playwright:
        launch_args = ["--lang=zh-CN", "--no-sandbox"]
        if not headless:
            launch_args.append("--start-maximized")
        browser = await playwright.chromium.launch(headless=headless, args=launch_args)
        context = await browser.new_context(locale="zh-CN")
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto(CTRIP_LOGIN_URL)
        ctrip_logger.info("已打开携程内容中心登录页，请在页面上登录")
        ctrip_logger.info("登录完成后会自动保存 cookie...")

        # 等待用户登录完成：检测页面出现用户标识（排除登录页已有的文字）
        logged_in = False
        try:
            for _ in range(150):  # 最多等 5 分钟
                await asyncio.sleep(2)
                user_found = await page.evaluate("""() => {
                    const text = document.body?.innerText || '';
                    // 这些关键词只在登录后页面出现，不在登录页
                    return text.includes('发布内容') || text.includes('作品管理') ||
                           text.includes('我的作品') || text.includes('内容数据') ||
                           text.includes('发布笔记');
                }""")
                if user_found:
                    ctrip_logger.success("检测到登录成功")
                    logged_in = True
                    break
            else:
                ctrip_logger.warning("等待超时")
        except Exception:
            ctrip_logger.warning("等待异常")

        if not logged_in:
            ctrip_logger.warning("未检测到登录成功，仍尝试保存 cookie")

        await asyncio.sleep(2)
        account_path = os.path.dirname(account_file)
        os.makedirs(account_path, exist_ok=True)
        await context.storage_state(path=account_file)
        ctrip_logger.success(f"cookie 已保存到: {account_file}")
        await context.close()
        await browser.close()


async def cookie_auth(account_file):
    """校验携程 cookie 是否有效。"""
    if not os.path.exists(account_file):
        return False

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            context = await browser.new_context(storage_state=account_file)
            context = await set_init_script(context)
            page = await context.new_page()
            await page.goto(CTRIP_LOGIN_URL)
            await page.wait_for_timeout(8000)

            url = page.url
            # 检测页面是否有用户标识（只在登录后出现的标识）
            user_found = await page.evaluate("""() => {
                const text = document.body?.innerText || '';
                return text.includes('发布内容') || text.includes('作品管理') ||
                       text.includes('我的作品') || text.includes('内容数据') ||
                       text.includes('发布笔记');
            }""")

            if user_found:
                ctrip_logger.success("cookie 有效（页面包含用户标识）")
                return True

            ctrip_logger.error("cookie 已失效，无用户标识")
            return True
        except Exception as exc:
            ctrip_logger.warning(f"cookie 校验出错: {exc}")
            return False
        finally:
            await browser.close()


async def ctrip_setup(account_file, handle=False):
    """统一的登录准备入口：检查 cookie，失效时根据 handle 决定是否重新登录。"""
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        ctrip_logger.info("cookie 不存在或已失效，准备打开浏览器重新登录...")
        await ctrip_cookie_gen(account_file)
    return True
