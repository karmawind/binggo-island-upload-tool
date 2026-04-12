"""
数据库迁移 v3 — 多平台分发 + 排期调度
新增 platforms（多平台目标）和 scheduled_at（定时发布时间）字段。
"""

import sqlite3
import os

db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# 添加多平台字段（JSON 数组，如 [5,7,8]）
try:
    cursor.execute("ALTER TABLE article_posts ADD COLUMN platforms TEXT DEFAULT ''")
    print("Added: platforms")
except sqlite3.OperationalError as e:
    print(f"platforms: {e} (可能已存在)")

# 添加定时发布时间字段
try:
    cursor.execute("ALTER TABLE article_posts ADD COLUMN scheduled_at DATETIME DEFAULT NULL")
    print("Added: scheduled_at")
except sqlite3.OperationalError as e:
    print(f"scheduled_at: {e} (可能已存在)")

conn.commit()
conn.close()
print("v3 migration done")
