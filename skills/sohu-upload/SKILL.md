# 搜狐号图文发布 Skill

## 命令速查

```bash
# 登录
sau sohu login --account <账号名> --headed

# 校验 cookie
sau sohu check --account <账号名>

# 发布图文
sau sohu upload-article --account <账号名> --title "标题" --content "正文" --images img1.jpg img2.jpg --headed
```

## 功能

| 功能 | 命令 | 说明 |
|------|------|------|
| 登录 | `sau sohu login` | 打开浏览器，用户扫码/账号密码登录 |
| 校验 | `sau sohu check` | headless 验证 cookie 是否有效 |
| 发布 | `sau sohu upload-article` | 发布图文文章（标题+正文+图片） |

## 注意事项

- 标题限制 30 字
- 正文使用 contenteditable 编辑器
- 推荐使用 `--headed` 模式
- 不支持定时发布
