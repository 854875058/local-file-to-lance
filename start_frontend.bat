@echo off
chcp 65001 >nul
echo ========================================
echo DataVerse Pro - 启动前端开发服务
echo ========================================
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [1/2] 首次运行，安装依赖...
    echo 这可能需要几分钟，请耐心等待...
    call npm install
    if errorlevel 1 (
        echo.
        echo 依赖安装失败！请检查：
        echo 1. 是否已安装 Node.js
        echo 2. 网络连接是否正常
        pause
        exit /b 1
    )
) else (
    echo [1/2] 依赖已安装
)

echo [2/2] 启动 Vite 开发服务器...
echo.
echo 前端地址: http://localhost:3000
echo 后端代理: http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务
echo.

call npm run dev

pause
