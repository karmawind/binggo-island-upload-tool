# 前端可视化图文发布系统 — 开发进度

## 模块总览

| # | 模块 | 状态 | 完成日期 |
|---|------|------|---------|
| 1 | 数据库扩展 | ✅ 完成 | 2026-04-12 |
| 2 | 后端账号与 Cookie 校验扩展 | ✅ 完成 | 2026-04-12 |
| 3 | 后端图文发布 API | ✅ 完成 | 2026-04-12 |
| 4 | 前端账号管理扩展 | ✅ 完成 | 2026-04-12 |
| 5 | 前端图文发布页面 | ✅ 完成 | 2026-04-12 |
| 6 | 前端帖子管理与批量发布 | ✅ 完成 | 2026-04-12 |
| 7 | 任务进度跟踪 | ✅ 完成 | 2026-04-12 |
| 8 | 多平台并行分发 | ✅ 完成 | 2026-04-12 |
| 9 | 定时排期调度器 | ✅ 完成 | 2026-04-12 |
| 10 | CSV 批量导入 | ✅ 完成 | 2026-04-12 |
| 11 | CLI 登录集成到前端 | ✅ 完成 | 2026-04-12 |
| 12 | 登录流程修复（page.pause 问题） | ✅ 完成 | 2026-04-12 |
| 13 | 编辑状态保留 + 重新认证 + 平台修复 | ✅ 完成 | 2026-04-12 |
| 14 | Pinia storeToRefs 修复（发布/保存按钮无反应） | ✅ 完成 | 2026-04-12 |

---

## 模块 1：数据库扩展

**目标：** 新增 `article_posts` 和 `article_images` 表

### 经验记录

- `db/createTable.py` 的 `db_file` 原来用 `'./database.db'`（相对 CWD），从项目根运行时会创建错误位置的数据库。已修正为 `os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')`，与 `sau_backend.py` 的 `BASE_DIR / "db" / "database.db"` 一致。
- 后端统一使用 `db/database.db`，所有脚本必须指向同一路径。
- 迁移脚本用 `CREATE TABLE IF NOT EXISTS`，可重复运行。

### 踩坑记录

- **数据库路径不一致**：`createTable.py` 用 `./database.db`，后端用 `db/database.db`。从项目根运行 `python db/createTable.py` 时 CWD 是项目根，导致数据库建在根目录而非 `db/` 目录下。修正为使用 `__file__` 的绝对路径。

---

## 模块 2：后端账号与 Cookie 校验扩展

**目标：** 扩展 `myUtils/auth.py` 的 `check_cookie()` 支持 type 5-8

### 经验记录

- 各平台的 `cookie_auth(account_file)` 函数签名一致，直接导入即可
- 图文平台（5-8）的 `cookie_auth` 内部用 `patchright`，视频平台（1-4）的用 `playwright`，两者不冲突，各自管理浏览器实例
- Web 后端的 cookie 存在 `cookiesFile/<uuid>.json`，CLI 存在 `cookies/<platform>_<account>.json`，两套独立。Web 端直接传 `str(cookie_path)` 给各平台的 `cookie_auth` 即可

### 踩坑记录

- **百家号 `cookie_auth` 缺少文件存在检查：** 文件不存在时直接抛 `FileNotFoundError` 而不是返回 False。已加上 `if not os.path.exists(account_file): return False`。smzdm/toutiao/ctrip 已有此检查。

---

## 模块 3：后端图文发布 API

**目标：** 创建 `myUtils/postArticle.py` + `sau_backend.py` 新端点

### 新增文件
- `myUtils/postArticle.py` — 图文发布调度（4 个平台函数 + `_run_in_thread` + `dispatch_multi_platform`）
- 后端新增路由：`/uploadImage` `/getImages` `/deleteImage` `/postArticle` `/articleTaskStatus` `/getArticlePosts` `/saveArticlePost` `/updateArticlePost` `/deleteArticlePost` `/loginArticleAccount` `/scheduleArticles` `/importArticles`

### 经验记录
- 图文发布用后台线程（`threading.Thread`）执行，不阻塞 Flask 主线程
- 每个平台函数内部用 `asyncio.new_event_loop()` 创建独立事件循环
- callback 模式：发布完成后回调 `on_result` 更新 `article_tasks` 字典
- 图片存储在 `imageFile/` 目录（与视频的 `videoFile/` 分离）
- 任务跟踪用全局字典 `article_tasks`，前端可轮询 `/articleTaskStatus`

