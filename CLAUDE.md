## Project Overview

This project, `social-auto-upload`, is a powerful automation tool designed to help content creators and operators efficiently publish video content to multiple domestic and international mainstream social media platforms in one click. The project implements video upload, scheduled release and other functions for platforms such as `Douyin`, `Bilibili`, `Xiaohongshu`, `Kuaishou`, `WeChat Channel`, `Baijiahao` and `TikTok`.

The project consists of a Python backend and a Vue.js frontend.

**Backend:**

*   Framework: Flask
*   Core Functionality:
    *   Handles file uploads and management.
    *   Interacts with a SQLite database to store information about files and user accounts.
    *   Uses `patchright` for browser automation to interact with social media platforms.
    *   Provides a RESTful API for the frontend to consume.
    *   Uses Server-Sent Events (SSE) for real-time communication with the frontend during the login process.

**Frontend:**

*   Framework: Vue.js
*   Build Tool: Vite
*   UI Library: Element Plus
*   State Management: Pinia
*   Routing: Vue Router
*   Core Functionality:
    *   Provides a web interface for managing social media accounts, video files, and publishing videos.
    *   Communicates with the backend via a RESTful API.

**Command-line Interface:**

The project also provides a command-line interface (CLI) for users who prefer to work from the terminal.

Supported platforms: `douyin`, `kuaishou`, `xiaohongshu`, `bilibili`, `baijiahao`.

Each platform supports:
*   `login`: To log in and save cookie.
*   `check`: To verify whether the saved cookie is still valid.
*   `upload-video`: To upload one video file with explicit metadata flags.
*   `upload-note`: To upload image-based posts (douyin, kuaishou, xiaohongshu).
*   `upload-article`: To publish articles (baijiahao only, with title, content, images, cover selection).

For new platform CLI work, prefer the `sau <platform> ...` entrypoint over legacy example scripts.

## Building and Running

### Backend

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install patchright browser drivers:**
    ```bash
    patchright install chromium
    ```

3.  **Initialize the database:**
    ```bash
    python db/createTable.py
    ```

4.  **Run the backend server:**
    ```bash
    python sau_backend.py
    ```
    The backend server will start on `http://localhost:5409`.

### Frontend

1.  **Navigate to the frontend directory:**
    ```bash
    cd sau_frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Run the development server:**
    ```bash
    npm run dev
    ```
    The frontend development server will start on `http://localhost:5173`.

### Command-line Interface

To use the CLI, activate the virtual environment first:

```bash
source .venv/Scripts/activate  # Windows Git Bash
```

**Douyin:**

```bash
sau douyin login --account <account_name>
sau douyin check --account <account_name>
sau douyin upload-video --account <account_name> --file <video_file> --title <title> [--desc "desc"] [--tags tag1,tag2]
sau douyin upload-note --account <account_name> --images img1.png img2.png --title <title> [--note "content"] [--tags tag1,tag2]
```

**Kuaishou:**

```bash
sau kuaishou login --account <account_name>
sau kuaishou upload-video --account <account_name> --file <video_file> --title <title> [--desc "desc"] [--tags tag1,tag2]
sau kuaishou upload-note --account <account_name> --images img1.png img2.png --title <title> [--note "content"] [--tags tag1,tag2]
```

**Xiaohongshu:**

```bash
sau xiaohongshu login --account <account_name>
sau xiaohongshu upload-video --account <account_name> --file <video_file> --title <title> [--desc "desc"] [--tags tag1,tag2]
sau xiaohongshu upload-note --account <account_name> --images img1.png img2.png --title <title> [--note "content"] [--tags tag1,tag2]
```

**Bilibili:**

```bash
sau bilibili login --account <account_name>
sau bilibili upload-video --account <account_name> --file <video_file> --title <title> --desc "desc" --tid <int> [--tags tag1,tag2]
```

**Baijiahao:**

```bash
sau baijiahao login --account <account_name> --headed
sau baijiahao check --account <account_name>
sau baijiahao upload-article --account <account_name> --title <title> --content "content" --images img1.png img2.png [--tags tag1,tag2] [--schedule "YYYY-MM-DD HH:MM"] [--headed]
```

百家号图文发布使用 UEditor 编辑器，上传图片时会自动选择封面。推荐使用 `--headed` 模式便于观察和调试。

**Install bundled skill:**

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

## Development Conventions

*   The backend code is located in the root directory and the `myUtils` and `uploader` directories.
*   The frontend code is located in the `sau_frontend` directory.
*   The project uses a SQLite database for data storage. The database file is located at `db/database.db`.
*   The `conf.example.py` file should be copied to `conf.py` and configured with the appropriate settings.
*   The `requirements.txt` file lists the Python dependencies.
*   The `package.json` file in the `sau_frontend` directory lists the frontend dependencies.
*   Browser automation uses `patchright` (Playwright fork without anti-bot detection), not `playwright`.
*   Each platform uploader lives in `uploader/<platform>_uploader/`. Baijiahao has both video (`main.py`) and article (`article.py`) uploaders.
*   Skill packages are in `skills/<platform>-upload/`, providing SKILL.md, CLI contract, runtime requirements, troubleshooting, and example scripts.
*   Cookie files are stored in `cookies/<platform>_<account_name>.json`.
*   Version history is tracked in `CHANGELOG.md`.
*   When adding a new platform or feature, update `CHANGELOG.md` and `CLAUDE.md`.
