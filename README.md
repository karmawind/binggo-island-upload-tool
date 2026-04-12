# 灵感岛推文分发器

> 一键将图文/视频内容自动发布到百家号、什么值得买、头条号、携程、抖音、B站、小红书、快手等主流平台。
> 支持 CLI 命令行、Web 可视化界面、AI Agent 三种使用方式。

`灵感岛推文分发器` 是一个多平台社交媒体自动化分发工具。你可以用一条命令、或一个网页界面，将图文文章同时发布到多个平台，也可以批量排期定时自动发送。

## 目录

- [功能特性](#功能特性)
- [新手引导](#新手引导初次运行必读)
- [使用方式一：Web 可视化界面](#使用方式一web-可视化界面)
- [使用方式二：CLI 命令行](#使用方式二cli-命令行)
- [使用方式三：AI Agent](#使用方式三ai-agent)
- [平台支持详情](#平台支持详情)
- [详细文档](#详细文档)
- [贡献指南](#贡献指南)
- [致谢](#致谢)
- [许可证](#许可证)

## 功能特性

| 能力 | 说明 |
| --- | --- |
| 多平台一键分发 | 一篇帖子同时发布到百家号、头条号、什么值得买、携程等多个平台 |
| 批量排期定时发布 | 准备多篇内容，设定起始时间和间隔，自动按时逐篇发布 |
| CSV 批量导入 | 通过 CSV 文件批量创建帖子内容 |
| Web 可视化管理 | 浏览器中管理账号、编辑帖子、查看发布进度 |
| CLI 命令行 | 终端中一行命令完成登录、发布、校验 |
| AI Agent 集成 | 配合 Claude Code / Codex / OpenClaw 等 AI 工具自动执行 |
| 8 平台统一管理 | 视频平台（抖音、B站、小红书、快手、视频号）+ 图文平台（百家号、什么值得买、头条号、携程） |

## 新手引导（初次运行必读）

### 第一步：安装环境

**前置要求：** Python 3.10+、Node.js 18+（仅 Web 界面需要）

```bash
# 1. 克隆项目
git clone https://github.com/karmawind/binggo-island-upload-tool.git
cd binggo-island-upload-tool

# 2. 创建并激活虚拟环境
uv venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. 安装 Python 依赖
uv pip install -e .

# 4. 安装浏览器驱动（patchright，playwright 的反检测分支）
patchright install chromium

# 5. 初始化数据库
python db/createTable.py
```

### 第二步：选择使用方式

你有三种方式使用本工具：

| 方式 | 适合场景 | 启动方式 |
| --- | --- | --- |
| **Web 界面** | 日常运营、可视化管理、批量操作 | 双击 `start.bat`（Windows）或手动启动前后端 |
| **CLI 命令行** | 单次发布、脚本集成、自动化流水线 | `sau <平台> <命令>` |
| **AI Agent** | 让 AI 帮你操作、批量任务自动化 | 把仓库给 Agent + 参照 [Agent 文档](./docs/agent-bootstrap.md) |

### 第三步：登录账号

无论使用哪种方式，都需要先登录平台账号获取 Cookie：

```bash
# CLI 方式登录（会弹出浏览器，扫码或手动登录）
sau baijiahao login --account 我的百家号 --headed
sau smzdm login --account 我的值得买 --headed
sau toutiao login --account 我的头条号 --headed
sau ctrip login --account 我的携程 --headed

# 视频平台同理
sau douyin login --account 我的抖音
sau xiaohongshu login --account 我的小红书
sau kuaishou login --account 我的快手
sau bilibili login --account 我的B站
```

> **说明：** `--headed` 表示显示浏览器窗口，图文平台推荐加此参数，方便手动操作登录。视频平台默认弹出窗口，不需要加。

### 第四步：开始发布

**CLI 快速发布：**

```bash
# 发布图文文章到百家号
sau baijiahao upload-article --account 我的百家号 --title "文章标题" --content "正文内容" --images img1.jpg img2.jpg --headed

# 发布视频到抖音
sau douyin upload-video --account 我的抖音 --file video.mp4 --title "视频标题"
```

**Web 界面发布：** 双击 `start.bat`，浏览器自动打开 `http://localhost:5173`，在"图文发布"页面操作。

## 使用方式一：Web 可视化界面

Web 界面提供完整的可视化管理功能，适合日常运营使用。

### 启动方式

**Windows 一键启动：** 双击项目根目录的 `start.bat`

**手动启动：**

```bash
# 终端 1：启动后端（端口 5409）
python sau_backend.py

# 终端 2：启动前端（端口 5173）
cd sau_frontend
npm install   # 首次需要安装依赖
npm run dev
```

浏览器打开 `http://localhost:5173` 即可使用。

### 功能页面

| 页面 | 功能 |
| --- | --- |
| 发布中心 | 视频发布（抖音/B站/小红书/快手/视频号） |
| 图文发布 | 多平台图文分发（百家号/什么值得买/头条号/携程），支持选择多个平台同时发布 |
| 帖子管理 | 帖子列表、状态筛选、批量发布、排期调度、CSV 导入 |
| 账号管理 | 8 平台账号管理、Cookie 状态检测、在线登录、重新认证 |

### 核心操作流程

1. **添加账号** → 在"账号管理"页面选择平台 Tab，点击"添加账号"，浏览器自动弹出供你登录
2. **创建帖子** → 在"图文发布"页面填写标题、正文、上传图片、选择平台和账号
3. **一键分发** → 点击"立即发布"，系统自动将内容并行发布到所选平台
4. **排期发布** → 在"帖子管理"页面勾选多篇帖子，设定起始时间和间隔，自动定时发布
5. **批量导入** → 点击"导入 CSV"，按模板格式批量创建帖子

### CSV 模板

| title | content | image_paths | tags | location | platforms |
| --- | --- | --- | --- | --- | --- |
| 杭州三日游 | 杭州真的太美了... | img1.jpg,img2.jpg | 旅游,杭州 | 杭州 | [5,7,8] |

> `platforms` 中的数字：5=百家号 6=什么值得买 7=头条号 8=携程

## 使用方式二：CLI 命令行

CLI 适合单次发布、脚本集成、自动化流水线场景。

### 安装 CLI

```bash
# 虚拟环境已激活的情况下
uv pip install -e .

# 验证安装
sau --help
```

### 命令格式

```bash
sau <平台> <命令> [选项]
```

### 图文平台命令

```bash
# 百家号
sau baijiahao login --account <账号名> --headed       # 登录
sau baijiahao check --account <账号名>                  # 校验 Cookie
sau baijiahao upload-article --account <账号名> --title "标题" --content "正文" --images 1.jpg 2.jpg [--tags 标签1,标签2] [--schedule "2026-04-12 10:00"] --headed

# 什么值得买
sau smzdm login --account <账号名> --headed
sau smzdm check --account <账号名>
sau smzdm upload-article --account <账号名> --title "标题" --content "正文" --images 1.jpg 2.jpg --headed

# 头条号
sau toutiao login --account <账号名> --headed
sau toutiao check --account <账号名>
sau toutiao upload-article --account <账号名> --title "标题" --content "正文" --images 1.jpg 2.jpg --headed

# 携程
sau ctrip login --account <账号名> --headed
sau ctrip check --account <账号名>
sau ctrip upload-article --account <账号名> --title "标题" --content "正文" --images 1.jpg 2.jpg --location "杭州" --headed
```

### 视频平台命令

```bash
# 抖音
sau douyin login --account <账号名>
sau douyin upload-video --account <账号名> --file video.mp4 --title "标题" [--desc "描述"] [--tags 标签1,标签2]
sau douyin upload-note --account <账号名> --images 1.png 2.png --title "图文标题" [--note "正文"]

# B站
sau bilibili login --account <账号名>
sau bilibili upload-video --account <账号名> --file video.mp4 --title "标题" --desc "描述" --tid 249

# 小红书
sau xiaohongshu login --account <账号名>
sau xiaohongshu upload-video --account <账号名> --file video.mp4 --title "标题"
sau xiaohongshu upload-note --account <账号名> --images 1.png 2.png --title "图文标题" [--note "正文"]

# 快手
sau kuaishou login --account <账号名>
sau kuaishou upload-video --account <账号名> --file video.mp4 --title "标题"
sau kuaishou upload-note --account <账号名> --images 1.png 2.png --title "图文标题" [--note "正文"]
```

> **补充说明：**
> - 一个 `account_name` 对应一个账号文件，可以准备多个账号
> - B站不需要手动安装 `biliup`，首次运行会自动下载
> - B站登录建议在本地终端执行；二维码显示不完整时可打开 `qrcode.png` 扫码
> - CLI 详细文档：[CLI 使用说明](./docs/CLI.md)

## 使用方式三：AI Agent

你可以把整个仓库交给 AI Agent（Claude Code、Codex、OpenClaw 等），让它帮你安装、登录、发布。

### 快速开始

1. 把仓库给你的 Agent 客户端
2. 把下面这段提示词发给它
3. 等 Agent 完成安装和验证后，再继续下达任务

### Agent 启动提示词

```text
你现在在一个名为 binggo-island-upload-tool（灵感岛推文分发器）的仓库中工作。

这是一个多平台社交媒体自动发布项目。当前已接入：
- bilibili, douyin, kuaishou, xiaohongshu (视频平台)
- baijiahao, smzdm, toutiao, ctrip (图文平台)

请按以下步骤操作：

1. 安装依赖：uv pip install -e .
2. 安装浏览器驱动：patchright install chromium
3. 验证 CLI 入口：sau douyin --help
4. 验证数据库：python db/createTable.py

完成后报告就绪状态，等待后续任务指令。
```

### Skill 包

每个平台都有独立的 Skill 包，Agent 可以直接调用：

| 平台 | Skill 路径 |
| --- | --- |
| 抖音 | [skills/douyin-upload/SKILL.md](./skills/douyin-upload/SKILL.md) |
| B站 | [skills/bilibili-upload/SKILL.md](./skills/bilibili-upload/SKILL.md) |
| 小红书 | [skills/xiaohongshu-upload/SKILL.md](./skills/xiaohongshu-upload/SKILL.md) |
| 快手 | [skills/kuaishou-upload/SKILL.md](./skills/kuaishou-upload/SKILL.md) |
| 百家号 | [skills/baijiahao-upload/SKILL.md](./skills/baijiahao-upload/SKILL.md) |
| 什么值得买 | [skills/smzdm-upload/SKILL.md](./skills/smzdm-upload/SKILL.md) |
| 头条号 | [skills/toutiao-upload/SKILL.md](./skills/toutiao-upload/SKILL.md) |
| 携程 | [skills/ctrip-upload/SKILL.md](./skills/ctrip-upload/SKILL.md) |

> Agent 详细引导：[Agent Bootstrap Prompt](./docs/agent-bootstrap.md)

## 平台支持详情

| 平台 | 登录 | 视频上传 | 图文上传 | 定时发布 | CLI | Web | Skill |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 抖音 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B站 | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 小红书 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 快手 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 视频号 | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ |
| 百家号 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 什么值得买 | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ |
| 头条号 | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ |
| 携程 | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ |
| TikTok | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |

### 编辑器类型说明

| 平台 | 编辑器类型 | 输入方式 |
| --- | --- | --- |
| 百家号 | UEditor（iframe） | `execCommand('insertHTML')` |
| 什么值得买 | ProseMirror | `execCommand('insertHTML')` |
| 头条号 | ProseMirror | `execCommand('insertHTML')` |
| 携程 | Draft.js | `keyboard.insert_text()` |

## 详细文档

| 文档 | 说明 |
| --- | --- |
| [安装说明](./docs/install.md) | 环境搭建、依赖安装 |
| [更新说明](./docs/update.md) | 版本升级指南 |
| [CLI 使用说明](./docs/CLI.md) | 命令行详细用法 |
| [Agent 引导](./docs/agent-bootstrap.md) | AI Agent 接入指南 |
| [开发进度](./docs/PROGRESS.md) | 功能模块进度和踩坑记录 |
| [更新日志](./CHANGELOG.md) | 版本变更记录 |

## 贡献指南

欢迎各种形式的贡献：

1. Fork 本仓库
2. 创建分支 (`git checkout -b feature/YourFeature`)
3. 提交更改 (`git commit -m 'Add some feature'`)
4. 推送到分支 (`git push origin feature/YourFeature`)
5. 创建 Pull Request

## 致谢

- 本项目基于 [social-auto-upload](https://github.com/dreammis/social-auto-upload) 二次开发
- Bilibili 上传能力基于 [biliup](https://github.com/biliup/biliup)
- 浏览器自动化使用 [patchright](https://github.com/AshampooOpenSource/patchright)（Playwright 反检测分支）

## 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。
