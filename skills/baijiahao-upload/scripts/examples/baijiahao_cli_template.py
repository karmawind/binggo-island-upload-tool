from __future__ import annotations

import shlex
import subprocess


def run_command(command: list[str]) -> None:
    print("Running:", " ".join(shlex.quote(part) for part in command))
    subprocess.run(command, check=True)


def main() -> None:
    account = "account_a"
    # account_name is user-defined. One account_name maps to one account file.
    # You can prepare multiple account names and run them in parallel.

    commands = [
        ["sau", "baijiahao", "login", "--account", account, "--headed"],
        ["sau", "baijiahao", "check", "--account", account],
        [
            "sau",
            "baijiahao",
            "upload-article",
            "--account",
            account,
            "--title",
            "百家号图文文章标题",
            "--content",
            "这里是文章正文内容，支持多段文字。",
            "--images",
            "images/1.png",
            "images/2.png",
            "--tags",
            "标签1,标签2",
            "--headed",
        ],
    ]

    for command in commands:
        run_command(command)


if __name__ == "__main__":
    main()
