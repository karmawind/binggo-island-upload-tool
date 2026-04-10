# Changelog

All notable changes to `social-auto-upload` will be documented in this file.

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
