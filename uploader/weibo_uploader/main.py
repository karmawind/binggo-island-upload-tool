# -*- coding: utf-8 -*-
"""微博登录与 Cookie 管理。

提供 weibo_cookie_gen（扫码登录）、cookie_auth（校验）、weibo_setup（统一入口）。
使用移动版 m.weibo.cn，DOM 简单稳定。
"""

import asyncio
import os

from patchright.async_api import async_playwright

from utils.base_social_media import set_init_script
from utils.log import weibo_logger

WEIBO_HOME_URL = "https://weibo.com"

# 登录后页面出现的文本
LOGIN_INDICATORS = ["首页", "消息", "发现", "热门", "写微博"]

# Cookie 注入需要覆盖的域名（微博认证系统跨域）
COOKIE_DOMAINS = ["weibo.cn", "weibo.com", "sina.com.cn", "sina.cn"]


async def weibo_cookie_gen(account_file, headless: bool = False):
    """打开微博桌面版登录页，等待用户扫码登录后保存 cookie。"""
    browser = None
    context = None

    try:
        async with async_playwright() as playwright:
            weibo_logger.info("[登录] 启动浏览器...")
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

            weibo_logger.info("[登录] 正在打开微博...")
            await page.goto(WEIBO_HOME_URL, timeout=60000)
            weibo_logger.info("[登录] 已打开微博，请在浏览器中扫码登录")

            # 轮询检测登录成功：URL 不再包含 newlogin/login 且页面有用户头像
            logged_in = False
            for attempt in range(150):  # 最多 5 分钟
                await asyncio.sleep(2)
                current_url = page.url
                if "newlogin" in current_url or "login" in current_url.split("/")[-1]:
                    continue
                # URL 已离开登录页，确认有用户头像
                has_user = await page.evaluate("""() => {
                    // 桌面版登录后顶部有用户头像（class 含 avatar）
                    const avatar = document.querySelector('img.woo-avatar-img');
                    return !!avatar;
                }""")
                if has_user:
                    weibo_logger.success("[登录] 检测到登录成功")
                    logged_in = True
                    break

            if not logged_in:
                weibo_logger.warning("[登录] 等待超时，仍尝试保存 cookie")

            # 保存 cookie
            account_path = os.path.dirname(account_file)
            os.makedirs(account_path, exist_ok=True)
            await context.storage_state(path=account_file)
            weibo_logger.success(f"[登录] Cookie 已保存: {account_file}")

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
        weibo_logger.info("[登录] 浏览器已关闭")


async def cookie_auth(account_file):
    """校验微博 cookie 是否有效。"""
    if not os.path.exists(account_file):
        weibo_logger.warning("[校验] Cookie 文件不存在")
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

            weibo_logger.info("[校验] 正在验证 cookie...")
            await page.goto(WEIBO_HOME_URL, timeout=60000)
            await page.wait_for_timeout(5000)

            # 校验：URL 不含 newlogin 且有用户头像
            current_url = page.url
            if "newlogin" in current_url:
                weibo_logger.error("[校验] Cookie 已失效（仍在登录页）")
                return False

            has_avatar = await page.evaluate("""() => {
                return !!document.querySelector('img.woo-avatar-img');
            }""")
            if has_avatar:
                weibo_logger.success("[校验] Cookie 有效")
                await context.close()
                return True

            weibo_logger.error("[校验] Cookie 已失效")
            return False

    except Exception as exc:
        weibo_logger.warning(f"[校验] 校验出错: {exc}")
        return False
    finally:
        try:
            if browser:
                await browser.close()
        except Exception:
            pass


async def weibo_setup(account_file, handle=False):
    """统一的登录准备入口。"""
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        weibo_logger.info("[准备] Cookie 无效，启动浏览器重新登录...")
        await weibo_cookie_gen(account_file)
    return True
