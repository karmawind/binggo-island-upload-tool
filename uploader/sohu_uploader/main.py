# -*- coding: utf-8 -*-
"""搜狐号登录与 Cookie 管理。

提供 sohu_cookie_gen（扫码/账号登录）、cookie_auth（校验）、sohu_setup（统一入口）。
"""

import asyncio
import os

from patchright.async_api import async_playwright

from utils.base_social_media import set_init_script
from utils.log import sohu_logger

SOHU_HOME_URL = "https://mp.sohu.com"
SOHU_EDITOR_URL = "https://mp.sohu.com/api/author/article/new"

# 登录后页面出现的关键词（不在登录页出现）
LOGIN_INDICATORS = ["发布文章", "内容管理", "个人中心", "数据统计", "创作中心"]


async def sohu_cookie_gen(account_file, headless: bool = False):
    """打开搜狐号登录页，等待用户登录后保存 cookie。"""
    browser = None
    context = None

    try:
        async with async_playwright() as playwright:
            sohu_logger.info("[登录] 启动浏览器...")
            launch_args = [
                "--lang=zh-CN",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=AutomationControlled",
                "--disable-infobars",
                "--window-size=1920,1080",
            ]
            if not headless:
                launch_args.append("--start-maximized")
            browser = await playwright.chromium.launch(
                headless=headless, args=launch_args
            )
            context = await browser.new_context(locale="zh-CN")
            context = await set_init_script(context)
            # 额外反检测
            await context.add_init_script(script="""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){} };
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
            """)
            page = await context.new_page()

            sohu_logger.info("[登录] 正在打开搜狐号后台...")
            await page.goto(SOHU_HOME_URL, timeout=60000)
            sohu_logger.info("[登录] 已打开搜狐号后台，请在浏览器中完成登录")

            # 轮询检测登录成功
            logged_in = False
            for attempt in range(150):  # 最多 5 分钟
                await asyncio.sleep(2)
                user_found = await page.evaluate("""(indicators) => {
                    const text = document.body?.innerText || '';
                    return indicators.some(kw => text.includes(kw));
                }""", LOGIN_INDICATORS)
                if user_found:
                    sohu_logger.success("[登录] 检测到登录成功")
                    logged_in = True
                    break

            if not logged_in:
                sohu_logger.warning("[登录] 等待超时，仍尝试保存 cookie")

            # 保存 cookie
            account_path = os.path.dirname(account_file)
            os.makedirs(account_path, exist_ok=True)
            await context.storage_state(path=account_file)
            sohu_logger.success(f"[登录] Cookie 已保存: {account_file}")

    finally:
        try:
            if context:
                await context.close()
        except Exception:
            pass
        try:
            if browser:
                await browser.close()
        except Exception:
            pass
        sohu_logger.info("[登录] 浏览器已关闭")


async def cookie_auth(account_file):
    """校验搜狐号 cookie 是否有效。"""
    if not os.path.exists(account_file):
        sohu_logger.warning("[校验] Cookie 文件不存在")
        return False

    browser = None
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                storage_state=account_file, locale="zh-CN"
            )
            context = await set_init_script(context)
            page = await context.new_page()

            sohu_logger.info("[校验] 正在验证 cookie...")
            await page.goto(SOHU_HOME_URL, timeout=60000)
            await page.wait_for_timeout(5000)

            user_found = await page.evaluate("""(indicators) => {
                const text = document.body?.innerText || '';
                return indicators.some(kw => text.includes(kw));
            }""", LOGIN_INDICATORS)

            if user_found:
                sohu_logger.success("[校验] Cookie 有效")
                await context.close()
                return True

            sohu_logger.error("[校验] Cookie 已失效")
            return False

    except Exception as exc:
        sohu_logger.warning(f"[校验] 校验出错: {exc}")
        return False
    finally:
        try:
            if browser:
                await browser.close()
        except Exception:
            pass


async def sohu_setup(account_file, handle=False):
    """统一的登录准备入口。"""
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        sohu_logger.info("[准备] Cookie 无效，启动浏览器重新登录...")
        await sohu_cookie_gen(account_file)
    return True
