# Changelog

All notable changes to `social-auto-upload` will be documented in this file.

## [0.2.4] - 2026-04-14

### Fixed

- **搜狐号图文发布完整流程验证通过** — 通过 Chrome DevTools MCP 实际发布验证，修复所有已知问题
- **编辑器类型识别错误** — 编辑器实际为 Quill.js（`.ql-editor`），而非简单 contenteditable；选择器从 `[contenteditable='true']` 修正为 `.ql-editor`
- **SPA 路由跳转导致标题选择器失效** — `history.pushState` 跳转未正确渲染编辑器 DOM，改为直接 `goto(editor_url)` 导航
- **发布按钮选择器错误** — 发布按钮是 `<li>` 元素（`li.positive-button.publish-report-btn`），不是 `<button>`
- **缺少发布确认弹窗处理** — 搜狐号发布有两步确认："确认发布文章么？" → 点"确定"
- **图片上传流程重写** — 通过工具栏 image 按钮打开上传弹窗，而非直接找 hidden file input
- **编辑器 URL 更新** — 从旧版 `/api/author/article/new` 更新为 `/mpfe/v4/contentManagement/news/addarticle?contentStatus=1`
- **标题字数限制修正** — 从 30 字修正为 72 字（placeholder 明确标注"5-72字"）
- `main.py` 登录流程增加反检测参数和脚本

### Changed

- `CLAUDE.md` 搜狐号 SOP 从"参考项目"更新为实际验证的完整 SOP
- `skills/sohu-upload/` 全部文档同步更新

## [0.2.3] - 2026-04-13

### Added

- **搜狐号图文文章发布** — `sau sohu upload-article` 命令，支持标题、正文、多图片上传
- **搜狐号登录与 cookie 校验** — `sau sohu login` / `sau sohu check` 命令（mp.sohu.com 后台扫码登录）
- `uploader/sohu_uploader/__init__.py` — Cookie 目录初始化
- `uploader/sohu_uploader/main.py` — 登录流程（`sohu_cookie_gen` + `cookie_auth` + `sohu_setup`）
- `uploader/sohu_uploader/article.py` — `EditorPage` + `SohuArticle` 类，contenteditable 编辑器交互逻辑
- `utils/log.py` — 添加 `sohu_logger`
- 平台 ID 9 映射到搜狐号（`sau_cli.py`、`myUtils/postArticle.py`、`myUtils/auth.py`、`sau_backend.py`）

### Changed

- 前端系统名称支持 9 平台（新增搜狐号）
- `PLATFORM_DISPATCH` 和 `PLATFORM_NAMES` 新增 `{9: 'sohu'}`
- `ARTICLE_CLI_PLATFORMS` 新增 `{9: 'sohu'}`

## [0.2.2] - 2026-04-13

### Fixed

- **携程图文发布导航慢（1 分钟+）** — `navigate_to_editor()` 先加载 publishHome 再点按钮再跳转编辑器，两次页面加载 + 多处固定 sleep。改为直接 `goto(EDITOR_URL)` + `wait_for_load_state("domcontentloaded")`，跳过发布首页
- **携程标题/正文输入慢** — `fill_title()` 逐字输入 delay=50ms、调试 JS 遍历所有编辑器、两处 sleep(0.5)、验证 JS；`fill_content()` 调试 `__editor_debug`、两处 sleep。删除所有调试代码和不必要 sleep，标题输入 delay 从 50ms 降到 20ms
- **携程编辑器等待多余 sleep** — `wait_for_editor_ready()` 末尾 sleep(2) 和 `clear_editor()` 后 sleep(1) 均已删除

### Changed

- 携程图文发布整体响应时间从 1 分钟+ 降至约 10 秒

## [0.2.1] - 2026-04-13

### Fixed

