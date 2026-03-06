#!/usr/bin/env bash
# =============================================================================
# DataVerse Pro - Linux 自动化部署运维脚本
# 用法: bash deploy.sh [命令]
#   install     首次部署（安装全部依赖 + 构建前端 + 创建 systemd 服务）
#   start       启动服务（前后端）
#   stop        停止服务
#   restart     重启服务
#   status      查看服务状态 + 健康检查
#   logs        查看后端实时日志
#   build       仅重新构建前端
#   update      拉取代码 + 重新部署
#   dev         开发模式启动（前后端分离，带热更新）
#   health      仅执行健康检查
#   uninstall   移除 systemd 服务
# =============================================================================

set -euo pipefail

# ---- 项目路径 ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_FILE="$PROJECT_DIR/app.log"

# ---- 服务配置 ----
BACKEND_PORT=8090
FRONTEND_PORT=3000
SERVICE_NAME="dataverse-pro"
PIDFILE_BACKEND="/tmp/${SERVICE_NAME}-backend.pid"
PIDFILE_FRONTEND="/tmp/${SERVICE_NAME}-frontend.pid"

# ---- Python 虚拟环境 ----
VENV_DIR="$PROJECT_DIR/venv"

# ---- 颜色输出 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# =============================================================================
# 环境检测
# =============================================================================
check_system() {
    info "检测系统环境..."

    # 操作系统
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        ok "操作系统: $PRETTY_NAME"
    fi

    # Python
    if command -v python3 &>/dev/null; then
        PYTHON_BIN=$(command -v python3)
        PYTHON_VER=$($PYTHON_BIN --version 2>&1)
        ok "Python: $PYTHON_VER ($PYTHON_BIN)"
    else
        err "未检测到 python3，请先安装: sudo apt install python3 python3-pip python3-venv"
        exit 1
    fi

    # Node.js
    if command -v node &>/dev/null; then
        ok "Node.js: $(node --version)"
    else
        warn "未检测到 Node.js，前端构建将不可用"
        warn "安装方法: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs"
    fi

    # npm
    if command -v npm &>/dev/null; then
        ok "npm: $(npm --version)"
    fi

    # GPU (可选)
    if command -v nvidia-smi &>/dev/null; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
        ok "GPU: $GPU_NAME"
    else
        warn "未检测到 NVIDIA GPU，AI 模型将使用 CPU（速度较慢）"
    fi

    # poppler (pdf2image 依赖)
    if command -v pdftoppm &>/dev/null; then
        ok "poppler-utils: 已安装"
    else
        warn "未检测到 poppler-utils，PDF 图像提取将不可用"
        warn "安装方法: sudo apt install poppler-utils"
    fi

    # ffmpeg (whisper 依赖)
    if command -v ffmpeg &>/dev/null; then
        ok "ffmpeg: 已安装"
    else
        warn "未检测到 ffmpeg，音视频转录将不可用"
        warn "安装方法: sudo apt install ffmpeg"
    fi
}

# =============================================================================
# 安装系统依赖
# =============================================================================
install_system_deps() {
    info "安装系统依赖..."

    if command -v apt &>/dev/null; then
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv \
            poppler-utils ffmpeg curl git
        ok "系统依赖安装完成 (apt)"
    elif command -v yum &>/dev/null; then
        sudo yum install -y python3 python3-pip \
            poppler-utils ffmpeg curl git
        ok "系统依赖安装完成 (yum)"
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip \
            poppler-utils ffmpeg curl git
        ok "系统依赖安装完成 (dnf)"
    else
        warn "无法识别包管理器，请手动安装: python3 python3-pip poppler-utils ffmpeg"
    fi
}

# =============================================================================
# Python 虚拟环境 + 依赖
# =============================================================================
setup_python() {
    info "配置 Python 虚拟环境..."

    if [[ ! -d "$VENV_DIR" ]]; then
        python3 -m venv "$VENV_DIR"
        ok "虚拟环境已创建: $VENV_DIR"
    else
        ok "虚拟环境已存在: $VENV_DIR"
    fi

    source "$VENV_DIR/bin/activate"

    info "安装 Python 依赖..."
    pip install --upgrade pip -q
    pip install -r "$PROJECT_DIR/requirements.txt" -q
    ok "Python 依赖安装完成"
}

# =============================================================================
# 前端构建
# =============================================================================
build_frontend() {
    info "构建前端..."

    if ! command -v npm &>/dev/null; then
        err "npm 未安装，无法构建前端"
        return 1
    fi

    cd "$FRONTEND_DIR"

    if [[ ! -d "node_modules" ]]; then
        info "安装前端依赖..."
        npm install
    fi

    npm run build
    ok "前端构建完成: $FRONTEND_DIR/dist"
    cd "$PROJECT_DIR"
}

