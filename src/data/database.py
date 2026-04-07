"""SQLite 异步连接管理 + 数据库初始化"""

from __future__ import annotations

from pathlib import Path

import aiosqlite

from src.config import get_settings

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """获取数据库连接单例"""
    global _db
    if _db is None:
        settings = get_settings()
        db_path = Path(settings.data.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _db = await aiosqlite.connect(str(db_path))
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def close_db() -> None:
    """关闭数据库连接"""
    global _db
    if _db is not None:
        await _db.close()
        _db = None


async def reset_db() -> None:
    """重置数据库（用于测试）"""
    global _db
    if _db is not None:
        await _db.close()
    import tempfile, os
    # 使用临时文件
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    _db = await aiosqlite.connect(tmp.name)
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA journal_mode=WAL")
    await _db.execute("PRAGMA foreign_keys=ON")
    await init_db()


# ── 迁移 ──────────────────────────────────────────

MIGRATIONS = [
    # v1: 初始表结构
    """
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL DEFAULT '新对话',
        status TEXT NOT NULL DEFAULT 'active',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        agent_name TEXT,
        content TEXT NOT NULL,
        created_at REAL NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_messages_conversation
        ON messages(conversation_id, created_at);
    """,
]


async def init_db() -> None:
    """运行全部迁移"""
    db = await get_db()
    # 创建迁移追踪表
    await db.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            version INTEGER PRIMARY KEY,
            applied_at REAL NOT NULL
        )
    """)
    # 查询已执行的迁移
    cursor = await db.execute("SELECT version FROM _migrations")
    applied = {row[0] for row in await cursor.fetchall()}

    import time
    for i, sql in enumerate(MIGRATIONS, start=1):
        if i not in applied:
            await db.executescript(sql)
            await db.execute(
                "INSERT INTO _migrations (version, applied_at) VALUES (?, ?)",
                (i, time.time()),
            )
            await db.commit()
