#!/bin/bash
# MT5 Django API 停止脚本

echo "========================================"
echo "停止 MT5 Django REST API 服务器"
echo "========================================"
echo ""

echo "[1/2] 查找运行中的Python进程..."
echo ""

# 查找占用8000端口的进程
PID=$(lsof -ti:8000)

if [ -n "$PID" ]; then
    echo "找到进程 PID: $PID"
    echo ""
    echo "[2/2] 终止进程..."
    kill -9 $PID
    echo ""
    echo "✓ 服务器已停止"
else
    echo "未找到运行在8000端口的服务器"
fi

echo ""
echo "========================================"
