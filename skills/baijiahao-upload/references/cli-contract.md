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
  - `--content`：文章正文内容
  - `--images`：图片文件路径（支持多张）
  - `--tags`：逗号分隔的标签
  - `--schedule`：定时发布时间
  - `--debug`：启用调试模式
  - `--headless`：无头模式（默认）
  - `--headed`：显示浏览器界面

## 发布策略

- 如果不传 `--schedule`，CLI 使用立即发布
- 如果传了 `--schedule`，CLI 自动切换为定时发布
- 时间格式为:

```text
YYYY-MM-DD HH:MM
```

## 额外说明

- 百家号图文文章需要选择封面图，如果上传了图片，会自动从正文图片中选择封面
- 发布成功后会跳转到 `/builder/rc/clue` 页面
- 如果遇到百度安全验证，需要使用 `--headed` 模式手动处理
- 百家号使用 UEditor 编辑器，正文在 iframe 中编辑