---

## 模块 4：前端账号管理扩展

**目标：** 扩展 stores/account.js + AccountManagement.vue 支持 8 平台

### 经验记录
- 前端构建验证用 `npx vite build`，不能直接用 `vite build`（全局没装 vite）
- Vue 文件中的缩进混合了空格和 tab，导致 Edit 工具匹配困难。用 Python 脚本处理编码更可靠
- AccountManagement.vue 的 Tab 代码是高度重复的（每个平台一个 Tab），后续可以重构为动态生成

### 踩坑记录
- **Edit 工具匹配中文+空格的字符串失败**：多次尝试 Edit 工具替换失败，因为文件中 tab/空格混合导致精确匹配困难。最终用 Python 脚本直接操作文件内容解决

---

## 模块 5：前端图文发布页面（多平台版）

**目标：** 新建 `views/ArticlePublish.vue` + `api/article.js`

### 新增文件
- `sau_frontend/src/views/ArticlePublish.vue` — 图文发布页面（多平台多选→每平台选账号→标题→正文→图片上传→标签→地点→发布）
- `sau_frontend/src/api/article.js` — 图文相关 API
- `sau_frontend/src/views/ArticleManagement.vue` — 帖子管理页面（列表、筛选、排期、批量发布、CSV导入）
- `sau_frontend/src/stores/articleDraft.js` — 编辑状态持久化（路由切换不丢失）
- 路由：`/article-publish` 和 `/article-management`
- 侧边栏：新增"图文发布"和"帖子管理"菜单

### 经验记录
- 图片上传使用 Element Plus 的 `el-upload` 组件，`action` 指向后端 `/uploadImage`
- 发布后通过轮询 `/articleTaskStatus` 获取进度（2秒间隔）
- 多平台分发：平台选择从 `el-radio-group` 改为 `el-checkbox-group`，每个平台独立选账号
- 后端 `/postArticle` 支持 `platformAccounts` 参数（`{5: ['cookie1.json'], 7: ['cookie2.json']}`）
- 后端 `dispatch_multi_platform` 为每个平台创建独立线程并行执行

---

## 模块 8：多平台并行分发

**目标：** 一篇帖子同时发到多个平台

### 改动点
- 数据库 `article_posts` 新增 `platforms` 字段（JSON 数组）
- `myUtils/postArticle.py` 新增 `dispatch_multi_platform()` 函数，为每个平台创建线程并行执行
- `sau_backend.py` `/postArticle` 支持 `platformAccounts` 参数，兼容旧的 `type` + `accountList` 单平台模式
- 前端 `ArticlePublish.vue` 平台选择改为多选，每个平台独立选账号

### 经验记录
- 多平台并行分发用 `threading.Thread` + `join()` 等待所有平台完成
- 前端构造 `platformAccounts` 对象（每个平台对应其账号列表），后端按平台分发

---

## 模块 9：定时排期调度器

**目标：** 批量排期自动发送

### 改动点
- 数据库 `article_posts` 新增 `scheduled_at` 字段（DATETIME）
- 后端新增 `_article_scheduler()` 后台线程，每 60 秒检查到期帖子
- 新增 `/scheduleArticles` 端点：接收帖子 ID 列表 + 起始时间 + 间隔分钟数
- 前端 `ArticleManagement.vue` 新增排期对话框

### 经验记录
- 调度线程在 Flask 启动时自动启动（`threading.Thread(daemon=True)`）
- 排期计算：`base + timedelta(minutes=interval * i)`
- 帖子状态流转：`draft` → `scheduled` → `published`/`failed`

---

## 模块 10：CSV 批量导入

**目标：** 通过上传 CSV 文件批量创建帖子

### 改动点
- 后端新增 `/importArticles` 端点，解析 CSV（支持中英文列名）
- 前端 `ArticleManagement.vue` 新增"导入 CSV"按钮

### CSV 模板格式
| title | content | image_paths | tags | location | platforms |
|-------|---------|-------------|------|----------|-----------|
| 杭州三日游 | 杭州真的太美了... | img1.jpg,img2.jpg | 旅游,杭州 | 杭州 | [5,7,8] |

---

## 模块 11：CLI 登录集成到前端

**目标：** 前端图文平台添加账号时自动调用 CLI 登录，自动上传 cookie

