# -*- coding: utf-8 -*-
"""文件上传 API"""

import os
import uuid
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from pydantic import BaseModel

from config import TEMP_DIR
from etl import process_files_batch

logger = logging.getLogger(__name__)
router = APIRouter()

class UploadResponse(BaseModel):
    success: bool
    message: str
    file_count: int
    task_id: str = None

@router.post("/batch", response_model=UploadResponse)
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """批量上传文件并后台处理"""
    if not files:
        return UploadResponse(success=False, message="未选择文件", file_count=0)

    # 保存上传的文件到临时目录
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_files = []

    try:
        for file in files:
            temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:8]}_{file.filename}")
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)
            temp_files.append((temp_path, file.filename))
            logger.info(f"文件已保存: {file.filename} -> {temp_path}")

        # 后台任务处理文件
        task_id = uuid.uuid4().hex[:12]
        background_tasks.add_task(process_files_batch, temp_files, user_id=0)

        return UploadResponse(
            success=True,
            message=f"已接收 {len(temp_files)} 个文件，正在后台处理",
            file_count=len(temp_files),
            task_id=task_id
        )

    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        # 清理已保存的临时文件
        for temp_path, _ in temp_files:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        return UploadResponse(
            success=False,
            message=f"上传失败: {str(e)}",
            file_count=0
        )
