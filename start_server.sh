#!/bin/bash
# MT5 Django API 启动脚本

echo "========================================"
echo "MT5 Django REST API 服务器"
echo "========================================"
echo ""

# 检查是否已运行数据库迁移
if [ ! -f "db.sqlite3" ]; then
    echo "[1/2] 运行数据库迁移..."
    python manage.py migrate
    echo ""
else
    echo "[1/2] 数据库已存在，跳过迁移"
    echo ""
fi

echo "[2/2] 启动 Django 开发服务器..."
echo ""
echo "服务器地址: http://localhost:8000"
echo "API 文档: 查看 API_DOCS.md"
echo "测试脚本: python test_api.py"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "========================================"
echo ""

python manage.py runserver 0.0.0.0:8000
