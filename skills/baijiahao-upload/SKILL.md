---
name: baijiahao-upload
description: 当 agent 需要通过已安装的 `sau` CLI 完成百家号登录、cookie 校验、图文文章发布时使用这个 skill。该 skill 适用于已经安装 `social-auto-upload` 且可调用 `sau` 命令的环境。优先使用这个 skill 进行稳定的命令式百家号工作流，而不是一开始就阅读 uploader 源码。
---

# 百家号上传 Skill

优先把 `sau` 作为主接口。

不要假设当前环境一定能读取仓库源码。
不要一开始就去读 `uploader/`。
只有在命令不可用或 CLI 执行失败时，才回退到故障排查说明。

## 功能概览

| 功能 | 命令入口 | 说明 |
| --- | --- | --- |
| 百家号登录 | `sau baijiahao login --account <name>` | 生成或刷新指定账号的 cookie |
| cookie 校验 | `sau baijiahao check --account <name>` | 检查指定账号 cookie 是否有效 |
| 图文发布 | `sau baijiahao upload-article ...` | 发布百家号图文文章 |

元数据约定：

- 文章使用 `title + content + images`

## 默认工作流

1. 先确认 `references/runtime-requirements.md` 里的运行前提。
2. 再确认 `references/cli-contract.md` 里的命令契约。
3. 执行匹配的 `sau baijiahao ...` 命令。
4. 如果命令失败，再看 `references/troubleshooting.md`。

## 支持动作

- 使用 `sau baijiahao login --account <name>` 登录百家号
- 使用 `sau baijiahao check --account <name>` 校验 cookie 是否有效
- 使用 `sau baijiahao upload-article ...` 发布百家号图文文章

## 命令选择建议

- 当用户需要新的 cookie，或现有 cookie 已失效时，使用 `login`
- 当用户只需要确认 cookie 状态时，使用 `check`
- 当用户要发布图文文章时，使用 `upload-article`

## 执行前检查

- 先确认当前 shell 里是否可以调用 `sau`
- 如果 `sau` 不可用，按 `references/runtime-requirements.md` 里的回退方式处理
- 当用户明确指定无头或有头模式时，显式传 `--headless` 或 `--headed`
- 只有用户明确要求定时发布时，才使用 `--schedule`
- 百家号登录需要扫码，建议使用 `--headed` 模式

## 模板文件

当你需要稳定的命令模板时，使用 `scripts/examples/` 下的文件：

- `baijiahao_commands.ps1`
- `baijiahao_commands.sh`
- `baijiahao_cli_template.py`

## 已验证的发布流程

完整发布流程（多次实测通过）：

1. **Cookie 校验** → 2. **打开浏览器** → 3. **导航到编辑器**（`is_from_cms=1`）→ 4. **关闭新手引导**（仅首次，非阻塞）→ 5. **填写标题** → 6. **填写正文**（`execCommand('insertHTML')`）→ 7. **上传图片** → 8. **选择封面**（单图模式，点击容器 → 确定）→ 9. **发布**（JS MouseEvent dispatch）→ 10. **验证**（URL 跳转 + "提交成功"关键词）

关键经验：
- 正文必须用 `execCommand('insertHTML')`，不能用 `innerHTML`
- 封面不要点"选正文图"（会禁用 30 秒），直接点击封面容器 `div._73a3a52aab7e3a36-content`
- 发布按钮 `.click()` 无效，必须用 JS `dispatchEvent(new MouseEvent(...))`
- 推荐使用 `--headed` 模式便于观察

## 参考文档

- 运行前提：`references/runtime-requirements.md`
- CLI 契约：`references/cli-contract.md`
- 故障排查：`references/troubleshooting.md`
