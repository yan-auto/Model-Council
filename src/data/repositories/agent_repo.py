"""Agent DB Repository —— 从数据库管理角色"""

from __future__ import annotations

import json
import time

from src.data.database import get_db
from src.data.models import Agent, AgentCreate, AgentUpdate


async def create_agent(data: AgentCreate) -> Agent:
    db = await get_db()
    a = Agent(
        name=data.name, display_name=data.display_name or data.name,
        description=data.description, system_prompt=data.system_prompt,
        model_id=data.model_id, personality_tone=data.personality_tone,
        personality_traits=data.personality_traits,
        personality_constraints=data.personality_constraints,
    )
    await db.execute(
        "INSERT INTO agents (id, name, display_name, description, system_prompt, model_id, "
        "personality_tone, personality_traits, personality_constraints, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (a.id, a.name, a.display_name, a.description, a.system_prompt, a.model_id,
         a.personality_tone, json.dumps(a.personality_traits, ensure_ascii=False),
         a.personality_constraints, a.status, a.created_at, a.updated_at),
    )
    await db.commit()
    return a


async def get_agent(agent_id: str) -> Agent | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
    row = await cursor.fetchone()
    return _row_to_agent(row) if row else None


async def get_agent_by_name(name: str) -> Agent | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM agents WHERE name = ?", (name,))
    row = await cursor.fetchone()
    return _row_to_agent(row) if row else None


async def list_agents(status: str | None = None) -> list[Agent]:
    db = await get_db()
    if status:
        cursor = await db.execute("SELECT * FROM agents WHERE status = ? ORDER BY created_at ASC", (status,))
    else:
        cursor = await db.execute("SELECT * FROM agents ORDER BY created_at ASC")
    rows = await cursor.fetchall()
    return [_row_to_agent(r) for r in rows]


async def update_agent(agent_id: str, data: AgentUpdate) -> Agent | None:
    db = await get_db()
    existing = await get_agent(agent_id)
    if not existing:
        return None
    updates: dict = {}
    if data.display_name is not None:
        updates["display_name"] = data.display_name
    if data.description is not None:
        updates["description"] = data.description
    if data.system_prompt is not None:
        updates["system_prompt"] = data.system_prompt
    if data.model_id is not None:
        updates["model_id"] = data.model_id
    if data.personality_tone is not None:
        updates["personality_tone"] = data.personality_tone
    if data.personality_traits is not None:
        updates["personality_traits"] = json.dumps(data.personality_traits, ensure_ascii=False)
    if data.personality_constraints is not None:
        updates["personality_constraints"] = data.personality_constraints
    if not updates:
        return existing
    updates["updated_at"] = time.time()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    await db.execute(
        f"UPDATE agents SET {set_clause} WHERE id = ?",
        (*updates.values(), agent_id)
    )
    await db.commit()
    return await get_agent(agent_id)


async def update_agent_model(agent_id: str, model_id: str | None) -> Agent | None:
    db = await get_db()
    await db.execute(
        "UPDATE agents SET model_id = ?, updated_at = ? WHERE id = ?",
        (model_id, time.time(), agent_id)
    )
    await db.commit()
    return await get_agent(agent_id)


async def delete_agent(agent_id: str) -> bool:
    db = await get_db()
    cursor = await db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
    await db.commit()
    return cursor.rowcount > 0


async def count_agents() -> int:
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) FROM agents")
    row = await cursor.fetchone()
    return row[0]


def _row_to_agent(row) -> Agent:
    traits = []
    raw = row["personality_traits"]
    if raw:
        try:
            traits = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            traits = []
    return Agent(
        id=row["id"], name=row["name"], display_name=row["display_name"],
        description=row["description"], system_prompt=row["system_prompt"],
        model_id=row["model_id"], personality_tone=row["personality_tone"] or "",
        personality_traits=traits,
        personality_constraints=row["personality_constraints"] or "",
        status=row["status"], created_at=row["created_at"], updated_at=row["updated_at"],
    )
