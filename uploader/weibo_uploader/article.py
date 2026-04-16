# -*- coding: utf-8 -*-
"""微博图文发布器（桌面版）。

适配 social-auto-upload 框架，使用桌面版 weibo.com 发帖。
通过 patchright launch + storage_state 加载 cookie 实现账号管理闭环。

微博是微客平台（短文本+图片），与文章平台不同：
- 无标题字段 — title 会拼接到 content 前面
- 无标签功能 — tags 参数被忽略
- 最多 9 张图片
- 最多约 2000 字

发布流程：
1. patchright launch + storage_state 加载 cookie
2. 导航到 weibo.com 首页
3. 点击"写微博"打开编辑弹窗
4. 填写正文（textarea）
5. 上传图片（input[type=file]._file_hqmwy_20）
6. 点击"发送"（button 发送）
7. 验证发布结果
"""

import asyncio
from pathlib import Path

from patchright.async_api import Page, async_playwright, Playwright

from utils.base_social_media import set_init_script
from utils.log import weibo_logger


SELECTORS = {
    # 正文输入（桌面版 textarea）
    "compose_textarea": 'textarea[placeholder="有什么新鲜事想分享给大家？"]',
    # 图片上传 file input
    "photo_input": 'input[type="file"]',
    # 发送按钮
    "send_btn": 'button.woo-button-primary',
    # 写微博按钮
    "write_btn": 'button',
}

TIMEOUTS = {
    "page_load": 60000,
    "click": 10000,
    "upload": 30000,
}

# 微博限制
MAX_IMAGES = 9
MAX_CONTENT_LENGTH = 2000


class EditorPage:
    """微博桌面版发帖页面交互模型。"""

    def __init__(self, page: Page, debug: bool = False):
        self.page = page
        self._debug = debug

    async def _screenshot(self, name: str):
        """debug 模式下自动截图。"""
        if not self._debug:
            return
        try:
            screenshot_dir = Path("logs")
            screenshot_dir.mkdir(exist_ok=True)
            path = screenshot_dir / f"weibo_{name}.png"
            await self.page.screenshot(path=str(path))
            weibo_logger.debug(f"[截图] {path}")
        except Exception:
            pass

    async def navigate_to_compose(self):
        """导航到微博桌面版首页，点击写微博打开编辑弹窗。"""
        weibo_logger.info("[导航] 正在打开微博桌面版...")
        await self.page.goto("https://weibo.com/", timeout=TIMEOUTS["page_load"])
        await asyncio.sleep(5)

        # 检查是否已登录（URL 不含 newlogin 且有用户头像）
        if "newlogin" in self.page.url:
            raise CookieExpiredError("Cookie 已失效，页面停留在登录页")

        has_avatar = await self.page.evaluate(
            "() => !!document.querySelector('img.woo-avatar-img')"
        )
        if not has_avatar:
            raise CookieExpiredError("Cookie 已失效，未检测到用户头像")

        await self._screenshot("01_home")

        # 点击"写微博"按钮打开编辑弹窗
        weibo_logger.info("[导航] 点击'写微博'按钮...")
        clicked = await self.page.evaluate("""() => {
            const btns = [...document.querySelectorAll('button')];
            const writeBtn = btns.find(b => b.textContent.trim().includes('写微博'));
            if (writeBtn) { writeBtn.click(); return true; }
            return false;
        }""")
        if not clicked:
            raise RuntimeError("未找到'写微博'按钮")

        await asyncio.sleep(2)
        await self._screenshot("02_compose")
        weibo_logger.success("[导航] 编辑弹窗已打开")

    async def clear_editor(self):
        """清空编辑器中的正文。"""
        weibo_logger.info("[清空] 清空编辑器...")
        # 关闭可能存在的弹窗，重新打开
        await self.page.keyboard.press("Escape")
        await asyncio.sleep(0.5)

        # 重新点击写微博
        await self.page.evaluate("""() => {
            const btns = [...document.querySelectorAll('button')];
            const writeBtn = btns.find(b => b.textContent.trim().includes('写微博'));
            if (writeBtn) writeBtn.click();
        }""")
        await asyncio.sleep(1)
        weibo_logger.success("[清空] 编辑器已清空")

    async def fill_content(self, title: str, content: str):
        """填写正文。微博无标题字段，title 拼接到 content 前面。"""
        parts = []
        if title:
            parts.append(title.strip())
        if content:
            parts.append(content.strip())
        text = "\n".join(parts)

        if not text:
            return

        text = text[:MAX_CONTENT_LENGTH]
        weibo_logger.info(f"[正文] 填写正文（{len(text)} 字）...")

        # 桌面版可能有多个 textarea（首页和弹窗各一个），取可见的那个
        textarea = self.page.locator(SELECTORS["compose_textarea"]).last
        await textarea.click(timeout=TIMEOUTS["click"])
        await asyncio.sleep(0.3)
        await textarea.fill(text)

        await self._screenshot("03_content_filled")
        weibo_logger.success("[正文] 已填写")

    async def upload_images(self, image_paths: list[Path]):
        """上传图片。通过 file input 上传。"""
        if not image_paths:
            return

        if len(image_paths) > MAX_IMAGES:
            weibo_logger.warning(f"[图片] 最多上传 {MAX_IMAGES} 张，截断为 {MAX_IMAGES} 张")
            image_paths = image_paths[:MAX_IMAGES]

        valid_images = []
        for img_path in image_paths:
            img_path = Path(img_path)
            if img_path.exists():
                valid_images.append(str(img_path))
            else:
                weibo_logger.warning(f"[图片] 不存在: {img_path}")

        if not valid_images:
            return

        weibo_logger.info(f"[图片] 上传 {len(valid_images)} 张图片...")

        # 桌面版有多个 file input，取最后一个（弹窗内的）
        photo_inputs = self.page.locator(SELECTORS["photo_input"])
        count = await photo_inputs.count()
        if count == 0:
            weibo_logger.error("[图片] 未找到文件上传 input")
            return

        await photo_inputs.nth(count - 1).set_input_files(valid_images)
        weibo_logger.info("[图片] 文件已选择，等待上传完成...")

        # 等待图片缩略图出现
        for attempt in range(15):
            has_preview = await self.page.evaluate("""() => {
                // 桌面版弹窗内图片预览
                const previews = document.querySelectorAll('[class*="composePic"], [class*="picPreview"], img[class*="preview"]');
                return previews.length > 0;
            }""")
            if has_preview:
                weibo_logger.info(f"[图片] 图片预览已出现（第 {attempt + 1} 次检测）")
                break
            await asyncio.sleep(2)

        await asyncio.sleep(2)
        await self._screenshot("04_images_uploaded")
        weibo_logger.success(f"[图片] {len(valid_images)} 张图片已上传")

    async def publish(self):
        """点击发送按钮。"""
        weibo_logger.info("[发布] 点击发送按钮...")
        await asyncio.sleep(1)

        # 桌面版弹窗内的发送按钮（取最后一个 woo-button-primary）
        send_btns = self.page.locator(SELECTORS["send_btn"])
        count = await send_btns.count()
        if count == 0:
            raise RuntimeError("未找到发送按钮")

        # 取最后一个发送按钮（弹窗内的）
        send_btn = send_btns.nth(count - 1)
        try:
            await send_btn.click(timeout=TIMEOUTS["click"])
            weibo_logger.info("[发布] 已点击发送按钮")
        except Exception:
            weibo_logger.warning("[发布] 按钮点击失败，尝试 JS 点击...")
            await self.page.evaluate("""() => {
                const btns = [...document.querySelectorAll('button.woo-button-primary')];
                const sendBtn = btns.find(b => b.textContent.trim() === '发送');
                if (sendBtn) sendBtn.click();
            }""")

        await asyncio.sleep(3)
        await self._screenshot("05_after_publish")

    async def verify_publish_success(self) -> bool:
        """验证发布是否成功。"""
        weibo_logger.info("[验证] 验证发布结果...")

        for attempt in range(10):
            # 检查页面 toast/提示
            body_text = await self.page.evaluate(
                "() => document.body.innerText.substring(0, 2000)"
            )

            success_keywords = ["发布成功", "发送成功", "已发送"]
            for kw in success_keywords:
                if kw in body_text:
                    weibo_logger.success(f"[验证] 发布成功（检测到 '{kw}'）")
                    return True

            # 弹窗关闭（textarea 消失）也说明发送成功
            textarea_count = await self.page.locator(
                'textarea[placeholder="有什么新鲜事想分享给大家？"]'
            ).count()
            if textarea_count <= 1:
                weibo_logger.success("[验证] 编辑弹窗已关闭，发布成功")
                return True

            await asyncio.sleep(2)

        await self._screenshot("06_verify_timeout")
        weibo_logger.warning("[验证] 未检测到明确结果")
        return False


class CookieExpiredError(Exception):
    pass


class PublishError(Exception):
    pass


class WeiboArticle:
    """微博图文发布器。"""

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
        """执行完整的微博发布流程。"""
        weibo_logger.info(f"{'=' * 20} 开始发布: {self.title or '(无标题)'} {'=' * 20}")

        try:
            weibo_logger.info("[启动] 启动 patchright 浏览器...")
            launch_args = [
                "--lang=zh-CN",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=AutomationControlled",
                "--disable-infobars",
                "--window-size=1280,800",
            ]
            self._browser = await playwright.chromium.launch(
                headless=self.headless, args=launch_args
            )

            storage_state = self.account_file if Path(self.account_file).exists() else None
            self._context = await self._browser.new_context(
                storage_state=storage_state,
                locale="zh-CN",
            )
            self._context = await set_init_script(self._context)

            self._page = await self._context.new_page()
            weibo_logger.info("[启动] 浏览器已启动")

            editor = EditorPage(self._page, debug=self.debug)

            # 导航到发帖页
            await editor.navigate_to_compose()

            # 填写正文（title + content 合并）
            await editor.fill_content(self.title, self.content)

            # 上传图片
            if self.image_paths:
                await editor.upload_images(self.image_paths)

            # 发布
            await editor.publish()

            # 验证
            success = await editor.verify_publish_success()

            if success:
                weibo_logger.success(f"{'=' * 20} 发布完成: {self.title or '(无标题)'} {'=' * 20}")
            else:
                weibo_logger.warning(f"{'=' * 20} 发布结果未确认: {self.title or '(无标题)'} {'=' * 20}")

            return success

        except CookieExpiredError as e:
            weibo_logger.error(f"[Cookie 失效] {e}")
            return False
        except Exception as e:
            weibo_logger.error(f"[异常] {e}")
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
            weibo_logger.info("[清理] 浏览器已关闭")
