# Changelog

All notable changes to `social-auto-upload` will be documented in this file.

## [0.3.0] - 2026-04-17

### Added

- **运营者管理系统** — 独立管理运营者（增/删/重命名），与账号解耦
  - 新增 `operators` 数据库表（迁移 v4）
  - 账号管理页新增「运营者管理」按钮，弹窗支持添加、重命名、删除运营者
  - 删除运营者时自动解除关联账号的绑定，重命名时自动同步关联账号
  - 添加账号弹窗新增运营者下拉选择（仅从已有运营者中选择）
  - 表格内运营者列可直接切换账号归属（单个转移）
  - 运营者筛选下拉：账号管理页、帖子管理页、图文发布页均支持按运营者过滤
- **帖子管理行内选账号** — 展开帖子行即可为每个平台选择发布账号，无需进入编辑页
  - 账号选择自动保存到 `article_posts.selected_accounts` 字段
  - 发布时优先使用绑定账号，兜底使用全部有效账号
- **批量选择账号发布** — 勾选多篇帖子后，弹窗统一选择各平台账号，一键批量发布
- **CLI --group 参数** — 登录时可通过 `--group 张三` 指定运营者分组
- **后端新接口** — `GET /getGroups`、`POST /addOperator`、`POST /deleteOperator`、`POST /renameOperator`、`POST /updateAccountGroup`、`POST /updatePostAccounts`

### Changed

- **调度器优化** — 排期发布时优先使用帖子绑定的 `selected_accounts`，而非全部有效账号
- **account store 补全** — `platformTypes` 补上 `9: '搜狐号'`、`10: '微博'`

### Fixed

- **start.bat 双开浏览器** — 去掉 bat 中手动打开浏览器的逻辑，保留 Vite 自动打开
- **图文发布默认选中百家号** — `selectedPlatforms` 默认值改为空数组
- **帖子管理显示"平台10"** — `PLATFORM_ID_TO_NAME` 补上 `10: '微博'`
- **CSV 模板缺少微博编号** — 后端模板说明补上 `10=微博`
- **帖子管理页语法错误** — 修复 `v-model` 使用可选链 `?.` 赋值导致的编译失败

## [0.3.2] - 2026-04-20

### Added

- **排期发布可选账号** — 排期对话框新增按平台选择发布账号的功能，选择结果写入帖子 `selected_accounts` 字段
  - 前端排期对话框自动收集选中帖子涉及的所有平台，按平台分组展示账号多选下拉
  - 不选账号时提示"不选则用全部账号"，走调度器兜底逻辑
  - 后端 `scheduleArticles` 接口新增 `accounts` 参数，排期时同时写入账号选择

## [0.3.1] - 2026-04-18

### Fixed

- **排期发布重复执行** — 调度器每 60 秒检查一次到期帖子，但发布一篇需要 30+ 秒，期间帖子仍是 `scheduled` 状态，导致下一轮重复拾取同一帖子，触发两次发帖。修复：拾取后立即标记为 `publishing`，防止重复
- **CSV 导入图片路径不兼容** — CSV 导入的 `image_paths` 是原始字符串（如 `C:/images/pic.png`），调度器 `json.loads()` 解析失败导致图片丢失。修复：`json.loads` 失败时 fallback 为逗号分隔解析
- **绝对路径图片无法发布** — 各平台发布函数把图片路径统一拼 `imageFile/` 前缀，但 CSV 导入的本地绝对路径（如 `C:\Users\...\pic.png`）拼接后路径错误。新增 `_resolve_image_paths()` 辅助函数，自动区分绝对路径和相对路径
- **CSV 模板优化** — 去掉多余的空行和提示行，新增微博示例（标题留空），标题列说明标注"微博留空"
- **排期间隔最小值** — 发布间隔从 10 分钟改为 1 分钟，步进 5 分钟
- **搜狐号 CDP 自动启动** — 搜狐发帖前自动检测 Chrome 调试模式（端口 9222），未启动则自动以 `--remote-debugging-port=9222` + 独立 profile 启动 Chrome，无需手动操作
- **搜狐号弹窗统一处理** — 重写 `publish()` 方法为统一循环：每轮检测 URL 跳转（发布成功）、"不足200字"警告弹窗、"确认发布文章么"确认弹窗，最多 5 轮，不再遗漏任何弹窗类型
- **搜狐号铁律** — CLAUDE.md 新增铁律：搜狐号必须使用 CDP 方式，禁止改为 `chromium.launch()`
- **新增 `start_chrome_debug.bat`** — 备用脚本，手动启动 Chrome 调试模式

