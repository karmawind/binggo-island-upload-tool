# 百家号 CLI 契约

这个 skill 默认假设当前环境已经安装并可调用 `sau` 命令。

## 命令列表

### 登录

```bash
sau baijiahao login --account <account> [--headed] [--debug]
```

- 必填参数:
  - `--account`
- 可选参数:
  - `--headed`：显示浏览器界面（推荐，用于扫码登录）
  - `--headless`：无头模式（默认）
  - `--debug`：启用调试模式
- 作用:
  - 启动百家号登录流程，为指定账号生成或刷新 cookie 文件
  - 登录时会打开浏览器，用户需要扫码完成登录
  - 登录完成后自动保存 cookie
- 账号说明:
  - `--account` 传的是用户自定义的 `account_name`，不是固定只能叫某个名字
  - 一个 `account_name` 对应一个账号文件，可用于多账号隔离和并发任务
- 注意:
  - 刚登录后立即发布可能被重定向到首页，代码已内置重试逻辑
  - 如果多次重试仍失败，等几秒后重新执行发布命令即可

### 校验 cookie

```bash
sau baijiahao check --account <account>
```

- 必填参数:
  - `--account`
- 预期输出:
  - `valid`：cookie 可用
  - `invalid`：cookie 缺失或已失效

### 发布图文文章

```bash
sau baijiahao upload-article \
  --account <account> \
  --title "<title>" \
  [--content "<content>"] \
  [--images <image-1> [image-2 ...]] \
  [--tags tag1,tag2] \
  [--schedule "YYYY-MM-DD HH:MM"] \
  [--debug] \
  [--headless | --headed]
```

- 必填参数:
  - `--account`
  - `--title`
- 可选参数:
  - `--content`：文章正文内容（支持 HTML 标签，如 `<p>`, `<b>`, `<br>`）
  - `--images`：图片文件路径（支持多张，建议 1-9 张）
  - `--tags`：逗号分隔的标签
  - `--schedule`：定时发布时间
  - `--debug`：启用调试模式
  - `--headless`：无头模式（默认）
  - `--headed`：显示浏览器界面（推荐用于调试）

## 发布流程（已验证）

完整发布流程如下：

1. **Cookie 校验** — 自动检查 cookie 是否有效
2. **打开浏览器** — 启动 patchright Chromium
3. **导航到编辑器** — 打开 `builder/rc/edit?type=news&is_from_cms=1`
   - 如果被重定向到首页，自动重试（最多 3 次）
4. **关闭新手引导** — 仅首次发帖时出现，自动跳过（非阻塞）
5. **填写标题** — 输入文章标题
6. **填写正文** — 通过 UEditor iframe 的 `execCommand('insertHTML')` 写入
7. **上传图片** — 逐张通过 UEditor 工具栏上传
8. **选择封面** — 单图模式 → 点击封面容器 → 自动加载正文图片 → 确定
9. **发布** — JS MouseEvent dispatch 点击发布按钮
10. **验证** — 检测 URL 跳转到 `/builder/rc/clue` + 页面"提交成功"关键词

## 发布策略

- 如果不传 `--schedule`，CLI 使用立即发布
- 如果传了 `--schedule`，CLI 自动切换为定时发布
- 时间格式为:

```text
YYYY-MM-DD HH:MM
```

## 已知注意事项

- **推荐使用 `--headed` 模式**，百家号使用 UEditor 编辑器，有头模式便于观察和调试
- 正文内容使用 `execCommand('insertHTML')` 写入，不要用 `innerHTML`（UEditor 不会识别）
- 封面选择不要点"选正文图"按钮（会触发 30 秒禁用），直接点击封面容器
- 发布按钮需要 JS `dispatchEvent` 方式点击，普通 `.click()` 无效
- 发布成功后会跳转到 `/builder/rc/clue` 页面，并显示"提交成功"
- 如果遇到百度安全验证，需要使用 `--headed` 模式手动处理
- 百家号使用 UEditor 编辑器，正文在 iframe 中编辑
