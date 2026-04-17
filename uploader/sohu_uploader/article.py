# -*- coding: utf-8 -*-
"""搜狐号图文文章发布器。

适配 social-auto-upload 框架，基于 Quill.js 富文本编辑器的 DOM 交互。

发布流程（已通过 Chrome DevTools MCP 验证 2026-04-13）：
1. 导航到文章编辑页面
2. 关闭弹窗
3. 清空编辑器
4. 填写标题（5-72字）
5. 填写正文（Quill.js + execCommand）
6. 上传图片（工具栏 image 按钮 → 上传弹窗）
7. 发布（两步确认：发布按钮 → 确认发布 → 确定）
8. 验证发布结果

关键发现：
- 编辑器是 Quill.js（.ql-editor），不是简单 contenteditable
- 发布按钮是 <li> 元素，不是 <button>
- 发布有两步确认弹窗："确认发布文章么？" → 点"确定"
- 封面图自动从正文图片选取，无需手动设置
- 正文不足200字会警告但仍可发布
"""

import asyncio
import json
from pathlib import Path

from patchright.async_api import Page, async_playwright, Playwright

from conf import LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.log import sohu_logger


# ==================== 集中选择器管理 ====================
SELECTORS = {
    # 标题 — placeholder="请输入标题（5-72字）"
    "title_input": "input[placeholder*='标题']",
    # 正文编辑器（Quill.js）
    "editor_body": ".ql-editor",
    # 工具栏图片按钮
    "toolbar_image_btn": "button.ql-image",
    # 图片上传弹窗中的上传按钮（file input）
    "image_upload_input": "input[type='file']",
    # 摘要 textarea
    "summary_input": "textarea",
    # 发布按钮 — 是 <li> 元素，不是 <button>
    "publish_btn": "li.positive-button.publish-report-btn",
    # 确认弹窗中的"确定"按钮
    "confirm_btn": "button",
}

URLS = {
    "home": "https://mp.sohu.com",
    # 直接导航到编辑器（不需要 SPA 路由跳转）
    "editor": "https://mp.sohu.com/mpfe/v4/contentManagement/news/addarticle?contentStatus=1",
}

# 弹窗关闭关键词
POPUP_CLOSE_KEYWORDS = ["我知道了", "知道了", "关闭"]

# 超时配置（毫秒）
TIMEOUTS = {
    "page_load": 60000,
    "editor_ready": 15000,
    "click": 10000,
    "upload": 30000,
}


