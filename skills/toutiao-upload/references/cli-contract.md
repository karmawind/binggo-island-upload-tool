# 头条号 CLI 契约

## 命令列表

### 登录

```bash
sau toutiao login --account <account> [--headed] [--debug]
```

- 必填: `--account`
- 可选: `--headed`（推荐），`--headless`，`--debug`
- 登录时打开浏览器，用户扫码完成

### 校验 cookie

```bash
sau toutiao check --account <account>
```

- 输出: `valid` 或 `invalid`

### 发布图文文章

```bash
sau toutiao upload-article \
  --account <account> \
  --title "<title>" \
  [--content "<content>"] \
  [--images <image-1> [image-2 ...]] \
  [--tags tag1,tag2] \
  [--headed] [--debug]
```

- 必填: `--account`, `--title`
- 可选: `--content`, `--images`, `--tags`, `--headed`, `--debug`
- 图片不超过 20MB

## 发布策略

- 文章提交后进入审核队列，不支持定时发布

## 已验证的发布流程

```
Cookie 校验 → 启动浏览器 → 导航编辑器 → 关闭 AI 遮罩 → 清空编辑器
→ 填写标题 → 填写正文 → 上传图片 → 点击"确定"插入正文
→ 设置封面+不投放广告 → 预览并发布 → 确认发布 → 验证跳转
```

## 已知注意事项

- 推荐使用 `--headed` 模式
- 编辑器为 ProseMirror，一次性填入内容
- 上传图片后需点击"确定"插入正文
- 发布需两步确认：预览并发布 → 确认发布
- AI 助手遮罩需先移除才能操作
- 需手动设置"不投放广告"