## [0.2.8] - 2026-04-15

### Added

- **微博平台全流程支持** — 新增微博图文发布功能（平台 ID=10），覆盖后端、CLI、前端、技能包
  - 上传器：`uploader/weibo_uploader/`（__init__.py、main.py、article.py）
  - 使用桌面版 `weibo.com` 发帖（从移动版 `m.weibo.cn` 迁移，桌面版更稳定）
  - patchright `chromium.launch()` + `storage_state` 方式（从 CDP `connect_over_cdp` 迁移）
  - 桌面版发帖流程：点击"写微博"按钮 → 弹出对话框 → textarea 输入正文 → file input 上传图片 → 点击"发送"按钮
  - 登录检测：检查 URL 不包含 "newlogin" + 检测头像元素，双重验证
  - 微博特殊性：无标题字段（title 拼接到 content 前）、无标签、最多 9 张图、约 2000 字
- **CLI 命令**：`sau weibo login/check/upload-article`
- **前端**：账号管理页新增微博 tab、发布页新增微博选项
- **技能包**：`skills/weibo-upload/`

### Changed

- **微博从移动版改为桌面版** — `weibo_uploader/article.py` 从 `m.weibo.cn`（移动版 textarea + file input）改为 `weibo.com`（桌面版弹窗对话框），交互更稳定可靠
- **微博从 CDP 改为 patchright launch** — 从 `connect_over_cdp` + 手动 cookie 注入改为 `chromium.launch()` + `storage_state` 自动加载 cookie，无需本地 Chrome 调试端口
- **什么值得买改为 CDP 模式** — `smzdm_uploader/article.py` 从 `chromium.launch` 改为 `connect_over_cdp` + cookie 注入（待测试验证）

### Verified

- 微博图文发布端到端验证通过：登录 → cookie 校验 → 桌面版发帖（写微博弹窗 → 正文 → 图片上传 → 发送）→ 图片上传成功确认

## [0.2.7] - 2026-04-15

### 搜狐号 CDP 发帖踩坑总结

- **CDP 连接的 Chrome 没有 Cookie** — `article.py` 用 `connect_over_cdp()` 连接本地 Chrome，但独立 profile 没有搜狐登录态；cookie 文件只在 patchright `storage_state` 生效，不自动注入 CDP context。修复：CDP 连接后手动 `context.add_cookies()` 注入 `sohu.com` 域名 cookie
- **`wait_for_load_state("networkidle")` 超时** — 搜狐后台加载慢，30s 超时不够。推荐用 `asyncio.sleep(5)` 替代 `networkidle`
- **Chrome 必须先关闭再以调试模式重启** — 已运行的 Chrome 无法附加调试端口，必须 `taskkill /F /IM chrome.exe` 后用 `--remote-debugging-port=9222` 重启
- **可跳过首页确认步骤** — 如果已注入 cookie，直接导航到编辑器 URL 即可，无需先访问首页

### Added

- **搜狐号 `article.py` Cookie 自动注入** — CDP 连接后自动从 `account_file` 读取 cookie 并注入到浏览器 context，兼顾 CDP 反爬能力和账号管理 cookie 系统
- **账号管理页新增搜狐号** — 平台下拉选项、Tab 页签、平台类型映射（type=9）、SSE 登录通道全部补齐
- **平台下拉菜单自适应高度** — 添加账号弹窗中的平台选择器不再被截断，所有 9 个平台选项完整可见

### Fixed

- **`start.bat` 路径警告** — 6 处 Unix 风格 `>/dev/null` 改为 Windows `>nul`，消除"系统找不到指定的路径"红色报错

## [0.2.6] - 2026-04-14

### Fixed

- **CSV 模板下载 500 错误** — `downloadArticleTemplate()` 函数缺少 `return` 语句，补上 `send_file` 返回 CSV 文件流；同时添加 `import io` 和 `send_file` 导入
- **CSV 模板下载被拦截器误判** — axios 响应拦截器对 Blob 类型响应做了 `data.code` 检查导致"请求失败"，增加 `Blob instanceof` 判断直接放行
- **CSV 导入 0 篇** — 用户 CSV 无表头行时 `DictReader` 把数据行当字段名，改为 `csv.reader` + 自动检测表头，无表头时按固定列顺序读取
- **CSV 图片路径含多余引号** — `get_col()` 自动 `.strip('"')`，避免路径两端 `"` 导致文件找不到
- **编辑帖子表单空白** — 新增 `GET /getArticlePost?id=` 接口 + 前端 `onMounted` 检测路由 `id` 参数，自动加载并填充标题/正文/标签/图片/平台/地点
- **编辑模式无保存按钮** — "保存草稿"改为动态文字：新建时"保存草稿"，编辑时"保存"；编辑保存调用 `updateArticlePost` 而非新建
- **`updateArticlePost` 缺少字段** — 补上 `platforms` 和 `video_path` 字段的更新
- **图片预览失败（本地路径）** — 新增 `/getLocalFile?path=` 接口按绝对路径读取本地文件（仅限图片/视频格式），前端根据路径类型自动选择 `/getFile` 或 `/getLocalFile`
- **百家号发布按钮点击无效** — 发布按钮改为重试 3 次机制，每次点击后检查弹窗并验证 URL 跳转；方法2 也改为 `mousedown`+`mouseup`+`click` 三连事件

