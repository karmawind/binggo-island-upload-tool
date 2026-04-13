# -*- coding: utf-8 -*-
"""搜狐号图文文章发布器。

适配 social-auto-upload 框架，基于 contenteditable 富文本编辑器的 DOM 交互。

发布流程：
1. 导航到文章编辑页面
2. 关闭弹窗
3. 清空编辑器
4. 填写标题（30 字限制）
5. 填写正文（contenteditable + execCommand）
6. 上传图片
7. 发布
8. 验证发布结果
"""

import asyncio
from pathlib import Path

from patchright.async_api import Page, async_playwright, Playwright

from conf import LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.log import sohu_logger


# ==================== 集中选择器管理 ====================
SELECTORS = {
    # 标题
    "title_input": "input[name='title'], input[placeholder*='标题']",
    # 正文编辑器（contenteditable）
    "editor_body": "#editor, .editor-content, [contenteditable='true']",
    # 封面上传
    "cover_upload": ".cover-upload",
    # 图片 file input
    "image_file_input": "input[type='file'][accept*='image']",
    # 摘要
    "summary_input": "textarea[name='summary']",
    # 发布按钮
    "publish_btn": "button.publish-btn, button:has-text('发布')",
    # 栏目选择
    "column_select": ".column-select",
}

URLS = {
    "home": "https://mp.sohu.com",
    "editor": "https://mp.sohu.com/api/author/article/new",
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
        """导航到文章编辑页面。"""
        sohu_logger.info("[导航] 正在打开搜狐号文章编辑页...")
        await self.page.goto(URLS["editor"], timeout=TIMEOUTS["page_load"])
        await self.page.wait_for_load_state("domcontentloaded")

        # 检查是否被重定向到登录页
        body_text = await self.page.evaluate(
            "() => document.body?.innerText?.substring(0, 500) || ''"
        )
        if "登录" in body_text and "发布" not in body_text:
            raise CookieExpiredError("Cookie 已失效，页面显示登录")

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

        # 清空正文
        editor = self.page.locator(SELECTORS["editor_body"]).first
        if await editor.count() > 0:
            await editor.click()
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Backspace")

        # 清除残留图片
        await self.page.evaluate("""() => {
            const editor = document.querySelector('#editor, .editor-content, [contenteditable="true"]');
            if (editor) editor.querySelectorAll('img').forEach(img => img.remove());
        }""")

        for _ in range(3):
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.2)

        sohu_logger.success("[清空] 编辑器已清空")

    async def fill_title(self, title: str):
        """填写文章标题（30 字限制）。"""
        truncated = title[:30]
        sohu_logger.info(f"[标题] 填写: {truncated}")

        title_input = self.page.locator(SELECTORS["title_input"]).first
        await title_input.click(timeout=TIMEOUTS["click"])
        await title_input.fill(truncated)

        await self._screenshot("03_title_filled")
        sohu_logger.success("[标题] 已填写")

    async def fill_content(self, content: str):
        """填写正文。contenteditable 编辑器使用 execCommand('insertHTML')。"""
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
                const editor = document.querySelector('#editor, .editor-content, [contenteditable="true"]');
                if (editor) {
                    editor.focus();
                    document.execCommand('insertHTML', false, html);
                }
            }""", html_content)

        await self._screenshot("04_content_filled")
        sohu_logger.success("[正文] 已填写")

    async def upload_images(self, image_paths: list[Path]):
        """上传图片。通过 file input 上传。"""
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

        # 找到 file input 并上传
        file_input = self.page.locator(SELECTORS["image_file_input"]).first
        try:
            await file_input.wait_for(state="attached", timeout=TIMEOUTS["click"])
            await file_input.set_input_files(valid_images)
        except Exception:
            # 备选：尝试通过封面上传按钮触发 file input
            sohu_logger.info("[图片] 尝试通过上传按钮触发...")
            try:
                cover_btn = self.page.locator(SELECTORS["cover_upload"]).first
                if await cover_btn.count() > 0:
                    await cover_btn.click()
                    await asyncio.sleep(1)
                    file_input2 = self.page.locator("input[type='file']").first
                    await file_input2.set_input_files(valid_images)
            except Exception as e:
                sohu_logger.warning(f"[图片] 上传失败: {e}")
                return

        # 等待上传完成
        for _ in range(15):
            upload_done = await self.page.evaluate("""() => {
                const loading = document.querySelector('.ant-upload-animate, .anticon-loading, .uploading');
                return !loading;
            }""")
            if upload_done:
                break
            await asyncio.sleep(2)

        await self._screenshot("05_images_uploaded")
        sohu_logger.success(f"[图片] {len(valid_images)} 张图片已上传")

    async def publish(self):
        """点击发布按钮。"""
        sohu_logger.info("[发布] 点击发布按钮...")

        await self.dismiss_popups()

        publish_btn = self.page.locator(SELECTORS["publish_btn"]).first
        try:
            await publish_btn.click(timeout=TIMEOUTS["click"])
        except Exception:
            sohu_logger.warning("[发布] 直接点击失败，尝试 JS 点击...")
            await self.page.evaluate("""() => {
                const btn = document.querySelector('button.publish-btn');
                if (btn) {
                    btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                }
            }""")

        await asyncio.sleep(3)
        await self._screenshot("06_after_publish")

    async def verify_publish_success(self) -> bool:
        """验证发布是否成功。"""
        sohu_logger.info("[验证] 验证发布结果...")

        success_keywords = ["发布成功", "提交成功", "审核", "已发布"]
        error_keywords = ["发布失败", "请填写", "不能为空"]

        for attempt in range(10):
            url = self.page.url
            body_text = await self.page.evaluate(
                "() => document.body.innerText.substring(0, 2000)"
            )

            for kw in success_keywords:
                if kw in body_text:
                    sohu_logger.success(f"[验证] 发布成功（检测到 '{kw}'）")
                    return True

            if "article/new" not in url and "edit" not in url:
                sohu_logger.success(f"[验证] 已跳转到 {url[:60]}")
                return True

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
        """执行完整的文章发布流程。"""
        sohu_logger.info(f"{'=' * 20} 开始发布: {self.title} {'=' * 20}")

        try:
            # 启动浏览器
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--lang=zh-CN",
                "--no-sandbox",
            ]
            if not self.headless:
                launch_args.append("--start-maximized")
            options = {"headless": self.headless, "args": launch_args}
            if LOCAL_CHROME_PATH:
                options["executable_path"] = LOCAL_CHROME_PATH

            self._browser = await playwright.chromium.launch(**options)

            context_options = {"locale": "zh-CN"}
            if self.account_file and Path(self.account_file).exists():
                context_options["storage_state"] = self.account_file
            else:
                raise CookieExpiredError(f"Cookie 文件不存在: {self.account_file}")

            self._context = await self._browser.new_context(**context_options)
            self._context = await set_init_script(self._context)
            self._page = await self._context.new_page()
            sohu_logger.info("[启动] 浏览器已启动")

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

            # 发布
            await editor.publish()

            # 验证
            success = await editor.verify_publish_success()

            # 保存 cookie
            account_path = Path(self.account_file)
            account_path.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(account_path))

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
            if self.debug and self._page:
                try:
                    await self._page.pause()
                except Exception:
                    pass
            return False
        finally:
            try:
                if self._context:
                    await self._context.close()
            except Exception:
                pass
            try:
                if self._browser:
                    await self._browser.close()
            except Exception:
                pass
            sohu_logger.info("[清理] 浏览器已关闭")
