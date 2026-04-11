# CLI 命令

```bash
sau ctrip login --account <name> [--headed]
sau ctrip check --account <name>
sau ctrip upload-article --account <name> --title <title> --content <text> --images <img1> [img2...] --location <地点> [--tags tag1,tag2] [--headed]
```

## 参数说明

- `--account`: 用户自定义账号名
- `--title`: 笔记标题（建议 5-20 字）
- `--content`: 描述正文（≥60 字有机会评为优质，最多 3000 字）
- `--images`: 图片路径（最多 20 张）
- `--location`: 地点名称（必填，如"杭州"、"北京"）
- `--tags`: 逗号分隔的标签
- `--headed`: 有头模式（推荐）
- `--headless`: 无头模式
- `--debug`: 调试模式