- **什么值得买登录检测选择器失效** — 什么值得买首页改版后 `a.nickname`、`a[href*='hai']` 等旧选择器全部失效，`wait_for_selector` 永远等不到登录成功。改为 `a.name-link`、`a[href*='zhiyou.smzdm.com/user']`、`a[href*='user/logout']`
- **后端 CLI 登录子进程编码崩溃** — subprocess 用 `encoding='utf-8'` 读取 stdout，遇到什么值得买 GBK 中文输出抛 `UnicodeDecodeError`，导致登录成功但后端无法检测。改为 binary 模式读取 + `decode('utf-8', errors='replace')` 容错
- **后端 CLI 登录子进程卡死** — `for line in proc.stdout` 阻塞读取，CLI 子进程不退出时后端永远卡住。改为独立线程读取 + 180 秒超时 `proc.kill()` 保护
- **后端 cookie 新鲜度检查 10 秒窗口过窄** — CLI 保存 cookie 后关闭浏览器需要数秒，加上 stdout 管道延迟，经常超过 10 秒导致误判登录失败。改为检查 `exit_code == 0 and cookie_file.exists()`
- **什么值得买编辑器页面导航无超时** — `smzdm_cookie_gen` 登录后跳转编辑器页面验证时可能卡住。改为 15 秒超时 + try/except 保护
- **start.bat Windows 兼容性** — 修复 UTF-8 编码导致 CMD 解析乱码（改为纯 ASCII）、LF 换行改为 CRLF、`start` 命令引号嵌套问题
- **删除冗余 start-win.bat** — 未激活 venv、无环境检查，功能完全被 start.bat 覆盖

### Changed

- `pyproject.toml` version `0.1.0` → `0.2.0`
- `CLAUDE.md` 铁律路径从 `C:\Users\laoga\...` 绝对路径改为相对路径 `CHANGELOG.md`
- `CLAUDE.md` 携程 SOP 正文输入方法更新为 `keyboard.insert_text()`
- `requirements.txt` 修复 UTF-16 编码损坏，移除 `playwright`，添加 `patchright`/`Flask`/`flask-cors`/`opencv-python`
- `docs/install.md` Git clone URL 统一为当前仓库，补充百家号/什么值得买/头条号/携程 CLI 示例和 skill 引用
- `新手入门指南.md` 安装命令从 `pip install -r requirements.txt` 改为 `pip install -e .`
- `project-overview.md` 项目名称、平台数量（10）、携程输入方法同步更新
- `README.md` 携程编辑器表格同步更新

### Added

- `setup.sh` — Git Bash 一键安装脚本

## [0.2.0] - 2026-04-12

### Added

- **前端可视化图文发布系统** — 将 CLI 图文发布功能集成到 Web 前端，实现 8 平台统一管理
- **数据库扩展** — `article_posts`（帖子）和 `article_images`（图片）表，`platforms`（多平台）和 `scheduled_at`（定时）字段
- **后端图文发布 API** — 12+ 新端点（`/postArticle`、`/uploadImage`、`/saveArticlePost`、`/scheduleArticles`、`/importArticles` 等）
- **多平台并行分发** — 一篇帖子同时发到多个平台（百家号+什么值得买+头条号+携程），每平台独立线程
- **定时排期调度器** — 批量排期自动发布，后台线程每 60 秒检查到期帖子
- **CSV 批量导入** — 通过上传 CSV 文件批量创建帖子
- **CLI 登录集成到前端** — 前端添加图文平台账号时自动调用 CLI 登录，SSE 实时推送进度
- **编辑状态持久化** — Pinia `articleDraft` store，路由切换不丢失编辑状态
- **前端页面** — `ArticlePublish.vue`（多平台图文发布）、`ArticleManagement.vue`（帖子管理/筛选/排期/批量发布/CSV导入）

### Changed

