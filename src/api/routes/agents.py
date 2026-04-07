"""Agents API —— 角色列表端点"""

from __future__ import annotations

from fastapi import APIRouter

from src.core.agent_loader import list_agent_infos

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/agents")
async def get_agents():
    """返回所有可用角色"""
    agents = list_agent_infos()
    return {"agents": [{"name": a.name, "description": a.description} for a in agents]}
