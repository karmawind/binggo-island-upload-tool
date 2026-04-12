# 待办功能清单

## 一、一篇帖子多平台分发 ✅ 已完成

**优先级：高**

### 需求
一篇帖子同时发布到多个平台（百家号+头条号+携程+什么值得买），每个平台各自选择账号。

### 改动点

#### 数据库
- `article_posts` 表 `platform` 字段改为 `platforms`（TEXT，JSON 数组，如 `[5,7,8]`）
- 保留 `platform` 字段做向后兼容，新增 `platforms`

#### 后端
- `sau_backend.py` `/postArticle` 端点支持 `typeList`（数组），为每个平台+账号组合创建独立任务
- `myUtils/postArticle.py` 新增 `dispatch_multi_platform()` 并行分发函数
- 统一进度跟踪：一个 taskId 下包含多个子任务

#### 前端
- `ArticlePublish.vue` 平台选择从 `el-radio-group` 改为 `el-checkbox-group`
- 每个平台下方显示对应的账号选择
- 发布进度面板显示每个平台的独立状态

---

## 二、批量排期自动发送 ✅ 已完成

**优先级：高**

### 需求
准备多个图文内容，设置排期规则（每天发X篇，间隔Y小时），自动定时发布。

### 改动点

#### 数据库
- `article_posts` 新增字段：
  - `scheduled_at` DATETIME — 计划发布时间
  - `platforms` TEXT — JSON 数组，多平台目标
  - `schedule_rule` TEXT — JSON，排期规则（如 `{"interval_hours": 4, "daily_limit": 3}`）

#### 后端
- 新增排期计算函数：给定一批帖子 + 排期规则 → 自动分配 `scheduled_at`
- 新增调度线程：每 60 秒检查 `article_posts` 中 `status='scheduled' AND scheduled_at <= NOW()` 的记录，执行发布
- `sau_backend.py` 新增端点：
  - `POST /scheduleArticles` — 接收帖子 ID 列表 + 排期规则，批量设置定时
  - `GET /scheduledTasks` — 查看待执行的任务列表

#### 前端
- `ArticleManagement.vue` 批量操作新增"排期发布"按钮
- 弹出排期设置对话框：
  - 起始日期/时间
  - 每天发布数量
  - 发布间隔（小时）
- 新增"排期任务"Tab 或页面，查看所有待执行的定时任务

---

## 三、Excel/CSV 批量导入帖子 ✅ 已完成

**优先级：中**

### 需求
通过上传 Excel 或 CSV 文件批量创建帖子，避免手动逐篇填写。

### 改动点

#### 后端
- `sau_backend.py` 新增 `POST /importArticles` 端点
- 解析 CSV/XLSX，每行对应一篇帖子（标题、正文、图片路径、标签、地点）
- 批量写入 `article_posts` 表
- 依赖：`openpyxl`（Excel）或 `pandas`

#### 前端
- `ArticleManagement.vue` 新增"导入"按钮
- 上传文件后预览解析结果，确认后批量创建

#### Excel 模板格式
| 标题 | 正文 | 图片路径 | 标签 | 地点 | 平台 |
|------|------|---------|------|------|------|
| 杭州三日游 | 杭州真的太美了... | img1.jpg,img2.jpg | 旅游,杭州 | 杭州 | 百家号,头条号 |

---

## 四、图片库管理优化

**优先级：低**

### 需求
当前图片上传后只关联一次，需要独立的图片库，帖子创建时可从图库中选择复用。

### 改动点
- 图片列表页，支持多选插入到帖子
- 图片预览缩略图
- 图片标签/分类
- 与 `article_images` 表关联

---

## 五、发布结果回写与统计

**优先级：低**

### 需求
发布成功/失败后结果回写到数据库，支持查看历史发布记录和统计。

### 改动点
- 发布完成后更新 `article_posts.status` 和 `publish_result`
- 新增发布历史页面（按日期/平台/状态筛选）
- 统计面板：各平台发布成功率、发布数量趋势

---

## 已完成功能

- [x] 数据库扩展（article_posts + article_images 表）
- [x] 后端 8 平台 Cookie 校验
- [x] 后端图文发布 API（9 个端点）
- [x] 前端 8 平台账号管理
- [x] 前端图文发布页面（ArticlePublish.vue）
- [x] 前端帖子管理页面（ArticleManagement.vue）
- [x] 任务进度跟踪（轮询）
- [x] CLI 登录集成到前端（自动上传 Cookie）
- [x] 启动脚本（start.bat）