class EditorPage:
    """搜狐号编辑器页面交互模型。"""

    def __init__(self, page: Page, debug: bool = False):
        self.page = page
        self._debug = debug

    async def _screenshot(self, name: str):
        """debug 模式下自动截图。"""
        if not self._debug:
            return
        try:
            from pathlib import Path as P
            screenshot_dir = P("logs")
            screenshot_dir.mkdir(exist_ok=True)
            path = screenshot_dir / f"sohu_{name}.png"
            await self.page.screenshot(path=str(path))
            sohu_logger.debug(f"[截图] {path}")
        except Exception:
            pass

    async def navigate_to_editor(self):
        """导航到搜狐号编辑器页面。先加载首页确认登录，再直接导航到编辑器。"""
        sohu_logger.info("[导航] 正在打开搜狐号后台首页...")
        await self.page.goto(URLS["home"], timeout=TIMEOUTS["page_load"])
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        # 检查是否已登录
        body_text = await self.page.evaluate(
            "() => document.body?.innerText?.substring(0, 1000) || ''"
        )
        if "登录" in body_text and "发布内容" not in body_text:
            raise CookieExpiredError("Cookie 已失效，页面显示登录")

        await self._screenshot("01_dashboard")

        # 直接导航到编辑器（不需要 SPA 路由跳转）
        sohu_logger.info("[导航] 正在打开编辑器...")
        await self.page.goto(URLS["editor"], timeout=TIMEOUTS["page_load"])
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        await self._screenshot("01_editor_loaded")
        sohu_logger.success("[导航] 编辑页已打开")

    async def dismiss_popups(self):
        """关闭可能出现的弹窗。"""
        for keyword in POPUP_CLOSE_KEYWORDS:
            try:
                btn = self.page.get_by_text(keyword).first
                if await btn.is_visible():
                    await btn.click()
                    sohu_logger.debug(f"[弹窗] 已关闭: {keyword}")
                    await asyncio.sleep(0.3)
            except Exception:
                pass

    async def wait_for_editor_ready(self):
        """等待编辑器加载完成。"""
        sohu_logger.info("[等待] 等待编辑器加载...")
        try:
            await self.page.wait_for_selector(
                SELECTORS["editor_body"], timeout=TIMEOUTS["editor_ready"]
            )
        except Exception:
            sohu_logger.warning("[等待] 编辑器加载超时，继续执行...")

        await self.dismiss_popups()
        await self._screenshot("02_editor_ready")
        sohu_logger.success("[等待] 编辑器就绪")

    async def clear_editor(self):
        """清空编辑器中的标题和正文。"""
        sohu_logger.info("[清空] 清空编辑器...")

        # 清空标题
        title_input = self.page.locator(SELECTORS["title_input"]).first
        if await title_input.count() > 0:
            await title_input.click()
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Backspace")

        # 清空正文（Quill.js 编辑器）
        editor = self.page.locator(SELECTORS["editor_body"]).first
        if await editor.count() > 0:
            await editor.click()
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Backspace")

        # 清除残留图片
        await self.page.evaluate("""() => {
            const editor = document.querySelector('.ql-editor');
            if (editor) editor.querySelectorAll('img, .ql-image-container').forEach(el => el.remove());
        }""")

        for _ in range(3):
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.2)

        sohu_logger.success("[清空] 编辑器已清空")

    async def fill_title(self, title: str):
        """填写文章标题（5-72字）。"""
        truncated = title[:72]
        sohu_logger.info(f"[标题] 填写: {truncated}")

        title_input = self.page.locator(SELECTORS["title_input"]).first
        await title_input.click(timeout=TIMEOUTS["click"])
        await title_input.fill(truncated)

        await self._screenshot("03_title_filled")
        sohu_logger.success("[标题] 已填写")

    async def fill_content(self, content: str):
        """填写正文。Quill.js 编辑器使用 execCommand('insertHTML')。"""
        if not content:
            return

        sohu_logger.info(f"[正文] 填写正文（{len(content)} 字）...")

        editor = self.page.locator(SELECTORS["editor_body"]).first
        await editor.click(timeout=TIMEOUTS["click"])
        await asyncio.sleep(0.3)

        # 纯文本 → HTML 段落
        paragraphs = content.split("\n")
        html_parts = [f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()]
        html_content = "".join(html_parts)

        if html_content:
            await self.page.evaluate("""(html) => {
                const editor = document.querySelector('.ql-editor');
                if (editor) {
                    editor.focus();
                    document.execCommand('insertHTML', false, html);
                }
            }""", html_content)

        await self._screenshot("04_content_filled")
        sohu_logger.success("[正文] 已填写")

    async def upload_images(self, image_paths: list[Path]):
        """上传图片。通过工具栏 image 按钮打开上传弹窗，逐张上传。"""
        if not image_paths:
            return

        sohu_logger.info(f"[图片] 上传 {len(image_paths)} 张图片...")

        valid_images = []
        for img_path in image_paths:
            img_path = Path(img_path)
            if img_path.exists():
                valid_images.append(str(img_path))
            else:
                sohu_logger.warning(f"[图片] 不存在: {img_path}")

        if not valid_images:
            return

        # 点击工具栏 image 按钮，打开上传弹窗
        image_btn = self.page.locator("button.ql-image").first
        await image_btn.click(timeout=TIMEOUTS["click"])
        await asyncio.sleep(1)

        # 在上传弹窗中找到 file input 并上传
        file_input = self.page.locator("input[type='file']").first
        await file_input.wait_for(state="attached", timeout=TIMEOUTS["click"])
        await file_input.set_input_files(valid_images)

        # 等待上传完成
        for attempt in range(15):
            upload_done = await self.page.evaluate("""() => {
                const text = document.body?.innerText || '';
                return text.includes('已成功上传') && !text.includes('上传中');
            }""")
            if upload_done:
                break
            await asyncio.sleep(2)

        # 点击"确定"按钮将图片插入正文
        confirm_btn = self.page.locator("text=确定").first
        try:
            if await confirm_btn.is_visible():
                await confirm_btn.click()
                sohu_logger.debug("[图片] 已点击确定插入图片")
        except Exception:
            pass

        await asyncio.sleep(1)
        await self._screenshot("05_images_uploaded")
        sohu_logger.success(f"[图片] {len(valid_images)} 张图片已上传")

    async def _click_publish_btn(self):
        """点击发布按钮（<li> 元素，需要 JS 兜底）。"""
        publish_btn = self.page.locator(SELECTORS["publish_btn"]).first
        try:
            await publish_btn.click(timeout=TIMEOUTS["click"])
        except Exception:
            await self.page.evaluate("""() => {
                const btn = document.querySelector('li.positive-button.publish-report-btn');
                if (btn) btn.click();
            }""")

    async def _click_visible_button(self, text: str):
        """点击页面上可见的指定文字按钮（多层兜底）。"""
        # 方法1: Playwright text locator
        try:
            btn = self.page.locator(f"text={text}").first
            if await btn.is_visible():
                await btn.click()
                sohu_logger.debug(f"[点击] Playwright 点击 '{text}'")
                return True
        except Exception:
            pass

        # 方法2: CSS button selector
        try:
            btn = self.page.locator(f"button:has-text('{text}')").first
            if await btn.is_visible():
                await btn.click()
                sohu_logger.debug(f"[点击] CSS button 点击 '{text}'")
                return True
        except Exception:
            pass

        # 方法3: JS dispatchEvent（遍历所有元素）
        clicked = await self.page.evaluate("""(text) => {
            const all = document.querySelectorAll('button, a, span, div[role="button"], li');
            for (const el of all) {
                if (el.innerText?.trim() === text && el.offsetParent !== null) {
                    el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
                    el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
                    el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                    return true;
                }
            }
            return false;
        }""", text)
        if clicked:
            sohu_logger.debug(f"[点击] JS dispatchEvent 点击 '{text}'")
        return clicked

    async def publish(self):
        """点击发布按钮。搜狐号发布需要多步确认。"""
        sohu_logger.info("[发布] 点击发布按钮...")

        await self.dismiss_popups()
        await self._click_publish_btn()
        await asyncio.sleep(2)

        # 循环处理所有弹窗（200字警告 / 确认发布），最多 5 轮
        for attempt in range(5):
            # 检查是否已跳转（发布成功）
            if "addarticle" not in self.page.url:
                sohu_logger.info("[发布] 页面已跳转，发布成功")
                return

            # 检测"正文不足200字"警告
            try:
                warn = self.page.locator("text=不足200字").first
                if await warn.is_visible():
                    sohu_logger.info(f"[发布] 第{attempt + 1}轮：检测到'不足200字'警告")
                    await self._click_visible_button("确定")
                    await asyncio.sleep(2)
                    await self._click_publish_btn()
                    await asyncio.sleep(2)
                    continue
            except Exception:
                pass

            # 检测"确认发布文章么？"弹窗
            try:
                confirm = self.page.locator("text=确认发布文章么").first
                if await confirm.is_visible():
                    sohu_logger.info(f"[发布] 第{attempt + 1}轮：检测到确认弹窗")
                    await self._click_visible_button("确定")
                    await asyncio.sleep(3)
                    continue
            except Exception:
                pass

            # 没有弹窗，等待一下再检查
            await asyncio.sleep(2)

        await self._screenshot("06_after_publish")

        await asyncio.sleep(3)
        await self._screenshot("06_after_publish")

    async def verify_publish_success(self) -> bool:
        """验证发布是否成功。"""
        sohu_logger.info("[验证] 验证发布结果...")

        success_keywords = ["发布成功", "提交成功", "审核", "已发布", "审核中"]
        error_keywords = ["发布失败", "请填写", "不能为空"]

        for attempt in range(10):
            url = self.page.url
            body_text = await self.page.evaluate(
                "() => document.body.innerText.substring(0, 2000)"
            )

            if attempt == 0:
                sohu_logger.debug(f"[验证] URL={url[:80]}")
                sohu_logger.debug(f"[验证] 页面文本前200字: {body_text[:200]}")

            # 检测成功关键词
            for kw in success_keywords:
                if kw in body_text:
                    sohu_logger.success(f"[验证] 发布成功（检测到 '{kw}'）")
                    return True

            # 检测已跳离编辑页
            if "addarticle" not in url:
                sohu_logger.success(f"[验证] 已跳转到 {url[:60]}")
                return True

            # 检测失败关键词
            for kw in error_keywords:
                if kw in body_text:
                    sohu_logger.error(f"[验证] 发布失败（检测到 '{kw}'）")
                    return False

            await asyncio.sleep(2)

        await self._screenshot("07_verify_timeout")
        sohu_logger.warning("[验证] 未检测到明确结果")
        return False


