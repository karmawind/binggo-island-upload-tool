# 灵感岛推文分发器 — 技术交接文档

> 版本: 0.2.5 | 更新日期: 2026-04-14
> 项目仓库: `karmawind/binggo-island-upload-tool`

---

## 一、项目概览

本项目是一套**多平台社交媒体自动化发布系统**，支持将视频和图文内容一键分发到国内主流社交媒体平台。系统由 Python 后端 + Vue.js 前端 + CLI 命令行工具三部分组成。

### 核心能力

| 能力 | 说明 |
|------|------|
| 视频上传 | 支持抖音、快手、小红书、B站、视频号 |
| 图文发布 | 支持百家号、什么值得买、头条号、携程、搜狐号 |
| 账号管理 | 多平台账号统一管理，Cookie 自动保存/校验 |
| 定时发布 | 支持排期自动发布（后台线程每 60 秒检查） |
| 多平台并行 | 一篇内容同时发到多个平台，每平台独立线程 |
| 批量导入 | CSV 批量导入帖子 |
| Web 前端 | 可视化管理界面，无需命令行操作 |

---

## 二、技术架构

```
┌─────────────────────────────────────────────────────┐
│                    用户入口                          │
│  ┌───────────┐  ┌───────────┐  ┌──────────────────┐ │
│  │ Web 前端   │  │ CLI 命令行 │  │ Chrome DevTools  │ │
│  │ Vue3+Vite │  │ sau CLI   │  │ MCP（调试用）    │ │
│  └─────┬─────┘  └─────┬─────┘  └────────┬─────────┘ │
│        │              │                  │           │
├────────┼──────────────┼──────────────────┼───────────┤
│        ▼              ▼                  ▼           │
│  ┌───────────────────────────────────────────────┐   │
│  │           Flask 后端 (Port 5409)               │   │
│  │    REST API + SSE + 定时调度 + 文件管理        │   │
│  └───────────────┬───────────────────────────────┘   │
│                  │                                    │
│  ┌───────────────▼───────────────────────────────┐   │
│  │           SQLite 数据库 (database.db)          │   │
│  │      user_info / file_records                 │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  ┌───────────────────────────────────────────────┐   │
│  │           浏览器自动化层                        │   │
│  │   patchright: 百家号/什么值得买/头条号/携程等   │   │
│  │   Chrome DevTools MCP: 搜狐号（绕过反爬）      │   │
│  └───────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 后端 | Python + Flask | 3.10-3.12 / Flask 3.1 |
| 浏览器自动化 | patchright（Playwright 无反爬分支） | 1.58 |
| 数据库 | SQLite | 内置 |
| 前端 | Vue 3 + Vite + Element Plus + Pinia | 3.5 / 6.3 / 2.9 / 3.0 |
| CLI | argparse + pyproject.toml entry_point | - |
| 日志 | loguru（按平台分文件、10MB 轮转、保留 10 天） | 0.7 |

---

## 三、平台能力矩阵

### 平台 ID 映射

| ID | 平台 | 类型 | 登录方式 | 编辑器 | 视频上传 | 图文发布 |
|----|------|------|----------|--------|----------|----------|
| 1 | 小红书 | 视频+图文 | 扫码 | 自有 | ✅ | ✅ (upload-note) |
| 2 | 视频号 | 视频 | 扫码 | - | ✅ | - |
| 3 | 抖音 | 视频+图文 | 扫码 | 自有 | ✅ | ✅ (upload-note) |
| 4 | 快手 | 视频+图文 | 扫码 | 自有 | ✅ | ✅ (upload-note) |
| 5 | 百家号 | 视频+图文 | 扫码 | UEditor | ✅ | ✅ (upload-article) |
| 6 | 什么值得买 | 图文 | 扫码 | ProseMirror | - | ✅ |
| 7 | 头条号 | 图文 | 扫码 | ProseMirror | - | ✅ |
| 8 | 携程 | 图文 | 扫码 | Draft.js | - | ✅ |
| 9 | 搜狐号 | 图文 | 扫码 | Quill.js | - | ✅（MCP 直操 Chrome）|
| - | B站 | 视频 | Cookie导入 | - | ✅ (biliup) | - |

### 编辑器交互方式速查

| 平台 | 编辑器 | 标题输入 | 正文输入 | 关键注意 |
|------|--------|----------|----------|----------|
| 百家号 | UEditor（iframe） | `fill()` | `execCommand('insertHTML')` | 正文在 iframe 中，必须先 focus iframe |
| 什么值得买 | ProseMirror | `textarea.fill()` | `execCommand('insertHTML')` | 遮罩层拦截点击，需 JS dispatchEvent |
| 头条号 | ProseMirror | `textarea.fill()` | `execCommand('insertHTML')` | 需关闭 AI 助手遮罩 |
| 携程 | Draft.js | `keyboard.type()` 逐字 | `keyboard.insert_text()` | 必须用键盘事件，execCommand 无效 |
| 搜狐号 | Quill.js | `fill()` | `execCommand('insertHTML')` | **不走 patchright**，通过 Chrome DevTools MCP 操作 |

---

## 四、环境搭建

### 前置条件

- Python 3.10 - 3.12
- Node.js 18+
- Google Chrome（用于 CDP 连接）
- Git Bash（Windows）

### 一键安装

```bash
# Windows 一键启动（自动检查环境、安装依赖、初始化数据库、启动服务）
start.bat

