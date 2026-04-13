## 项目概述

本项目 `social-auto-upload` 是一款强大的自动化工具，旨在帮助内容创作者和运营人员高效地将视频内容一键发布到多个国内外主流社交媒体平台。项目实现了对 `抖音`、`B站`、`小红书`、`快手`、`视频号`、`百家号`、`TikTok` 等平台的视频上传、定时发布等功能。

项目由 Python 后端和 Vue.js 前端组成。

**后端：**

*   框架：Flask
*   核心功能：
    *   处理文件上传和管理。
    *   使用 SQLite 数据库存储文件和用户账号信息。
    *   使用 `patchright` 进行浏览器自动化，与社交媒体平台交互。
    *   提供 RESTful API 供前端调用。
    *   使用 Server-Sent Events（SSE）在登录过程中与前端实时通信。

**前端：**

*   框架：Vue.js
*   构建工具：Vite
*   UI 组件库：Element Plus
*   状态管理：Pinia
*   路由：Vue Router
*   核心功能：
    *   提供网页界面，用于管理社交媒体账号、视频文件和发布视频。
    *   通过 RESTful API 与后端通信。

**命令行界面：**

项目还提供命令行界面（CLI），方便偏好终端操作的用户使用。

支持的平台：`douyin`、`kuaishou`、`xiaohongshu`、`bilibili`、`baijiahao`、`smzdm`、`ctrip`、`sohu`。

每个平台支持：
*   `login`：登录并保存 cookie。
*   `check`：验证已保存的 cookie 是否仍然有效。
*   `upload-video`：上传单个视频文件，需显式指定元数据参数。
*   `upload-note`：上传图文笔记（抖音、快手、小红书）。
*   `upload-article`：发布图文文章（百家号、什么值得买、头条号、携程、搜狐号，支持标题、正文、图片、封面选择）。

新增平台 CLI 开发时，优先使用 `sau <platform> ...` 入口，而非旧版示例脚本。

## 构建与运行

### 后端

1.  **安装依赖：**
    ```bash
    pip install -r requirements.txt
    ```

2.  **安装 patchright 浏览器驱动：**
    ```bash
    patchright install chromium
    ```

3.  **初始化数据库：**
    ```bash
    python db/createTable.py
    ```

4.  **启动后端服务器：**
    ```bash
    python sau_backend.py
    ```
    后端服务将启动在 `http://localhost:5409`。

### 前端

1.  **进入前端目录：**
    ```bash
    cd sau_frontend
    ```

2.  **安装依赖：**
    ```bash
    npm install
    ```

3.  **启动开发服务器：**
    ```bash
    npm run dev
    ```
    前端开发服务器将启动在 `http://localhost:5173`。

### 命令行界面

使用 CLI 前，请先激活虚拟环境：

```bash
source .venv/Scripts/activate  # Windows Git Bash
```

**抖音：**

```bash
sau douyin login --account <账号名>
sau douyin check --account <账号名>
sau douyin upload-video --account <账号名> --file <视频文件> --title <标题> [--desc "描述"] [--tags 标签1,标签2]
sau douyin upload-note --account <账号名> --images 图片1.png 图片2.png --title <标题> [--note "正文"] [--tags 标签1,标签2]
```

**快手：**

```bash
sau kuaishou login --account <账号名>
sau kuaishou upload-video --account <账号名> --file <视频文件> --title <标题> [--desc "描述"] [--tags 标签1,标签2]
sau kuaishou upload-note --account <账号名> --images 图片1.png 图片2.png --title <标题> [--note "正文"] [--tags 标签1,标签2]
```

**小红书：**

```bash
sau xiaohongshu login --account <账号名>
sau xiaohongshu upload-video --account <账号名> --file <视频文件> --title <标题> [--desc "描述"] [--tags 标签1,标签2]
sau xiaohongshu upload-note --account <账号名> --images 图片1.png 图片2.png --title <标题> [--note "正文"] [--tags 标签1,标签2]
```

**B站：**

```bash
sau bilibili login --account <账号名>
sau bilibili upload-video --account <账号名> --file <视频文件> --title <标题> --desc "描述" --tid <分区ID> [--tags 标签1,标签2]
```

**百家号：**

```bash
sau baijiahao login --account <账号名> --headed
sau baijiahao check --account <账号名>
sau baijiahao upload-article --account <账号名> --title <标题> --content "正文" --images 图片1.png 图片2.png [--tags 标签1,标签2] [--schedule "YYYY-MM-DD HH:MM"] [--headed]
```

百家号图文发布使用 UEditor 编辑器，上传图片时会自动选择封面。推荐使用 `--headed` 模式便于观察和调试。

**什么值得买：**

