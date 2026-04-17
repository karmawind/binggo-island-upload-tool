"""
数据库迁移 v4 — 账号分组 + 帖子账号绑定
1. user_info 新增 group_name 字段（运营者分组）
2. article_posts 新增 selected_accounts 字段（每篇帖子绑定的账号选择）
"""

import sqlite3
import os

db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# user_info 加 group_name
try:
    cursor.execute("ALTER TABLE user_info ADD COLUMN group_name TEXT DEFAULT ''")
    print("Added: user_info.group_name")
except sqlite3.OperationalError as e:
    print(f"user_info.group_name: {e} (可能已存在)")

# article_posts 加 selected_accounts（JSON 格式 {"5": [1,2], "7": [3]}）
try:
    cursor.execute("ALTER TABLE article_posts ADD COLUMN selected_accounts TEXT DEFAULT ''")
    print("Added: article_posts.selected_accounts")
except sqlite3.OperationalError as e:
    print(f"article_posts.selected_accounts: {e} (可能已存在)")

conn.commit()

# 创建运营者表（独立管理）
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    print("Created: operators table")
except sqlite3.OperationalError as e:
    print(f"operators: {e} (可能已存在)")

# 把已有 group_name 迁移进 operators 表
try:
    cursor.execute("""
        INSERT OR IGNORE INTO operators (name)
        SELECT DISTINCT group_name FROM user_info WHERE group_name != ''
    """)
    print("Migrated existing groups to operators table")
except Exception as e:
    print(f"Migration: {e}")

conn.commit()
conn.close()
print("v4 migration done")
