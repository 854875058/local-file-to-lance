# -*- coding: utf-8 -*-
"""仪表盘统计 API"""

import logging
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from stats_service import get_dashboard_stats, get_task_trend
from models_loader import get_lancedb_tables
from database import get_file_entities

logger = logging.getLogger(__name__)
router = APIRouter()

class DashboardStats(BaseModel):
    total_files: int
    today_files: int
    week_files: int
    week_tasks_total: int
    week_tasks_success: int
    week_success_rate: float
    week_avg_time_sec: float
    text_rows: int
    image_rows: int

class TrendData(BaseModel):
    date: str
    file_count: int
    success_count: int

class FileTypeCount(BaseModel):
    doc_type: str
    count: int

class EntityData(BaseModel):
    file_hash: str
    entity_name: str
    entity_type: str

@router.get("/stats", response_model=DashboardStats)
async def get_stats():
    """获取仪表盘核心指标"""
    try:
        stats = get_dashboard_stats()
        tbl_text, tbl_image, tbl_files = get_lancedb_tables()

        return DashboardStats(
            total_files=stats["total_files"],
            today_files=stats["today_files"],
            week_files=stats["week_files"],
            week_tasks_total=stats["week_tasks_total"],
            week_tasks_success=stats["week_tasks_success"],
            week_success_rate=stats["week_success_rate"],
            week_avg_time_sec=stats["week_avg_time_sec"],
            text_rows=tbl_text.count_rows(),
            image_rows=tbl_image.count_rows()
        )

    except Exception as e:
        logger.error(f"获取统计数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/trend", response_model=List[TrendData])
async def get_trend(days: int = 7):
    """获取近N天接入趋势"""
    try:
        trend = get_task_trend(days)
        return [TrendData(**item) for item in trend]

    except Exception as e:
        logger.error(f"获取趋势数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取趋势数据失败: {str(e)}")

@router.get("/file-types", response_model=List[FileTypeCount])
async def get_file_types():
    """获取文件类型分布"""
    try:
        tbl_text, tbl_image, tbl_files = get_lancedb_tables()

        df = tbl_files.search().select(["doc_type"]).limit(100000).to_pandas()

        if df.empty:
            return []

        type_counts = df["doc_type"].fillna("未知").value_counts()

        return [
            FileTypeCount(doc_type=doc_type, count=int(count))
            for doc_type, count in type_counts.items()
        ]

    except Exception as e:
        logger.error(f"获取文件类型分布失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文件类型分布失败: {str(e)}")

@router.get("/entities", response_model=List[EntityData])
async def get_entities(file_hash: str = None):
    """获取知识图谱实体数据"""
    try:
        entities = get_file_entities(file_hash)
        return [EntityData(**entity) for entity in entities]

    except Exception as e:
        logger.error(f"获取实体数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取实体数据失败: {str(e)}")
