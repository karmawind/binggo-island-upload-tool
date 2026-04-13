import asyncio
import json
import os
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid
from pathlib import Path
from queue import Queue
from flask_cors import CORS
from myUtils.auth import check_cookie
from flask import Flask, request, jsonify, Response, render_template, send_from_directory
from conf import BASE_DIR
from myUtils.login import get_tencent_cookie, douyin_cookie_gen, get_ks_cookie, xiaohongshu_cookie_gen
from myUtils.postVideo import post_video_tencent, post_video_DouYin, post_video_ks, post_video_xhs
from myUtils.postArticle import (
    post_article_baijiahao, post_article_smzdm,
    post_article_toutiao, post_article_ctrip,
    dispatch_multi_platform, PLATFORM_DISPATCH
)

active_queues = {}
app = Flask(__name__)

#允许所有来源跨域访问
CORS(app)

# 限制上传文件大小为160MB
app.config['MAX_CONTENT_LENGTH'] = 160 * 1024 * 1024

# 获取当前目录（假设 index.html 和 assets 在这里）
current_dir = os.path.dirname(os.path.abspath(__file__))

# 处理所有静态资源请求（未来打包用）
@app.route('/assets/<filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(current_dir, 'assets'), filename)

# 处理 favicon.ico 静态资源（未来打包用）
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

@app.route('/vite.svg')
def vite_svg():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

# （未来打包用）
@app.route('/')
def index():  # put application's code here
    return send_from_directory(current_dir, 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400
    try:
        # 保存文件到指定位置
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        filepath = Path(BASE_DIR / "videoFile" / f"{uuid_v1}_{file.filename}")
        file.save(filepath)
        return jsonify({"code":200,"msg": "File uploaded successfully", "data": f"{uuid_v1}_{file.filename}"}), 200
    except Exception as e:
        return jsonify({"code":500,"msg": str(e),"data":None}), 500

@app.route('/getFile', methods=['GET'])
def get_file():
    # 获取 filename 参数
    filename = request.args.get('filename')

    if not filename:
        return jsonify({"code": 400, "msg": "filename is required", "data": None}), 400

    # 防止路径穿越攻击
    if '..' in filename or filename.startswith('/'):
        return jsonify({"code": 400, "msg": "Invalid filename", "data": None}), 400

    # 拼接完整路径
    file_path = str(Path(BASE_DIR / "videoFile"))

    # 返回文件
    return send_from_directory(file_path,filename)


@app.route('/uploadSave', methods=['POST'])
def upload_save():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400

    # 获取表单中的自定义文件名（可选）
    custom_filename = request.form.get('filename', None)
    if custom_filename:
        filename = custom_filename + "." + file.filename.split('.')[-1]
    else:
        filename = file.filename

    try:
        # 生成 UUID v1
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 构造文件名和路径
        final_filename = f"{uuid_v1}_{filename}"
        filepath = Path(BASE_DIR / "videoFile" / f"{uuid_v1}_{filename}")

        # 保存文件
        file.save(filepath)

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO file_records (filename, filesize, file_path)
            VALUES (?, ?, ?)
                                ''', (filename, round(float(os.path.getsize(filepath)) / (1024 * 1024),2), final_filename))
            conn.commit()
            print("✅ 上传文件已记录")

        return jsonify({
            "code": 200,
            "msg": "File uploaded and saved successfully",
            "data": {
                "filename": filename,
                "filepath": final_filename
            }
        }), 200

    except Exception as e:
        print(f"Upload failed: {e}")
        return jsonify({
            "code": 500,
            "msg": f"upload failed: {e}",
            "data": None
        }), 500

@app.route('/getFiles', methods=['GET'])
def get_all_files():
    try:
        # 使用 with 自动管理数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row  # 允许通过列名访问结果
            cursor = conn.cursor()

            # 查询所有记录
            cursor.execute("SELECT * FROM file_records")
            rows = cursor.fetchall()

            # 将结果转为字典列表，并提取UUID
            data = []
            for row in rows:
                row_dict = dict(row)
                # 从 file_path 中提取 UUID (文件名的第一部分，下划线前)
                if row_dict.get('file_path'):
                    file_path_parts = row_dict['file_path'].split('_', 1)  # 只分割第一个下划线
                    if len(file_path_parts) > 0:
                        row_dict['uuid'] = file_path_parts[0]  # UUID 部分
                    else:
                        row_dict['uuid'] = ''
                else:
                    row_dict['uuid'] = ''
                data.append(row_dict)

            return jsonify({
                "code": 200,
                "msg": "success",
                "data": data
            }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("get file failed!"),
            "data": None
        }), 500


@app.route("/getAccounts", methods=['GET'])
def getAccounts():
    """快速获取所有账号信息，不进行cookie验证"""
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM user_info''')
            rows = cursor.fetchall()
            rows_list = [list(row) for row in rows]

            print("\n📋 当前数据表内容（快速获取）：")
            for row in rows:
                print(row)

            return jsonify(
                {
                    "code": 200,
                    "msg": None,
                    "data": rows_list
                }), 200
    except Exception as e:
        print(f"获取账号列表时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取账号列表失败: {str(e)}",
            "data": None
        }), 500


