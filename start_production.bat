@echo off
chcp 65001 >nul
echo ========================================
echo DataVerse Pro - 生产环境部署
echo ========================================
echo.

echo [1/3] 构建前端...
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
    if errorlevel 1 (
        echo 依赖安装失败！
        pause
        exit /b 1
    )
)

call npm run build
if errorlevel 1 (
    echo 前端构建失败！
    pause
    exit /b 1
)

echo.
echo [2/3] 检查后端依赖...
cd /d "%~dp0backend"
python -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo 安装后端依赖...
    pip install fastapi uvicorn python-multipart
)

echo.
echo [3/3] 启动生产服务...
echo.
echo 服务地址: http://localhost:8090
echo API 文档: http://localhost:8090/docs
echo.
echo 前端已构建并集成到后端，访问 http://localhost:8090 即可
echo.
echo 按 Ctrl+C 停止服务
echo.

python main.py

pause
