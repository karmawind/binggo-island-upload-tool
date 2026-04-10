"""百家号图文文章发布器。

适配 social-auto-upload 框架，从 baijiahao-auto-poster 移植已验证的 DOM 交互逻辑。
"""

import asyncio
import random
from datetime import datetime
from pathlib import Path

from patchright.async_api import Page, async_playwright, Playwright

from conf import BASE_DIR, LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.log import baijiahao_logger


class EditorPage:
    """百家号图文编辑器的页面交互模型。

    所有 DOM 选择器集中管理在此类中，方便百家号改版后统一修改。
    """

    EDITOR_URL = "https://baijiahao.baidu.com/builder/rc/edit?type=news"
    HOME_URL = "https://baijiahao.baidu.com/builder/rc/home"

    def __init__(self, page: Page):
        self.page = page

    async def navigate_to_editor(self):
        """导航到图文编辑页面。"""
        baijiahao_logger.info("正在打开图文编辑器...")
        await self.page.goto(self.EDITOR_URL, timeout=60000)
        await self.page.wait_for_url("**/builder/rc/edit**", timeout=60000)

        # 检测是否被重定向到登录页
        if await self.page.get_by_text("注册/登录百家号").count():
            raise CookieExpiredError("Cookie 已失效，被重定向到登录页")

        baijiahao_logger.success("编辑器已打开")

    async def dismiss_guides(self):
        """关闭百家号编辑器的新手引导弹窗。"""
        await asyncio.sleep(2)

        has_guide = await self.page.evaluate("""
            () => {
                const texts = document.body.innerText;
                return texts.includes('下一步') || texts.includes('完成');
            }
        """)
        if not has_guide:
            baijiahao_logger.debug("未检测到新手引导")
            return

        baijiahao_logger.info("检测到新手引导，开始逐步跳过...")

        for step in range(10):
            await asyncio.sleep(1)
            clicked = await self.page.evaluate("""
                (texts) => {
                    for (const text of texts) {
                        const elements = document.querySelectorAll('button, a, span, div[role="button"]');
                        for (const el of elements) {
                            if (el.innerText.trim() === text && el.offsetParent !== null) {
                                el.click();
                                return text;
                            }
                        }
                    }
                    return null;
                }
            """, ["下一步", "完成", "我知道了", "知道了", "跳过", "关闭"])
            if clicked:
                baijiahao_logger.info(f"引导步骤 {step + 1}: 点击了 '{clicked}'")
            else:
                baijiahao_logger.info(f"引导步骤 {step + 1}: 未找到可点击按钮，引导结束")
                break

        await asyncio.sleep(1)
        baijiahao_logger.info("引导关闭处理完毕")

    async def wait_for_editor_ready(self):
        """等待编辑器完全加载，并关闭引导弹窗。"""
        try:
            await self.page.wait_for_selector(
                "input[placeholder*='标题'], div[contenteditable='true']",
                timeout=15000,
            )
            baijiahao_logger.debug("编辑器加载完毕")
        except Exception:
            baijiahao_logger.warning("等待编辑器加载超时，继续执行...")

        await self.dismiss_guides()

    async def _find_title_input(self):
        """尝试多种选择器定位标题输入框。"""
        selectors = [
            '[placeholder*="请输入标题"]',
            '[placeholder*="标题"]',
            '[data-placeholder*="标题"]',
            '[aria-placeholder*="标题"]',
        ]
        for sel in selectors:
            loc = self.page.locator(sel)
            if await loc.count() > 0:
                baijiahao_logger.debug(f"标题输入框定位成功: {sel}")
                return loc

        loc = self.page.locator("div[contenteditable='true']").first
        if await loc.count() > 0:
            baijiahao_logger.debug("标题输入框定位成功: div[contenteditable='true'].first")
            return loc

        raise Exception("未找到标题输入框")

    async def fill_title(self, title: str):
        """填写文章标题。"""
        title_input = await self._find_title_input()
        await title_input.click(timeout=10000)
        await asyncio.sleep(0.5)
        await title_input.fill("")
        await self.page.keyboard.type(title[:64], delay=random.randint(30, 60))
        baijiahao_logger.info(f"标题已填写: {title[:64]}")
        await self.page.keyboard.press("Tab")
        await asyncio.sleep(1)

    async def _get_content_frame(self):
        """获取 UEditor iframe 内的 frame locator。"""
        iframe_holder = self.page.locator(".edui-editor-iframeholder iframe")
        if await iframe_holder.count() > 0:
            baijiahao_logger.debug("找到 UEditor iframe")
            return self.page.frame_locator(".edui-editor-iframeholder iframe")

        editor_iframe = self.page.locator(".editor-outter-wrapper iframe")
        if await editor_iframe.count() > 0:
            baijiahao_logger.debug("找到编辑器 iframe")
            return self.page.frame_locator(".editor-outter-wrapper iframe")

        raise Exception("未找到正文编辑器 iframe")

    async def fill_content(self, content: str):
        """填写正文内容到 UEditor iframe 中。"""
        frame = self._get_content_frame()
        body = frame.locator("body")
        await body.click(timeout=10000)
        await asyncio.sleep(0.5)

        paragraphs = content.split("\n")
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            await self.page.keyboard.type(para, delay=random.randint(20, 50))
            if i < len(paragraphs) - 1:
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(random.uniform(0.3, 0.8))

        baijiahao_logger.info("正文已填写")

    async def upload_images(self, image_paths: list[Path | str]):
        """上传多张图片到文章（通过 UEditor 图片上传弹窗）。"""
        if not image_paths:
            return

        baijiahao_logger.info(f"开始上传 {len(image_paths)} 张图片...")

        # 关键前提：必须先 focus 编辑器 iframe body，否则图片按钮不会触发上传对话框
        try:
            frame = self._get_content_frame()
            body = frame.locator("body")
            await body.click(timeout=5000)
            await asyncio.sleep(0.5)
            baijiahao_logger.debug("已 focus 编辑器 iframe body")
        except Exception as e:
            baijiahao_logger.warning(f"focus iframe body 失败: {e}")

        # 点击工具栏 insertimage 按钮打开图片上传弹窗
        insertimage_btn = self.page.locator("div.edui-for-insertimage")
        if await insertimage_btn.count() > 0:
            await insertimage_btn.click()
            baijiahao_logger.info("已点击工具栏图片按钮，等待上传弹窗...")
            try:
                await self.page.wait_for_selector(
                    ".cheetah-upload input[type='file']",
                    state="attached",
                    timeout=10000,
                )
                baijiahao_logger.debug("图片上传弹窗已出现")
            except Exception:
                baijiahao_logger.warning("等待图片上传弹窗超时，尝试继续...")
        else:
            baijiahao_logger.warning("未找到 insertimage 按钮")

        image_file_input = self.page.locator(".cheetah-upload input[type='file']")

        for i, img_path in enumerate(image_paths):
            img_path = Path(img_path)
            if not img_path.exists():
                baijiahao_logger.warning(f"图片不存在，跳过: {img_path}")
                continue

            try:
                if await image_file_input.count() > 0:
                    await image_file_input.first.set_input_files(str(img_path))
                    baijiahao_logger.info(f"图片 {i + 1}/{len(image_paths)} 上传中: {img_path.name}")
                else:
                    baijiahao_logger.error(f"未找到图片 file input，跳过: {img_path.name}")

                await asyncio.sleep(random.uniform(2, 4))
            except Exception as e:
                baijiahao_logger.error(f"上传图片失败: {img_path.name}，错误: {e}")

        # 点击确认按钮
        await asyncio.sleep(3)
        confirm_btn = self.page.locator(
            ".cheetah-ui-pro-image-modal button:has-text('确认')"
        )
        if await confirm_btn.count() > 0:
            await confirm_btn.click()
            baijiahao_logger.info("已确认图片上传")
            await asyncio.sleep(1)

        baijiahao_logger.info("所有图片上传完毕")

    async def wait_for_images_processed(self, timeout: int = 120):
        """等待所有图片上传处理完成。"""
        baijiahao_logger.info("等待图片处理完成...")
        elapsed = 0
        while elapsed < timeout:
            uploading = await self.page.locator("text=上传中").count()
            if not uploading:
                baijiahao_logger.success("图片处理完成")
                return
            if elapsed % 10 == 0:
                baijiahao_logger.debug(f"图片仍在处理中... ({elapsed}s)")
            await asyncio.sleep(2)
            elapsed += 2
        baijiahao_logger.warning(f"图片处理等待超时 ({timeout}s)，继续执行...")

    async def select_cover(self):
        """选择封面图（从正文中选择第一张图作为单图封面）。"""
        baijiahao_logger.info("开始选择封面图...")

        # 选择"单图"封面模式
        single_cover = self.page.locator(".cheetah-radio-wrapper:has-text('单图')")
        if await single_cover.count() > 0:
            await single_cover.first.click()
            baijiahao_logger.debug("已选择单图封面模式")
            await asyncio.sleep(1)

        # 点击"选正文图"区域
        select_btn = self.page.locator("div._93c3fe2a3121c388-item")
        if await select_btn.count() > 0:
            await select_btn.click()
            baijiahao_logger.info("已点击选正文图")
            await asyncio.sleep(2)

            # 用 JS 点击第一张可选图片的容器
            await self.page.evaluate("""
                () => {
                    const wrappers = document.querySelectorAll('.cheetah-modal-wrap [class*="imgWrapper"]');
                    for (const w of wrappers) {
                        const img = w.querySelector('img');
                        if (img && img.src) {
                            w.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                            return;
                        }
                    }
                }
            """)
            await asyncio.sleep(1)

            # 用 JS 点击确认按钮
            await self.page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('.cheetah-modal-wrap button');
                    for (const btn of btns) {
                        const text = btn.innerText?.trim();
                        if (text === '确认' || text === '确定') {
                            btn.click();
                            return;
                        }
                    }
                }
            """)
            await asyncio.sleep(2)

            baijiahao_logger.success("封面图已选择")
        else:
            baijiahao_logger.warning("未找到选正文图按钮，跳过封面选择")

    async def set_schedule_and_publish(self, publish_date: datetime):
        """设置定时发布。"""
        baijiahao_logger.info(f"设置定时发布: {publish_date.strftime('%Y-%m-%d %H:%M')}")

        schedule_btn = self.page.locator(
            "div.op-btn-outter-content >> text=定时发布"
        ).locator("..").locator("button")
        await schedule_btn.click()
        await self.page.wait_for_selector("div.select-wrap:visible", timeout=5000)
        await asyncio.sleep(2)

        publish_day = self._format_day(publish_date)
        for _ in range(3):
            try:
                await self.page.locator("div.select-wrap").nth(0).click()
                await self.page.wait_for_selector(
                    "div.rc-virtual-list div.cheetah-select-item", timeout=5000
                )
                await self.page.locator(
                    f"div.rc-virtual-list div.cheetah-select-item >> text={publish_day}"
                ).click()
                break
            except Exception:
                await asyncio.sleep(1)
        await asyncio.sleep(2)

        publish_hour = f"{publish_date.hour}点"
        for _ in range(3):
            try:
                await self.page.locator("div.select-wrap").nth(1).click()
                await self.page.wait_for_selector(
                    "div.rc-virtual-list:visible div.cheetah-select-item-option",
                    timeout=5000,
                )
                await self.page.locator(
                    f"div.rc-virtual-list:visible div.cheetah-select-item-option >> text={publish_hour}"
                ).click()
                break
            except Exception:
                await asyncio.sleep(1)
        await asyncio.sleep(2)

        publish_min = f"{publish_date.minute}分"
        for _ in range(3):
            try:
                await self.page.locator("div.select-wrap").nth(2).click()
                await self.page.wait_for_selector(
                    "div.rc-virtual-list:visible div.cheetah-select-item-option",
                    timeout=5000,
                )
                await self.page.locator(
                    f"div.rc-virtual-list:visible div.cheetah-select-item-option >> text={publish_min}"
                ).click()
                break
            except Exception:
                await asyncio.sleep(1)
        await asyncio.sleep(1)

        await self.page.locator("button >> text=定时发布").click()
        baijiahao_logger.success("定时发布已设置")

    async def _dismiss_modal(self):
        """关闭或确认页面上的弹窗。"""
        modal = self.page.locator(".cheetah-modal-wrap:visible")
        if await modal.count() == 0:
            return False

        baijiahao_logger.info("检测到弹窗，尝试处理...")

        for text in ["确定", "确认", "继续", "是", "发布", "提交", "OK"]:
            btn = modal.locator(f"button:has-text('{text}')")
            if await btn.count() > 0:
                try:
                    await btn.first.click(timeout=5000)
                except Exception:
                    await btn.first.click(force=True)
                baijiahao_logger.info(f"点击弹窗按钮: {text}")
                await asyncio.sleep(1)
                return True

        for text in ["取消", "关闭", "返回修改"]:
            btn = modal.locator(f"button:has-text('{text}')")
            if await btn.count() > 0:
                await btn.first.click()
                baijiahao_logger.info(f"关闭弹窗: {text}")
                await asyncio.sleep(1)
                return True

        baijiahao_logger.warning("弹窗未处理，尝试 Escape 关闭")
        await self.page.keyboard.press("Escape")
        await asyncio.sleep(1)
        return False

    async def publish_immediately(self):
        """立即发布。"""
        # 关闭所有可能残留的弹窗/遮罩
        for _ in range(3):
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

        publish_btn = self.page.locator('[data-testid="publish-btn"]')
        if await publish_btn.count() == 0:
            publish_btn = self.page.get_by_test_id("publish-btn")
        await publish_btn.click(force=True)
        baijiahao_logger.info("已点击发布按钮")

        await asyncio.sleep(3)
        await self._dismiss_modal()

    async def verify_publish_success(self) -> bool:
        """验证发布是否成功（检测页面跳转或审核提示）。"""
        await asyncio.sleep(3)

        # 检测百度安全验证
        captcha = self.page.locator("div.passMod_dialog-container >> text=百度安全验证")
        if await captcha.count():
            baijiahao_logger.error("出现百度安全验证，请使用 --headed 模式手动处理")
            return False

        for _ in range(10):
            url = self.page.url
            body_text = await self.page.evaluate(
                "() => document.body.innerText.substring(0, 1000)"
            )

            if "/builder/rc/clue" in url or "/builder/rc/home" in url:
                baijiahao_logger.success("文章发布成功（已跳转）!")
                return True

            success_keywords = [
                "审核", "已发布", "发布成功", "提交成功", "作品管理",
            ]
            for kw in success_keywords:
                if kw in body_text:
                    baijiahao_logger.success(f"文章发布成功（检测到'{kw}'）!")
                    return True

            error_elements = self.page.locator(
                ".error-message, .ant-message-error, .cheetah-message-error"
            )
            if await error_elements.count():
                error_text = await error_elements.first.text_content()
                baijiahao_logger.error(f"发布失败: {error_text}")
                return False

            await self._dismiss_modal()
            await asyncio.sleep(2)

        baijiahao_logger.warning("未检测到明确的发布成功信号")
        return False

    @staticmethod
    def _format_day(publish_date: datetime) -> str:
        """格式化日期为百家号选择器文本。"""
        day_str = f"{publish_date.month}月{publish_date.day}日"
        if publish_date.day < 10:
            day_str = f"{publish_date.month}月0{publish_date.day}日"
        return day_str


class CookieExpiredError(Exception):
    pass


class SecurityCaptchaError(Exception):
    pass


class PublishError(Exception):
    pass


class BaiJiaHaoArticle:
    """百家号图文文章发布器。

    协调浏览器管理、页面交互、cookie 保存的完整生命周期。
    """

    def __init__(
        self,
        title: str,
        content: str,
        image_paths: list[str],
        tags: list[str] | None = None,
        publish_date: datetime | int = 0,
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
        """入口方法：创建 Playwright 实例并执行上传。"""
        async with async_playwright() as playwright:
            return await self.upload(playwright)

    async def upload(self, playwright: Playwright) -> bool:
        """执行完整的图文文章发布流程。"""
        baijiahao_logger.info(f"===== 开始发布: {self.title} =====")

        try:
            # Step 1: 启动浏览器 + 加载 cookie
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
            baijiahao_logger.info("浏览器已启动")

            # Step 2: 打开编辑器
            editor = EditorPage(self._page)
            await editor.navigate_to_editor()

            # Step 3: 等待编辑器加载
            await editor.wait_for_editor_ready()
            await asyncio.sleep(1)

            # Step 4: 填写标题
            await editor.fill_title(self.title)

            # Step 5: 填写正文
            if self.content:
                await editor.fill_content(self.content)

            # Step 6: 上传图片
            await editor.upload_images(self.image_paths)

            # Step 7: 等待图片处理完成
            if self.image_paths:
                await editor.wait_for_images_processed(timeout=120)

            # Step 8: 选择封面图
            if self.image_paths:
                await editor.select_cover()

            # Step 9: 发布（定时或立即）
            if self.publish_date != 0 and isinstance(self.publish_date, datetime):
                await editor.set_schedule_and_publish(self.publish_date)
            else:
                await editor.publish_immediately()

            # Step 10: 验证发布结果
            success = await editor.verify_publish_success()

            # Step 11: 保存 cookie
            account_path = Path(self.account_file)
            account_path.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(account_path))
            baijiahao_logger.info("Cookie 已更新")

            if success:
                baijiahao_logger.success(f"===== 发布完成: {self.title} =====")
            else:
                baijiahao_logger.warning(f"===== 发布结果未确认: {self.title} =====")

            return success

        except CookieExpiredError:
            baijiahao_logger.error("Cookie 已失效，请重新登录")
            return False
        except SecurityCaptchaError:
            baijiahao_logger.error("遇到百度安全验证，请在 --headed 模式下手动处理")
            return False
        except Exception as e:
            baijiahao_logger.error(f"发布失败: {e}")

            if self.debug and self._page:
                baijiahao_logger.info(
                    "【调试模式】浏览器已暂停，请手动检查页面 DOM。"
                )
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
            baijiahao_logger.info("浏览器已关闭")