```bash
sau smzdm login --account <账号名> --headed
sau smzdm check --account <账号名>
sau smzdm upload-article --account <账号名> --title <标题> --content "正文" --images 图片1.png 图片2.png [--tags 标签1,标签2] [--headed]
```

什么值得买图文发布使用 ProseMirror 编辑器，上传图片后需点击"插入正文"。推荐使用 `--headed` 模式。文章发布后需要人工审核，暂不支持定时发布。

**头条号：**

```bash
sau toutiao login --account <账号名> --headed
sau toutiao check --account <账号名>
sau toutiao upload-article --account <账号名> --title <标题> --content "正文" --images 图片1.png 图片2.png [--tags 标签1,标签2] [--headed]
```

头条号图文发布使用 ProseMirror 编辑器，发布需两步确认（预览并发布 → 确认发布）。推荐使用 `--headed` 模式。文章发布后需要人工审核。

**携程：**

```bash
sau ctrip login --account <账号名> --headed
sau ctrip check --account <账号名>
sau ctrip upload-article --account <账号名> --title <标题> --content "正文" --images 图片1.png 图片2.png --location "地点" [--headed]
```

携程图文发布使用 Draft.js 编辑器，标题和描述均为 DraftEditor contenteditable 组件。标题用 `page.keyboard.type()` 输入，正文用 `page.keyboard.insert_text()` 一次性输入，不能用 `execCommand` 或 `fill()`。发布必须指定地点（`--location`），否则验证不通过。推荐使用 `--headed` 模式。最多上传 20 张图片，推荐宽高比 3:4~2:1。不支持定时发布。

**搜狐号：**

```bash
sau sohu login --account <账号名> --headed
sau sohu check --account <账号名>
sau sohu upload-article --account <账号名> --title <标题> --content "正文" --images 图片1.png 图片2.png [--headed]
```

搜狐号图文发布使用 contenteditable 编辑器，标题限制 30 字，使用 `fill()` 填入。正文使用 `execCommand('insertHTML')` 写入。推荐使用 `--headed` 模式。不支持定时发布。

**安装内置技能包：**

```bash
sau skill install
```

## 百家号图文发布 SOP（已验证）

以下经验来自多次实际发布验证，修改百家号相关代码时务必遵守。

### 编辑器页面

- 编辑器 URL 必须带 `is_from_cms=1` 参数：`https://baijiahao.baidu.com/builder/rc/edit?type=news&is_from_cms=1`
- 刚登录后直接导航到编辑器可能被重定向到首页（stoken → home），需要重试（最多 3 次，每次等 3 秒）

### 正文填写

- 百家号使用 UEditor 编辑器，正文在 iframe 中
- **禁止使用 `innerHTML` 直接写入**，UEditor 不会识别内容状态变化，导致发布时认为编辑器为空
- **必须使用 `document.execCommand('insertHTML', false, html)`**，这样 UEditor 内部状态才会正确更新
- 填写正文前必须先 `await frame.focus()` 让 iframe 获得焦点

### 图片上传

- 上传图片前**必须先 focus iframe body**，否则文件上传对话框不会触发
- 流程：focus iframe → 点击工具栏图片按钮 → 等待上传弹窗出现 → 逐张 set_input_files → 点击确认

### 封面选择

- 使用单图封面模式（点击"单图"选项卡）
- **不要点击"选正文图"按钮**（会触发 30 秒禁用计时）
- 点击封面容器 `div._73a3a52aab7e3a36-content` 打开弹窗，正文图片会自动加载进弹窗
- 然后直接点击"确定"按钮完成封面选择

### 发布按钮

- 发布按钮的选择器是 `[data-testid="publish-btn"]`
- **`.click()` 和 `force_click()` 都无效**，该元素是包装层，真实事件监听在子元素上
- **必须使用 JS `dispatchEvent(new MouseEvent('mousedown', ...))` + `mouseup` + `click`**，且设置 `bubbles: true, cancelable: true`
- 发布前按 Escape 清除可能的残留弹窗

### 新手引导

- 新手引导只在首次发帖时出现，再次发帖不会出现
- 引导关闭逻辑用 `try/except` 包裹，**不要作为必填步骤**
- 检测关键词：页面文本包含"下一步"或"完成"
- 最多循环 10 次点击"下一步"/"完成"，找不到按钮就结束

### 验证发布成功

- 发布成功后页面会跳转到 `/builder/rc/clue` 页面
- 同时检测页面是否包含"提交成功"关键词

## 什么值得买图文发布 SOP（已验证）

以下经验来自多次实际发布验证，修改什么值得买相关代码时务必遵守。

### 编辑器页面

- 编辑器 URL：`https://post.smzdm.com/edit/a70658o9`
- 刚打开可能有"立即体验"升级弹窗，自动点击 `div.upgrade-tip-btn` 关闭
- **每次发布前必须调用 `clear_editor()`** 清空残留状态（SPA 页面不刷新，残留的标题/正文/图片/遮罩面板会导致不可预测的行为）

