"""消息 Repository"""

from __future__ import annotations

import time

from src.data.database import get_db
from src.data.models import Message, MessageRole


async def create_message(
    conversation_id: str,
    role: MessageRole,
    content: str,
    agent_name: str | None = None,
    image_data: str | None = None,
) -> Message:
    db = await get_db()
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        agent_name=agent_name,
        content=content,
        image_data=image_data,
    )
    await db.execute(
        "INSERT INTO messages (id, conversation_id, role, agent_name, content, image_data, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (msg.id, msg.conversation_id, msg.role.value, msg.agent_name, msg.content, msg.image_data, msg.created_at),
    )
    # 更新对话的 updated_at
    await db.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (time.time(), conversation_id),
    )
    await db.commit()
    return msg


async def get_messages(
    conversation_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[Message]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, conversation_id, role, agent_name, content, image_data, created_at "
        "FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
        (conversation_id, limit, offset),
    )
    rows = await cursor.fetchall()
    return [
        Message(
            id=r["id"],
            conversation_id=r["conversation_id"],
            role=MessageRole(r["role"]),
            agent_name=r["agent_name"],
            content=r["content"],
            image_data=r["image_data"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


async def get_recent_messages(
    conversation_id: str,
    limit: int = 50,
) -> list[Message]:
    """获取最近 N 条消息（按时间正序）"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, conversation_id, role, agent_name, content, image_data, created_at "
        "FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?",
        (conversation_id, limit),
    )
    rows = await cursor.fetchall()
    # 反转回正序
    return list(reversed([
        Message(
            id=r["id"],
            conversation_id=r["conversation_id"],
            role=MessageRole(r["role"]),
            agent_name=r["agent_name"],
            content=r["content"],
            image_data=r["image_data"],
            created_at=r["created_at"],
        )
        for r in rows
    ]))


async def count_messages(conversation_id: str) -> int:
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
        (conversation_id,),
    )
    row = await cursor.fetchone()
    return row[0]
