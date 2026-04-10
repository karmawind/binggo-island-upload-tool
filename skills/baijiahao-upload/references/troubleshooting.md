# 故障排查

## 找不到 `sau` 命令

可以尝试以下方式：

```powershell
.\.venv\Scripts\Activate.ps1
sau baijiahao --help
```

```powershell
.\.venv\Scripts\sau.exe baijiahao --help
```

```bash
uv run sau baijiahao --help
```

如果当前环境还没有安装项目：

```bash
uv pip install -e .
```

## cookie 无效或已过期

先检查 cookie 状态：

```bash
sau baijiahao check --account <account>
```

如果无效，就重新登录：

```bash
sau baijiahao login --account <account> --headed
```

## 刚登录后导航编辑器失败（被重定向到首页）

**现象：** 登录成功后，导航到编辑器 URL 被重定向到 `stoken.html` → `builder/rc/home`，而非编辑器页面。

**原因：** 刚保存 cookie 后 session 可能还未完全生效。

**修复：** 代码已内置重试逻辑（最多 3 次，每次等 3 秒）。如果仍然失败，手动等几秒后重新执行发布命令。

**编辑器 URL 必须带 `is_from_cms=1` 参数：**

```
https://baijiahao.baidu.com/builder/rc/edit?type=news&is_from_cms=1
```

## 正文内容发布后不被识别（UEditor 状态问题）

**现象：** 正文看起来已填写，但点击发布后页面无跳转，或者发布按钮无响应。

**原因：** 使用 `innerHTML` 直接写入内容时，UEditor 的内部状态不会更新，编辑器仍认为内容为空。

**修复：** 必须使用 `document.execCommand('insertHTML', false, html)` 插入内容。代码已修复，无需手动干预。

**调试建议：** 使用 `--headed --debug` 模式观察编辑器中内容是否正确显示。

## 图片上传失败

百家号使用 UEditor 编辑器，图片上传有以下注意事项：

- **必须先 focus 编辑器 iframe body，再点击图片上传按钮**，否则文件上传对话框不会触发
- 流程：focus iframe → 点击工具栏图片按钮 → 等待上传弹窗 → 逐张 `set_input_files` → 点击确认
- 如果上传失败，尝试使用 `--headed --debug` 模式观察页面状态
- 检查图片文件是否存在且格式正确（支持 JPG、PNG）

## 封面选择失败

### "选正文图"按钮被禁用 30 秒

**现象：** 点击"选正文图"后按钮变为禁用状态，等待 30 秒。

**修复：** 不要点击"选正文图"按钮。正确流程是：
1. 选择"单图"封面模式
2. 点击封面容器 `div._73a3a52aab7e3a36-content`，弹窗会自动加载正文图片
3. 直接点击"确定"按钮

### 封面选择弹窗未出现

- 确认已上传图片到正文
- 使用 `--headed` 模式观察封面区域状态
- 检查是否有弹窗遮挡封面区域（按 Escape 清除）

## 发布按钮点击无响应

**现象：** 点击发布按钮后页面无任何反应。

**原因：** `[data-testid="publish-btn"]` 是包装层元素，`.click()` 和 Playwright 的 `force_click()` 均无法触发实际发布逻辑。

**修复：** 代码已改为使用 JS `dispatchEvent` 方式：

```javascript
const btn = document.querySelector('[data-testid="publish-btn"]');
const innerBtn = btn.querySelector('button') || btn.firstElementChild;
['mousedown', 'mouseup', 'click'].forEach(evt => {
    innerBtn.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true }));
});
```

## 新手引导弹窗阻塞

**现象：** 首次发帖时出现新手引导弹窗遮挡编辑器。

**注意：** 新手引导只在首次发帖时出现，再次发帖不会出现。代码已用 `try/except` 包裹引导关闭逻辑，不会阻塞后续流程。

如果确实遇到引导弹窗，代码会自动检测并逐步点击"下一步"/"完成"按钮（最多 10 次）。

## 发布未成功（未跳转）

- 百家号发布成功后会跳转到 `/builder/rc/clue` 页面
- 同时页面会显示"提交成功"关键词
- 如果页面没有跳转，检查是否有弹窗遮挡发布按钮（按 Escape 清除）
- 使用 `--headed --debug` 模式可以手动观察页面状态

## 百度安全验证

如果出现百度安全验证（验证码）：

- 无头模式下无法自动处理
- 使用 `--headed` 模式手动完成验证
- 完成验证后 cookie 会自动更新

## 定时发布

时间格式使用：

```text
YYYY-MM-DD HH:MM
```

如果不传 `--schedule`，默认立即发布。

## `'coroutine' object has no attribute 'locator'`

**原因：** `_get_content_frame()` 是 async 方法，调用时遗漏了 `await`。

**修复：** 代码已修复，确保所有 async 调用都带有 `await`。