### 正文填写

- 什么值得买使用 ProseMirror 编辑器（`div.ProseMirror[contenteditable=true]`）
- **必须使用 `document.execCommand('insertHTML', false, html)`** 一次性写入，将纯文本段落转为 `<p>` 标签
- 填写前先 `editor.focus()`
- 标题使用 `textarea.fill()` 一次性填入（最多 80 字）

### 图片上传

- 上传图片必须通过工具栏图片按钮（`svg.zicon-picture`），不是页面上的"添加长图"按钮
- **JS 点击必须用 `dispatchEvent`**：`target.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))`，不要用 `.click()`（可能报 `btn.click is not a function`）
- 上传后必须点击"插入正文"（`div.btn-item`）关闭上传面板，否则面板遮挡后续操作
- 图片大小建议 500KB~8MB，小于 500KB 可能上传失败

### 封面图设置

- 封面图也通过工具栏图片按钮上传（不是独立的"添加长图"按钮）
- 上传后点击上传的图片本身（base64/blob src 的 img 元素）设为封面
- 然后点击"确定此图"（`button.cancel-btn`）→ 点击"确认"（`button.ok-btn`）

### 创作声明

- 有两个 radio 组：利益相关性和 AI 生成合成
- `div.mask` 遮罩层会拦截 `.click()`，必须用 JS `evaluate("el.click()")` 绕过

### 发布按钮

- 选择器：`.publish-btn`
- **`.click()` 可能被遮罩层拦截**，必须用 JS `dispatchEvent(new MouseEvent('mousedown', ...))` + `mouseup` + `click` 三连
- 发布前先关闭所有残留面板（`_close_residual_panels`）

### 验证发布成功

- 检测页面文本包含"提交成功"、"发布成功"、"审核"等关键词
- 或检测 URL 是否已跳转离开编辑页

### 遮罩层处理（全局规则）

- smzdm 页面大量使用 `div.mask`、浮层面板（`.upload-container-scroll`、`.insert-wrap`、`.pics`），所有点击操作都可能被遮挡，统一用 JS `evaluate` + `dispatchEvent` 或 `evaluate("el.click()")` 绕过

## 头条号图文发布 SOP（已验证）

以下经验来自实际发布验证，修改头条号相关代码时务必遵守。

### 编辑器页面

- 编辑器 URL：`https://mp.toutiao.com/profile_v4/graphic/publish`
- 页面加载后需关闭 AI 助手抽屉遮罩（`div.ai-assistant-drawer` + `div.byte-drawer-mask`），否则所有操作被拦截
- **每次发布前必须调用 `clear_editor()`** 清空残留状态

### 标题填写

- 选择器：`textarea[placeholder*='请输入文章标题']`
- 使用 `textarea.fill()` 一次性填入（最多 30 字）

### 正文填写

- 头条号使用 ProseMirror 编辑器（`div.ProseMirror[contenteditable=true]`）
- **必须使用 `document.execCommand('insertHTML', false, html)`** 一次性写入

### 图片上传

- 通过工具栏图片按钮上传（`div.syl-toolbar-tool.image button`），**必须用 JS `dispatchEvent` 点击**（遮罩拦截）
- 上传后需等待面板显示"已上传 X 张图片"
- **必须点击"确定"按钮**（`button.byte-btn-primary:has-text('确定')`）将图片插入正文
- 图片上传面板有 tab：上传图片 / 免费正版图片 / 热点图库 / 我的素材
- 图片大小限制 20MB

### 封面与广告

- 封面区域在编辑器右侧（`div.article-cover`），默认"单图"模式
- 正文有图片时自动匹配封面
- **广告设置必须选择"不投放广告"**，否则默认"投放广告赚收益"

### 发布按钮（两步确认）

- 第一步：点击"预览并发布"（`button.publish-btn.byte-btn-primary:has-text('预览并发布')`）
- 第二步：等待按钮文字变为"确认发布"，再点击"确认发布"
- **`dispatchEvent` 点击可能不可靠**，优先用 `.click()`，失败再用 JS

### 验证发布成功

- 发布成功后跳转到 `/profile_v4/graphic/articles` 内容管理页
- 同时检测页面文本含"发布成功"等关键词

## 携程图文发布 SOP（已验证）

以下经验来自实际发布验证，修改携程相关代码时务必遵守。

### 编辑器页面

- 编辑器 URL：`https://we.ctrip.com/publish/publishPictureText`
- 登录通过 we.ctrip.com 内容中心，扫码登录
- **每次发布前必须调用 `clear_editor()`** 清空残留状态

### 标题填写

