#!/usr/bin/env bash
# 停止 DataVerse Pro（Streamlit）

PID_FILE="app.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "未找到 PID 文件：$PID_FILE，尝试按照进程名停止…"
  pkill -f "streamlit run app.py" || true
  exit 0
fi

PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
  echo "停止应用，PID=$PID"
  kill "$PID" || true
  # 等待最多 10 秒
  for i in {1..10}; do
    if kill -0 "$PID" 2>/dev/null; then
      sleep 1
    else
      break
    fi
  done
  if kill -0 "$PID" 2>/dev/null; then
    echo "进程未退出，执行强制杀死"
    kill -9 "$PID" || true
  fi
else
  echo "PID=$PID 的进程不存在，直接清理 PID 文件"
fi

rm -f "$PID_FILE"
echo "已停止应用并清理 PID 文件"
