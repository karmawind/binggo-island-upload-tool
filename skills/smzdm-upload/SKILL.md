---
name: smzdm-upload
description: 当 agent 需要通过已安装的 `sau` CLI 完成什么值得买登录、cookie 校验、图文文章发布时使用这个 skill。
---

# 什么值得买上传 Skill

优先把 `sau` 作为主接口。

## 功能概览

| 功能 | 命令入口 | 说明 |
| --- | --- | --- |
| 登录 | `sau smzdm login --account <name>` | 打开浏览器扫码登录，保存 cookie |
| cookie 校验 | `sau smzdm check --account <name>` | 检查 cookie 是否有效 |
| 图文发布 | `sau smzdm upload-article ...` | 发布图文文章（需审核） |

## 支持动作

- 使用 `sau smzdm login --account <name> --headed` 登录（推荐 headed 模式）
- 使用 `sau smzdm check --account <name>` 校验 cookie
- 使用 `sau smzdm upload-article ...` 发布图文文章

## 命令选择建议

- 新 cookie 或 cookie 失效时，使用 `login`
- 仅确认 cookie 状态时，使用 `check`
- 发布图文文章时，使用 `upload-article`

## 执行前检查

- 先确认当前 shell 里可以调用 `sau`
- 推荐使用 `--headed` 模式便于观察
- 图片建议 500KB~8MB

## 已验证的发布流程

1. **Cookie 校验** → 2. **启动浏览器** → 3. **导航编辑器** → 4. **关闭升级弹窗** → 5. **清空编辑器** → 6. **填写标题** → 7. **填写正文** → 8. **上传封面图**（工具栏图片按钮 → file input → 点击图片设为封面 → 确定此图 → 确认） → 9. **上传正文图片**（工具栏图片按钮 → file input → 插入正文） → 10. **设置创作声明** → 11. **发布** → 12. **验证成功**

关键经验：
- **每次发布前必须清空编辑器**：SPA 页面不刷新，残留的标题/正文/图片/遮罩面板会导致后续操作不可预测
- **标题限制 30 字**：什么值得买标题最多 30 字，超出会被截断
- 标题和正文一次性填入，不要逐字输入
- 编辑器是 ProseMirror，正文用 `execCommand('insertHTML')`
- **JS 点击统一用 `dispatchEvent`**：`.click()` 可能报 `btn.click is not a function`
- 上传图片后必须点击"插入正文"关闭面板
- 封面图、发布按钮等操作有遮罩层，需要 JS 强制点击
- 文章发布后需要人工审核

## 参考文档

- CLI 契约：`references/cli-contract.md`
- 运行前提：`references/runtime-requirements.md`
- 故障排查：`references/troubleshooting.md`
