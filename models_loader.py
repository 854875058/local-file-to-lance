# -*- coding: utf-8 -*-
"""AI 模型与 LanceDB 连接"""

import logging
import pyarrow as pa
import lancedb

from config import LANCE_DB_URI, S3_CONFIG

logger = logging.getLogger(__name__)

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

def get_text_splitter(chunk_size=500, chunk_overlap=50):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )


def _load_models():
    from sentence_transformers import SentenceTransformer
    import whisper
    import os

    # 使用 HuggingFace 镜像中转站（如果能联网的话）
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

    # whisper: 优先用本地缓存文件路径直接加载，绕过联网校验
    whisper_cache = os.path.join(os.getenv("XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache")), "whisper")
    whisper_local = os.path.join(whisper_cache, "base.pt")
    if os.path.isfile(whisper_local):
        # 传入文件路径而非模型名，whisper 会直接 open() 加载，不联网
        whisper_model = whisper.load_model(whisper_local)
    else:
        whisper_model = whisper.load_model("base")

    return {
        "text": SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True),
        "clip_text": SentenceTransformer("sentence-transformers/clip-ViT-B-32-multilingual-v1", local_files_only=True),
        "clip_vision": SentenceTransformer("clip-ViT-B-32", local_files_only=True),
        "whisper": whisper_model,
    }


def load_models_cached():
    """供 Streamlit st.cache_resource 使用，在 app 里包装一层"""
    return _load_models()


def get_lancedb_tables():
    """打开或创建 LanceDB 表（带 file_hash）。

    - `text_chunks` / `image_chunks`：用于向量检索（必要字段含 file_hash，支持整文件预览定位）
    - `files`：存原始文件 bytes + 可选全文 text_full（用于前端整文件预览/下载）

    若旧表已存在但无 file_hash 列则一次性重建（仅一次），保证新接入可预览。
    """
    storage_options = {
        "endpoint_url": S3_CONFIG["endpoint_url"],
        "access_key_id": S3_CONFIG["access_key_id"],
        "secret_access_key": S3_CONFIG["secret_access_key"],
        # SeaweedFS 常见为 HTTP + path-style
        # 一些 lancedb 版本要求 storage_options 的值为字符串
        "allow_http": "true",
        "force_path_style": "true",
    }
    db = lancedb.connect(LANCE_DB_URI, storage_options=storage_options)
    text_schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("vector", lancedb.vector(512)),
        pa.field("text", pa.string()),
        pa.field("source_uri", pa.string()),
        pa.field("doc_name", pa.string()),
        pa.field("doc_type", pa.string()),
        pa.field("file_hash", pa.string()),
    ])
    image_schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("vector", lancedb.vector(512)),
        pa.field("source_uri", pa.string()),
        pa.field("doc_name", pa.string()),
        pa.field("meta_info", pa.string()),
        pa.field("file_hash", pa.string()),
    ])
    files_schema = pa.schema([
        pa.field("file_hash", pa.string()),
        pa.field("doc_name", pa.string()),
        pa.field("doc_type", pa.string()),
        pa.field("source_uri", pa.string()),
        pa.field("file_bytes", pa.binary()),
        pa.field("text_full", pa.string()),
    ])
    tbl_text = db.create_table("text_chunks", schema=text_schema, exist_ok=True)
    tbl_image = db.create_table("image_chunks", schema=image_schema, exist_ok=True)
    tbl_files = db.create_table("files", schema=files_schema, exist_ok=True)
    # 若旧表没有 file_hash 列，无法预览整份文档，做一次性重建（仅此一次）
    schema_names = getattr(tbl_text.schema, "names", []) if hasattr(tbl_text, "schema") else []
    if "file_hash" not in schema_names:
        logger.info("text_chunks 缺少 file_hash 列，一次性重建以支持整份文档预览")
        db.drop_table("text_chunks")
        tbl_text = db.create_table("text_chunks", schema=text_schema)
    schema_names_img = getattr(tbl_image.schema, "names", []) if hasattr(tbl_image, "schema") else []
    if "file_hash" not in schema_names_img:
        logger.info("image_chunks 缺少 file_hash 列，一次性重建以支持整份文档/图片预览")
        db.drop_table("image_chunks")
        tbl_image = db.create_table("image_chunks", schema=image_schema)
    return tbl_text, tbl_image, tbl_files


def get_file_entities_table():
    """打开或创建 file_entities 表，用于存储文件-实体关系。"""
    storage_options = {
        "endpoint_url": S3_CONFIG["endpoint_url"],
        "access_key_id": S3_CONFIG["access_key_id"],
        "secret_access_key": S3_CONFIG["secret_access_key"],
        "allow_http": "true",
        "force_path_style": "true",
    }
    db = lancedb.connect(LANCE_DB_URI, storage_options=storage_options)
    entities_schema = pa.schema([
        pa.field("file_hash", pa.string()),
        pa.field("entity", pa.string()),
        pa.field("entity_type", pa.string()),
    ])
    tbl_entities = db.create_table("file_entities", schema=entities_schema, exist_ok=True)
    return tbl_entities
