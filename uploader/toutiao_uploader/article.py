# -*- coding: utf-8 -*-
"""头条号图文文章发布器。

适配 social-auto-upload 框架，基于 ProseMirror 编辑器的 DOM 交互。

发布流程：
1. 导航到编辑器（https://mp.toutiao.com/profile_v4/graphic/publish）
2. 关闭 AI 助手遮罩和新手引导
3. 清空编辑器
4. 填写标题（textarea placeholder='请输入文章标题（2～30个字）'）
5. 填写正文（div.ProseMirror，execCommand insertHTML）
6. 上传图片（工具栏图片按钮 → 本地上传 → file input）
7. 发布（button '预览并发布'）
"""

import asyncio
from pathlib import Path

from patchright.async_api import Page, async_playwright, Playwright

from conf import LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.log import toutiao_logger


class EditorPage:
    """头条号编辑器页面交互模型。"""

    EDITOR_URL = "https://mp.toutiao.com/profile_v4/graphic/publish"
    HOME_URL = "https://mp.toutiao.com"

    def __init__(self, page: Page):
        self.page = page

    async def navigate_to_editor(self):
        """导航到文章编辑页面。"""
        toutiao_logger.info("正在打开发帖页面...")
        await self.page.goto(self.EDITOR_URL, timeout=60000)
        await asyncio.sleep(5)

        if "login" in self.page.url.lower() or "passport" in self.page.url.lower():
            raise CookieExpiredError("Cookie 已失效，被重定向到登录页")

        toutiao_logger.success("发帖页面已打开")

    async def wait_for_editor_ready(self):
        """等待编辑器加载完成。"""
        try:
            await self.page.wait_for_selector("div.ProseMirror", timeout=15000)
            toutiao_logger.debug("ProseMirror 编辑器加载完毕")
        except Exception:
            toutiao_logger.warning("等待编辑器加载超时，继续执行...")

        await asyncio.sleep(2)
        await self._close_overlays()

    async def _close_overlays(self):
        """关闭 AI 助手遮罩、新手引导等覆盖层。"""
        await self.page.evaluate("""() => {
            // 关闭 AI 助手抽屉及其遮罩
            const drawer = document.querySelector('div.ai-assistant-drawer');
            if (drawer) drawer.remove();
            document.querySelectorAll('div.byte-drawer-mask').forEach(el => el.remove());

            // 关闭新手引导 popover
            document.querySelectorAll('.mp-func-guide, .byte-popover').forEach(el => {
                if (el.offsetParent !== null) el.remove();
            });
        }""")
        await asyncio.sleep(0.5)

    async def clear_editor(self):
        """清空编辑器中的标题和正文，确保从空白状态开始。"""
        toutiao_logger.info("清空编辑器...")
        await self._close_overlays()

        # 清空标题
        title_input = self.page.locator("textarea[placeholder*='请输入文章标题']")
        if await title_input.count() > 0:
            await title_input.click()
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Backspace")
            toutiao_logger.debug("标题已清空")

        # 清空正文（ProseMirror）
        editor = self.page.locator("div.ProseMirror")
        if await editor.count() > 0:
            await editor.click()
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Backspace")
            toutiao_logger.debug("正文已清空")

        # 清除残留的图片
        await self.page.evaluate("""() => {
            const editor = document.querySelector('div.ProseMirror');
            if (editor) {
                editor.querySelectorAll('img').forEach(img => img.remove());
            }
        }""")

        # 关闭上传弹窗等残留面板
        await self._close_upload_panel()
        await asyncio.sleep(0.5)
        toutiao_logger.success("编辑器已清空")

    async def _close_upload_panel(self):
        """关闭图片上传面板。"""
        await self.page.evaluate("""() => {
            document.querySelectorAll('div.pgc-ic-imag, div.byte-drawer-mask').forEach(el => {
                if (el.offsetParent !== null) el.remove();
            });
        }""")
        await self.page.keyboard.press("Escape")
        await asyncio.sleep(0.3)

    async def fill_title(self, title: str):
        """填写文章标题。"""
        toutiao_logger.info(f"填写标题: {title[:50]}")
        title_input = self.page.locator("textarea[placeholder*='请输入文章标题']")
        await title_input.click(timeout=10000)
        await title_input.fill(title[:30])
        toutiao_logger.success("标题已填写")

    async def fill_content(self, content: str):
        """填写正文内容到 ProseMirror 编辑器。"""
        if not content:
            return

        toutiao_logger.info("开始填写正文...")

        editor = self.page.locator("div.ProseMirror")
        await editor.click(timeout=10000)
        await asyncio.sleep(0.3)

        # 将纯文本转为 HTML 段落
        paragraphs = content.split("\n")
        html_parts = []
        for para in paragraphs:
            p = para.strip()
            if p:
                html_parts.append(f"<p>{p}</p>")
        html_content = "".join(html_parts)

        if html_content:
            await self.page.evaluate("""(html) => {
                const editor = document.querySelector('div.ProseMirror');
                if (editor) {
                    editor.focus();
                    document.execCommand('insertHTML', false, html);
                }
            }""", html_content)

        toutiao_logger.success("正文已填写")

    async def upload_images(self, image_paths: list[Path]):
        """上传图片到正文编辑器。

        流程：点击工具栏图片按钮 → 本地上传 tab → file input → 等待上传
        """
        if not image_paths:
            return

        toutiao_logger.info(f"开始上传 {len(image_paths)} 张图片...")

        await self._close_overlays()
        await self._close_upload_panel()
        await asyncio.sleep(0.5)

        # 收集有效图片
        valid_images = []
        for img_path in image_paths:
            img_path = Path(img_path)
            if not img_path.exists():
                toutiao_logger.warning(f"图片不存在，跳过: {img_path}")
                continue
            file_size = img_path.stat().st_size
            if file_size > 20 * 1024 * 1024:
                toutiao_logger.warning(f"图片大于 20MB，可能上传失败: {img_path.name}")
            valid_images.append(str(img_path))

        if not valid_images:
            return

        # 点击工具栏图片按钮（用 JS dispatchEvent 绕过遮罩）
        await self.page.evaluate("""() => {
            const btn = document.querySelector('div.syl-toolbar-tool.image button');
            if (btn) {
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }""")
        toutiao_logger.info("已点击工具栏图片按钮")
        await asyncio.sleep(2)

        # 找到 file input 并上传
        file_input = self.page.locator('input[type="file"][accept*="image"]').first
        await file_input.wait_for(state="attached", timeout=10000)
        await file_input.set_input_files(valid_images)
        toutiao_logger.info(f"已上传 {len(valid_images)} 张图片，等待处理...")

        # 等待上传完成（面板显示"已上传 X 张图片"）
        for _ in range(15):
            upload_done = await self.page.evaluate("""() => {
                const panel = document.querySelector('.upload-image-panel, .pgc-ic-imag');
                return panel && panel.innerText?.includes('已上传');
            }""")
            if upload_done:
                break
            await asyncio.sleep(2)

        await asyncio.sleep(2)

        # 点击"确定"将图片插入正文
        confirm_btn = self.page.locator("button.byte-btn-primary:has-text('确定')")
        try:
            if await confirm_btn.count() > 0 and await confirm_btn.first.is_visible(timeout=5000):
                await confirm_btn.first.click()
                toutiao_logger.info("已点击'确定'将图片插入正文")
                await asyncio.sleep(2)
        except Exception:
            toutiao_logger.warning("未找到'确定'按钮")

        # 关闭上传面板
        await self._close_upload_panel()
        toutiao_logger.success("所有图片已插入正文")

    async def set_cover(self):
        """设置封面为单图模式（自动从正文图片中选择）和关闭广告。"""
        toutiao_logger.info("设置封面和广告选项...")

        # 关闭 AI 助手遮罩
        await self._close_overlays()
        await asyncio.sleep(0.5)

        # 设置广告为"不投放广告"
        try:
            ad_clicked = await self.page.evaluate("""() => {
                const labels = document.querySelectorAll('label, span, div');
                for (const l of labels) {
                    if (l.innerText?.trim() === '不投放广告') {
                        l.click();
                        return true;
                    }
                }
                return false;
            }""")
            if ad_clicked:
                toutiao_logger.info("已设置'不投放广告'")
        except Exception as e:
            toutiao_logger.warning(f"广告设置失败: {e}")

        # 封面区域，选择"单图"模式（默认已选中）
        cover_area = self.page.locator("div.article-cover")
        try:
            if await cover_area.count() > 0:
                await asyncio.sleep(1)
                toutiao_logger.success("封面设置完成")
            else:
                toutiao_logger.warning("未找到封面区域，跳过")
        except Exception as e:
            toutiao_logger.warning(f"封面设置异常: {e}")

    async def publish(self):
        """点击发布按钮。流程：预览并发布 → 确认发布。"""
        toutiao_logger.info("点击发布按钮...")

        await self._close_overlays()
        await self._close_upload_panel()
        await asyncio.sleep(1)

        # 点击"预览并发布"按钮
        publish_btn = self.page.locator("button.publish-btn.byte-btn-primary:has-text('预览并发布')")
        try:
            await publish_btn.click(timeout=10000)
            toutiao_logger.info("已点击'预览并发布'")
        except Exception:
            toutiao_logger.warning("直接点击失败，尝试 JS 点击...")
            clicked = await self.page.evaluate("""() => {
                const btns = document.querySelectorAll('button.publish-btn');
                for (const btn of btns) {
                    if (btn.innerText.includes('预览并发布')) {
                        btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                        return true;
                    }
                }
                return false;
            }""")
            if not clicked:
                raise PublishError("未找到发布按钮")

        await asyncio.sleep(3)

        # 等待按钮变为"确认发布"（可能先触发保存草稿）
        for _ in range(10):
            btn_text = await self.page.evaluate("""() => {
                const btns = document.querySelectorAll('button.publish-btn.byte-btn-primary');
                for (const btn of btns) {
                    if (btn.offsetParent !== null) {
                        return btn.innerText?.trim() || '';
                    }
                }
                return '';
            }""")
            if "确认发布" in btn_text:
                toutiao_logger.info("按钮已变为'确认发布'")
                break
            await asyncio.sleep(1)

        # 点击"确认发布"
        confirm_btn = self.page.locator("button.publish-btn.byte-btn-primary:has-text('确认发布')")
        try:
            await confirm_btn.click(timeout=10000)
            toutiao_logger.info("已点击'确认发布'")
        except Exception:
            toutiao_logger.warning("直接点击失败，尝试 JS 点击...")
            clicked = await self.page.evaluate("""() => {
                const btns = document.querySelectorAll('button.publish-btn');
                for (const btn of btns) {
                    if (btn.innerText.includes('确认发布')) {
                        btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                        return true;
                    }
                }
                return false;
            }""")
            if not clicked:
                toutiao_logger.warning("未找到'确认发布'按钮")

        await asyncio.sleep(3)

    async def verify_publish_success(self) -> bool:
        """验证发布是否成功。"""
        toutiao_logger.info("验证发布结果...")
        await asyncio.sleep(3)

        for attempt in range(10):
            url = self.page.url
            body_text = await self.page.evaluate(
                "() => document.body.innerText.substring(0, 2000)"
            )

            toutiao_logger.debug(f"验证轮次 {attempt + 1}: URL={url[:80]}")

            success_keywords = ["发布成功", "提交成功", "审核", "已提交", "待审核", "已发布"]
            for kw in success_keywords:
                if kw in body_text:
                    toutiao_logger.success(f"发布成功（检测到 '{kw}'）")
                    return True

            if "publish" not in url and "graphic" not in url:
                toutiao_logger.success(f"发布成功（已跳转离开编辑页到 {url[:60]}）")
                return True

            # 头条号发布后可能跳转到内容管理页
            if "content" in url or "article" in url:
                toutiao_logger.success(f"发布成功（已跳转到内容页 {url[:60]}）")
                return True

            await asyncio.sleep(2)

        toutiao_logger.warning("未检测到明确的发布成功信号")
        return False


