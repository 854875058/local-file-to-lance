# -*- coding: utf-8 -*-
"""文件管理 API"""

import base64
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from models_loader import get_lancedb_tables
from database import get_file_registry_count, delete_file_from_registry
from s3_utils import delete_from_s3

logger = logging.getLogger(__name__)
router = APIRouter()

class FileItem(BaseModel):
    file_hash: str
    doc_name: str
    doc_type: str
    source_uri: str

class FilesListResponse(BaseModel):
    success: bool
    files: List[FileItem]
    total: int
    page: int
    page_size: int

class FilePreviewResponse(BaseModel):
    success: bool
    file_hash: str
    doc_name: str
    doc_type: str
    content_type: str
    content: str  # base64 编码或文本内容
    text_full: Optional[str] = None

class DeleteResponse(BaseModel):
    success: bool
    message: str

@router.get("/list", response_model=FilesListResponse)
async def list_files(page: int = 1, page_size: int = 20, doc_type: str = None):
    """获取文件列表（分页）"""
    try:
        tbl_text, tbl_image, tbl_files = get_lancedb_tables()

        # 查询文件表
        df = tbl_files.search().select(["file_hash", "doc_name", "doc_type", "source_uri"]).limit(10000).to_pandas()

        # 过滤文件类型
        if doc_type and doc_type != "all":
            df = df[df["doc_type"] == doc_type]

        total = len(df)

        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        df_page = df.iloc[start:end]

        files = []
        for _, row in df_page.iterrows():
            files.append(FileItem(
                file_hash=row["file_hash"],
                doc_name=row["doc_name"],
                doc_type=row["doc_type"],
                source_uri=row["source_uri"]
            ))

        return FilesListResponse(
            success=True,
            files=files,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"获取文件列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@router.get("/preview/{file_hash}", response_model=FilePreviewResponse)
async def preview_file(file_hash: str):
    """预览文件内容"""
    try:
        tbl_text, tbl_image, tbl_files = get_lancedb_tables()

        # 查询文件
        df = tbl_files.search().where(f"file_hash = '{file_hash}'").select(
            ["file_hash", "doc_name", "doc_type", "file_bytes", "text_full"]
        ).limit(1).to_pandas()

        if df.empty:
            raise HTTPException(status_code=404, detail="文件不存在")

        row = df.iloc[0]
        doc_name = row["doc_name"]
        doc_type = row["doc_type"]
        file_bytes = row["file_bytes"]
        text_full = row.get("text_full", "")

        # 根据文件类型返回不同内容
        ext = doc_type.lower()

        # 图片
        if ext in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
            content_b64 = base64.b64encode(file_bytes).decode()
            return FilePreviewResponse(
                success=True,
                file_hash=file_hash,
                doc_name=doc_name,
                doc_type=doc_type,
                content_type="image",
                content=content_b64
            )

        # 音频
        elif ext in ["mp3", "wav", "ogg", "m4a", "flac"]:
            content_b64 = base64.b64encode(file_bytes).decode()
            return FilePreviewResponse(
                success=True,
                file_hash=file_hash,
                doc_name=doc_name,
                doc_type=doc_type,
                content_type="audio",
                content=content_b64
            )

        # 视频
        elif ext in ["mp4", "avi", "mov", "mkv", "webm"]:
            content_b64 = base64.b64encode(file_bytes).decode()
            return FilePreviewResponse(
                success=True,
                file_hash=file_hash,
                doc_name=doc_name,
                doc_type=doc_type,
                content_type="video",
                content=content_b64
            )

        # 文本
        else:
            return FilePreviewResponse(
                success=True,
                file_hash=file_hash,
                doc_name=doc_name,
                doc_type=doc_type,
                content_type="text",
                content="",
                text_full=text_full or "无文本内容"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览文件失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览文件失败: {str(e)}")

@router.delete("/{file_hash}", response_model=DeleteResponse)
async def delete_file(file_hash: str):
    """删除文件"""
    try:
        tbl_text, tbl_image, tbl_files = get_lancedb_tables()

        # 查询文件信息
        df = tbl_files.search().where(f"file_hash = '{file_hash}'").select(
            ["file_hash", "source_uri"]
        ).limit(1).to_pandas()

        if df.empty:
            return DeleteResponse(success=False, message="文件不存在")

        source_uri = df.iloc[0]["source_uri"]

        # 从 LanceDB 删除
        tbl_text.delete(f"file_hash = '{file_hash}'")
        tbl_image.delete(f"file_hash = '{file_hash}'")
        tbl_files.delete(f"file_hash = '{file_hash}'")

        # 从 SQLite 删除
        delete_file_from_registry(file_hash)

        # 从 S3 删除
        if source_uri.startswith("s3://"):
            delete_from_s3(source_uri)

        logger.info(f"文件已删除: {file_hash}")
        return DeleteResponse(success=True, message="文件删除成功")

    except Exception as e:
        logger.error(f"删除文件失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")