- 前端系统名称改为"灵感岛推文分发器"，支持 8 平台（1=小红书 2=视频号 3=抖音 4=快手 5=百家号 6=什么值得买 7=头条号 8=携程）
- `AccountManagement.vue` 扩展至 8 平台 Tab，所有账号操作列新增"重新认证"按钮
- 什么值得买标题截断从 80 字改为 30 字（平台限制）
- 携程正文输入从 `keyboard.type()` 逐字输入改为 `keyboard.insert_text()` 一次性输入
- `start.bat` 改为纯英文，自动创建必要目录

### Key Fixes

- **`page.pause()` 不能用于生产环境** ⚠️ 最关键修复 — 百家号/什么值得买/头条号的登录函数都用了 `page.pause()` 等待用户操作，在后端 subprocess 中完全无效（浏览器打开即关闭）。全部改为轮询检测页面状态
- **Cookie 新鲜度误判** — 旧 cookie 文件导致重新认证时误判为成功。新增 10 秒修改时间检查
- **重新认证重复 INSERT** — 原逻辑只有 INSERT，重新认证时主键冲突。改为先查再决定 INSERT/UPDATE
- **数据库路径不一致** — `createTable.py` 用相对路径，从不同目录运行会创建错误位置的数据库。统一为 `__file__` 绝对路径
- **Pinia storeToRefs 陷阱** ⚠️ — `ref()` 属性通过 `store.property` 访问时被 Pinia 自动解包，`.value` 为 `undefined` 导致 TypeError 静默崩溃（按钮"无反应"）。改用 `storeToRefs()` 解构

### 端点一览

| 端点 | 方法 | 功能 |
|------|------|------|
| `/uploadImage` | POST | 上传图文图片 |
| `/getImages` | GET | 获取所有图片 |
| `/deleteImage` | GET | 删除图片 |
| `/postArticle` | POST | 发布图文（单平台/多平台） |
| `/articleTaskStatus` | GET | 查询发布任务进度 |
| `/getArticlePosts` | GET | 获取所有帖子 |
| `/saveArticlePost` | POST | 保存草稿 |
| `/updateArticlePost` | POST | 更新帖子 |
| `/deleteArticlePost` | GET | 删除帖子 |
| `/loginArticleAccount` | GET (SSE) | 图文平台 CLI 登录 |
| `/scheduleArticles` | POST | 批量排期 |
| `/importArticles` | POST | CSV 批量导入 |

## [0.1.5] - 2026-04-11

### Added

- **携程图文笔记发布** — `sau ctrip upload-article` 命令，支持标题、描述正文、多图片上传（最多 20 张，推荐宽高比 3:4~2:1）
- **携程登录与 cookie 校验** — `sau ctrip login` / `sau ctrip check` 命令（通过 we.ctrip.com 内容中心扫码登录）
- `uploader/ctrip_uploader/__init__.py` — Cookie 目录初始化
- `uploader/ctrip_uploader/main.py` — 登录流程（`ctrip_cookie_gen` + `cookie_auth` + `ctrip_setup`）
- `uploader/ctrip_uploader/article.py` — `EditorPage` + `CtripArticle` 类，完整的携程 Draft.js 编辑器交互逻辑
- `skills/ctrip-upload/` — 携程 skill 包（SKILL.md、CLI 契约、运行前提、故障排查）

### Changed

- `utils/log.py` — 添加 `ctrip_logger`
- `sau_cli.py` — 集成携程平台（import、dataclass、handler、parser、dispatch）
- `CLAUDE.md` — 添加携程平台信息和发布 SOP

### Key Fixes

- **Draft.js 编辑器交互** — 携程使用 Draft.js（非 ProseMirror 或 UEditor），标题和正文均为 `contenteditable` 的 `DraftEditor` 组件，`execCommand` 无效，**必须使用 `page.keyboard.type()` 逐字输入**
- **地点必填** — 携程要求必须添加至少一个地点，否则发布被阻止（错误提示"请添加一个地点！"）。已添加 `--location` 参数和 `fill_location()` 方法，使用 `ant-select` 搜索选择
- **图片上传** — 使用 `ant-upload` 组件的 file input 上传图片，需定位 `input[type='file']` 元素进行 `set_input_files`
- **发布按钮文本** — 按钮文字为"发 布"（中间有空格），需用 `has-text` 匹配时注意空格

