"""
图文发布调度模块 — 参照 myUtils/postVideo.py 模式
直接导入各平台 Article 类，在独立线程中执行浏览器自动化。
"""

import asyncio
import logging
from pathlib import Path

from conf import BASE_DIR
from uploader.baijiahao_uploader.article import BaiJiaHaoArticle
from uploader.smzdm_uploader.article import SmzdmArticle
from uploader.toutiao_uploader.article import ToutiaoArticle
from uploader.ctrip_uploader.article import CtripArticle
from uploader.sohu_uploader.article import SohuArticle

logger = logging.getLogger(__name__)


def _run_in_thread(coro):
    """在新事件循环中运行协程（用于在后台线程中执行）。"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def post_article_baijiahao(title, content, image_paths, tags, account_files,
                           publish_date=0, callback=None):
    """发布百家号图文文章。"""
    cookie_paths = [str(Path(BASE_DIR / "cookiesFile" / f)) for f in account_files]
    img_paths = [str(Path(BASE_DIR / "imageFile" / img)) for img in image_paths]

    for cookie_path in cookie_paths:
        logger.info(f"百家号发布: title={title}, account={cookie_path}")

        async def _do():
            app = BaiJiaHaoArticle(
                title=title,
                content=content,
                image_paths=img_paths,
                tags=tags,
                publish_date=publish_date,
                account_file=cookie_path,
                headless=False,
            )
            return await app.main()

        success = _run_in_thread(_do())
        if callback:
            callback('baijiahao', cookie_path, success)
        logger.info(f"百家号发布结果: {success}")


def post_article_smzdm(title, content, image_paths, tags, account_files,
                       callback=None):
    """发布什么值得买图文文章。"""
    cookie_paths = [str(Path(BASE_DIR / "cookiesFile" / f)) for f in account_files]
    img_paths = [str(Path(BASE_DIR / "imageFile" / img)) for img in image_paths]

    for cookie_path in cookie_paths:
        logger.info(f"什么值得买发布: title={title}, account={cookie_path}")

        async def _do():
            app = SmzdmArticle(
                title=title,
                content=content,
                image_paths=img_paths,
                tags=tags,
                account_file=cookie_path,
                headless=False,
            )
            return await app.main()

        success = _run_in_thread(_do())
        if callback:
            callback('smzdm', cookie_path, success)
        logger.info(f"什么值得买发布结果: {success}")


def post_article_toutiao(title, content, image_paths, tags, account_files,
                         callback=None):
    """发布头条号图文文章。"""
    cookie_paths = [str(Path(BASE_DIR / "cookiesFile" / f)) for f in account_files]
    img_paths = [str(Path(BASE_DIR / "imageFile" / img)) for img in image_paths]

    for cookie_path in cookie_paths:
        logger.info(f"头条号发布: title={title}, account={cookie_path}")

        async def _do():
            app = ToutiaoArticle(
                title=title,
                content=content,
                image_paths=img_paths,
                tags=tags,
                account_file=cookie_path,
                headless=False,
            )
            return await app.main()

        success = _run_in_thread(_do())
        if callback:
            callback('toutiao', cookie_path, success)
        logger.info(f"头条号发布结果: {success}")


def post_article_ctrip(title, content, image_paths, tags, account_files,
                       location="", callback=None):
    """发布携程图文笔记。"""
    cookie_paths = [str(Path(BASE_DIR / "cookiesFile" / f)) for f in account_files]
    img_paths = [str(Path(BASE_DIR / "imageFile" / img)) for img in image_paths]

    for cookie_path in cookie_paths:
        logger.info(f"携程发布: title={title}, account={cookie_path}")

        async def _do():
            app = CtripArticle(
                title=title,
                content=content,
                image_paths=img_paths,
                tags=tags,
                location=location,
                account_file=cookie_path,
                headless=False,
            )
            return await app.main()

        success = _run_in_thread(_do())
        if callback:
            callback('ctrip', cookie_path, success)
        logger.info(f"携程发布结果: {success}")


def post_article_sohu(title, content, image_paths, tags, account_files,
                      callback=None):
    """发布搜狐号图文文章。"""
    cookie_paths = [str(Path(BASE_DIR / "cookiesFile" / f)) for f in account_files]
    img_paths = [str(Path(BASE_DIR / "imageFile" / img)) for img in image_paths]

    for cookie_path in cookie_paths:
        logger.info(f"搜狐号发布: title={title}, account={cookie_path}")

        async def _do():
            app = SohuArticle(
                title=title,
                content=content,
                image_paths=img_paths,
                tags=tags,
                account_file=cookie_path,
                headless=False,
            )
            return await app.main()

        success = _run_in_thread(_do())
        if callback:
            callback('sohu', cookie_path, success)
        logger.info(f"搜狐号发布结果: {success}")


# 平台类型 → 发布函数映射
PLATFORM_DISPATCH = {
    5: post_article_baijiahao,
    6: post_article_smzdm,
    7: post_article_toutiao,
    8: post_article_ctrip,
    9: post_article_sohu,
}

PLATFORM_NAMES = {5: 'baijiahao', 6: 'smzdm', 7: 'toutiao', 8: 'ctrip', 9: 'sohu'}


def dispatch_multi_platform(title, content, image_paths, tags,
                            platform_accounts, location="", callback=None):
    """
    多平台并行分发。

    platform_accounts: dict，{平台type: [cookie文件列表]}
        例如 {5: ['uuid1.json'], 7: ['uuid2.json']}

    callback: 回调函数 callback(platform_type, account, success)
    """
    import threading

    threads = []

    def _dispatch_one(platform_type, account_files):
        func = PLATFORM_DISPATCH.get(platform_type)
        if not func:
            logger.error(f"不支持的平台类型: {platform_type}")
            return

        kwargs = dict(
            title=title,
            content=content,
            image_paths=image_paths,
            tags=tags,
            account_files=account_files,
            callback=callback,
        )
        # 携程需要额外传 location
        if platform_type == 8:
            kwargs['location'] = location

        func(**kwargs)

    for platform_type, account_files in platform_accounts.items():
        t = threading.Thread(
            target=_dispatch_one,
            args=(platform_type, account_files),
            daemon=True,
        )
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()
