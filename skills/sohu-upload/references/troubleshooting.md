# 故障排查

## Cookie 失效

- 症状：被重定向到登录页
- 解决：重新执行 `sau sohu login --account <name> --headed`

## 弹窗阻止操作

- 症状：页面出现"我知道了"弹窗，遮挡编辑器
- 解决：代码已自动关闭弹窗（"我知道了"、"知道了"、"关闭"关键词）

## 标题未填入

- 症状：标题区域为空
- 原因：SPA 路由跳转未正确渲染编辑器 DOM
- 解决：改为直接 `goto(editor_url)` 导航到编辑器，不使用 SPA 路由跳转

## 正文未填入

- 症状：编辑器区域为空
- 原因：编辑器是 Quill.js（`.ql-editor`），不是简单 contenteditable
- 解决：使用 `document.querySelector('.ql-editor')` 定位 + `execCommand('insertHTML')` 写入

## 发布按钮点击无效

- 症状：点击"发布"无反应
- 原因：发布按钮是 `<li>` 元素（`li.positive-button.publish-report-btn`），不是 `<button>`
- 解决：使用 `li.positive-button.publish-report-btn` 选择器，`.click()` 失败时用 JS `dispatchEvent` 兜底

## 发布后未实际提交

- 症状：点击发布后仍在编辑页
- 原因：搜狐号有两步确认弹窗（"确认发布文章么？" → "确定"）
- 解决：发布后检测确认弹窗，自动点击"确定"按钮；`.click()` 无效时用 `dispatchEvent` 兜底

## 图片上传失败

- 症状：图片未出现在正文中
- 原因：需通过工具栏 image 按钮打开上传弹窗，而非直接找 hidden file input
- 解决：点击工具栏 `button.ql-image` → 等待上传弹窗 → `set_input_files` → 点"确定"

## 登录检测误判

- 症状：登录页被误认为已登录
- 解决：使用"发布内容"关键词检测登录状态
