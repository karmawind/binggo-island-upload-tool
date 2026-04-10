# Changelog

All notable changes to `social-auto-upload` will be documented in this file.

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
