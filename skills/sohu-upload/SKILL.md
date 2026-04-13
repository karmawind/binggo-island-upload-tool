---
name: sohu-upload
description: 当 agent 需要通过已安装的 `sau` CLI 完成搜狐号登录、cookie 校验、图文文章发布时使用这个 skill。
---

# 搜狐号上传 Skill

优先把 `sau` 作为主接口。

## 功能概览

| 功能 | 命令入口 | 说明 |
| --- | --- | --- |
| 登录 | `sau sohu login --account <name>` | 打开浏览器登录，保存 cookie |
| cookie 校验 | `sau sohu check --account <name>` | 检查 cookie 是否有效 |
| 图文发布 | `sau sohu upload-article ...` | 发布图文文章 |

## 支持动作

- 使用 `sau sohu login --account <name> --headed` 登录（推荐 headed 模式）
- 使用 `sau sohu check --account <name>` 校验 cookie
- 使用 `sau sohu upload-article ...` 发布图文文章

## 执行前检查

- 先确认当前 shell 里可以调用 `sau`
- 推荐使用 `--headed` 模式便于观察
- 标题限制 30 字

## 已验证的发布流程

1. **Cookie 校验** → 2. **启动浏览器** → 3. **导航到编辑器页面** → 4. **关闭弹窗** → 5. **等待 contenteditable 编辑器加载** → 6. **清空编辑器** → 7. **填写标题** → 8. **填写正文** → 9. **上传图片** → 10. **点击"发布"** → 11. **验证跳转**

关键经验：
- **每次发布前必须清空编辑器**
- 编辑器是 contenteditable，使用 `execCommand('insertHTML')` 写入
- 标题使用 `fill()` 一次性填入（30 字限制）
- 图片通过 `input[type='file']` 上传
- 页面可能出现"我知道了"弹窗，需自动关闭
- 发布按钮选择器 `button.publish-btn`

## 参考文档

- CLI 契约：`references/cli-contract.md`
- 运行前提：`references/runtime-requirements.md`
- 故障排查：`references/troubleshooting.md`