# Linux/Mac 一键安装
bash setup.sh
```

### 手动安装

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate     # Linux/Mac

# 2. 安装后端依赖
pip install -e .

# 3. 安装浏览器驱动
patchright install chromium

# 4. 初始化配置
cp conf.example.py conf.py

# 5. 初始化数据库
python db/createTable.py

# 6. 安装前端依赖
cd sau_frontend && npm install && cd ..

# 7. 启动服务
python sau_backend.py          # 后端 :5409
cd sau_frontend && npm run dev # 前端 :5173
```

### 配置文件

`conf.py`（从 `conf.example.py` 复制）：

```python
BASE_DIR = Path(__file__).parent.resolve()
XHS_SERVER = "http://127.0.0.1:11901"    # 小红书服务
LOCAL_CHROME_PATH = ""                    # 自定义 Chrome 路径，留空用默认
LOCAL_CHROME_HEADLESS = True              # 默认无头模式
DEBUG_MODE = True                         # 调试模式
```

---

## 五、项目目录结构

```
social-auto-upload/
├── sau_cli.py                  # CLI 入口（sau 命令）
├── sau_backend.py              # Flask 后端（API 服务器）
├── conf.py                     # 配置文件（需从 conf.example.py 复制）
├── pyproject.toml              # 项目元数据、依赖、CLI 入口定义
├── requirements.txt            # Python 依赖清单
├── CLAUDE.md                   # AI 开发指南（各平台 SOP）
├── CHANGELOG.md                # 版本变更日志
│
├── uploader/                   # 各平台上传器
│   ├── douyin_uploader/        # 抖音（main.py）
│   ├── ks_uploader/            # 快手（main.py）
│   ├── xiaohongshu_uploader/   # 小红书（main.py）
│   ├── tencent_uploader/       # 视频号（main.py）
│   ├── bilibili_uploader/      # B站（main.py + runtime.py）
│   ├── baijiahao_uploader/     # 百家号（main.py 视频 + article.py 图文）
│   ├── smzdm_uploader/         # 什么值得买（main.py + article.py）
│   ├── toutiao_uploader/       # 头条号（main.py + article.py）
│   ├── ctrip_uploader/         # 携程（main.py + article.py）
│   ├── sohu_uploader/          # 搜狐号（main.py + article.py）
│   └── tk_uploader/            # TikTok（main.py + main_chrome.py）
│
├── skills/                     # 各平台 Skill 包（AI Agent 用）
│   ├── baijiahao-upload/
│   ├── smzdm-upload/
│   ├── toutiao-upload/
│   ├── ctrip-upload/
│   ├── sohu-upload/
│   ├── douyin-upload/
│   ├── kuaishou-upload/
│   ├── xiaohongshu-upload/
│   └── bilibili-upload/
│   └── <platform>-upload/
│       ├── SKILL.md                     # Skill 主文档
│       ├── references/
│       │   ├── cli-contract.md          # CLI 命令契约
│       │   ├── runtime-requirements.md  # 运行前提
│       │   └── troubleshooting.md       # 故障排查
│       └── scripts/examples/            # 示例脚本
│
├── sau_frontend/               # Vue.js 前端
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── router/index.js     # 路由定义（7 个页面）
│       ├── views/              # 页面组件
│       │   ├── Dashboard.vue
│       │   ├── AccountManagement.vue
│       │   ├── PublishCenter.vue
│       │   ├── MaterialManagement.vue
│       │   ├── ArticlePublish.vue
│       │   ├── ArticleManagement.vue
│       │   └── About.vue
│       ├── stores/             # Pinia 状态管理
│       │   ├── account.js      # 账号数据
│       │   ├── app.js          # 全局状态
│       │   ├── articleDraft.js # 图文草稿
│       │   └── user.js         # 用户状态
│       └── api/                # API 调用封装
│           ├── account.js
│           ├── material.js
│           └── article.js
│
├── db/                         # 数据库
│   ├── createTable.py          # 建表脚本
│   └── database.db             # SQLite 数据库文件
│
├── utils/                      # 工具模块
│   ├── base_social_media.py    # 平台常量 + 反检测脚本
│   ├── browser_hook.py         # 浏览器自动化钩子
│   ├── constant.py             # 常量定义
│   ├── files_times.py          # 文件/时间工具
│   ├── log.py                  # 日志配置（12 个平台 logger）
│   ├── login_qrcode.py         # 二维码登录
│   ├── network.py              # 网络工具
│   └── stealth.min.js          # 浏览器反检测脚本
│
├── myUtils/                    # 后端辅助模块
│   ├── postArticle.py          # 图文发布调度（多平台并行）
│   ├── auth.py                 # Cookie 校验调度
│   └── postVideo.py            # 视频发布调度
│
├── cookies/                    # Cookie 存储（自动创建）
├── logs/                       # 日志文件（按平台分文件，自动轮转）
├── imageFile/                  # 图片文件存储
├── videoFile/                  # 视频文件存储
└── cookiesFile/                # Cookie 文件存储
```

