# Changelog

All notable changes to `social-auto-upload` will be documented in this file.

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