class CookieExpiredError(Exception):
    pass


class PublishError(Exception):
    pass


class ToutiaoArticle:
    """头条号图文文章发布器。"""

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
        toutiao_logger.info(f"===== 开始发布: {self.title} =====")

        try:
            # Step 1: 启动浏览器
            options = {
                "headless": self.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--lang=zh-CN",
                    "--no-sandbox",
                ],
            }
            if LOCAL_CHROME_PATH:
                options["executable_path"] = LOCAL_CHROME_PATH

            self._browser = await playwright.chromium.launch(**options)

            context_options = {}
            if self.account_file and Path(self.account_file).exists():
                context_options["storage_state"] = self.account_file

            self._context = await self._browser.new_context(**context_options)
            self._context = await set_init_script(self._context)
            self._page = await self._context.new_page()
            toutiao_logger.info("浏览器已启动")

            # Step 2: 打开编辑器 + 等待加载 + 关闭遮罩
            editor = EditorPage(self._page)
            await editor.navigate_to_editor()
            await editor.wait_for_editor_ready()
            await editor.clear_editor()
            await asyncio.sleep(1)

            # Step 3: 填写标题
            await editor.fill_title(self.title)

            # Step 4: 填写正文
            if self.content:
                await editor.fill_content(self.content)

            # Step 5: 上传图片
            if self.image_paths:
                await editor.upload_images(self.image_paths)

            # Step 6: 设置封面
            if self.image_paths:
                await editor.set_cover()

            # Step 7: 发布
            await editor.publish()

            # Step 7: 验证发布结果
            success = await editor.verify_publish_success()

            # Step 8: 保存 cookie
            account_path = Path(self.account_file)
            account_path.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(account_path))
            toutiao_logger.info("Cookie 已更新")

            if success:
                toutiao_logger.success(f"===== 发布完成: {self.title} =====")
            else:
                toutiao_logger.warning(f"===== 发布结果未确认: {self.title} =====")

            return success

        except CookieExpiredError:
            toutiao_logger.error("Cookie 已失效，请重新登录")
            return False
        except Exception as e:
            toutiao_logger.error(f"发布失败: {e}")
            if self.debug and self._page:
                toutiao_logger.info("【调试模式】浏览器已暂停")
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
            toutiao_logger.info("浏览器已关闭")
