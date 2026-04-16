# CLI Contract — weibo

## Commands
| Command | Required Args | Optional Args |
|---------|--------------|---------------|
| `sau weibo login` | `--account` | `--headed`, `--debug` |
| `sau weibo check` | `--account` | — |
| `sau weibo upload-article` | `--account` | `--title`, `--content`, `--images`, `--tags`, `--headed`, `--debug` |

## 微博特殊性
- `--title` 会被拼接到 `--content` 前面（微博无单独标题字段）
- `--tags` 被忽略（微博无标签功能）
- `--images` 最多 9 张，超出部分自动截断
- 正文最多 2000 字，超出部分自动截断

## Exit Codes
- 0: Success
- 1: Failure (cookie expired, publish failed)
