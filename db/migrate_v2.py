"""
数据库迁移 v2 — 图文发布系统
新增 article_posts 和 article_images 表，不修改已有表。
可重复运行（CREATE TABLE IF NOT EXISTS）。
"""

import sqlite3
import os

db_file = os.path.join(os.path.dirname(__file__), 'database.db')
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# 帖子内容管理表
cursor.execute('''
CREATE TABLE IF NOT EXISTS article_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    image_paths TEXT DEFAULT '',          -- JSON 数组，图片文件路径
    tags TEXT DEFAULT '',                 -- JSON 数组，标签字符串
    location TEXT DEFAULT '',             -- 携程专用：地点
    status TEXT DEFAULT 'draft',          -- draft / publishing / published / failed
    platform INTEGER NOT NULL,            -- 5=百家号 6=什么值得买 7=头条号 8=携程
    account_ids TEXT DEFAULT '',          -- JSON 数组，user_info.id 值
    publish_result TEXT DEFAULT '',       -- JSON，每个账号的发布结果
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# 图文图片文件表
cursor.execute('''
CREATE TABLE IF NOT EXISTS article_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filesize REAL,
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT NOT NULL
)
''')

conn.commit()
print("v2 migration done: article_posts + article_images tables created")
conn.close()