@app.route("/getValidAccounts",methods=['GET'])
async def getValidAccounts():
    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM user_info''')
        rows = cursor.fetchall()
        rows_list = [list(row) for row in rows]
        print("\n📋 当前数据表内容：")
        for row in rows:
            print(row)
        for row in rows_list:
            flag = await check_cookie(row[1],row[2])
            if not flag:
                row[4] = 0
                cursor.execute('''
                UPDATE user_info 
                SET status = ? 
                WHERE id = ?
                ''', (0,row[0]))
                conn.commit()
                print("✅ 用户状态已更新")
        for row in rows:
            print(row)
        return jsonify(
                        {
                            "code": 200,
                            "msg": None,
                            "data": rows_list
                        }),200

@app.route('/deleteFile', methods=['GET'])
def delete_file():
    file_id = request.args.get('id')

    if not file_id or not file_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing file ID",
            "data": None
        }), 400

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM file_records WHERE id = ?", (file_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }), 404

            record = dict(record)

            # 获取文件路径并删除实际文件
            file_path = Path(BASE_DIR / "videoFile" / record['file_path'])
            if file_path.exists():
                try:
                    file_path.unlink()  # 删除文件
                    print(f"✅ 实际文件已删除: {file_path}")
                except Exception as e:
                    print(f"⚠️ 删除实际文件失败: {e}")
                    # 即使删除文件失败，也要继续删除数据库记录，避免数据不一致
            else:
                print(f"⚠️ 实际文件不存在: {file_path}")

            # 删除数据库记录
            cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "File deleted successfully",
            "data": {
                "id": record['id'],
                "filename": record['filename']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

@app.route('/deleteAccount', methods=['GET'])
def delete_account():
    account_id = request.args.get('id')

    if not account_id or not account_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing account ID",
            "data": None
        }), 400

    account_id = int(account_id)

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "account not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除关联的cookie文件
            if record.get('filePath'):
                cookie_file_path = Path(BASE_DIR / "cookiesFile" / record['filePath'])
                if cookie_file_path.exists():
                    try:
                        cookie_file_path.unlink()
                        print(f"✅ Cookie文件已删除: {cookie_file_path}")
                    except Exception as e:
                        print(f"⚠️ 删除Cookie文件失败: {e}")

            # 删除数据库记录
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account deleted successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"delete failed: {str(e)}",
            "data": None
        }), 500


# SSE 登录接口
@app.route('/login')
def login():
    # 1 小红书 2 视频号 3 抖音 4 快手
    type = request.args.get('type')
    # 账号名
    id = request.args.get('id')

    # 模拟一个用于异步通信的队列
    status_queue = Queue()
    active_queues[id] = status_queue

    def on_close():
        print(f"清理队列: {id}")
        del active_queues[id]
    # 启动异步任务线程
    thread = threading.Thread(target=run_async_function, args=(type,id,status_queue), daemon=True)
    thread.start()
    response = Response(sse_stream(status_queue,), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # 关键：禁用 Nginx 缓冲
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/postVideo', methods=['POST'])
def postVideo():
    # 获取JSON数据
    data = request.get_json()

    if not data:
        return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400

    # 从JSON数据中提取fileList和accountList
    file_list = data.get('fileList', [])
    account_list = data.get('accountList', [])
    type = data.get('type')
    title = data.get('title')
    tags = data.get('tags')
    category = data.get('category')
    enableTimer = data.get('enableTimer')
    if category == 0:
        category = None
    productLink = data.get('productLink', '')
    productTitle = data.get('productTitle', '')
    thumbnail_path = data.get('thumbnail', '')
    is_draft = data.get('isDraft', False)  # 新增参数：是否保存为草稿

    videos_per_day = data.get('videosPerDay')
    daily_times = data.get('dailyTimes')
    start_days = data.get('startDays')

    # 参数校验
    if not file_list:
        return jsonify({"code": 400, "msg": "文件列表不能为空", "data": None}), 400
    if not account_list:
        return jsonify({"code": 400, "msg": "账号列表不能为空", "data": None}), 400
    if not type:
        return jsonify({"code": 400, "msg": "平台类型不能为空", "data": None}), 400
    if not title:
        return jsonify({"code": 400, "msg": "标题不能为空", "data": None}), 400

    # 打印获取到的数据（仅作为示例）
    print("File List:", file_list)
    print("Account List:", account_list)

    try:
        match type:
            case 1:
                post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days)
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days, is_draft)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days, thumbnail_path, productLink, productTitle)
            case 4:
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
            case _:
                return jsonify({"code": 400, "msg": f"不支持的平台类型: {type}", "data": None}), 400

        # 返回响应给客户端
        return jsonify(
            {
                "code": 200,
                "msg": "发布任务已提交",
                "data": None
            }), 200
    except Exception as e:
        print(f"发布视频时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"发布失败: {str(e)}",
            "data": None
        }), 500


@app.route('/updateUserinfo', methods=['POST'])
def updateUserinfo():
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取 type 和 userName
    user_id = data.get('id')
    type = data.get('type')
    userName = data.get('userName')
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 更新数据库记录
            cursor.execute('''
                           UPDATE user_info
                           SET type     = ?,
                               userName = ?
                           WHERE id = ?;
                           ''', (type, userName, user_id))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account update successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("update failed!"),
            "data": None
        }), 500

@app.route('/postVideoBatch', methods=['POST'])
def postVideoBatch():
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({"code": 400, "msg": "Expected a JSON array", "data": None}), 400
    for data in data_list:
        # 从JSON数据中提取fileList和accountList
        file_list = data.get('fileList', [])
        account_list = data.get('accountList', [])
        type = data.get('type')
        title = data.get('title')
        tags = data.get('tags')
        category = data.get('category')
        enableTimer = data.get('enableTimer')
        if category == 0:
            category = None
        productLink = data.get('productLink', '')
        productTitle = data.get('productTitle', '')
        is_draft = data.get('isDraft', False)

        videos_per_day = data.get('videosPerDay')
        daily_times = data.get('dailyTimes')
        start_days = data.get('startDays')
        # 打印获取到的数据（仅作为示例）
        print("File List:", file_list)
        print("Account List:", account_list)
        match type:
            case 1:
                post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                               start_days)
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days, is_draft)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days, productLink, productTitle)
            case 4:
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200

# ==================== 图文发布相关 API ====================

@app.route('/uploadImage', methods=['POST'])
def upload_image():
    """上传图文图片到 imageFile/ 目录，记录到 article_images 表。"""
    if 'file' not in request.files:
        return jsonify({"code": 400, "msg": "No file part", "data": None}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"code": 400, "msg": "No selected file", "data": None}), 400

    try:
        uuid_v1 = uuid.uuid1()
        final_filename = f"{uuid_v1}_{file.filename}"
        filepath = Path(BASE_DIR / "imageFile" / final_filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        file.save(filepath)

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO article_images (filename, filesize, file_path) VALUES (?, ?, ?)',
                (file.filename, round(float(os.path.getsize(filepath)) / (1024 * 1024), 2), final_filename)
            )
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "Image uploaded",
            "data": {"filename": file.filename, "filepath": final_filename}
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500


@app.route('/copyMaterialToImage', methods=['POST'])
def copy_material_to_image():
    """将素材库中的图片复制到图文图片目录，供图文发布使用。"""
    data = request.get_json() or {}
    file_path = data.get('filePath')  # 素材的 file_path，如 UUID_name.jpg

    if not file_path:
        return jsonify({"code": 400, "msg": "filePath is required", "data": None}), 400

    # 安全检查：防止路径穿越
    if '..' in file_path or file_path.startswith('/'):
        return jsonify({"code": 400, "msg": "Invalid filePath", "data": None}), 400

    # 只允许图片文件
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    ext = Path(file_path).suffix.lower()
    if ext not in image_extensions:
        return jsonify({"code": 400, "msg": "只支持图片文件", "data": None}), 400

    src = Path(BASE_DIR / "videoFile" / file_path)
    if not src.exists():
        return jsonify({"code": 404, "msg": "素材文件不存在", "data": None}), 404

    try:
        # 目标路径使用新的 UUID，避免文件名冲突
        new_uuid = uuid.uuid1()
        original_name = file_path.split('_', 1)[1] if '_' in file_path else file_path
        new_filename = f"{new_uuid}_{original_name}"

        dst = Path(BASE_DIR / "imageFile" / new_filename)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))

        # 记录到 article_images 表
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO article_images (filename, filesize, file_path) VALUES (?, ?, ?)',
                (original_name, round(float(os.path.getsize(dst)) / (1024 * 1024), 2), new_filename)
            )
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "复制成功",
            "data": {"filepath": new_filename}
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500


@app.route('/getImages', methods=['GET'])
def get_images():
    """获取所有已上传的图文图片。"""
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM article_images ORDER BY upload_time DESC")
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
        return jsonify({"code": 200, "msg": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500


@app.route('/deleteImage', methods=['GET'])
def delete_image():
    """删除图文图片（文件 + 数据库记录）。"""
    image_id = request.args.get('id')
    if not image_id or not image_id.isdigit():
        return jsonify({"code": 400, "msg": "Invalid ID", "data": None}), 400

    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM article_images WHERE id = ?", (image_id,))
            record = cursor.fetchone()
            if not record:
                return jsonify({"code": 404, "msg": "Image not found", "data": None}), 404

            record = dict(record)
            file_path = Path(BASE_DIR / "imageFile" / record['file_path'])
            if file_path.exists():
                file_path.unlink()

            cursor.execute("DELETE FROM article_images WHERE id = ?", (image_id,))
            conn.commit()

        return jsonify({"code": 200, "msg": "Image deleted", "data": None}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500


# 全局任务状态跟踪（用于批量发布进度）
article_tasks = {}


@app.route('/postArticle', methods=['POST'])
def postArticle():
    """发布图文文章 — 支持单平台和多平台分发。"""
    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400

    title = data.get('title')
    content = data.get('content', '')
    image_list = data.get('imageList', [])
    tags = data.get('tags', [])
    location = data.get('location', '')

    # 多平台模式：platformAccounts = {5: ['cookie1.json'], 7: ['cookie2.json']}
    platform_accounts = data.get('platformAccounts', {})

    # 单平台兼容模式
    platform_type = data.get('type')
    account_list = data.get('accountList', [])

    if not title:
        return jsonify({"code": 400, "msg": "标题不能为空", "data": None}), 400

    # 如果传了 platformAccounts，用多平台模式
    if platform_accounts:
        # 把字符串 key 转为 int
        pa = {int(k): v for k, v in platform_accounts.items()}
        total = sum(len(v) for v in pa.values())
    elif account_list and platform_type:
        pa = {int(platform_type): account_list}
        total = len(account_list)
    else:
        return jsonify({"code": 400, "msg": "账号列表不能为空", "data": None}), 400

    task_id = str(uuid.uuid1())

    def run_publish():
        def on_result(platform, account, success):
            article_tasks[task_id]['results'].append({
                'platform': platform,
                'account': account,
                'success': success
            })
            article_tasks[task_id]['completed'] += 1

        try:
            dispatch_multi_platform(
                title=title,
                content=content,
                image_paths=image_list,
                tags=tags,
                platform_accounts=pa,
                location=location,
                callback=on_result,
            )
        except Exception as e:
            article_tasks[task_id]['error'] = str(e)
        finally:
            article_tasks[task_id]['status'] = 'completed'

    article_tasks[task_id] = {
        'status': 'running',
        'total': total,
        'completed': 0,
        'results': [],
        'error': None
    }

    thread = threading.Thread(target=run_publish, daemon=True)
    thread.start()

    return jsonify({
        "code": 200,
        "msg": "发布任务已提交",
        "data": {"taskId": task_id}
    }), 200


@app.route('/articleTaskStatus', methods=['GET'])
def article_task_status():
    """查询图文发布任务进度。"""
    task_id = request.args.get('taskId')
    if not task_id or task_id not in article_tasks:
        return jsonify({"code": 404, "msg": "任务不存在", "data": None}), 404

    task = article_tasks[task_id]
    return jsonify({
        "code": 200,
        "msg": "success",
        "data": {
            "status": task['status'],
            "total": task['total'],
            "completed": task['completed'],
            "results": task['results'],
            "error": task['error']
        }
    }), 200


@app.route('/getArticlePosts', methods=['GET'])
def get_article_posts():
    """获取所有图文帖子。"""
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM article_posts ORDER BY created_at DESC")
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
        return jsonify({"code": 200, "msg": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500


@app.route('/deleteArticlePost', methods=['GET'])
def delete_article_post():
    """删除图文帖子。"""
    post_id = request.args.get('id')
    if not post_id or not post_id.isdigit():
        return jsonify({"code": 400, "msg": "Invalid ID", "data": None}), 400
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM article_posts WHERE id = ?", (post_id,))
            conn.commit()
        return jsonify({"code": 200, "msg": "Post deleted", "data": None}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500


@app.route('/updateArticlePost', methods=['POST'])
def update_article_post():
    """更新图文帖子内容。"""
    data = request.get_json()
    if not data or not data.get('id'):
        return jsonify({"code": 400, "msg": "Missing post ID", "data": None}), 400
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE article_posts
                SET title = ?, content = ?, image_paths = ?, tags = ?,
                    location = ?, platform = ?, account_ids = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                data.get('title', ''),
                data.get('content', ''),
                data.get('image_paths', ''),
                data.get('tags', ''),
                data.get('location', ''),
                data.get('platform', 0),
                data.get('account_ids', ''),
                data['id']
            ))
            conn.commit()
        return jsonify({"code": 200, "msg": "Post updated", "data": None}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500


@app.route('/saveArticlePost', methods=['POST'])
def save_article_post():
    """保存图文帖子（新建草稿）。"""
    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO article_posts (title, content, image_paths, tags, location, platform, account_ids, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'draft')
            ''', (
                data.get('title', ''),
                data.get('content', ''),
                data.get('image_paths', ''),
                data.get('tags', ''),
                data.get('location', ''),
                data.get('platform', 0),
                data.get('account_ids', ''),
            ))
            conn.commit()
            post_id = cursor.lastrowid
        return jsonify({"code": 200, "msg": "Post saved", "data": {"id": post_id}}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500


# Cookie文件上传API
@app.route('/uploadCookie', methods=['POST'])
def upload_cookie():
    try:
        if 'file' not in request.files:
            return jsonify({
                "code": 400,
                "msg": "没有找到Cookie文件",
                "data": None
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "code": 400,
                "msg": "Cookie文件名不能为空",
                "data": None
            }), 400

        if not file.filename.endswith('.json'):
            return jsonify({
                "code": 400,
                "msg": "Cookie文件必须是JSON格式",
                "data": None
            }), 400

        # 获取账号信息
        account_id = request.form.get('id')
        platform = request.form.get('platform')

        if not account_id or not platform:
            return jsonify({
                "code": 400,
                "msg": "缺少账号ID或平台信息",
                "data": None
            }), 400

        # 从数据库获取账号的文件路径
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT filePath FROM user_info WHERE id = ?', (account_id,))
            result = cursor.fetchone()

        if not result:
            return jsonify({
                "code": 500,
                "msg": "账号不存在",
                "data": None
            }), 404

        # 保存上传的Cookie文件到对应路径
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / result['filePath'])
        cookie_file_path.parent.mkdir(parents=True, exist_ok=True)

        file.save(str(cookie_file_path))

        # 更新数据库中的账号信息（可选，比如更新更新时间）
        # 这里可以根据需要添加额外的处理逻辑

        return jsonify({
            "code": 200,
            "msg": "Cookie文件上传成功",
            "data": None
        }), 200

    except Exception as e:
        print(f"上传Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"上传Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# Cookie文件下载API
@app.route('/downloadCookie', methods=['GET'])
def download_cookie():
    try:
        file_path = request.args.get('filePath')
        if not file_path:
            return jsonify({
                "code": 500,
                "msg": "缺少文件路径参数",
                "data": None
            }), 400

        # 验证文件路径的安全性，防止路径遍历攻击
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / file_path).resolve()
        base_path = Path(BASE_DIR / "cookiesFile").resolve()

        if not cookie_file_path.is_relative_to(base_path):
            return jsonify({
                "code": 500,
                "msg": "非法文件路径",
                "data": None
            }), 400

        if not cookie_file_path.exists():
            return jsonify({
                "code": 500,
                "msg": "Cookie文件不存在",
                "data": None
            }), 404

        # 返回文件
        return send_from_directory(
            directory=str(cookie_file_path.parent),
            path=cookie_file_path.name,
            as_attachment=True
        )

    except Exception as e:
        print(f"下载Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"下载Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# ==================== 图文平台 SSE 登录（调用 CLI） ====================

# 图文平台 CLI 名称映射
ARTICLE_CLI_PLATFORMS = {5: 'baijiahao', 6: 'smzdm', 7: 'toutiao', 8: 'ctrip'}

@app.route('/loginArticleAccount')
def login_article_account():
    """SSE 端点：调用 CLI 登录图文平台，自动创建账号并上传 cookie。"""
    platform_type = request.args.get('type')  # 5/6/7/8
    account_name = request.args.get('name')

    if not platform_type or not account_name:
        return jsonify({"code": 400, "msg": "缺少参数"}), 400

    cli_name = ARTICLE_CLI_PLATFORMS.get(int(platform_type))
    if not cli_name:
        return jsonify({"code": 400, "msg": f"不支持的平台类型: {platform_type}"}), 400

    status_queue = Queue()
    queue_id = f"article_{platform_type}_{account_name}"
    active_queues[queue_id] = status_queue

    def on_close():
        active_queues.pop(queue_id, None)

    thread = threading.Thread(
        target=_run_cli_login,
        args=(cli_name, account_name, int(platform_type), status_queue),
        daemon=True
    )
    thread.start()

    response = Response(sse_stream(status_queue), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response


def _run_cli_login(cli_name, account_name, platform_type, status_queue):
    """在线程中运行 CLI 登录命令，完成后自动创建账号并复制 cookie。"""
    import sys

    status_queue.put("[引导] 正在启动浏览器，请在弹出的浏览器中完成登录...")

    # 构造命令：sau <platform> login --account <name> --headed
    python_exe = sys.executable
    cmd = [python_exe, "sau_cli.py", cli_name, "login", "--account", account_name, "--headed"]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(BASE_DIR),
            encoding='utf-8',
            errors='replace'
        )

        # 读取输出并转发
        for line in proc.stdout:
            line = line.strip()
            if line:
                status_queue.put(f"[CLI] {line}")

        proc.wait()
        exit_code = proc.returncode

        # 检查 cookie 文件是否生成
        cookie_src = Path(BASE_DIR) / "cookies" / f"{cli_name}_{account_name}.json"

        # 检查文件是否是本次新生成的（修改时间在最近 10 秒内）
        cookie_is_fresh = False
        if cookie_src.exists():
            import time as _time
            mtime = cookie_src.stat().st_mtime
            if _time.time() - mtime < 10:
                cookie_is_fresh = True

        if cookie_is_fresh:
            # 检查账号是否已存在（重新认证 vs 新建）
            with sqlite3.connect(Path(BASE_DIR) / "db" / "database.db") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT id, filePath FROM user_info WHERE type=? AND userName=?',
                               (platform_type, account_name))
                existing = cursor.fetchone()

            if existing:
                # 重新认证：覆盖旧 cookie
                cookie_dst = Path(BASE_DIR) / "cookiesFile" / existing['filePath']
                shutil.copy2(str(cookie_src), str(cookie_dst))
                # 更新状态为有效
                with sqlite3.connect(Path(BASE_DIR) / "db" / "database.db") as conn:
                    conn.execute('UPDATE user_info SET status=1 WHERE id=?', (existing['id'],))
                status_queue.put("[成功] 重新认证成功，Cookie 已更新！")
            else:
                # 新建账号
                cookie_uuid = f"{uuid.uuid1()}.json"
                cookie_dst = Path(BASE_DIR) / "cookiesFile" / cookie_uuid
                cookie_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(cookie_src), str(cookie_dst))
                with sqlite3.connect(Path(BASE_DIR) / "db" / "database.db") as conn:
                    conn.execute(
                        'INSERT INTO user_info (type, filePath, userName, status) VALUES (?, ?, ?, 1)',
                        (platform_type, cookie_uuid, account_name)
                    )
                status_queue.put("[成功] 登录成功，账号已自动创建！")

            status_queue.put("200")
        else:
            status_queue.put(f"[失败] 登录未完成（cookie 文件未生成，退出码={exit_code}）")
            status_queue.put("500")

    except Exception as e:
        status_queue.put(f"[错误] {str(e)}")
        status_queue.put("500")