- 携程使用 Draft.js 编辑器，标题是第一个 `div.public-DraftEditor-content` 组件
- **`execCommand('insertText')` 和 `execCommand('insertHTML')` 均无效**，Draft.js 是 React 状态管理
- **必须使用 `page.keyboard.type()` 逐字输入**，Draft.js 需要真实键盘事件触发状态更新
- 填写前先 `title_editor.click()` 聚焦

### 描述正文填写

- 描述正文是第二个 `div.public-DraftEditor-content` 组件
- **使用 `page.keyboard.insert_text()` 一次性输入**（比逐字输入快几十倍）
- 图片上传后可能有多个 DraftEditor 实例，用 JS 动态定位描述编辑器（跳过标题编辑器）
- 填写前先用 JS `focus()` 定位到描述编辑器

### 地点填写（必填）

- **携程要求必须添加至少一个地点，否则发布会被阻止并提示"请添加一个地点！"**
- 地点输入使用 `ant-select` 组件（`.ant-select-selection-search-input`）
- 输入地点关键词后等待下拉列表，选择第一个匹配项
- CLI 参数：`--location "杭州"`

### 图片上传

- 图片上传使用 `ant-upload` 组件（Ant Design 的上传组件）
- 需定位 `input[type='file'][accept='image/*']` 元素，使用 `set_input_files()` 上传图片
- 最多上传 20 张图片
- 推荐图片宽高比 3:4~2:1

### 发布按钮

- 发布按钮文字为"发 布"（中间有空格），匹配时需注意
- 使用 `.click()` 或 JS 点击发布

### 验证发布成功

- 发布成功后页面跳转到 `contentManagement`（内容管理页）
- 检测页面文本包含"已发布"、"发布成功"等关键词
- 或检测 URL 离开发布页

## 搜狐号图文发布 SOP

以下经验来自参考项目 aaaaqwq/claude-code-skills media-auto-publisher，修改搜狐号相关代码时务必遵守。

### 编辑器页面

- 编辑器 URL：`https://mp.sohu.com/api/author/article/new`
- 页面使用 Vue.js + Element UI 构建
- 登录后页面可能出现"我知道了"、"知道了"等弹窗，需自动关闭

### 标题填写

- 选择器：`input[name="title"]` 或 `input[placeholder*="标题"]`
- 标题限制 30 字
- 使用 `fill()` 一次性填入

### 正文填写

- 编辑器类型：contenteditable（`#editor` / `.editor-content` / `[contenteditable="true"]`）
- 使用 `document.execCommand('insertHTML', false, html)` 写入
- 填写前先 `editor.focus()`

### 图片上传

- 通过 `input[type="file"][accept*="image"]` 上传
- 备选：通过 `.cover-upload` 按钮触发 file input

### 发布按钮

- 选择器：`button.publish-btn` 或 `button:has-text('发布')`
- 直接 `.click()` 失败时用 JS `dispatchEvent` 兜底

### 验证发布成功

- 检测页面文本包含"发布成功"、"提交成功"、"审核"等关键词
- 或检测 URL 离开 `/article/new` 页面

## 开发规范

*   后端代码位于根目录以及 `myUtils` 和 `uploader` 目录。
*   前端代码位于 `sau_frontend` 目录。
*   项目使用 SQLite 数据库存储数据，数据库文件位于 `db/database.db`。
*   将 `conf.example.py` 复制为 `conf.py` 并进行相应配置。
*   `requirements.txt` 列出了 Python 依赖。
*   `sau_frontend` 目录下的 `package.json` 列出了前端依赖。
*   浏览器自动化使用 `patchright`（无反爬检测的 Playwright 分支），而非 `playwright`。
*   各平台上传器位于 `uploader/<平台>_uploader/`。百家号同时包含视频上传器（`main.py`）和图文上传器（`article.py`）。什么值得买、头条号和携程包含登录（`main.py`）和图文上传器（`article.py`）。
*   技能包位于 `skills/<平台>-upload/`，提供 SKILL.md、CLI 约定、运行时要求、故障排查和示例脚本。
*   Cookie 文件存储在 `cookies/<平台>_<账号名>.json`。
*   版本历史记录在 `CHANGELOG.md` 中。
*   新增平台或功能时，需同步更新 `CHANGELOG.md` 和 `CLAUDE.md`。

## 铁律

**每实现一个功能，经我确认后，必须将更新日志和踩过的坑总结到 `CHANGELOG.md` 中。**

**所有平台的自动化测试必须从空白/干净的编辑器状态开始，绝不延续上一次测试的编辑状态。** 残留的标题、正文、图片、遮罩面板、弹窗等 DOM 元素会导致后续所有操作出现不可预见的情况（按钮被遮挡、内容重复、选择器匹配错误、上传面板异常等）。每次发布/测试前必须有清空编辑器的步骤。
