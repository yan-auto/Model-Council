"""Model Repository"""

from __future__ import annotations

import time

from src.data.database import get_db
from src.data.models import Model, ModelCreate


async def create_model(data: ModelCreate) -> Model:
    db = await get_db()
    display = data.display_name or data.model_name
    m = Model(provider_id=data.provider_id, model_name=data.model_name, display_name=display)
    await db.execute(
        "INSERT INTO models (id, provider_id, model_name, display_name, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (m.id, m.provider_id, m.model_name, m.display_name, m.status, m.created_at, m.updated_at),
    )
    await db.commit()
    return m


async def get_model(model_id: str) -> Model | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM models WHERE id = ?", (model_id,))
    row = await cursor.fetchone()
    return _row_to_model(row) if row else None


async def list_models(provider_id: str | None = None, status: str | None = None) -> list[Model]:
    db = await get_db()
    conditions = []
    params = []
    if provider_id:
        conditions.append("provider_id = ?")
        params.append(provider_id)
    if status:
        conditions.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    cursor = await db.execute(
        f"SELECT * FROM models {where} ORDER BY created_at ASC", params
    )
    rows = await cursor.fetchall()
    return [_row_to_model(r) for r in rows]


async def get_model_by_name(model_name: str) -> Model | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM models WHERE model_name = ?", (model_name,))
    row = await cursor.fetchone()
    return _row_to_model(row) if row else None


async def delete_model(model_id: str) -> bool:
    db = await get_db()
    cursor = await db.execute("DELETE FROM models WHERE id = ?", (model_id,))
    await db.commit()
    return cursor.rowcount > 0


def _row_to_model(row) -> Model:
    return Model(
        id=row["id"], provider_id=row["provider_id"],
        model_name=row["model_name"], display_name=row["display_name"],
        status=row["status"], created_at=row["created_at"], updated_at=row["updated_at"],
    )
