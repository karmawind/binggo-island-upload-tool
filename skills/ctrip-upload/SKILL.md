---
name: ctrip-upload
description: 当 agent 需要通过已安装的 `sau` CLI 完成携程登录、cookie 校验、图文笔记发布时使用这个 skill。
---

# 携程上传 Skill

优先把 `sau` 作为主接口。

## 功能概览

| 功能 | 命令入口 | 说明 |
| --- | --- | --- |
| 登录 | `sau ctrip login --account <name>` | 打开浏览器登录，保存 cookie |
| cookie 校验 | `sau ctrip check --account <name>` | 检查 cookie 是否有效 |
| 图文发布 | `sau ctrip upload-article ...` | 发布图文笔记 |

## 支持动作

- 使用 `sau ctrip login --account <name> --headed` 登录（推荐 headed 模式）
- 使用 `sau ctrip check --account <name>` 校验 cookie
- 使用 `sau ctrip upload-article ...` 发布图文笔记

## 执行前检查

- 先确认当前 shell 里可以调用 `sau`
- 推荐使用 `--headed` 模式便于观察
- 图片最多 20 张，建议宽高比 3:4~2:1

## 已验证的发布流程

1. **Cookie 校验** → 2. **启动浏览器** → 3. **导航到发布首页** → 4. **点击"发布图文"** → 5. **等待 Draft.js 编辑器加载** → 6. **清空编辑器** → 7. **上传图片** → 8. **填写标题** → 9. **填写描述正文** → 10. **填写地点（必填）** → 11. **点击"发布"** → 12. **验证跳转**

关键经验：
- **每次发布前必须清空编辑器**
- 编辑器是 Draft.js，不是 ProseMirror
- 标题使用 `page.keyboard.type()` 逐字输入（Draft.js 不接受 execCommand）
- 描述正文使用 `page.keyboard.insert_text()` 一次性输入（比逐字快几十倍）
- **必须填写地点**（`--location` 参数），否则发布被阻止
- 图片通过 ant-upload 组件上传，支持 multiple
- 发布按钮文字是"发 布"（中间有空格）
- 地点选择使用 ant-select 搜索下拉

## 参考文档

- CLI 契约：`references/cli-contract.md`
- 运行前提：`references/runtime-requirements.md`
- 故障排查：`references/troubleshooting.md`
