# 什么值得买 CLI 契约

## 命令列表

### 登录

```bash
sau smzdm login --account <account> [--headed] [--debug]
```

- 必填: `--account`
- 可选: `--headed`（推荐），`--headless`，`--debug`
- 登录时打开浏览器，用户扫码完成

### 校验 cookie

```bash
sau smzdm check --account <account>
```

- 输出: `valid` 或 `invalid`

### 发布图文文章

```bash
sau smzdm upload-article \
  --account <account> \
  --title "<title>" \
  [--content "<content>"] \
  [--images <image-1> [image-2 ...]] \
  [--tags tag1,tag2] \
  [--headed] [--debug]
```

- 必填: `--account`, `--title`
- 可选: `--content`, `--images`, `--tags`, `--headed`, `--debug`
- `--images` 中第一张图会作为封面图，所有图片都会上传到正文
- 图片建议 500KB~8MB

## 发布策略

- 文章提交后进入审核队列，不支持定时发布

## 已验证的发布流程

```
Cookie 校验 → 启动浏览器 → 导航编辑器 → 关闭升级弹窗 → 清空编辑器
→ 填写标题 → 填写正文
→ 上传封面图（工具栏图片按钮 → file input → 点击图片设为封面 → 确定此图 → 确认）
→ 上传正文图片（工具栏图片按钮 → file input → 插入正文）
→ 设置创作声明 → 发布 → 验证"提交成功"
```

## 已知注意事项

- 推荐使用 `--headed` 模式
- 编辑器为 ProseMirror，一次性填入内容
- 上传图片后需点击"插入正文"
- 封面图通过工具栏图片按钮上传（不是"添加长图"按钮）
- JS 点击统一用 `dispatchEvent`，不要用 `.click()`
- 页面有遮罩层，部分操作需 JS 强制点击
