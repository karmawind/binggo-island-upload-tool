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

## 图片上传失败

百家号使用 UEditor 编辑器，图片上传有以下注意事项：

- **必须先 focus 编辑器 iframe body，再点击图片上传按钮**，否则文件上传对话框不会触发
- 如果上传失败，尝试使用 `--headed --debug` 模式观察页面状态
- 检查图片文件是否存在且格式正确（支持 JPG、PNG）

## 封面选择失败

- 如果有上传图片，系统会自动尝试从正文图片中选择封面
- 封面选择使用单图模式
- 如果封面选择弹窗未正确关闭，可能导致发布按钮被遮挡

## 发布未成功

- 百家号发布成功后会跳转到 `/builder/rc/clue` 页面
- 如果页面没有跳转，检查是否有弹窗遮挡发布按钮
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