# =============================================================================
# 启动服务
# =============================================================================
start_backend() {
    if is_running_backend; then
        warn "后端已在运行 (PID: $(cat "$PIDFILE_BACKEND"))"
        return 0
    fi

    info "启动后端服务..."

    # 激活虚拟环境
    if [[ -d "$VENV_DIR" ]]; then
        source "$VENV_DIR/bin/activate"
    fi

    cd "$BACKEND_DIR"
    nohup python main.py >> "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PIDFILE_BACKEND"
    cd "$PROJECT_DIR"

    # 等待启动
    sleep 3

    if kill -0 "$pid" 2>/dev/null; then
        ok "后端已启动 (PID: $pid, 端口: $BACKEND_PORT)"
    else
        err "后端启动失败，查看日志: tail -50 $LOG_FILE"
        return 1
    fi
}

start_frontend_dev() {
    if is_running_frontend; then
        warn "前端开发服务已在运行 (PID: $(cat "$PIDFILE_FRONTEND"))"
        return 0
    fi

    if ! command -v npm &>/dev/null; then
        err "npm 未安装"
        return 1
    fi

    info "启动前端开发服务..."

    cd "$FRONTEND_DIR"
    nohup npm run dev >> "$PROJECT_DIR/frontend-dev.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$PIDFILE_FRONTEND"
    cd "$PROJECT_DIR"

    sleep 3

    if kill -0 "$pid" 2>/dev/null; then
        ok "前端开发服务已启动 (PID: $pid, 端口: $FRONTEND_PORT)"
    else
        err "前端启动失败，查看日志: tail -50 $PROJECT_DIR/frontend-dev.log"
        return 1
    fi
}

# =============================================================================
# 停止服务
# =============================================================================
stop_backend() {
    if [[ -f "$PIDFILE_BACKEND" ]]; then
        local pid
        pid=$(cat "$PIDFILE_BACKEND")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            sleep 2
            # 强制终止残留
            kill -9 "$pid" 2>/dev/null || true
            ok "后端已停止 (PID: $pid)"
        else
            warn "后端进程不存在 (PID: $pid)"
        fi
        rm -f "$PIDFILE_BACKEND"
    else
        warn "后端未在运行"
    fi

    # 清理可能残留的 uvicorn 进程
    pkill -f "uvicorn.*main:app.*${BACKEND_PORT}" 2>/dev/null || true
}

stop_frontend() {
    if [[ -f "$PIDFILE_FRONTEND" ]]; then
        local pid
        pid=$(cat "$PIDFILE_FRONTEND")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            sleep 1
            kill -9 "$pid" 2>/dev/null || true
            ok "前端已停止 (PID: $pid)"
        else
            warn "前端进程不存在 (PID: $pid)"
        fi
        rm -f "$PIDFILE_FRONTEND"
    else
        warn "前端未在运行"
    fi
}

# =============================================================================
# 进程检查
# =============================================================================
is_running_backend() {
    [[ -f "$PIDFILE_BACKEND" ]] && kill -0 "$(cat "$PIDFILE_BACKEND")" 2>/dev/null
}

is_running_frontend() {
    [[ -f "$PIDFILE_FRONTEND" ]] && kill -0 "$(cat "$PIDFILE_FRONTEND")" 2>/dev/null
}

# =============================================================================
# 健康检查
# =============================================================================
health_check() {
    info "执行健康检查..."

    # 后端 API
    if curl -sf "http://localhost:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
        ok "后端 API:   http://localhost:${BACKEND_PORT}/api/health  -> OK"
    else
        err "后端 API:   无响应 (端口 $BACKEND_PORT)"
    fi

    # 系统资源
    local res
    if res=$(curl -sf "http://localhost:${BACKEND_PORT}/api/system/resources" 2>/dev/null); then
        local cpu mem
        cpu=$(echo "$res" | python3 -c "import sys,json; print(json.load(sys.stdin)['cpu_percent'])" 2>/dev/null || echo "N/A")
        mem=$(echo "$res" | python3 -c "import sys,json; print(json.load(sys.stdin)['memory_percent'])" 2>/dev/null || echo "N/A")
        ok "系统资源:   CPU ${cpu}%, 内存 ${mem}%"
    fi

    # 文件数
    local files_res
    if files_res=$(curl -sf "http://localhost:${BACKEND_PORT}/api/files/list?page_size=1" 2>/dev/null); then
        local total
        total=$(echo "$files_res" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "N/A")
        ok "数据湖文件: $total 个"
    fi
}

# =============================================================================
# 状态汇总
# =============================================================================
show_status() {
    echo ""
    echo "============================================"
    echo "  DataVerse Pro 服务状态"
    echo "============================================"

    # 后端
    if is_running_backend; then
        ok "后端:  运行中 (PID: $(cat "$PIDFILE_BACKEND"), 端口: $BACKEND_PORT)"
    else
        err "后端:  未运行"
    fi

    # 前端（开发模式）
    if is_running_frontend; then
        ok "前端:  运行中 (PID: $(cat "$PIDFILE_FRONTEND"), 端口: $FRONTEND_PORT)"
    else
        info "前端:  未运行（生产模式由后端直接提供静态文件）"
    fi

    # 前端构建产物
    if [[ -f "$FRONTEND_DIR/dist/index.html" ]]; then
        ok "前端构建: dist/ 已就绪"
    else
        warn "前端构建: dist/ 不存在，需要执行 bash deploy.sh build"
    fi

    echo ""
    health_check
    echo ""
}

