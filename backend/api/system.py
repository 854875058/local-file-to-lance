# -*- coding: utf-8 -*-
"""系统监控 API"""

import logging
import psutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

class SystemResources(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float

class ModelStatus(BaseModel):
    loaded: bool
    models: list

class LanceDBStatus(BaseModel):
    connected: bool
    text_rows: int
    image_rows: int
    files_count: int

class SystemStatus(BaseModel):
    resources: SystemResources
    models: ModelStatus
    lancedb: LanceDBStatus

@router.get("/resources", response_model=SystemResources)
async def get_resources():
    """获取系统资源使用情况"""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()

        return SystemResources(
            cpu_percent=round(cpu, 1),
            memory_percent=round(mem.percent, 1),
            memory_used_gb=round(mem.used / (1024**3), 2),
            memory_total_gb=round(mem.total / (1024**3), 2)
        )

    except Exception as e:
        logger.error(f"获取系统资源失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统资源失败: {str(e)}")

@router.get("/status", response_model=SystemStatus)
async def get_status():
    """获取系统整体状态"""
    try:
        # 系统资源
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        resources = SystemResources(
            cpu_percent=round(cpu, 1),
            memory_percent=round(mem.percent, 1),
            memory_used_gb=round(mem.used / (1024**3), 2),
            memory_total_gb=round(mem.total / (1024**3), 2)
        )

        # AI 模型状态
        try:
            from models_loader import load_models_cached
            models = load_models_cached()
            model_status = ModelStatus(
                loaded=True,
                models=list(models.keys())
            )
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            model_status = ModelStatus(loaded=False, models=[])

        # LanceDB 状态
        try:
            from models_loader import get_lancedb_tables
            tbl_text, tbl_image, tbl_files = get_lancedb_tables()
            lancedb_status = LanceDBStatus(
                connected=True,
                text_rows=tbl_text.count_rows(),
                image_rows=tbl_image.count_rows(),
                files_count=tbl_files.count_rows()
            )
        except Exception as e:
            logger.error(f"LanceDB 连接失败: {e}")
            lancedb_status = LanceDBStatus(
                connected=False,
                text_rows=0,
                image_rows=0,
                files_count=0
            )

        return SystemStatus(
            resources=resources,
            models=model_status,
            lancedb=lancedb_status
        )

    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

@router.get("/logs")
async def get_logs(lines: int = 500):
    """获取应用日志"""
    try:
        log_file = Path(__file__).parent.parent.parent / "app.log"

        if not log_file.exists():
            return {"logs": "日志文件不存在"}

        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return {"logs": "".join(recent_lines)}

    except Exception as e:
        logger.error(f"读取日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"读取日志失败: {str(e)}")
