@echo off
chcp 65001 >nul
echo ========================================
echo DataVerse Pro - 启动后端服务
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/2] 检查依赖...
python -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo 缺少依赖，正在安装...
    pip install fastapi uvicorn python-multipart
)

echo [2/2] 启动 FastAPI 服务...
echo.
echo 后端地址: http://localhost:8090
echo API 文档: http://localhost:8090/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

python main.py

pause
