#!/usr/bin/env bash
# 启动 DataVerse Pro（Streamlit）

set -e

APP_FILE="app.py"
LOG_FILE="app.log"
PID_FILE="app.pid"
PORT="8501"

# 关闭 HuggingFace / Transformers 在线访问，强制使用本地缓存模型
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

if [ -f "$PID_FILE" ]; then
  if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "应用已在运行，PID=$(cat "$PID_FILE")"
    exit 0
  else
    echo "发现残留 PID 文件，自动清理"
    rm -f "$PID_FILE"
  fi
fi

echo "启动应用: $APP_FILE (port=$PORT)"
nohup streamlit run "$APP_FILE" --server.port "$PORT" --server.address 0.0.0.0 >>"$LOG_FILE" 2>&1 &
PID=$!

echo $PID >"$PID_FILE"
echo "已在后台启动，PID=$PID，日志输出到 $LOG_FILE"
