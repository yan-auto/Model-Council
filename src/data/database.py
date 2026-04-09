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
    # v2: 供应商、模型、角色表
    """
    CREATE TABLE IF NOT EXISTS providers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        provider_type TEXT NOT NULL DEFAULT 'openai_compatible',
        api_key TEXT NOT NULL DEFAULT '',
        base_url TEXT NOT NULL DEFAULT '',
        group_id TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'active',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS models (
        id TEXT PRIMARY KEY,
        provider_id TEXT NOT NULL,
        model_name TEXT NOT NULL,
        display_name TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'active',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL DEFAULT '',
        description TEXT NOT NULL DEFAULT '',
        system_prompt TEXT NOT NULL DEFAULT '',
        model_id TEXT,
        personality_tone TEXT DEFAULT '',
        personality_traits TEXT DEFAULT '[]',
        personality_constraints TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'active',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
    );

    CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider_id);
    CREATE INDEX IF NOT EXISTS idx_agents_model ON agents(model_id);
    """,
    # v3: 记忆系统（用户档案、对话摘要、角色记忆、待办承诺）
    """
    CREATE TABLE IF NOT EXISTS user_profile (
        id TEXT PRIMARY KEY DEFAULT 'default',
        name TEXT NOT NULL DEFAULT '',
        background TEXT NOT NULL DEFAULT '',
        goals TEXT NOT NULL DEFAULT '',
        constraints TEXT NOT NULL DEFAULT '',
        financial_baseline TEXT NOT NULL DEFAULT '',
        current_projects TEXT NOT NULL DEFAULT '[]',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS conversation_summaries (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        content TEXT NOT NULL DEFAULT '',
        key_decisions TEXT NOT NULL DEFAULT '[]',
        action_items TEXT NOT NULL DEFAULT '[]',
        created_at REAL NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS agent_memories (
        id TEXT PRIMARY KEY,
        agent_name TEXT NOT NULL,
        memory_type TEXT NOT NULL DEFAULT 'fact',
        key TEXT NOT NULL,
        value TEXT NOT NULL DEFAULT '',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        UNIQUE(agent_name, memory_type, key)
    );

    CREATE TABLE IF NOT EXISTS action_items (
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        agent_name TEXT NOT NULL,
        content TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at REAL NOT NULL,
        completed_at REAL
    );

    CREATE INDEX IF NOT EXISTS idx_summaries_conv ON conversation_summaries(conversation_id);
    CREATE INDEX IF NOT EXISTS idx_agent_memories_name ON agent_memories(agent_name);
    CREATE INDEX IF NOT EXISTS idx_actions_status ON action_items(status);
    """,
    # v4: messages 支持图片（在 init_db 中特殊处理）
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
            if i == 4:
                # v4: 安全添加 image_data 列（已存在则跳过）
                cursor2 = await db.execute("PRAGMA table_info(messages)")
                cols = {row[1] for row in await cursor2.fetchall()}
                if "image_data" not in cols:
                    await db.execute("ALTER TABLE messages ADD COLUMN image_data TEXT")
            else:
                await db.executescript(sql)
            await db.execute(
                "INSERT INTO _migrations (version, applied_at) VALUES (?, ?)",
                (i, time.time()),
            )
            await db.commit()