class CookieExpiredError(Exception):
    pass


class PublishError(Exception):
    pass


class SohuArticle:
    """搜狐号图文文章发布器。"""

    def __init__(
        self,
        title: str,
        content: str = "",
        image_paths: list[str] | None = None,
        tags: list[str] | None = None,
        publish_date=None,
        account_file: str = "",
        headless: bool = True,
        debug: bool = False,
    ):
        self.title = title
        self.content = content
        self.image_paths = [Path(p) for p in (image_paths or [])]
        self.tags = tags or []
        self.publish_date = publish_date
        self.account_file = account_file
        self.headless = headless
        self.debug = debug
        self._page: Page | None = None
        self._browser = None
        self._context = None

    async def main(self) -> bool:
        async with async_playwright() as playwright:
            return await self.upload(playwright)

    async def upload(self, playwright: Playwright) -> bool:
        """执行完整的文章发布流程。使用 CDP 连接本地 Chrome 绕过反爬。"""
        sohu_logger.info(f"{'=' * 20} 开始发布: {self.title} {'=' * 20}")

        try:
            # 检查 CDP 是否可用，不可用则自动启动 Chrome 调试模式
            import subprocess
            import urllib.request

            cdp_url = "http://127.0.0.1:9222/json/version"
            try:
                urllib.request.urlopen(cdp_url, timeout=3)
                sohu_logger.info("[CDP] 检测到 Chrome 调试模式已启动")
            except Exception:
                sohu_logger.info("[CDP] Chrome 调试模式未启动，正在自动启动...")
                chrome_path = LOCAL_CHROME_PATH or r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                user_data_dir = str(Path(__file__).resolve().parent.parent.parent / "chrome_debug_profile")

                # 尝试启动（如果已有 Chrome 在运行，用独立 user-data-dir 可以共存）
                subprocess.Popen([
                    chrome_path,
                    f"--remote-debugging-port=9222",
                    f"--user-data-dir={user_data_dir}",
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # 等待 Chrome 启动并就绪
                started = False
                for i in range(15):
                    await asyncio.sleep(1)
                    try:
                        urllib.request.urlopen(cdp_url, timeout=2)
                        started = True
                        break
                    except Exception:
                        continue
                if started:
                    sohu_logger.info("[CDP] Chrome 调试模式已自动启动")
                else:
                    raise Exception("Chrome 调试模式自动启动失败，请检查 Chrome 是否已安装")

            # 通过 CDP 连接本地 Chrome（绕过反爬检测）
            sohu_logger.info("[启动] 通过 CDP 连接本地 Chrome...")
            self._browser = await playwright.chromium.connect_over_cdp(
                "http://127.0.0.1:9222"
            )
            context = self._browser.contexts[0] if self._browser.contexts else await self._browser.new_context()

            # 从 cookie 文件注入登录态到 CDP context
            if self.account_file:
                cookie_path = Path(self.account_file)
                if cookie_path.exists():
                    state = json.loads(cookie_path.read_text(encoding="utf-8"))
                    sohu_cookies = [
                        c for c in state.get("cookies", [])
                        if "sohu.com" in c.get("domain", "")
                    ]
                    if sohu_cookies:
                        await context.add_cookies(sohu_cookies)
                        sohu_logger.info(f"[Cookie] 已注入 {len(sohu_cookies)} 条 cookie")
                    else:
                        sohu_logger.warning("[Cookie] 文件中无 sohu.com 域名 cookie")
                else:
                    sohu_logger.warning(f"[Cookie] 文件不存在: {cookie_path}")

            self._page = await context.new_page()
            sohu_logger.info("[启动] 浏览器已连接")

            editor = EditorPage(self._page, debug=self.debug)

            # 导航到编辑器
            await editor.navigate_to_editor()
            await editor.wait_for_editor_ready()

            # 清空编辑器
            await editor.clear_editor()

            # 填写标题
            await editor.fill_title(self.title)

            # 填写正文
            if self.content:
                await editor.fill_content(self.content)

            # 上传图片
            if self.image_paths:
                await editor.upload_images(self.image_paths)

            # 发布（含两步确认）
            await editor.publish()

            # 验证
            success = await editor.verify_publish_success()

            # CDP 模式：不需要手动保存 cookie，Chrome 自行管理登录态

            if success:
                sohu_logger.success(f"{'=' * 20} 发布完成: {self.title} {'=' * 20}")
            else:
                sohu_logger.warning(f"{'=' * 20} 发布结果未确认: {self.title} {'=' * 20}")

            return success

        except CookieExpiredError as e:
            sohu_logger.error(f"[Cookie 失效] {e}")
            return False
        except Exception as e:
            sohu_logger.error(f"[异常] {e}")
            return False
        finally:
            # CDP 模式不关闭浏览器（是用户的 Chrome）
            sohu_logger.info("[清理] 任务结束")
