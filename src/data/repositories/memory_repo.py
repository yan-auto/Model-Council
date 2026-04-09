"""Memory Repository —— 记忆数据访问层"""

from __future__ import annotations

import json
import time

from src.data.database import get_db


# ── 用户档案 ──────────────────────────────────

async def get_profile() -> dict | None:
    """获取用户档案（单行）"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM user_profile WHERE id = 'default'"
    )
    row = await cursor.fetchone()
    if not row:
        return None
    return dict(row)


async def upsert_profile(data: dict) -> dict:
    """创建或更新用户档案"""
    db = await get_db()
    now = time.time()

    # 确保 default 行存在
    existing = await get_profile()
    if existing:
        # 只更新提供的字段
        fields = {k: v for k, v in data.items() if v is not None}
        if fields:
            fields["updated_at"] = now
            if "current_projects" in fields and isinstance(fields["current_projects"], list):
                fields["current_projects"] = json.dumps(fields["current_projects"])
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            values = list(fields.values())
            await db.execute(
                f"UPDATE user_profile SET {set_clause} WHERE id = 'default'",
                values,
            )
            await db.commit()
    else:
        # 初始化
        defaults = {
            "id": "default",
            "name": data.get("name", ""),
            "background": data.get("background", ""),
            "goals": data.get("goals", ""),
            "constraints": data.get("constraints", ""),
            "financial_baseline": data.get("financial_baseline", ""),
            "current_projects": json.dumps(data.get("current_projects", [])),
            "created_at": now,
            "updated_at": now,
        }
        keys = list(defaults.keys())
        await db.execute(
            f"INSERT INTO user_profile ({', '.join(keys)}) VALUES ({', '.join('?' * len(keys))})",
            list(defaults.values()),
        )
        await db.commit()

    return (await get_profile()) or {}


# ── 对话摘要 ──────────────────────────────────

async def create_summary(
    conversation_id: str,
    content: str,
    key_decisions: list[str] | None = None,
    action_items: list[str] | None = None,
) -> str:
    """创建对话摘要"""
    db = await get_db()
    import uuid
    summary_id = uuid.uuid4().hex[:16]
    now = time.time()
    await db.execute(
        """INSERT INTO conversation_summaries
           (id, conversation_id, content, key_decisions, action_items, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            summary_id,
            conversation_id,
            content,
            json.dumps(key_decisions or []),
            json.dumps(action_items or []),
            now,
        ),
    )
    await db.commit()
    return summary_id


async def get_summary(conversation_id: str) -> dict | None:
    """获取指定对话的摘要"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM conversation_summaries WHERE conversation_id = ?",
        (conversation_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return None
    return dict(row)


async def get_summaries(limit: int = 10) -> list[dict]:
    """获取最近的 N 条摘要"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM conversation_summaries ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    return [dict(row) for row in await cursor.fetchall()]


async def search_summaries(query: str, limit: int = 5) -> list[dict]:
    """简单关键词匹配搜索摘要"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM conversation_summaries
           WHERE content LIKE ? OR key_decisions LIKE ?
           ORDER BY created_at DESC LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit),
    )
    return [dict(row) for row in await cursor.fetchall()]


# ── 角色记忆 ──────────────────────────────────

async def upsert_agent_memory(
    agent_name: str,
    memory_type: str,
    key: str,
    value: str,
) -> str:
    """创建或更新角色记忆（key 相同则覆盖）"""
    db = await get_db()
    now = time.time()
    import uuid

    existing = await db.execute(
        "SELECT id FROM agent_memories WHERE agent_name = ? AND memory_type = ? AND key = ?",
        (agent_name, memory_type, key),
    )
    row = await existing.fetchone()

    if row:
        await db.execute(
            """UPDATE agent_memories SET value = ?, updated_at = ?
               WHERE agent_name = ? AND memory_type = ? AND key = ?""",
            (value, now, agent_name, memory_type, key),
        )
        await db.commit()
        return row[0]
    else:
        mem_id = uuid.uuid4().hex[:16]
        await db.execute(
            """INSERT INTO agent_memories
               (id, agent_name, memory_type, key, value, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (mem_id, agent_name, memory_type, key, value, now, now),
        )
        await db.commit()
        return mem_id


async def get_agent_memories(agent_name: str) -> list[dict]:
    """获取某角色的所有记忆"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM agent_memories WHERE agent_name = ? ORDER BY updated_at DESC",
        (agent_name,),
    )
    return [dict(row) for row in await cursor.fetchall()]


async def delete_agent_memory(mem_id: str) -> bool:
    """删除单条记忆"""
    db = await get_db()
    await db.execute("DELETE FROM agent_memories WHERE id = ?", (mem_id,))
    await db.commit()
    return True


# ── 待办承诺 ──────────────────────────────────

async def create_action(
    conversation_id: str | None,
    agent_name: str,
    content: str,
) -> str:
    """创建待办承诺"""
    db = await get_db()
    import uuid
    action_id = uuid.uuid4().hex[:16]
    now = time.time()
    await db.execute(
        """INSERT INTO action_items
           (id, conversation_id, agent_name, content, status, created_at)
           VALUES (?, ?, ?, ?, 'pending', ?)""",
        (action_id, conversation_id, agent_name, content, now),
    )
    await db.commit()
    return action_id


async def get_pending_actions(limit: int = 20) -> list[dict]:
    """获取未完成的待办"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM action_items
           WHERE status = 'pending'
           ORDER BY created_at DESC LIMIT ?""",
        (limit,),
    )
    return [dict(row) for row in await cursor.fetchall()]


async def get_all_actions(limit: int = 50) -> list[dict]:
    """获取所有待办"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM action_items ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    return [dict(row) for row in await cursor.fetchall()]


async def update_action_status(action_id: str, status: str) -> bool:
    """更新待办状态"""
    db = await get_db()
    now = time.time() if status == "done" else None
    await db.execute(
        """UPDATE action_items
           SET status = ?, completed_at = ?
           WHERE id = ?""",
        (status, now, action_id),
    )
    await db.commit()
    return True


async def delete_action(action_id: str) -> bool:
    """删除待办"""
    db = await get_db()
    await db.execute("DELETE FROM action_items WHERE id = ?", (action_id,))
    await db.commit()
    return True