# 包装函数：在线程中运行异步函数
def run_async_function(type,id,status_queue):
    match type:
        case '1':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(xiaohongshu_cookie_gen(id, status_queue))
            loop.close()
        case '2':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_tencent_cookie(id,status_queue))
            loop.close()
        case '3':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(douyin_cookie_gen(id,status_queue))
            loop.close()
        case '4':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_ks_cookie(id,status_queue))
            loop.close()

# SSE 流生成器函数
def sse_stream(status_queue):
    while True:
        if not status_queue.empty():
            msg = status_queue.get()
            yield f"data: {msg}\n\n"
        else:
            # 避免 CPU 占满
            time.sleep(0.1)

# ==================== 排期调度器 ====================

def _article_scheduler():
    """后台线程：每 60 秒检查是否有到期帖子需要发布。"""
    while True:
        time.sleep(60)
        try:
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            with sqlite3.connect(Path(BASE_DIR) / "db" / "database.db") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM article_posts WHERE status='scheduled' AND scheduled_at <= ?",
                    (now,)
                )
                posts = cursor.fetchall()

            for post in posts:
                post = dict(post)
                logger_key = f"schedule_{post['id']}"
                article_tasks[logger_key] = {
                    'status': 'running', 'total': 0, 'completed': 0, 'results': [], 'error': None
                }

                # 解析平台和账号
                platforms = json.loads(post.get('platforms') or '[]')
                if not platforms:
                    p = post.get('platform', 0)
                    platforms = [p] if p else []

                image_list = json.loads(post.get('image_paths') or '[]')
                tags = json.loads(post.get('tags') or '[]')

                # 构建 platform_accounts
                pa = {}
                for pt in platforms:
                    # 查找该平台所有有效账号
                    with sqlite3.connect(Path(BASE_DIR) / "db" / "database.db") as conn:
                        cursor2 = conn.cursor()
                        cursor2.execute("SELECT filePath FROM user_info WHERE type=? AND status=1", (pt,))
                        rows = cursor2.fetchall()
                        if rows:
                            pa[pt] = [r[0] for r in rows]

                if not pa:
                    article_tasks[logger_key]['status'] = 'completed'
                    article_tasks[logger_key]['error'] = '没有可用账号'
                    continue

                total = sum(len(v) for v in pa.values())
                article_tasks[logger_key]['total'] = total

                def on_result(platform, account, success, _key=logger_key):
                    article_tasks[_key]['results'].append({
                        'platform': platform, 'account': account, 'success': success
                    })
                    article_tasks[_key]['completed'] += 1

                try:
                    dispatch_multi_platform(
                        title=post['title'],
                        content=post.get('content', ''),
                        image_paths=image_list,
                        tags=tags,
                        platform_accounts=pa,
                        location=post.get('location', ''),
                        callback=on_result,
                    )
                    # 更新帖子状态
                    with sqlite3.connect(Path(BASE_DIR) / "db" / "database.db") as conn:
                        conn.execute("UPDATE article_posts SET status='published' WHERE id=?", (post['id'],))
                except Exception as e:
                    with sqlite3.connect(Path(BASE_DIR) / "db" / "database.db") as conn:
                        conn.execute("UPDATE article_posts SET status='failed' WHERE id=?", (post['id'],))
                    article_tasks[logger_key]['error'] = str(e)
                finally:
                    article_tasks[logger_key]['status'] = 'completed'

        except Exception as e:
            print(f"[Scheduler] Error: {e}")