### Verified

- 完整验证了携程图文发布全流程：登录 → cookie 校验 → 编辑器导航 → 清空编辑器 → 上传图片 → 填写标题 → 填写描述 → 填写地点 → 发布 → 跳转到内容管理页 → 检测到"已发布"关键词

## [0.1.4] - 2026-04-11

### Added

- **头条号图文文章发布** — `sau toutiao upload-article` 命令，支持标题、正文、多图片上传、封面自动设置、广告关闭
- **头条号登录与 cookie 校验** — `sau toutiao login` / `sau toutiao check` 命令（扫码登录）
- `uploader/toutiao_uploader/__init__.py` — Cookie 目录初始化
- `uploader/toutiao_uploader/main.py` — 登录流程（`toutiao_cookie_gen` + `cookie_auth` + `toutiao_setup`）
- `uploader/toutiao_uploader/article.py` — `EditorPage` + `ToutiaoArticle` 类，完整的头条号 ProseMirror 编辑器交互逻辑
- `skills/toutiao-upload/` — 头条号 skill 包（SKILL.md、CLI 契约、运行前提、故障排查）

### Changed

- `utils/log.py` — 添加 `toutiao_logger`
- `sau_cli.py` — 集成头条号平台（import、dataclass、handler、parser、dispatch）
- `CLAUDE.md` — 添加头条号平台信息和发布 SOP
- `start.md` — 添加头条号平台信息和测试示例

### Key Fixes

- **登录检测误判** — 头条号登录页本身有 20+ 个 `.avatar` 元素（平台 logo 和作者头像），导致 `cookie_gen` 误检测登录成功。改为检测 URL 离开登录/auth 页面
- **标题选择器不匹配** — placeholder 为 `请输入文章标题（2～30个字）`，需用 `*=` 模糊匹配
- **AI 助手遮罩拦截点击** — `div.ai-assistant-drawer` 和 `div.byte-drawer-mask` 遮罩拦截所有操作，需先移除
- **图片上传后未插入正文** — 上传图片后需点击"确定"按钮才能将图片插入 ProseMirror 编辑器
- **发布按钮两步确认** — 点击"预览并发布"后按钮变为"确认发布"，需再次点击才真正发布
- **广告设置** — 需手动设置"不投放广告"，否则默认选中"投放广告赚收益"

### Verified

- 完整验证了头条号图文发布全流程：登录 → cookie 校验 → 编辑器导航 → 清空编辑器 → 填写标题 → 填写正文 → 上传图片 → 插入正文 → 设置封面 → 不投放广告 → 预览并发布 → 确认发布 → 验证跳转到内容页

## [0.1.3] - 2026-04-11

### Added

- **什么值得买图文文章发布** — `sau smzdm upload-article` 命令，支持标题、正文、多图片上传（封面+正文图片）、创作声明设置
- **什么值得买登录与 cookie 校验** — `sau smzdm login` / `sau smzdm check` 命令（扫码登录）
- `uploader/smzdm_uploader/__init__.py` — Cookie 目录初始化
- `uploader/smzdm_uploader/main.py` — 登录流程（`smzdm_cookie_gen` + `cookie_auth` + `smzdm_setup`）
- `uploader/smzdm_uploader/article.py` — `EditorPage` + `SmzdmArticle` 类，完整的什么值得买 ProseMirror 编辑器交互逻辑
- `skills/smzdm-upload/` — 什么值得买 skill 包（SKILL.md、CLI 契约、运行前提、故障排查）

### Changed

- `utils/log.py` — 添加 `smzdm_logger`
- `sau_cli.py` — 集成什么值得买平台（import、dataclass、handler、parser、dispatch）
- `CLAUDE.md` — 添加什么值得买平台信息和发布 SOP