# =============================================================================
# systemd 服务管理
# =============================================================================
install_systemd() {
    info "创建 systemd 服务..."

    local service_file="/etc/systemd/system/${SERVICE_NAME}.service"
    local python_bin="$VENV_DIR/bin/python"

    if [[ ! -f "$python_bin" ]]; then
        python_bin=$(command -v python3)
    fi

    sudo tee "$service_file" > /dev/null <<UNIT
[Unit]
Description=DataVerse Pro - Multi-modal Data Lake
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$BACKEND_DIR
ExecStart=$python_bin main.py
Restart=on-failure
RestartSec=5
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

# 环境变量（按需修改）
# Environment=S3_ENDPOINT_URL=http://192.168.20.4:8333
# Environment=S3_ACCESS_KEY=mykey
# Environment=S3_SECRET_KEY=mysecret
# Environment=DEEPSEEK_API_KEY=sk-xxx

[Install]
WantedBy=multi-user.target
UNIT

    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    ok "systemd 服务已创建并设置为开机启动"
    info "管理命令:"
    info "  sudo systemctl start $SERVICE_NAME"
    info "  sudo systemctl stop $SERVICE_NAME"
    info "  sudo systemctl restart $SERVICE_NAME"
    info "  sudo systemctl status $SERVICE_NAME"
    info "  journalctl -u $SERVICE_NAME -f"
}

uninstall_systemd() {
    info "移除 systemd 服务..."
    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    sudo rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
    sudo systemctl daemon-reload
    ok "systemd 服务已移除"
}

# =============================================================================
# 主命令分发
# =============================================================================
case "${1:-help}" in
    install)
        echo ""
        echo "============================================"
        echo "  DataVerse Pro 首次部署"
        echo "============================================"
        echo ""
        check_system
        echo ""
        install_system_deps
        echo ""
        setup_python
        echo ""
        build_frontend
        echo ""
        install_systemd
        echo ""
        ok "部署完成！"
        info "启动服务: sudo systemctl start $SERVICE_NAME"
        info "或手动:   bash deploy.sh start"
        info "访问地址: http://<服务器IP>:$BACKEND_PORT"
        ;;

    start)
        start_backend
        echo ""
        health_check
        echo ""
        info "访问地址: http://localhost:$BACKEND_PORT"
        info "API 文档: http://localhost:$BACKEND_PORT/docs"
        ;;

    stop)
        stop_backend
        stop_frontend
        ;;

    restart)
        stop_backend
        stop_frontend
        sleep 2
        start_backend
        echo ""
        health_check
        ;;

    status)
        show_status
        ;;

    logs)
        if [[ -f "$LOG_FILE" ]]; then
            tail -f "$LOG_FILE"
        else
            warn "日志文件不存在: $LOG_FILE"
        fi
        ;;

    build)
        build_frontend
        ;;

    update)
        info "拉取最新代码..."
        cd "$PROJECT_DIR"
        git pull
        echo ""
        setup_python
        echo ""
        build_frontend
        echo ""
        stop_backend
        sleep 2
        start_backend
        echo ""
        health_check
        echo ""
        ok "更新部署完成！"
        ;;

    dev)
        echo ""
        info "开发模式启动..."
        start_backend
        echo ""
        start_frontend_dev
        echo ""
        health_check
        echo ""
        info "前端 (热更新): http://localhost:$FRONTEND_PORT"
        info "后端 API:      http://localhost:$BACKEND_PORT"
        info "停止服务: bash deploy.sh stop"
        ;;

    health)
        health_check
        ;;

    uninstall)
        uninstall_systemd
        ;;

    help|*)
        echo ""
        echo "DataVerse Pro 部署运维脚本"
        echo ""
        echo "用法: bash deploy.sh <命令>"
        echo ""
        echo "命令:"
        echo "  install     首次部署（系统依赖 + Python 环境 + 前端构建 + systemd 服务）"
        echo "  start       启动后端服务（生产模式，前端由后端提供）"
        echo "  stop        停止所有服务"
        echo "  restart     重启服务"
        echo "  status      查看服务状态 + 健康检查"
        echo "  logs        查看后端实时日志 (tail -f)"
        echo "  build       仅重新构建前端"
        echo "  update      git pull + 重新部署 + 重启"
        echo "  dev         开发模式（前后端分离，支持热更新）"
        echo "  health      仅执行健康检查"
        echo "  uninstall   移除 systemd 服务"
        echo ""
        echo "示例:"
        echo "  bash deploy.sh install      # 首次部署"
        echo "  bash deploy.sh start        # 启动服务"
        echo "  bash deploy.sh status       # 查看状态"
        echo "  bash deploy.sh logs         # 查看日志"
        echo ""
        ;;
esac
