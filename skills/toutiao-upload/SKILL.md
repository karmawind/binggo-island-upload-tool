---
name: toutiao-upload
description: 当 agent 需要通过已安装的 `sau` CLI 完成头条号登录、cookie 校验、图文文章发布时使用这个 skill。
---

# 头条号上传 Skill

优先把 `sau` 作为主接口。

## 功能概览

| 功能 | 命令入口 | 说明 |
| --- | --- | --- |
| 登录 | `sau toutiao login --account <name>` | 打开浏览器扫码登录，保存 cookie |
| cookie 校验 | `sau toutiao check --account <name>` | 检查 cookie 是否有效 |
| 图文发布 | `sau toutiao upload-article ...` | 发布图文文章（需审核） |

## 支持动作

- 使用 `sau toutiao login --account <name> --headed` 登录（推荐 headed 模式）
- 使用 `sau toutiao check --account <name>` 校验 cookie
- 使用 `sau toutiao upload-article ...` 发布图文文章

## 执行前检查

- 先确认当前 shell 里可以调用 `sau`
- 推荐使用 `--headed` 模式便于观察
- 图片建议不超过 20MB

## 已验证的发布流程

1. **Cookie 校验** → 2. **启动浏览器** → 3. **导航编辑器** → 4. **关闭 AI 助手遮罩** → 5. **清空编辑器** → 6. **填写标题** → 7. **填写正文** → 8. **上传图片** → 9. **点击"确定"插入正文** → 10. **设置封面+不投放广告** → 11. **预览并发布** → 12. **确认发布** → 13. **验证跳转**

关键经验：
- **每次发布前必须清空编辑器**
- AI 助手遮罩会拦截所有操作，必须先移除
- 编辑器是 ProseMirror，正文用 `execCommand('insertHTML')`
- 图片上传后必须点击"确定"才能插入正文
- 发布需两步：先"预览并发布"，按钮变为"确认发布"后再点击
- 需手动设置"不投放广告"
- JS 点击优先用 `dispatchEvent`

## 参考文档

- CLI 契约：`references/cli-contract.md`
- 运行前提：`references/runtime-requirements.md`
- 故障排查：`references/troubleshooting.md`