### Key Fixes

- **`btn.click is not a function`** — smzdm 工具栏 SVG 按钮的 `closest('button')` 可能返回非标准元素，`.click()` 失败。统一改为 `dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))`
- **编辑器残留状态** — `--headed` 模式连续测试时，上次的标题/正文/图片/遮罩面板残留在编辑器中，导致后续操作不可预测。添加 `clear_editor()` 方法，每次发布前彻底清空编辑器（标题、正文、残留图片、遮罩面板 DOM）

### Verified

- 完整验证了什么值得买图文发布全流程：登录 → cookie 校验 → 编辑器导航 → 清空编辑器 → 填写标题 → 填写正文 → 上传封面图 → 上传正文图片 → 创作声明 → 发布 → 验证"提交成功"
- 详细成功分析见 `docs/smzdm-success-analysis.md`

## [0.1.2] - 2026-04-10

### Fixed

- **编辑器导航重试** — 刚登录后导航到编辑器可能被重定向到首页（stoken → home），新增最多 3 次重试逻辑（每次等 3 秒）
- **编辑器 URL 修正** — `EDITOR_URL` 添加 `&is_from_cms=1` 参数，确保直接进入发布页面
- **正文填写方式** — 从 `innerHTML` 改为 `document.execCommand('insertHTML')`，修复 UEditor 不识别内容状态导致发布失败的问题
- **封面选择流程** — 不再点击"选正文图"按钮（会触发 30 秒禁用），改为直接点击封面容器 `div._73a3a52aab7e3a36-content`，自动加载正文图片后点击确定
- **发布按钮点击** — `.click()` 和 `force_click()` 均无效，改为 JS `dispatchEvent(new MouseEvent(...))` 并设置 `bubbles: true, cancelable: true`
- **新手引导处理** — 从必填步骤改为 try/except 非阻塞，首次发帖后不再出现引导
- **`async` 调用遗漏 `await`** — 修复 `_get_content_frame()` 两处缺少 `await` 导致的 `'coroutine' object has no attribute 'locator'` 错误
- **`baijiahao_setup` 签名兼容** — baijiahao 的 setup 函数不接受 `return_detail`/`headless` 参数，CLI handler 中用 try/except 包装
- **`main.py` playwright → patchright** — 百家号视频上传模块从 playwright 迁移到 patchright

### Verified

- 完整验证了百家号图文发布全流程：登录 → 编辑器导航 → 标题填写 → 正文填写 → 图片上传 → 封面选择 → 发布 → 成功跳转验证
- 推荐使用 `--headed` 模式，便于观察和调试

## [0.1.1] - 2026-04-10

### Added

- **百家号图文文章发布** — `sau baijiahao upload-article` 命令，支持标题、正文、图片上传、封面选择、定时/立即发布
- **百家号登录与 cookie 校验** — `sau baijiahao login` / `sau baijiahao check` 命令
- `uploader/baijiahao_uploader/article.py` — `EditorPage` + `BaiJiaHaoArticle` 类，包含完整的百家号 UEditor 编辑器交互逻辑
- `skills/baijiahao-upload/` — 百家号 skill 包（SKILL.md、CLI 契约、运行前提、故障排查、Bash/PowerShell/Python 模板）

### Changed

- `uploader/baijiahao_uploader/main.py` — playwright 迁移到 patchright
- `sau_cli.py` — 集成百家号平台（import、dataclass、handler、parser、dispatch）

## [0.1.0] - Initial

### Added

- `sau` CLI 入口，支持抖音、快手、小红书、B站
- 抖音：视频上传、图文发布、登录、cookie 校验
- 快手：视频上传、图文发布、登录、cookie 校验
- 小红书：视频上传、图文发布、登录、cookie 校验
- B站：视频上传（通过 biliup）、登录、cookie 校验
- `skills/douyin-upload/` skill 包