### Added

- **搜狐号平台选项** — 图文发布页平台选择新增"搜狐号"（ID=9）
- **批量删除帖子** — 帖子管理页批量操作栏新增"批量删除"按钮，后端新增 `POST /batchDeleteArticlePosts` 接口
- **单篇帖子查询** — 后端新增 `GET /getArticlePost?id=` 接口

## [0.2.5] - 2026-04-14

### Added

- **CSV 导入支持全部平台** — 模板和导入逻辑覆盖 1-9 全部平台（小红书/视频号/抖音/快手/百家号/什么值得买/头条号/携程/搜狐号）
- **CSV 导入支持视频发布** — 新增"视频"列，填本地路径即可；发布时自动分流：1-4 调 `/postVideo`，5-9 调 `/postArticle`
- **CSV 模板下载端点** — `GET /downloadArticleTemplate`，返回含示例行和平台映射说明的 CSV 模板
- **DB 自动迁移** — 导入时自动检测并添加 `video_path` 列，无需手动执行迁移
- **帖子列表显示平台列** — `ArticleManagement.vue` 表格新增"平台"列，将 ID 数组转为中文名称显示

### Changed

- **CSV 列顺序调整** — 平台 → 标题 → 正文 → 视频 → 图片 → 标签 → 地点
- **平台解析扩展** — 支持 1-9 全部平台 ID，无效 ID 自动过滤
- **搜狐号自动化方式文档修正** — 明确标注搜狐号通过 Chrome DevTools MCP 发布，不走 patchright

## [0.2.4] - 2026-04-14

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

### 踩过的坑

1. **SPA 路由跳转不渲染 DOM** — 用 `history.pushState` + `popstate` 事件跳转到编辑器，页面 URL 变了但 Vue Router 没有实际渲染编辑器组件。标题输入框 `input[placeholder*='标题']` 在 DOM 中不存在，导致 6 次尝试全部 `Locator.click: Timeout`。**教训：搜狐后台是 SPA，不要用 JS 路由跳转，直接 `goto(editor_url)` 全页导航。**

2. **编辑器不是 contenteditable** — 参考项目文档说编辑器是 contenteditable，实际是 Quill.js（`.ql-editor`）。Quill.js 有自己的 DOM 管理和状态同步机制，直接操作 `[contenteditable='true']` 可能写入成功但 Quill 内部状态不认。**教训：先检查编辑器实际类型（查看 DOM 中是否有 `.ql-editor`、`.ql-toolbar` 等 Quill 特征类名）。**

3. **发布按钮不是 `<button>`** — 搜狐号发布按钮是 `<li class="positive-button publish-report-btn">`，用 `button:has-text('发布')` 永远匹配不到。**教训：不要假设交互元素一定是 `<button>`，用 DevTools 检查实际标签。**

4. **发布有两步确认弹窗** — 点击"发布"后弹出"确认发布文章么？"对话框，需要再点"确定"才真正提交。之前代码没有处理这个弹窗，导致发布流程不完整。**教训：搜狐号发布不是一步到位，需要处理确认弹窗。**

5. **封面图自动选取** — 之前以为需要手动上传封面图，实际搜狐号会自动从正文图片中选取封面。封面区域出现 `.pic-cover` 和"编辑封面"文字表示已自动设置。**教训：先观察平台自动行为，不要过度实现。**

6. **MCP 直接操作 vs patchright CDP** — patchright 通过 CDP 连接本地 Chrome 时，SPA 页面的 DOM 操作可靠性不如直接用 Chrome DevTools MCP。MCP 工具（`take_snapshot`、`evaluate_script`、`upload_file`）可以实时查看 DOM 状态，调试效率远高于 patchright 的 try/except 循环。**教训：新平台开发时，先用 Chrome DevTools MCP 探索和验证流程，确认后再回写到 patchright 代码。**

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