---

## 六、后端架构

### API 端点一览

| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/` | GET | 主页面 | 返回前端 SPA |
| `/upload` | POST | 上传文件 | 160MB 限制 |
| `/uploadSave` | POST | 上传并保存 | 记录到数据库 |
| `/getFile` | GET | 获取单个文件 | |
| `/getFiles` | GET | 获取所有文件 | |
| `/deleteFile` | GET | 删除文件 | |
| `/getAccounts` | GET | 获取所有账号 | 不校验有效性 |
| `/getValidAccounts` | GET | 获取有效账号 | 校验 Cookie |
| `/updateUserinfo` | POST | 更新账号信息 | |
| `/deleteAccount` | GET | 删除账号 | |
| `/login` | GET (SSE) | 视频平台登录 | 实时推送进度 |
| `/loginArticleAccount` | GET (SSE) | 图文平台登录 | CLI 子进程登录 |
| `/postVideo` | POST | 发布视频 | 单平台 |
| `/postVideoBatch` | POST | 批量发布视频 | 多平台 |
| `/postArticle` | POST | 发布图文 | 单平台/多平台并行 |
| `/articleTaskStatus` | GET | 查询发布进度 | |
| `/uploadImage` | POST | 上传图文图片 | |
| `/getImages` | GET | 获取所有图片 | |
| `/deleteImage` | GET | 删除图片 | |
| `/getArticlePosts` | GET | 获取所有帖子 | |
| `/saveArticlePost` | POST | 保存草稿 | |
| `/updateArticlePost` | POST | 更新帖子 | |
| `/deleteArticlePost` | GET | 删除帖子 | |
| `/scheduleArticles` | POST | 批量排期 | |
| `/importArticles` | POST | CSV 导入 | |
| `/uploadCookie` | POST | 上传 Cookie | |
| `/downloadCookie` | GET | 下载 Cookie | |
| `/copyMaterialToImage` | POST | 素材转图片 | |

### 数据库表结构

**user_info（账号表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| type | INTEGER | 平台 ID（1-9） |
| filePath | TEXT | Cookie 文件路径 |
| userName | TEXT | 显示名称 |
| status | INTEGER | 状态（0=正常） |

**file_records（文件记录表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| filename | TEXT | 原始文件名 |
| filesize | REAL | 文件大小（MB） |
| upload_time | DATETIME | 上传时间 |
| file_path | TEXT | 存储路径 |

### 浏览器自动化机制

系统根据平台反爬强度使用两种浏览器自动化方式：

**方式一：patchright**（百家号、什么值得买、头条号、携程等）

patchright 是 Playwright 的反检测分支，适用于反爬较弱的平台。

- **登录流程**：启动 patchright 浏览器 → 打开平台登录页 → 等待用户扫码 → 检测登录成功 → 保存 Cookie
- **发布流程**：加载 Cookie → 启动浏览器 → 导航到编辑器 → 填写标题/正文/图片 → 点击发布

**方式二：Chrome DevTools MCP**（搜狐号）

搜狐号反爬机制较强，patchright（即使用 CDP 连接模式）仍会被检测拦截。最终通过 **Chrome DevTools MCP** 直接操作用户已打开的 Chrome 浏览器完成发布，完全绕过反爬。

- **前提**：用户以 `--remote-debugging-port=9222` 启动 Chrome 并手动登录
- **发布流程**：MCP `navigate_page` 导航编辑器 → `take_snapshot` 查看DOM → `fill` 填标题 → `evaluate_script` 写正文 → `upload_file` 上传图片 → `click` 点发布 → `evaluate_script` 处理确认弹窗
- **优势**：操作的是真实 Chrome 浏览器，与真人操作无区别，不存在指纹检测问题

### 定时调度器

后端内置定时调度线程：
- 每 60 秒检查一次 `scheduled_at` 到期的帖子
- 到期后自动调用 CLI 执行发布
- 支持批量排期

---

## 七、前端架构

### 路由与页面

| 路由 | 页面组件 | 功能 |
|------|----------|------|
| `/` | Dashboard | 总览面板（账号/平台/素材统计、快捷入口、最近上传） |
| `/account-management` | AccountManagement | 8 平台账号管理（Tab 切换、增删改查、Cookie 管理、SSE 登录） |
| `/material-management` | MaterialManagement | 素材管理（视频/图片上传、预览、删除） |
| `/publish-center` | PublishCenter | 视频发布中心（多 Tab、4 平台、定时/批量） |
| `/article-publish` | ArticlePublish | 图文发布（多平台选择、标题/正文/图片/标签、地点） |
| `/article-management` | ArticleManagement | 帖子管理（列表、筛选、排期、批量发布、CSV 导入） |
| `/about` | About | 关于页面 |

### 状态管理（Pinia Stores）

| Store | 文件 | 管理内容 |
|-------|------|----------|
| account | `account.js` | 账号列表、平台映射、CRUD 操作 |
| app | `app.js` | 全局状态、首次访问标记、素材管理状态 |
| articleDraft | `articleDraft.js` | 图文草稿编辑状态持久化 |
| user | `user.js` | 用户认证状态 |

### 前后端通信

- **REST API**：常规 CRUD 操作通过 Axios 调用
- **SSE（Server-Sent Events）**：登录流程实时推送进度，前端显示二维码和状态

---

## 八、CLI 工具链

CLI 通过 `sau` 命令调用，安装后自动注册到 PATH。

### 通用命令格式

```bash
sau <platform> <command> --account <name> [options]
```

### 命令类型

| 命令 | 说明 | 适用平台 |
|------|------|----------|
| `login` | 登录并保存 Cookie | 所有平台 |
| `check` | 校验 Cookie 是否有效 | 所有平台 |
| `upload-video` | 上传视频 | 抖音、快手、小红书、B站 |
| `upload-note` | 上传图文笔记 | 抖音、快手、小红书 |
| `upload-article` | 发布图文文章 | 百家号、什么值得买、头条号、携程、搜狐号 |

### 各平台 CLI 示例

**百家号（UEditor 编辑器）**
```bash
sau baijiahao login --account myaccount --headed
sau baijiahao check --account myaccount
sau baijiahao upload-article --account myaccount \
  --title "标题" --content "正文" \
  --images img1.png img2.png \
  --tags "标签1,标签2" --headed
