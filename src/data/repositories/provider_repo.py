"""Provider Repository"""

from __future__ import annotations

import time
import httpx

from src.data.database import get_db
from src.data.models import Provider, ProviderCreate, ProviderUpdate, ProviderType


async def create_provider(data: ProviderCreate) -> Provider:
    db = await get_db()
    p = Provider(name=data.name, provider_type=data.provider_type,
                 api_key=data.api_key, base_url=data.base_url, group_id=data.group_id)
    await db.execute(
        "INSERT INTO providers (id, name, provider_type, api_key, base_url, group_id, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (p.id, p.name, p.provider_type.value, p.api_key, p.base_url, p.group_id, p.status, p.created_at, p.updated_at),
    )
    await db.commit()
    return p


async def get_provider(provider_id: str) -> Provider | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM providers WHERE id = ?", (provider_id,)
    )
    row = await cursor.fetchone()
    return _row_to_provider(row) if row else None


async def list_providers(status: str | None = None) -> list[Provider]:
    db = await get_db()
    if status:
        cursor = await db.execute(
            "SELECT * FROM providers WHERE status = ? ORDER BY created_at ASC", (status,)
        )
    else:
        cursor = await db.execute("SELECT * FROM providers ORDER BY created_at ASC")
    rows = await cursor.fetchall()
    return [_row_to_provider(r) for r in rows]


async def update_provider(provider_id: str, data: ProviderUpdate) -> Provider | None:
    db = await get_db()
    existing = await get_provider(provider_id)
    if not existing:
        return None
    updates = {}
    if data.name is not None:
        updates["name"] = data.name
    if data.api_key is not None:
        updates["api_key"] = data.api_key
    if data.base_url is not None:
        updates["base_url"] = data.base_url
    if data.group_id is not None:
        updates["group_id"] = data.group_id
    if not updates:
        return existing
    updates["updated_at"] = time.time()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    await db.execute(
        f"UPDATE providers SET {set_clause} WHERE id = ?",
        (*updates.values(), provider_id)
    )
    await db.commit()
    return await get_provider(provider_id)


async def delete_provider(provider_id: str) -> bool:
    db = await get_db()
    cursor = await db.execute("DELETE FROM providers WHERE id = ?", (provider_id,))
    await db.commit()
    return cursor.rowcount > 0


async def validate_provider(provider: Provider) -> bool:
    """测试供应商连接是否有效"""
    if not provider.api_key:
        return False
    try:
        if provider.provider_type == ProviderType.ANTHROPIC:
            url = f"{provider.base_url}/v1/messages"
            headers = {"x-api-key": provider.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
            body = {"model": "claude-3-5-haiku-20240307", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}
        else:
            url = f"{provider.base_url}/chat/completions"
            headers = {"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json"}
            body = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=body, headers=headers)
            return resp.status_code < 500
    except Exception:
        return False


def _row_to_provider(row) -> Provider:
    return Provider(
        id=row["id"], name=row["name"],
        provider_type=ProviderType(row["provider_type"]),
        api_key=row["api_key"], base_url=row["base_url"],
        group_id=row["group_id"] or "", status=row["status"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )
