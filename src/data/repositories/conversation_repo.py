"""对话 Repository"""

from __future__ import annotations

from src.data.database import get_db
from src.data.models import Conversation, ConversationCreate, ConversationStatus


async def create_conversation(data: ConversationCreate) -> Conversation:
    db = await get_db()
    conv = Conversation(title=data.title)
    await db.execute(
        "INSERT INTO conversations (id, title, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (conv.id, conv.title, conv.status.value, conv.created_at, conv.updated_at),
    )
    await db.commit()
    return conv


async def get_conversation(conv_id: str) -> Conversation | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, title, status, created_at, updated_at FROM conversations WHERE id = ?",
        (conv_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return Conversation(
        id=row["id"],
        title=row["title"],
        status=ConversationStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


async def list_conversations(limit: int = 50, offset: int = 0, status: str | None = None) -> list[Conversation]:
    """列出对话，支持按 status 过滤"""
    db = await get_db()
    if status:
        cursor = await db.execute(
            "SELECT id, title, status, created_at, updated_at "
            "FROM conversations WHERE status = ? "
            "ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (status, limit, offset),
        )
    else:
        cursor = await db.execute(
            "SELECT id, title, status, created_at, updated_at "
            "FROM conversations ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
    rows = await cursor.fetchall()
    return [
        Conversation(
            id=r["id"],
            title=r["title"],
            status=ConversationStatus(r["status"]),
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


async def archive_conversation(conv_id: str) -> bool:
    db = await get_db()
    cursor = await db.execute(
        "UPDATE conversations SET status = ?, updated_at = ? WHERE id = ?",
        (ConversationStatus.ARCHIVED.value, __import__("time").time(), conv_id),
    )
    await db.commit()
    return cursor.rowcount > 0
