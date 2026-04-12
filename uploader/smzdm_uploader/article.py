# -*- coding: utf-8 -*-
"""什么值得买图文文章发布器。

适配 social-auto-upload 框架，基于 ProseMirror 编辑器的 DOM 交互。

发布流程（人工操作步骤）：
1. 关闭升级弹窗（div.upgrade-tip-btn "立即体验"）
2. 填写标题（textarea.article-title）
3. 填写正文（div.ProseMirror）
4. 上传图片到正文（工具栏图片按钮 → 本地上传 → input[type=file] → 插入正文）
5. 添加长图封面（div.img-upload-btn → input[type=file] → 设为封面图 → 确定此图 → 确认）
6. 发布（.publish-btn）
"""

import asyncio
from pathlib import Path

from patchright.async_api import Page, async_playwright, Playwright

from conf import LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.log import smzdm_logger


class EditorPage:
    """什么值得买编辑器页面交互模型。"""

    EDITOR_URL = "https://post.smzdm.com/edit/a70658o9"
    HOME_URL = "https://www.smzdm.com"

    def __init__(self, page: Page):
        self.page = page

    async def navigate_to_editor(self):
        """导航到文章编辑页面。"""
        smzdm_logger.info("正在打开发帖页面...")
        await self.page.goto(self.EDITOR_URL, timeout=60000)
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        if "login" in self.page.url.lower() or "passport" in self.page.url.lower():
            raise CookieExpiredError("Cookie 已失效，被重定向到登录页")

        smzdm_logger.success("发帖页面已打开")

    async def dismiss_upgrade_tip(self):
        """关闭"立即体验"升级弹窗。"""
        try:
            upgrade_btn = self.page.locator("div.upgrade-tip-btn")
            if await upgrade_btn.count() > 0 and await upgrade_btn.is_visible():
                await upgrade_btn.click()
                smzdm_logger.info("已关闭升级弹窗")
                await asyncio.sleep(1)
        except Exception:
            pass

    async def wait_for_editor_ready(self):
        """等待编辑器加载完成。"""
        try:
            await self.page.wait_for_selector(
                "textarea.article-title, div.ProseMirror",
                timeout=15000,
            )
            smzdm_logger.debug("编辑器加载完毕")
        except Exception:
            smzdm_logger.warning("等待编辑器加载超时，继续执行...")

        await self.dismiss_upgrade_tip()

    async def clear_editor(self):
        """清空编辑器中的标题和正文，确保从空白状态开始。"""
        smzdm_logger.info("清空编辑器...")

        # 清空标题
        title_input = self.page.locator("textarea.article-title")
        if await title_input.count() > 0:
            await title_input.click()
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Backspace")
            smzdm_logger.debug("标题已清空")

        # 清空正文（ProseMirror）
        editor = self.page.locator("div.ProseMirror")
        if await editor.count() > 0:
            await editor.click()
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Backspace")
            smzdm_logger.debug("正文已清空")

        # 清除可能残留的图片（正文中的 img 标签）
        await self.page.evaluate("""() => {
            const editor = document.querySelector('div.ProseMirror');
            if (editor) {
                const imgs = editor.querySelectorAll('img');
                imgs.forEach(img => img.remove());
            }
        }""")

        # 关闭所有残留弹窗/面板
        for _ in range(3):
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.3)

        # 删除残留的遮罩面板
        await self.page.evaluate("""() => {
            document.querySelectorAll('.upload-container-scroll, .insert-wrap, .pic-upload-btn, .pics, div[class*="sortable"]').forEach(el => {
                if (el.offsetParent !== null) el.remove();
            });
        }""")

        smzdm_logger.success("编辑器已清空")

    async def fill_title(self, title: str):
        """填写文章标题（一次性填入）。"""
        smzdm_logger.info(f"填写标题: {title[:50]}")
        title_input = self.page.locator("textarea.article-title")
        await title_input.click(timeout=10000)
        await title_input.fill(title[:30])
        smzdm_logger.success("标题已填写")

    async def fill_content(self, content: str):
        """填写正文内容到 ProseMirror 编辑器（一次性填入）。"""
        if not content:
            return

        smzdm_logger.info("开始填写正文...")

        editor = self.page.locator("div.ProseMirror")
        await editor.click(timeout=10000)
        await asyncio.sleep(0.3)

        # 用 ProseMirror 的 insertContent 原生方法一次性写入
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
                    // ProseMirror: 用 insertHTML 一次性写入
                    editor.focus();
                    document.execCommand('insertHTML', false, html);
                }
            }""", html_content)

        smzdm_logger.success("正文已填写")

    async def upload_images_to_content(self, image_paths: list[Path]):
        """上传图片到正文编辑器中。

        流程：点击工具栏图片按钮 → 本地上传 → 等待上传完成 → 插入正文
        """
        if not image_paths:
            return

        smzdm_logger.info(f"开始上传 {len(image_paths)} 张图片到正文...")

        # 先关闭残留面板
        await self._close_residual_panels()

        # 收集有效图片
        valid_images = []
        for img_path in image_paths:
            img_path = Path(img_path)
            if not img_path.exists():
                smzdm_logger.warning(f"图片不存在，跳过: {img_path}")
                continue

            file_size = img_path.stat().st_size
            if file_size < 500 * 1024:
                smzdm_logger.warning(f"图片小于 500KB，可能上传失败: {img_path.name} ({file_size / 1024:.0f}KB)")
            if file_size > 8 * 1024 * 1024:
                smzdm_logger.warning(f"图片大于 8MB，可能上传失败: {img_path.name} ({file_size / 1024 / 1024:.1f}MB)")
            valid_images.append(str(img_path))

        if not valid_images:
            return

        # 点击图片按钮打开上传面板（用 JS 点击避免遮挡）
        await self.page.evaluate("""() => {
            const svg = document.querySelector('svg.zicon-picture');
            if (!svg) return;
            const btn = svg.closest('button');
            const target = btn || svg;
            target.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        }""")
        smzdm_logger.info("已点击工具栏图片按钮")
        await asyncio.sleep(1)

        # 在面板中找到 file input 并上传
        file_input = self.page.locator('input[type="file"][accept*="image"]').first
        await file_input.wait_for(state="attached", timeout=10000)
        await file_input.set_input_files(valid_images)
        smzdm_logger.info(f"已上传 {len(valid_images)} 张图片，等待处理...")

        # 等待上传完成
        await asyncio.sleep(5)

        # 点击"插入正文"按钮（div.btn-item "插入正文"）
        insert_btn = self.page.locator("div.btn-item:has-text('插入正文')")
        if await insert_btn.count() > 0:
            await insert_btn.first.click()
            smzdm_logger.info("已点击'插入正文'")
            await asyncio.sleep(2)
        else:
            smzdm_logger.warning("未找到'插入正文'按钮")

        smzdm_logger.success("所有图片已插入正文")

    async def upload_cover_image(self, image_path: str | Path):
        """上传封面图（长图）。

        通过工具栏图片按钮上传，然后设为封面。
        流程：点击图片按钮 → 上传 → 设为封面图 → 确定此图 → 确认
        """
        if not image_path:
            return

        image_path = Path(image_path)
        if not image_path.exists():
            smzdm_logger.warning(f"封面图不存在，跳过: {image_path}")
            return

        smzdm_logger.info(f"上传封面图: {image_path.name}")

        # 先关闭可能残留的面板
        await self._close_residual_panels()

        # 点击工具栏图片按钮打开上传面板（用 JS 点击避免遮挡）
        await self.page.evaluate("""() => {
            const svg = document.querySelector('svg.zicon-picture');
            if (!svg) return;
            const btn = svg.closest('button');
            const target = btn || svg;
            target.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        }""")
        smzdm_logger.info("已点击工具栏图片按钮（封面）")
        await asyncio.sleep(1)

        # 找到 file input 并上传封面图
        file_input = self.page.locator('input[type="file"][accept*="image"]').first
        await file_input.wait_for(state="attached", timeout=10000)
        await file_input.set_input_files(str(image_path))
        smzdm_logger.info("封面图上传中...")
        await asyncio.sleep(5)

        # 等待上传完成
        for _ in range(10):
            has_preview = await self.page.evaluate("""() => {
                const imgs = document.querySelectorAll('.pic-upload-btn img, .upload-container-scroll img');
                return imgs.length > 0;
            }""")
            if has_preview:
                break
            await asyncio.sleep(2)

        # 点击上传的图片（设为封面）
        await self.page.evaluate("""() => {
            const imgs = document.querySelectorAll('.pic-upload-btn img, .upload-container-scroll img');
            if (imgs.length > 0) imgs[0].click();
        }""")
        smzdm_logger.info("已点击上传图片（设为封面）")
        await asyncio.sleep(1)

        # 点击"确定此图"
        await self.page.evaluate("""() => {
            const btns = document.querySelectorAll('button.cancel-btn');
            for (const btn of btns) {
                if (btn.innerText.includes('确定此图')) { btn.click(); return; }
            }
        }""")
        smzdm_logger.info("已点击'确定此图'")
        await asyncio.sleep(1)

        # 点击"确认"
        await self.page.evaluate("""() => {
            const btns = document.querySelectorAll('button.ok-btn');
            for (const btn of btns) {
                if (btn.innerText.includes('确认')) { btn.click(); return; }
            }
        }""")
        smzdm_logger.info("已点击'确认'")
        await asyncio.sleep(2)

        await self._close_residual_panels()
        smzdm_logger.success("封面图设置完成")

    async def _close_residual_panels(self):
        """关闭可能残留的图片上传面板/弹窗。"""
        await self.page.evaluate("""() => {
            // 关闭上传容器滚动面板
            const panels = document.querySelectorAll('.upload-container-scroll, .insert-wrap, .pic-upload-btn');
            panels.forEach(p => {
                if (p.offsetParent !== null) {
                    // 尝试找关闭按钮
                    const closeBtn = p.querySelector('.close, .btn-close, [class*=close]');
                    if (closeBtn) closeBtn.click();
                }
            });
            // 按 Escape 关闭弹窗
            document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', code: 'Escape', bubbles: true}));
        }""")
        await self.page.keyboard.press("Escape")
        await asyncio.sleep(0.5)

    async def set_declaration(self, interest_related: str = "否", ai_generated: str = "否"):
        """设置创作声明（利益相关 + AI生成）。用 JS 点击绕过 mask 遮罩。"""
        smzdm_logger.info("设置创作声明...")

        groups = self.page.locator(".el-radio-group.checkbox-type-raio-group")
        count = await groups.count()

        if count >= 1:
            await self._click_radio_by_text(groups.nth(0), interest_related, "利益相关性")
        if count >= 2:
            await self._click_radio_by_text(groups.nth(1), ai_generated, "AI生成合成")

    async def _click_radio_by_text(self, group, target_text: str, label: str):
        """用 JS 点击 radio 组中匹配文本的选项（绕过 mask 遮罩）。"""
        radios = group.locator(".el-radio")
        radio_count = await radios.count()
        for i in range(radio_count):
            text = await radios.nth(i).inner_text()
            if text.strip() == target_text:
                await radios.nth(i).evaluate("el => el.click()")
                smzdm_logger.info(f"{label}: {target_text}")
                return
        smzdm_logger.warning(f"{label}: 未找到选项 '{target_text}'")

    async def publish(self):
        """点击发布按钮。用 JS 强制点击避免被遮挡。"""
        smzdm_logger.info("点击发布按钮...")
        await asyncio.sleep(1)

        # 先关闭所有残留面板
        await self._close_residual_panels()

        await self.page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)

        # 用 JS 点击发布按钮
        clicked = await self.page.evaluate("""() => {
            const btn = document.querySelector('.publish-btn');
            if (btn) {
                btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
                btn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                return true;
            }
            return false;
        }""")

        if clicked:
            smzdm_logger.info("已通过 JS 点击发布按钮")
        else:
            raise PublishError("未找到发布按钮")

        await asyncio.sleep(3)

    async def verify_publish_success(self) -> bool:
        """验证发布是否成功。"""
        smzdm_logger.info("验证发布结果...")
        await asyncio.sleep(3)

        for attempt in range(10):
            url = self.page.url
            body_text = await self.page.evaluate(
                "() => document.body.innerText.substring(0, 2000)"
            )

            smzdm_logger.debug(f"验证轮次 {attempt + 1}: URL={url[:80]}")

            success_keywords = ["提交成功", "发布成功", "审核", "已提交", "待审核"]
            for kw in success_keywords:
                if kw in body_text:
                    smzdm_logger.success(f"发布成功（检测到 '{kw}'）")
                    return True

            if "/edit/" not in url and "post.smzdm.com" not in url:
                smzdm_logger.success(f"发布成功（已跳转到 {url}）")
                return True

            error_keywords = ["发布失败", "错误", "失败"]
            for kw in error_keywords:
                if kw in body_text:
                    smzdm_logger.error(f"发布失败（检测到 '{kw}'）")
                    return False

            await asyncio.sleep(2)

        smzdm_logger.warning("未检测到明确的发布成功信号")
        return False


class CookieExpiredError(Exception):
    pass


class PublishError(Exception):
    pass


class SmzdmArticle:
    """什么值得买图文文章发布器。"""

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
        smzdm_logger.info(f"===== 开始发布: {self.title} =====")

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
            smzdm_logger.info("浏览器已启动")

            # Step 2: 打开编辑器 + 等待加载 + 关闭弹窗
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

            # Step 5: 先添加长图封面（此时 file input 还可用）
            if self.image_paths:
                await editor.upload_cover_image(self.image_paths[0])

            # Step 6: 上传图片到正文（会打开上传面板并关闭）
            if self.image_paths:
                await editor.upload_images_to_content(self.image_paths)

            # Step 7: 设置创作声明
            await editor.set_declaration()

            # Step 8: 发布
            await editor.publish()

            # Step 9: 验证发布结果
            success = await editor.verify_publish_success()

            # Step 10: 保存 cookie
            account_path = Path(self.account_file)
            account_path.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(account_path))
            smzdm_logger.info("Cookie 已更新")

            if success:
                smzdm_logger.success(f"===== 发布完成: {self.title} =====")
            else:
                smzdm_logger.warning(f"===== 发布结果未确认: {self.title} =====")

            return success

        except CookieExpiredError:
            smzdm_logger.error("Cookie 已失效，请重新登录")
            return False
        except Exception as e:
            smzdm_logger.error(f"发布失败: {e}")
            if self.debug and self._page:
                smzdm_logger.info("【调试模式】浏览器已暂停")
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
            smzdm_logger.info("浏览器已关闭")
