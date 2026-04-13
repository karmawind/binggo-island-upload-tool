# CLI Contract — sohu

## Commands

| Command | Required Args | Optional Args |
|---------|--------------|---------------|
| `sau sohu login` | `--account` | `--headed`, `--debug` |
| `sau sohu check` | `--account` | — |
| `sau sohu upload-article` | `--account`, `--title` | `--content`, `--images`, `--tags`, `--headed`, `--debug` |

## Exit Codes

- 0: Success
- 1: Failure (cookie expired, publish failed)
