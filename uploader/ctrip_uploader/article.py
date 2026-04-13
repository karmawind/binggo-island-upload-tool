# -*- coding: utf-8 -*-
"""携程内容中心图文笔记发布器。

适配 social-auto-upload 框架，基于 Draft.js 编辑器的 DOM 交互。

携程图文发布页面: https://we.ctrip.com/publish/publishPictureText

发布流程：
1. 导航到发布首页 (publishHome)
2. 点击"发布图文"进入编辑器
3. 等待编辑器加载
4. 清空编辑器（从空白状态开始）
5. 填写标题（Draft.js contenteditable）
6. 填写描述正文（Draft.js contenteditable）
7. 上传图片（ant-upload file input, 最多 20 张）
8. 发布
"""

import asyncio
from pathlib import Path

from patchright.async_api import Page, async_playwright, Playwright

from conf import LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.log import ctrip_logger


class EditorPage:
    """携程内容中心编辑器页面交互模型。"""

    HOME_URL = "https://we.ctrip.com/?accountsource=c"
    PUBLISH_HOME_URL = "https://we.ctrip.com/publish/publishHome"
    EDITOR_URL = "https://we.ctrip.com/publish/publishPictureText"

    def __init__(self, page: Page):
        self.page = page

    async def navigate_to_editor(self):
        """导航到图文发布页面。直接打开编辑器 URL，跳过发布首页。"""
        ctrip_logger.info("正在打开图文发布页面...")
        await self.page.goto(self.EDITOR_URL, timeout=60000)
        await self.page.wait_for_load_state("domcontentloaded")

        # 检查是否被重定向到登录页
        body_text = await self.page.evaluate(
            "() => document.body?.innerText?.substring(0, 500) || ''"
        )
        if "个人登录" in body_text and "发布内容" not in body_text:
            raise CookieExpiredError("Cookie 已失效，页面显示登录")

        ctrip_logger.success("发帖页面已打开")

    async def wait_for_editor_ready(self):
        """等待编辑器加载完成。"""
        ctrip_logger.info("等待编辑器加载...")
        try:
            await self.page.wait_for_selector(
                "div.public-DraftEditor-content", timeout=15000
            )
            ctrip_logger.debug("Draft.js 编辑器加载完毕")
        except Exception:
            ctrip_logger.warning("等待编辑器加载超时，继续执行...")

    async def clear_editor(self):
        """清空编辑器中的标题和正文，确保从空白状态开始。"""
        ctrip_logger.info("清空编辑器...")

        # 清空标题区域（第一个 DraftEditor）
        title_editors = await self.page.evaluate("""() => {
            const editors = document.querySelectorAll('div.public-DraftEditor-content');
            return editors.length;
        }""")
        ctrip_logger.debug(f"找到 {title_editors} 个 DraftEditor")

        # 清空第一个编辑器（标题）
        if title_editors >= 1:
            title_editor = self.page.locator("div.public-DraftEditor-content").first
            await title_editor.click()
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Backspace")
            ctrip_logger.debug("标题已清空")

        # 清空第二个编辑器（描述正文）
        if title_editors >= 2:
            desc_editor = self.page.locator("div.public-DraftEditor-content").nth(1)
            await desc_editor.click()
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Backspace")
            ctrip_logger.debug("正文已清空")

        await asyncio.sleep(0.5)
        ctrip_logger.success("编辑器已清空")

    async def fill_title(self, title: str):
        """填写笔记标题。标题区域是 Draft.js 编辑器，必须用键盘输入。"""
        ctrip_logger.info(f"填写标题: {title[:50]}")

        # 点击标题编辑器（第一个 DraftEditor）
        title_editor = self.page.locator("div.public-DraftEditor-content").first
        await title_editor.click(timeout=10000)

        # Draft.js 是 React 状态管理，必须用键盘输入
        await self.page.keyboard.type(title[:20], delay=20)

        ctrip_logger.success("标题已填写")

    async def fill_content(self, content: str):
        """填写描述正文。正文也是 Draft.js 编辑器，必须用键盘输入。"""
        if not content:
            return

        ctrip_logger.info("开始填写正文...")

        # 找到描述编辑器并用 JS 定位并 focus
        await self.page.evaluate("""() => {
            const editors = document.querySelectorAll('div.public-DraftEditor-content');
            // 跳过第一个（标题），找描述编辑器
            for (let i = 1; i < editors.length; i++) {
                const editor = editors[i];
                const titleBody = editor.closest('.r-d-upload-image-title') ||
                                  editor.closest('div.editor-body');
                if (!titleBody) {
                    editor.focus();
                    return;
                }
            }
            // 如果都没找到，用第二个
            if (editors.length >= 2) {
                editors[1].focus();
            }
        }""")

        # 准备文本（将换行转为分段）
        paragraphs = content.split("\n")
        full_text = "\n".join(p.strip() for p in paragraphs if p.strip())

        # 使用 insertText 一次性输入（Draft.js 支持此方式，比逐字输入快得多）
        await self.page.keyboard.insert_text(full_text[:3000])

        ctrip_logger.success("正文已填写")

    async def fill_location(self, location: str):
        """填写地点。携程要求必须添加至少一个地点才能发布。"""
        if not location:
            return

        ctrip_logger.info(f"填写地点: {location}")

        # 找到"添加地点"按钮/输入框并点击
        # 携程使用 ant-select 或类似的可搜索选择器
        location_input = await self.page.evaluate("""() => {
            // 尝试多种选择器
            const selectors = [
                'input[placeholder*="地点"]',
                'input[placeholder*="添加地点"]',
                'input[placeholder*="搜索地点"]',
                '.ant-select-selection-search-input',
                'input[class*="location"]',
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) {
                    el.focus();
                    el.click();
                    return sel;
                }
            }
            // 尝试通过文本找"添加地点"区域
            const spans = document.querySelectorAll('span, div, p, a');
            for (const span of spans) {
                if (span.innerText?.trim() === '添加地点' || span.innerText?.trim() === '添加地点+') {
                    span.click();
                    return 'text:添加地点';
                }
            }
            return null;
        }""")
        ctrip_logger.info(f"地点输入框定位: {location_input}")
        await asyncio.sleep(1)

        if location_input:
            # 在搜索框中输入地点
            await self.page.keyboard.type(location, delay=50)
            await asyncio.sleep(2)

            # 等待下拉列表出现并选择第一个选项
            selected = await self.page.evaluate("""() => {
                // ant-select 下拉选项
                const items = document.querySelectorAll(
                    '.ant-select-item-option, .ant-select-dropdown .ant-select-item, [class*="dropdown"] [class*="item"]'
                );
                if (items.length > 0) {
                    items[0].click();
                    return { count: items.length, selected: items[0].innerText?.substring(0, 50) };
                }
                return { count: 0 };
            }""")
            ctrip_logger.info(f"地点选择结果: {selected}")
        else:
            ctrip_logger.warning("未找到地点输入框，尝试备用方案...")
            # 备用方案：用 Playwright locator
            try:
                loc_input = self.page.locator('input[placeholder*="地点"]')
                if await loc_input.count() > 0:
                    await loc_input.first.click()
                    await asyncio.sleep(0.5)
                    await self.page.keyboard.type(location, delay=50)
                    await asyncio.sleep(2)
                    # 选择下拉第一个
                    first_option = self.page.locator('.ant-select-item-option').first
                    await first_option.click(timeout=5000)
                    ctrip_logger.info("备用方案成功选择地点")
            except Exception as e:
                ctrip_logger.warning(f"备用方案也失败: {e}")

        await asyncio.sleep(1)
        ctrip_logger.success("地点已填写")

    async def upload_images(self, image_paths: list[Path]):
        """上传图片。携程使用 ant-upload 组件，file input 支持 multiple。"""
        if not image_paths:
            return

        ctrip_logger.info(f"开始上传 {len(image_paths)} 张图片...")

        # 收集有效图片
        valid_images = []
        for img_path in image_paths:
            img_path = Path(img_path)
            if not img_path.exists():
                ctrip_logger.warning(f"图片不存在，跳过: {img_path}")
                continue
            valid_images.append(str(img_path))

        if not valid_images:
            return

        if len(valid_images) > 20:
            ctrip_logger.warning(f"图片超过 20 张，只上传前 20 张")
            valid_images = valid_images[:20]

        # 找到 file input 并上传
        file_input = self.page.locator('input[type="file"][accept="image/*"]').first
        await file_input.wait_for(state="attached", timeout=10000)
        await file_input.set_input_files(valid_images)
        ctrip_logger.info(f"已上传 {len(valid_images)} 张图片，等待处理...")

        # 等待上传完成
        for _ in range(30):
            upload_done = await self.page.evaluate("""() => {
                // 检查是否有上传进度条
                const progress = document.querySelector('.ant-upload-animate, .anticon-loading');
                if (progress) return false;
                // 检查是否有已上传的图片缩略图
                const thumbs = document.querySelectorAll('.ant-upload-list-item-done, img[src*="blob"]');
                return thumbs.length >= 1;
            }""")
            if upload_done:
                break
            await asyncio.sleep(2)

        await asyncio.sleep(2)
        ctrip_logger.success("所有图片已上传")

    async def publish(self):
        """点击发布按钮。"""
        ctrip_logger.info("点击发布按钮...")
        await asyncio.sleep(1)

        # 发布前截图诊断
        await self._debug_screenshot("before_publish")

        # 点击"发 布"按钮（注意文字中间有空格）
        publish_btn = self.page.locator("button.ant-btn-primary:has-text('发 布')")
        try:
            await publish_btn.click(timeout=10000)
            ctrip_logger.info("已点击'发布'按钮")
        except Exception:
            ctrip_logger.warning("直接点击失败，尝试 JS 点击...")
            await self.page.evaluate("""() => {
                const btns = document.querySelectorAll('button.ant-btn-primary');
                for (const btn of btns) {
                    if (btn.innerText?.trim() === '发 布' || btn.innerText?.trim() === '发布') {
                        btn.click();
                        return true;
                    }
                }
                return false;
            }""")

        await asyncio.sleep(3)

        # 发布后检查是否有验证错误
        await self._check_publish_errors()

        # 发布后截图诊断
        await self._debug_screenshot("after_publish")

    async def verify_publish_success(self) -> bool:
        """验证发布是否成功。"""
        ctrip_logger.info("验证发布结果...")
        await asyncio.sleep(3)

        for attempt in range(15):
            url = self.page.url
            body_text = await self.page.evaluate(
                "() => document.body.innerText.substring(0, 3000)"
            )

            ctrip_logger.debug(f"验证轮次 {attempt + 1}: URL={url[:80]}")

            # 检查错误关键词
            error_keywords = ["请填写", "不能为空", "请选择", "发布失败", "请输入", "请添加"]
            for ekw in error_keywords:
                if ekw in body_text:
                    ctrip_logger.error(f"检测到验证错误 '{ekw}'，发布可能被阻止")
                    # 尝试获取更详细的错误信息
                    errors = await self.page.evaluate("""() => {
                        const errorEls = document.querySelectorAll('.ant-message-error, .ant-form-explain, .ant-alert-error, [class*="error"], [class*="Error"]');
                        return Array.from(errorEls).map(e => e.innerText?.trim()).filter(t => t);
                    }""")
                    if errors:
                        ctrip_logger.error(f"错误详情: {errors}")
                    return False

            success_keywords = ["发布成功", "提交成功", "已发布", "存草稿成功"]
            for kw in success_keywords:
                if kw in body_text:
                    ctrip_logger.success(f"发布成功（检测到 '{kw}'）")
                    return True

            # URL 离开发布页
            if "publishPictureText" not in url and "publish" not in url:
                ctrip_logger.success(f"发布成功（已跳转到 {url[:60]}）")
                return True

            await asyncio.sleep(2)

        ctrip_logger.warning("未检测到明确的发布成功信号")
        # 最终截图
        await self._debug_screenshot("verify_timeout")
        return False

    async def _debug_screenshot(self, label: str):
        """调试截图，保存到 logs/ 目录。"""
        try:
            from pathlib import Path
            screenshot_dir = Path("logs")
            screenshot_dir.mkdir(exist_ok=True)
            path = screenshot_dir / f"ctrip_{label}.png"
            await self.page.screenshot(path=str(path), full_page=False)
            ctrip_logger.info(f"调试截图已保存: {path}")
        except Exception as e:
            ctrip_logger.debug(f"截图失败: {e}")

    async def _check_publish_errors(self):
        """检查发布后是否有验证错误弹窗。"""
        try:
            # 检查 ant-design 消息提示
            messages = await self.page.evaluate("""() => {
                const results = [];
                // ant message
                document.querySelectorAll('.ant-message-notice, .ant-notification-notice').forEach(el => {
                    results.push(el.innerText?.trim());
                });
                // form validation
                document.querySelectorAll('.ant-form-explain, .ant-form-item-has-error').forEach(el => {
                    results.push(el.innerText?.trim());
                });
                // modal/dialog
                document.querySelectorAll('.ant-modal-content, .ant-confirm-body').forEach(el => {
                    results.push(el.innerText?.substring(0, 200));
                });
                return results.filter(t => t);
            }""")
            if messages:
                ctrip_logger.warning(f"检测到页面消息: {messages}")

            # 检查页面是否有明显的错误/提示文本
            page_text = await self.page.evaluate(
                "() => document.body.innerText.substring(0, 1000)"
            )
            for kw in ["请填写", "不能为空", "请选择地点", "请添加地点"]:
                if kw in page_text:
                    ctrip_logger.error(f"发布验证失败，页面包含: '{kw}'")

        except Exception as e:
            ctrip_logger.debug(f"错误检查异常: {e}")


