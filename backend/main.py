# -*- coding: utf-8 -*-
"""FastAPI 后端主入口"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import upload, search, files, dashboard, system

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ROOT_DIR / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="DataVerse Pro API",
    description="多模态数据湖 API 服务",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router, prefix="/api/upload", tags=["文件上传"])
app.include_router(search.router, prefix="/api/search", tags=["向量搜索"])
app.include_router(files.router, prefix="/api/files", tags=["文件管理"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表盘"])
app.include_router(system.router, prefix="/api/system", tags=["系统监控"])

# 静态文件服务（前端构建产物）
frontend_dist = ROOT_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    logger.info("=" * 60)
    logger.info("DataVerse Pro API 服务启动")
    logger.info("=" * 60)

    # 初始化数据库
    from database import init_db
    init_db()
    logger.info("✓ SQLite 数据库初始化完成")

    # 预加载 AI 模型和 LanceDB 连接（后台线程）
    import threading
    def load_resources():
        try:
            from models_loader import load_models_cached, get_lancedb_tables
            models = load_models_cached()
            logger.info(f"✓ AI 模型加载完成: {list(models.keys())}")

            tbl_text, tbl_image, tbl_files = get_lancedb_tables()
            logger.info(f"✓ LanceDB 连接成功: text={tbl_text.count_rows()}, image={tbl_image.count_rows()}, files={tbl_files.count_rows()}")
        except Exception as e:
            logger.error(f"✗ 资源加载失败: {e}")

    threading.Thread(target=load_resources, daemon=True).start()

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "DataVerse Pro API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