# ==================== 排期 + Excel 导入 API ====================

@app.route('/scheduleArticles', methods=['POST'])
def scheduleArticles():
    """批量排期：接收帖子 ID 列表和排期规则，自动分配发布时间。"""
    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400

    post_ids = data.get('postIds', [])
    start_time = data.get('startTime', '')       # '2026-04-12 10:00'
    interval_minutes = data.get('interval', 60)   # 间隔分钟数

    if not post_ids or not start_time:
        return jsonify({"code": 400, "msg": "缺少帖子ID或起始时间", "data": None}), 400

    try:
        from datetime import datetime, timedelta
        base = datetime.strptime(start_time, '%Y-%m-%d %H:%M')

        with sqlite3.connect(Path(BASE_DIR) / "db" / "database.db") as conn:
            cursor = conn.cursor()
            for i, pid in enumerate(post_ids):
                scheduled_at = base + timedelta(minutes=interval_minutes * i)
                cursor.execute(
                    "UPDATE article_posts SET status='scheduled', scheduled_at=? WHERE id=?",
                    (scheduled_at.strftime('%Y-%m-%d %H:%M:%S'), pid)
                )
            conn.commit()

        return jsonify({"code": 200, "msg": f"已排期 {len(post_ids)} 篇帖子", "data": None}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500


@app.route('/importArticles', methods=['POST'])
def importArticles():
    """批量导入帖子（CSV 文件）。"""
    if 'file' not in request.files:
        return jsonify({"code": 400, "msg": "请上传文件", "data": None}), 400

    file = request.files['file']
    if not file.filename.endswith(('.csv', '.CSV')):
        return jsonify({"code": 400, "msg": "仅支持 CSV 文件", "data": None}), 400

    import csv
    import io

    try:
        stream = io.StringIO(file.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)

        count = 0
        with sqlite3.connect(Path(BASE_DIR) / "db" / "database.db") as conn:
            cursor = conn.cursor()
            for row in reader:
                title = row.get('title', row.get('\u6807\u9898', '')).strip()
                content = row.get('content', row.get('\u6b63\u6587', '')).strip()
                if not title:
                    continue

                cursor.execute('''
                    INSERT INTO article_posts (title, content, image_paths, tags, location, platform, platforms, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'draft')
                ''', (
                    title,
                    content,
                    row.get('image_paths', row.get('\u56fe\u7247\u8def\u5f84', '')),
                    row.get('tags', row.get('\u6807\u7b7e', '')),
                    row.get('location', row.get('\u5730\u70b9', '')),
                    0,
                    row.get('platforms', row.get('\u5e73\u53f0', '[]')),
                ))
                count += 1
            conn.commit()

        return jsonify({"code": 200, "msg": f"成功导入 {count} 篇帖子", "data": {"count": count}}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500


# 启动排期调度线程
scheduler_thread = threading.Thread(target=_article_scheduler, daemon=True)
scheduler_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0' ,port=5409)