class CookieExpiredError(Exception):
    pass


class PublishError(Exception):
    pass


class CtripArticle:
    """携程内容中心图文笔记发布器。"""

    def __init__(
        self,
        title: str,
        content: str = "",
        image_paths: list[str] | None = None,
        tags: list[str] | None = None,
        location: str = "",
        publish_date=None,
        account_file: str = "",
        headless: bool = True,
        debug: bool = False,
    ):
        self.title = title
        self.content = content
        self.image_paths = [Path(p) for p in (image_paths or [])]
        self.tags = tags or []
        self.location = location
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
        """执行完整的图文笔记发布流程。"""
        ctrip_logger.info(f"===== 开始发布: {self.title} =====")

        try:
            # Step 1: 启动浏览器
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--lang=zh-CN",
                "--no-sandbox",
            ]
            if not self.headless:
                launch_args.append("--start-maximized")
            options = {
                "headless": self.headless,
                "args": launch_args,
            }
            if LOCAL_CHROME_PATH:
                options["executable_path"] = LOCAL_CHROME_PATH

            self._browser = await playwright.chromium.launch(**options)

            context_options = {"locale": "zh-CN"}
            if self.account_file and Path(self.account_file).exists():
                context_options["storage_state"] = self.account_file

            self._context = await self._browser.new_context(**context_options)
            self._context = await set_init_script(self._context)
            self._page = await self._context.new_page()
            ctrip_logger.info("浏览器已启动")

            # Step 2: 打开编辑器
            editor = EditorPage(self._page)
            await editor.navigate_to_editor()
            await editor.wait_for_editor_ready()
            await editor.clear_editor()

            # Step 3: 上传图片（携程要求先上传图片）
            if self.image_paths:
                await editor.upload_images(self.image_paths)

            # Step 4: 填写标题
            await editor.fill_title(self.title)

            # Step 5: 填写正文
            if self.content:
                await editor.fill_content(self.content)

            # Step 5.5: 填写地点（必填）
            if self.location:
                await editor.fill_location(self.location)

            # Step 6: 发布
            await editor.publish()

            # Step 7: 验证发布结果
            success = await editor.verify_publish_success()

            # Step 8: 保存 cookie
            account_path = Path(self.account_file)
            account_path.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(account_path))
            ctrip_logger.info("Cookie 已更新")

            if success:
                ctrip_logger.success(f"===== 发布完成: {self.title} =====")
            else:
                ctrip_logger.warning(f"===== 发布结果未确认: {self.title} =====")

            return success

        except CookieExpiredError:
            ctrip_logger.error("Cookie 已失效，请重新登录")
            return False
        except Exception as e:
            ctrip_logger.error(f"发布失败: {e}")
            if self.debug and self._page:
                ctrip_logger.info("【调试模式】浏览器已暂停")
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
            ctrip_logger.info("浏览器已关闭")
