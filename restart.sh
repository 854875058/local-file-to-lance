#!/usr/bin/env bash
# 重启 DataVerse Pro (NiceGUI)

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# 停止旧进程
PID=$(pgrep -f "python app_nicegui.py" || true)
if [ -n "$PID" ]; then
    echo "停止旧进程 PID: $PID"
    kill "$PID" 2>/dev/null || true
    sleep 2
    kill -9 "$PID" 2>/dev/null || true
fi

# 切换 conda 环境
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate to_lance

# 后台启动
nohup python app_nicegui.py > app.log 2>&1 &
echo "已启动 PID: $!, 日志: $DIR/app.log"
