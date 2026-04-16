---
name: weibo-upload
description: 微博登录、cookie 校验、微博图文发布（短文本+图片）。微博是微客平台，无标题字段、无标签，最多 9 张图片。
---

# 微博上传 Skill

优先把 `sau` 作为主接口。

## 功能概览
| 功能 | 命令入口 | 说明 |
| --- | --- | --- |
| 登录 | `sau weibo login --account <name> --headed` | 扫码登录，保存 cookie |
| cookie 校验 | `sau weibo check --account <name>` | 检查 cookie 是否有效 |
| 微博发布 | `sau weibo upload-article --account <name> --title "标题" --content "正文" --images img1.jpg img2.jpg --headed` | 发布微博 |

## 微博特殊性
- 微博是**微客**（短文本+图片），不是文章平台
- **没有标题字段** — title 会拼接到 content 前面
- **没有标签** — tags 参数被忽略
- **最多 9 张图片**
- **最多约 2000 字**
- 使用移动版 m.weibo.cn 发帖，DOM 简单稳定
- CDP 连接需要 cookie 注入，涵盖 .weibo.cn、.weibo.com、.sina.com.cn 域名

## 前提条件
- Chrome 必须以 `--remote-debugging-port=9222` 启动
- 已通过 `sau weibo login` 登录并保存 cookie

## 参考文档
- CLI 契约：`references/cli-contract.md`
- 运行前提：`references/runtime-requirements.md`
- 故障排查：`references/troubleshooting.md`