```

**什么值得买（ProseMirror 编辑器）**
```bash
sau smzdm login --account myaccount --headed
sau smzdm upload-article --account myaccount \
  --title "标题" --content "正文" \
  --images img1.png img2.png --headed
```

**头条号（ProseMirror 编辑器）**
```bash
sau toutiao login --account myaccount --headed
sau toutiao upload-article --account myaccount \
  --title "标题" --content "正文" \
  --images img1.png img2.png --headed
```

**携程（Draft.js 编辑器，必须指定地点）**
```bash
sau ctrip login --account myaccount --headed
sau ctrip upload-article --account myaccount \
  --title "标题" --content "正文" \
  --images img1.png img2.png \
  --location "杭州" --headed
```

**搜狐号（Quill.js 编辑器，通过 Chrome DevTools MCP 发布）**
```bash
# 登录（保存 Cookie）
sau sohu login --account myaccount --headed

# 实际发布时通过 Chrome DevTools MCP 操作（不是 CLI）
# 需先以 --remote-debugging-port=9222 启动 Chrome 并手动登录
# 然后在 Claude Code 中通过 MCP 工具完成发布
```

### 重要 CLI 参数

| 参数 | 说明 |
|------|------|
| `--account <name>` | 账号名称（必填），Cookie 文件保存为 `<平台>_<name>.json` |
| `--headed` | 有头模式（推荐），打开可见浏览器窗口便于观察 |
| `--title` | 标题 |
| `--content` | 正文内容 |
| `--images` | 图片路径（可多张，空格分隔） |
| `--tags` | 标签（逗号分隔） |
| `--schedule` | 定时发布时间 `"YYYY-MM-DD HH:MM"` |
| `--location` | 地点（携程必填） |

---

## 九、各平台发布流程与注意事项

### 9.1 百家号

**编辑器**：UEditor（内容在 iframe 中）

**发布流程**：
1. Cookie 校验 → 2. 启动浏览器 → 3. 导航编辑器（需带 `is_from_cms=1` 参数，重试最多 3 次）→ 4. 清空编辑器 → 5. 填写标题 → 6. 填写正文（`execCommand('insertHTML')`）→ 7. 上传图片 → 8. 选择封面 → 9. 发布

**关键注意事项**：
- 正文在 iframe 中，**禁止用 `innerHTML` 直接写入**，必须用 `execCommand('insertHTML')`
- 上传图片前必须先 focus iframe body
- 封面选择：用"单图"模式，点击封面容器自动加载正文图片，不要点"选正文图"按钮（会触发 30 秒禁用）
- 发布按钮必须用 JS `dispatchEvent` 三连（mousedown → mouseup → click），`.click()` 无效
- 标题限制 2-30 字

### 9.2 什么值得买

**编辑器**：ProseMirror（`div.ProseMirror[contenteditable=true]`）

**发布流程**：
1. Cookie 校验 → 2. 导航编辑器 → 3. 关闭升级弹窗 → 4. 清空编辑器 → 5. 填写标题（`textarea.fill()`）→ 6. 填写正文（`execCommand('insertHTML')`）→ 7. 上传封面图 → 8. 上传正文图片 → 9. 设置创作声明 → 10. 发布

**关键注意事项**：
- **每次发布前必须 `clear_editor()`**（SPA 不刷新，残留状态会导致不可预测行为）
- 图片上传按钮必须用 `dispatchEvent` 点击，`.click()` 可能报 `btn.click is not a function`
- 上传后必须点"插入正文"关闭面板
- 大量 `div.mask` 遮罩层，所有点击操作都可能被遮挡，需用 JS 绕过
- 标题限制 30 字（不是 80）

### 9.3 头条号

**编辑器**：ProseMirror（`div.ProseMirror[contenteditable=true]`）

**发布流程**：
1. Cookie 校验 → 2. 导航编辑器 → 3. 关闭 AI 助手遮罩 → 4. 清空编辑器 → 5. 填写标题 → 6. 填写正文 → 7. 上传图片 → 8. 点击"确定"插入正文 → 9. 设置不投放广告 → 10. 预览并发布 → 11. 确认发布

**关键注意事项**：
- **必须先关闭 AI 助手遮罩**（`div.ai-assistant-drawer` + `div.byte-drawer-mask`），否则所有操作被拦截
- 发布是两步确认："预览并发布" → 等按钮变为"确认发布" → 再点
- 图片上传后必须点"确定"插入正文
- 广告默认选中"投放广告"，必须手动设为"不投放广告"
- 标题限制 2-30 字

### 9.4 携程

**编辑器**：Draft.js（React 状态管理）

**发布流程**：
1. Cookie 校验 → 2. 导航编辑器 → 3. 清空编辑器 → 4. 填写标题（`keyboard.type()` 逐字输入）→ 5. 填写描述正文（`keyboard.insert_text()`）→ 6. 上传图片 → 7. 填写地点（必填）→ 8. 发布

**关键注意事项**：
- **`execCommand` 和 `fill()` 对 Draft.js 完全无效**，必须用键盘事件
- 标题必须用 `keyboard.type()` 逐字输入（Draft.js 需要真实键盘事件触发 React 状态更新）
- 正文用 `keyboard.insert_text()` 一次性输入（比逐字快几十倍）
- **地点是必填字段**，不填会阻止发布并提示"请添加一个地点！"
- 图片限制 20 张，推荐宽高比 3:4~2:1
- 发布按钮文字为"发 布"（中间有空格），匹配时需注意

### 9.5 搜狐号（特殊：使用 Chrome DevTools MCP）

> **重要**：搜狐号反爬机制较强，patchright（Playwright 分支）无法绕过，即使使用 CDP 连接模式也会被检测。实际的发布流程是通过 **Chrome DevTools MCP** 直接操作用户已打开的 Chrome 浏览器完成的，不走 patchright。

**编辑器**：Quill.js（`.ql-editor`）

**自动化方式**：Chrome DevTools MCP（非 patchright）

**前置条件**：
1. 以远程调试模式启动 Chrome：`chrome.exe --remote-debugging-port=9222`
2. 在 Chrome 中手动登录搜狐号后台（`mp.sohu.com`）
3. 在 Claude Code 中通过 MCP 工具执行发布操作

**发布流程**（通过 MCP 工具）：
1. `navigate_page` → 打开编辑器 URL（`/mpfe/v4/contentManagement/news/addarticle?contentStatus=1`）
2. `take_snapshot` → 检查页面状态，关闭"我知道了"等弹窗
3. `fill` → 填写标题（5-72 字）
4. `evaluate_script` → 通过 `execCommand('insertHTML')` 写入正文到 `.ql-editor`
5. `click` → 点击工具栏 `button.ql-image` 打开上传弹窗
6. `upload_file` → 上传图片
7. `click` → 点击"确定"插入图片到正文
8. `click` → 点击发布按钮（`li.positive-button.publish-report-btn`）
9. `evaluate_script` → 检测确认弹窗"确认发布文章么？"，`dispatchEvent` 点击"确定"
10. `wait_for` → 等待跳转到内容管理页，验证"审核中"

**关键注意事项**：
- **不是 patchright 自动化**，是人工通过 Chrome DevTools MCP 工具远程操作浏览器
- **编辑器是 Quill.js（`.ql-editor`），不是 `[contenteditable='true']`**
- **必须直接导航到编辑器 URL**，不能用 SPA 路由跳转（`history.pushState` 改了 URL 但不渲染 DOM，这是之前 6 次失败测试的根因）
- 发布按钮是 **`<li>` 元素**，不是 `<button>`
- 发布有两步确认："确认发布文章么？" → 点"确定"
- 封面图自动从正文图片选取，无需手动设置
- 正文不足 200 字会警告但仍可发布
- `.click()` 在确认弹窗上可能无效，需用 `evaluate_script` + `dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))` 兜底

---

## 十、Skill 包体系

Skill 包是 AI Agent（如 Claude Code）使用的平台操作手册，位于 `skills/<platform>-upload/`。

### Skill 包结构

```
skills/<platform>-upload/
├── SKILL.md                        # 主文档：功能概览、支持动作、发布流程
├── references/
│   ├── cli-contract.md             # CLI 命令契约（参数、返回值）
│   ├── runtime-requirements.md     # 运行前提（依赖、环境）
│   └── troubleshooting.md          # 故障排查（症状+原因+解决）
└── scripts/examples/
    ├── cli_template.py             # Python 调用模板
    ├── commands.sh                 # Bash 命令示例
    └── commands.ps1                # PowerShell 命令示例
