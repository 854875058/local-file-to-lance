# -*- coding: utf-8 -*-
"""SQLite：文件注册、任务统计（无登录）"""

import hashlib
import sqlite3
from pathlib import Path

from config import DB_PATH


def _ensure_dir():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def init_db():
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS file_registry (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           file_hash TEXT UNIQUE NOT NULL,
           file_name TEXT,
           file_size INTEGER,
           upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS task_stats (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER,
           task_type TEXT,
           file_count INTEGER,
           success_count INTEGER,
           processing_time REAL,
           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS file_entities (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           file_hash TEXT NOT NULL,
           entity_name TEXT NOT NULL,
           entity_type TEXT,
           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.commit()
    conn.close()


def calculate_file_hash(file_path):
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def check_file_exists(file_hash):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM file_registry WHERE file_hash=?", (file_hash,))
        exists = c.fetchone() is not None
        return exists
    except Exception as e:
        import logging
        logging.error(f"检查文件是否存在失败: {e}")
        return False
    finally:
        if conn:
            conn.close()


def register_file(file_hash, file_name, file_size):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO file_registry (file_hash, file_name, file_size) VALUES (?, ?, ?)",
            (file_hash, file_name, file_size),
        )
        conn.commit()
        return True
    except Exception as e:
        import logging
        logging.warning(f"注册文件失败（可能已存在）: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_file_registry_count():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        n = conn.execute("SELECT COUNT(*) FROM file_registry").fetchone()[0]
        return n
    except Exception as e:
        import logging
        logging.error(f"获取文件注册数量失败: {e}")
        return 0
    finally:
        if conn:
            conn.close()


def get_task_stats(limit=50):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT id, user_id, task_type, file_count, success_count, processing_time, created_at "
            "FROM task_stats ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return rows
    except Exception as e:
        import logging
        logging.error(f"获取任务统计失败: {e}")
        return []
    finally:
        if conn:
            conn.close()


def delete_file_from_registry(file_hash):
    """从 SQLite file_registry 删除记录"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM file_registry WHERE file_hash=?", (file_hash,))
        c.execute("DELETE FROM file_entities WHERE file_hash=?", (file_hash,))
        conn.commit()
        return True
    except Exception as e:
        import logging
        logging.error(f"删除文件注册记录失败: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_file_entities(file_hash=None):
    """获取实体数据。file_hash 为 None 时返回全部。"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        if file_hash:
            rows = conn.execute(
                "SELECT file_hash, entity_name, entity_type FROM file_entities WHERE file_hash=?",
                (file_hash,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT file_hash, entity_name, entity_type FROM file_entities"
            ).fetchall()
        return [{"file_hash": r[0], "entity_name": r[1], "entity_type": r[2]} for r in rows]
    except Exception as e:
        import logging
        logging.error(f"获取实体数据失败: {e}")
        return []
    finally:
        if conn:
            conn.close()


def insert_file_entities(file_hash, entities):
    """批量插入实体。entities: list of (entity_name, entity_type)"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.executemany(
            "INSERT INTO file_entities (file_hash, entity_name, entity_type) VALUES (?, ?, ?)",
            [(file_hash, name, etype) for name, etype in entities],
        )
        conn.commit()
    except Exception as e:
        import logging
        logging.error(f"插入实体数据失败: {e}")
    finally:
        if conn:
            conn.close()


def insert_task_stat(task_type, file_count, success_count, processing_time, user_id=0):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO task_stats (user_id, task_type, file_count, success_count, processing_time) VALUES (?, ?, ?, ?, ?)",
            (user_id, task_type, file_count, success_count, processing_time),
        )
        conn.commit()
    except Exception as e:
        import logging
        logging.error(f"插入任务统计失败: {e}")
    finally:
        if conn:
            conn.close()