### 实现方式
- 后端新增 `/loginArticleAccount` SSE 端点
- 后端用 `subprocess.Popen` 调用 `sau <platform> login --account <name> --headed`
- CLI 输出通过 SSE 实时推送到前端
- 登录成功后后端自动：复制 cookie + 创建/更新 user_info 记录
- 前端 `connectSSE` 函数判断平台类型 5-8 走新端点，显示文字引导消息

### 经验记录
- `subprocess.Popen` 的 `cwd` 要设为项目根目录，否则 CLI 找不到模块
- 图文平台用 `loginMessages` ref 显示文字引导，视频平台用 `qrCodeData` 显示二维码
- SSE 消息格式统一：文字消息直接推送，状态码 '200'/'500' 表示成功/失败
- 需要区分新建账号（INSERT）和重新认证（UPDATE cookie），不能重复 INSERT

### 踩坑记录
- **Cookie 新鲜度误判**：旧的 cookie 文件可能已存在，子进程报错退出时代码误判为成功。已加上文件修改时间检查（10 秒内才算新生成）
- **重新认证重复创建账号**：原逻辑只有 INSERT，重新认证时会主键冲突。已改为先查是否已存在，存在则 UPDATE cookie

---

## 模块 12：登录流程修复（page.pause 问题）⚠️ 关键坑

**目标：** 修复百家号等平台的登录流程在子进程中直接跳过浏览器的问题

### 问题
百家号 `baijiahao_cookie_gen()` 使用 `await page.pause()` 等待用户登录。`page.pause()` 是 Playwright 的调试功能，需要 **Playwright Inspector 界面**才能点击"继续"。在 subprocess 子进程中没有 Inspector，`page.pause()` 直接跳过或超时退出，导致：
- 浏览器打开后立即关闭
- Cookie 未生成或为空
- 后端误判为登录成功（旧 cookie 文件仍存在）

### 修复方案
百家号改为**轮询检测登录状态**（最多等 2 分钟）：
```python
for i in range(120):  # 最多等 2 分钟
    await asyncio.sleep(1)
    url = page.url
    if 'login' not in url.lower():
        break
```

同样修复了什么值得买和头条号的 fallback `page.pause()`。

### 经验记录（重要）
- **`page.pause()` 不能用于生产环境**：它是 Playwright 调试工具，只在有 Inspector 的交互式终端中有效。子进程、后台线程、服务进程中都会直接跳过
- **正确的登录等待方式**：轮询检测 URL 跳转或页面元素出现（登录成功标识）
- **百家号登录成功检测**：URL 离开 login/auth 页面，或页面出现"发布内容"/"作品管理"
- **什么值得买**：检测 `a.nickname`、`a[href*='hai']` 等用户标识
- **头条号**：检测 URL 中不再包含 login/auth/passport
- **携程**：检测页面文字包含"发布内容"/"作品管理"/"发布笔记"

### 踩坑记录
- **百家号登录秒过**：`page.pause()` 在子进程中无效，浏览器打开即关闭。改为轮询 URL 跳转
- **什么值得买/头条号 fallback 也是 page.pause**：登录超时后的 fallback 同样无效，改为直接超时退出

---

## 模块 13：编辑状态保留 + 重新认证 + 平台修复

**目标：** 路由切换保留编辑状态，账号管理加重新认证按钮，修复平台特定问题

### 改动点
- 新增 `stores/articleDraft.js` — Pinia store 持久化图文发布页的表单、平台选择、账号选择、图片列表
- `ArticlePublish.vue` 改为从 store 读取数据，发布成功后 `draftStore.reset()`
- 所有平台 Tab 的账号操作列新增"重新认证"按钮（橙色 warning 样式）
- 什么值得买标题截断从 80 字改为 30 字
- 携程正文从 `keyboard.type()` 逐字输入改为 `keyboard.insert_text()` 一次性输入

### 经验记录
- Pinia store 天然是全局响应式的，路由切换时组件销毁但 store 数据保留
- `el-checkbox` 在 Element Plus 中用 `:value` 绑定数值（非 `:label`）
- 携程的 Draft.js 编辑器支持 `keyboard.insert_text()`，比逐字输入快几十倍
- `fileList` 也需要持久化到 store，否则已上传的图片预览会丢失

### 踩坑记录
- **携程正文逐字输入太慢**：`keyboard.type(text, delay=10)` 3000 字需要 30 秒。改为 `keyboard.insert_text()` 一次性粘贴，瞬间完成
- **什么值得买标题超限**：什么值得买标题限制 30 字，原代码截断到 80 字导致发布失败。改为 30 字截断