```

### 安装 Skill 包

```bash
sau skill install
```

### 何时使用 Skill 包

- 新增平台时，参考已有 skill 包的模板创建
- AI Agent 开发/调试时，skill 包提供完整的平台操作指南
- 故障排查时，`troubleshooting.md` 提供症状-原因-解决方案映射

---

## 十一、日志系统

### 日志配置

- **日志库**：loguru
- **存储位置**：`logs/` 目录
- **文件命名**：`<platform>.log`（如 `sohu.log`、`baijiahao.log`）
- **轮转策略**：10MB 自动轮转，保留 10 天
- **日志级别**：DEBUG / INFO / WARNING / ERROR / SUCCESS

### 各平台 Logger

| Logger 名称 | 文件 | 平台 |
|-------------|------|------|
| douyin_logger | logs/douyin.log | 抖音 |
| tencent_logger | logs/tencent.log | 视频号 |
| xhs_logger | logs/xhs.log | 小红书 |
| bilibili_logger | logs/bilibili.log | B站 |
| kuaishou_logger | logs/kuaishou.log | 快手 |
| baijiahao_logger | logs/baijiahao.log | 百家号 |
| smzdm_logger | logs/smzdm.log | 什么值得买 |
| toutiao_logger | logs/toutiao.log | 头条号 |
| ctrip_logger | logs/ctrip.log | 携程 |
| sohu_logger | logs/sohu.log | 搜狐号 |

---

## 十二、关键踩坑记录

以下是实际开发中遇到的最重要的问题和解决方案，新增平台或修改代码时务必参考。

### 12.1 通用原则

| 原则 | 说明 |
|------|------|
| **每次发布前必须清空编辑器** | SPA 页面不刷新，残留的标题/正文/图片/遮罩会导致不可预测行为 |
| **先观察再实现** | 新平台先用 Chrome DevTools MCP 探索 DOM 结构和交互流程，确认后再写代码 |
| **不要假设元素类型** | 发布按钮可能是 `<li>`、`<div>`、`<a>`，不一定都是 `<button>` |
| **不要假设编辑器类型** | 先检查 DOM 特征类名（`.ql-editor` / `.ProseMirror` / `.DraftEditor`）再决定交互方式 |
| **不要过度实现** | 封面图可能自动选取（搜狐号），新手引导只在首次出现，不要写死处理逻辑 |
| **SPA 路由跳转不可靠** | 直接 `goto(url)` 全页导航，不要用 `history.pushState` 或点击 SPA 内链接 |

### 12.2 各平台特有坑

**百家号**
- UEditor 正文在 iframe 中，`innerHTML` 写入后 UEditor 内部状态不认，必须用 `execCommand('insertHTML')`
- 发布按钮 `.click()` 和 `force_click()` 都无效，必须用 JS `dispatchEvent` 三连
- 刚登录后导航编辑器可能被重定向到首页，需要重试（最多 3 次）

**什么值得买**
- SVG 工具栏按钮的 `closest('button')` 可能返回非标准元素，`.click()` 报错，统一用 `dispatchEvent`
- `div.mask` 遮罩层无处不在，所有 `.click()` 都可能被拦截
- 标题限制 30 字（文档可能写 80）

**头条号**
- AI 助手抽屉遮罩（`div.ai-assistant-drawer`）加载后拦截所有操作，必须先移除
- 发布按钮两步确认：先点"预览并发布"，等按钮变为"确认发布"再点
- 图片上传后需点"确定"插入正文，否则图片只在面板中不进入编辑器

**携程**
- Draft.js 是 React 状态管理，`execCommand`、`fill()`、`innerHTML` 全部无效
- 标题必须逐字输入（`keyboard.type()`），正文可用 `keyboard.insert_text()` 一次性输入
- 地点是必填字段，缺少会阻止发布

**搜狐号**
- **patchright 无法绕过搜狐号反爬**，即使 CDP 连接也会被检测。实际通过 Chrome DevTools MCP 操作用户已打开的 Chrome 完成
- 编辑器是 Quill.js 不是 contenteditable，选择器用 `.ql-editor`
- SPA 路由跳转不渲染 DOM（6 次失败测试的根因），必须直接导航到编辑器 URL
- 发布按钮是 `<li>` 元素，不是 `<button>`
- 发布有两步确认弹窗
- `.click()` 在确认弹窗上可能无效，需用 JS `dispatchEvent` 兜底

### 12.3 后端架构坑

| 问题 | 说明 |
|------|------|
| `page.pause()` 不能用于生产 | 后端 subprocess 中浏览器打开即关闭，`page.pause()` 完全无效，改为轮询检测 |
| Cookie 新鲜度误判 | 旧 Cookie 文件导致重新认证时误判成功，需检查修改时间 |
| subprocess 编码崩溃 | 什么值得买 GBK 中文输出导致 `UnicodeDecodeError`，改为 binary 模式 + `errors='replace'` |
| subprocess 卡死 | `for line in proc.stdout` 阻塞读取，CLI 不退出时后端卡死，改为独立线程 + 超时保护 |
| Pinia `storeToRefs` 陷阱 | `ref()` 属性通过 `store.property` 访问被 Pinia 自动解包，`.value` 为 `undefined` 导致静默崩溃 |

---

## 十三、新增平台指南

如需新增一个图文发布平台，按以下步骤操作：

### Step 1: 创建上传器

```
uploader/<platform>_uploader/
├── __init__.py     # Cookie 目录初始化
├── main.py         # 登录流程（cookie_gen + cookie_auth + setup）
└── article.py      # EditorPage + <Platform>Article 类
```

### Step 2: 实现 main.py（登录）

必须包含三个函数：
- `<platform>_cookie_gen()` — 启动浏览器，扫码登录，保存 Cookie
- `cookie_auth()` — 加载 Cookie 验证有效性
- `<platform>_setup()` — 组合入口函数

### Step 3: 实现 article.py（发布）

必须包含两个类：
- `EditorPage` — 编辑器页面交互模型
  - `navigate_to_editor()` — 导航到编辑器
  - `dismiss_popups()` — 关闭弹窗
  - `wait_for_editor_ready()` — 等待编辑器加载
  - `clear_editor()` — 清空编辑器（铁律：每次发布前必须清空）
  - `fill_title()` — 填写标题
  - `fill_content()` — 填写正文
  - `upload_images()` — 上传图片
  - `publish()` — 点击发布
  - `verify_publish_success()` — 验证发布结果
- `<Platform>Article` — 发布器主类
  - `main()` — async 入口
  - `upload()` — 完整发布流程

### Step 4: 集成到 CLI

修改 `sau_cli.py`：
1. 添加 import
2. 添加 platform dataclass
3. 添加 handler 函数
4. 添加 subparser
5. 添加到 dispatch 映射

### Step 5: 集成到后端

修改以下文件：
- `myUtils/postArticle.py` — 添加平台发布逻辑
- `myUtils/auth.py` — 添加 Cookie 校验调度
- `sau_backend.py` — 更新平台映射（如需要）

### Step 6: 集成到前端

- `AccountManagement.vue` — 添加平台 Tab
- `ArticlePublish.vue` — 添加平台选项
- `stores/account.js` — 添加平台 ID 映射

### Step 7: 创建 Skill 包

```
skills/<platform>-upload/
├── SKILL.md
├── references/
│   ├── cli-contract.md
│   ├── runtime-requirements.md
│   └── troubleshooting.md
└── scripts/examples/
```

### Step 8: 更新文档

- `CLAUDE.md` — 添加平台 SOP
- `CHANGELOG.md` — 记录变更
- `utils/log.py` — 添加平台 logger

### Step 9: 验证流程

1. 先用 Chrome DevTools MCP 探索平台编辑器 DOM 结构
2. 确认编辑器类型（UEditor / ProseMirror / Draft.js / Quill.js / 其他）
3. 确认交互方式（fill / execCommand / keyboard.type / keyboard.insert_text）
4. 用 MCP 完整走一遍发布流程
5. 将验证过的选择器和流程写入代码
6. 用 `--headed` 模式实际测试

---

## 十四、Chrome DevTools MCP

Chrome DevTools MCP 在本项目中有两个角色：**调试工具**（所有平台）和**发布工具**（搜狐号）。

### 启用方式

1. 用远程调试模式启动 Chrome：
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

2. 在 Claude Code 中使用 MCP 工具：
- `take_snapshot` — 获取页面 DOM 快照（a11y 树）
- `evaluate_script` — 执行 JS 代码
- `click` / `fill` / `upload_file` — 模拟用户操作
- `navigate_page` — 页面导航
- `take_screenshot` — 截图
- `wait_for` — 等待特定文本出现

### 角色 1：调试工具（所有平台通用）

新平台开发时，推荐用 MCP 先探索再写代码：

1. 用 MCP `navigate_page` 打开平台编辑器
2. 用 `take_snapshot` 查看完整 DOM 结构
3. 用 `evaluate_script` 检查编辑器类型
4. 用 `click` / `fill` 测试交互
5. 用 `upload_file` 测试图片上传
6. 确认完整流程后，将选择器和交互方式写入 `article.py`

### 角色 2：搜狐号的正式发布工具

搜狐号反爬机制较强，patchright 无法绕过（测试 6 次全部失败）。最终改为通过 MCP 直接操作用户已打开的 Chrome 浏览器完成发布。

**为什么搜狐号必须用 MCP**：
- patchright（Playwright 分支）即使通过 CDP 连接也会被搜狐号检测为自动化工具
- MCP 操作的是用户真实的 Chrome 浏览器，与真人操作完全一致，不存在指纹检测问题
- MCP 工具可以直接操作 DOM（`evaluate_script`、`click`、`fill`），调试效率远高于 patchright 的 try/except 循环

**搜狐号 MCP 发布的完整操作序列**：

| 步骤 | MCP 工具 | 操作 |
|------|----------|------|
| 1 | `navigate_page` | 导航到编辑器 URL |
| 2 | `take_snapshot` | 查看页面状态 |
| 3 | `click` | 关闭"我知道了"弹窗 |
| 4 | `fill` | 填写标题 |
| 5 | `evaluate_script` | `execCommand('insertHTML')` 写入正文 |
| 6 | `click` | 点击工具栏图片按钮 |
| 7 | `upload_file` | 上传图片文件 |
| 8 | `wait_for` | 等待上传完成 |
| 9 | `click` | 点击"确定"插入图片 |
| 10 | `click` | 点击发布按钮 |
| 11 | `evaluate_script` | 检测确认弹窗 + `dispatchEvent` 点"确定" |
| 12 | `wait_for` | 等待跳转到内容管理页 |

---

## 十五、常见问题排查

### Cookie 失效

- **症状**：被重定向到登录页
- **排查**：检查 `logs/<platform>.log` 是否有 Cookie 过期提示
- **解决**：重新执行 `sau <platform> login --account <name> --headed`

### 编辑器加载超时

- **症状**：日志显示"编辑器加载超时，继续执行..."
- **排查**：
  1. 是否被重定向到登录页？
  2. 编辑器选择器是否正确？
  3. 网络是否正常？
- **解决**：用 `--headed` 模式观察实际页面状态

### 标题/正文填写失败

- **症状**：Locator.click Timeout
- **排查**：
  1. 编辑器是否已加载？
  2. 选择器是否匹配当前 DOM？
  3. 是否有弹窗遮挡？
  4. SPA 路由是否正确渲染？
- **解决**：用 Chrome DevTools MCP `take_snapshot` 检查实际 DOM

### 发布按钮点击无效

- **症状**：点击发布无反应
- **排查**：
  1. 按钮元素类型（button / li / div / a）？
  2. 是否有遮罩层拦截？
  3. 是否需要两步确认？
- **解决**：用 JS `dispatchEvent` 代替 `.click()`

### 后端登录子进程卡死

- **症状**：前端登录一直转圈
- **排查**：检查后端日志，是否 subprocess 阻塞
- **解决**：已加 180 秒超时保护 + 独立线程读取

---

## 十六、Git 与发布

### 仓库配置

- **myrepo**: `karmawind/binggo-island-upload-tool`（自有仓库，推送目标）

### 常用操作

```bash
# 推送到自有仓库
git push myrepo main

# 拉取上游更新
git pull origin main
```

### 版本号

遵循语义化版本（Semantic Versioning），记录在 `pyproject.toml` 和 `CHANGELOG.md` 中。

当前版本：**0.2.4**

---

*本文档由项目维护者编写，如有疑问请联系团队成员。*
