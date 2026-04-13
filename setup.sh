#!/bin/bash
# social-auto-upload 一键安装脚本 (Windows Git Bash)
# 请确保已安装 Python、Node.js，并已在项目根目录下运行此脚本

set -e

echo "===== Step 1: 创建并激活 Python 虚拟环境 ====="
python -m venv .venv
source .venv/Scripts/activate

echo "===== Step 2: 安装 Python 依赖 ====="
pip install -r requirements.txt

echo "===== Step 3: 安装 patchright 浏览器驱动 ====="
python -m patchright install chromium

echo "===== Step 4: 初始化数据库 ====="
python db/createTable.py

echo "===== Step 5: 创建配置文件 ====="
if [ ! -f conf.py ]; then
    cp conf.example.py conf.py
    echo "已从 conf.example.py 复制创建 conf.py"
else
    echo "conf.py 已存在，跳过"
fi

echo "===== Step 6: 安装前端依赖 ====="
cd sau_frontend
npm install
cd ..

echo ""
echo "===== 安装完成！ ====="
echo "启动后端：source .venv/Scripts/activate && python sau_backend.py"
echo "启动前端：cd sau_frontend && npm run dev"