---

## 全局踩坑总结

### 1. `page.pause()` 不能用于生产环境
这是最大的坑。百家号、什么值得买、头条号的登录函数都用了 `page.pause()` 等待用户手动操作。这在 CLI 直接运行时有效（有终端 Inspector），但在后端 subprocess 中完全无效。**所有等待用户操作的地方都必须改为轮询检测页面状态。**

### 2. Cookie 文件路径不统一
CLI 用 `cookies/<platform>_<account>.json`，Web 后端用 `cookiesFile/<uuid>.json`。两者完全独立，不能混用。后端 `_run_cli_login` 需要：CLI 生成 → 检测文件存在 → 复制到 cookiesFile → 写入数据库。

### 3. 数据库迁移路径
`createTable.py` 用 `'./database.db'`（相对 CWD），迁移脚本用 `__file__` 绝对路径。必须统一用 `__file__` 绝对路径，否则从不同目录运行会创建多个数据库文件。

### 4. Flask async 路由 + 子进程
Flask 的 `async def` 路由配合 `subprocess.Popen` 时，子进程的 stdout 读取是阻塞的，会占用 Flask 线程。必须放在 `threading.Thread` 中执行。

### 5. Vue 文件编码问题
`.vue` 文件中 tab 和空格混合、中文字符等导致 Edit 工具精确匹配困难。遇到此类问题直接用 Python 脚本 `sed` 或 `open()` 操作更可靠。

### 6. 前端依赖缺失
.venv 缺少 `flask-cors`、`playwright`、`xhs` 等依赖，导致后端启动失败。必须用 `.venv/Scripts/python.exe -m pip install -r requirements.txt` 一次性安装。`start.bat` 应检查关键依赖是否存在。

### 7. 目录不存在导致上传失败
`videoFile/`、`imageFile/`、`cookiesFile/` 目录如果不存在，文件上传会报 `FileNotFoundError`。`start.bat` 中应自动 `mkdir` 这些目录。

### 8. Pinia setup store 的 ref 自动解包陷阱 ⚠️ 关键坑

Pinia setup store 中 `ref()` 返回的属性，通过 `store.property` 访问时会被 Pinia **自动解包**（返回原始值而非 ref wrapper）。如果直接赋值给 const 变量，后续调用 `.value` 会得到 `undefined`，引发 TypeError 静默崩溃。

**正确做法：**
- `ref()` 属性 → 用 `storeToRefs(store)` 解构
- `reactive()` 属性 → 可以直接 `store.property` 解构

```javascript
// ❌ 错误 — selectedPlatforms 变成普通数组，.value 为 undefined
const selectedPlatforms = draftStore.selectedPlatforms

// ✅ 正确 — 保持 ref 包装
const { selectedPlatforms, fileList } = storeToRefs(draftStore)
const form = draftStore.form  // reactive 可以直接解构
```

**症状：** async 函数中 TypeError 导致静默崩溃，按钮点击后"无反应"，无任何错误提示。

---

## 模块 14：Pinia storeToRefs 修复（发布/保存按钮无反应）

**目标：** 修复图文发布页面"立即发布"按钮无反应、"保存草稿"显示保存失败的问题

### 改动点
- `ArticlePublish.vue` 中 `selectedPlatforms` 和 `fileList` 从直接赋值改为 `storeToRefs()` 解构

### 经验记录
- Pinia setup store 中 `ref()` 属性通过 `store.property` 访问时会被自动解包为原始值
- 直接 `const x = store.refProp` 得到的是原始值，调用 `x.value` 为 `undefined`
- async 函数中 `undefined.length` 抛 TypeError，成为 unhandled rejection，不显示任何错误
- `reactive()` 属性不受影响，可以直接解构
- 必须用 `storeToRefs(store)` 保留 ref 包装

### 踩坑记录
- **发布按钮"无反应"**：`selectedPlatforms.value.length` 抛 TypeError（`selectedPlatforms` 是被解包的普通数组，`.value` 为 `undefined`），async 函数静默崩溃
- **保存草稿失败**：同上，`selectedPlatforms.value` 为 `undefined` 导致请求数据异常

**症状：** async 函数中 TypeError 导致静默崩溃，按钮点击后"无反应"，无任何错误提示。
