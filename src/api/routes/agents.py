"""Agent API —— 角色管理（数据库版）"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.data.models import AgentCreate, AgentUpdate, AgentModelUpdate
from src.data.repositories.agent_repo import (
    create_agent, get_agent, get_agent_by_name, list_agents,
    update_agent, update_agent_model, delete_agent,
)
from src.data.repositories.model_repo import list_models

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/agents")
async def api_list_agents():
    """获取所有角色（带模型信息）"""
    agents = await list_agents(status="active")
    result = []
    for a in agents:
        model_info = None
        if a.model_id:
            from src.data.repositories.model_repo import get_model
            m = await get_model(a.model_id)
            if m:
                model_info = {"id": m.id, "model_name": m.model_name, "display_name": m.display_name}
        result.append({
            "id": a.id,
            "name": a.name,
            "display_name": a.display_name,
            "description": a.description,
            "system_prompt": a.system_prompt,
            "personality_tone": a.personality_tone,
            "personality_traits": a.personality_traits,
            "personality_constraints": a.personality_constraints,
            "model": model_info,
        })
    return {"agents": result}


@router.get("/agents/simple")
async def api_list_agents_simple():
    """简化版角色列表（用于选择器）"""
    agents = await list_agents(status="active")
    return {
        "agents": [
            {"name": a.name, "description": a.description, "display_name": a.display_name}
            for a in agents
        ]
    }


@router.post("/agents")
async def api_create_agent(data: AgentCreate):
    """创建角色"""
    existing = await get_agent_by_name(data.name)
    if existing:
        return JSONResponse(status_code=400, content={"error": f"角色 {data.name} 已存在"})
    a = await create_agent(data)
    return {"id": a.id, "name": a.name}


@router.get("/agents/{agent_id}")
async def api_get_agent(agent_id: str):
    """获取角色详情"""
    a = await get_agent(agent_id)
    if not a:
        return JSONResponse(status_code=404, content={"error": "角色不存在"})
    return _agent_response(a)


@router.put("/agents/{agent_id}")
async def api_update_agent(agent_id: str, data: AgentUpdate):
    """更新角色"""
    a = await update_agent(agent_id, data)
    if not a:
        return JSONResponse(status_code=404, content={"error": "角色不存在"})
    return _agent_response(a)


@router.put("/agents/{agent_id}/model")
async def api_update_agent_model(agent_id: str, data: AgentModelUpdate):
    """单独给角色换模型"""
    a = await update_agent_model(agent_id, data.model_id)
    if not a:
        return JSONResponse(status_code=404, content={"error": "角色不存在"})
    model_info = None
    if a.model_id:
        from src.data.repositories.model_repo import get_model
        m = await get_model(a.model_id)
        if m:
            model_info = {"id": m.id, "model_name": m.model_name, "display_name": m.display_name}
    return {"id": a.id, "name": a.name, "model": model_info}


@router.delete("/agents/{agent_id}")
async def api_delete_agent(agent_id: str):
    """删除角色"""
    ok = await delete_agent(agent_id)
    if not ok:
        return JSONResponse(status_code=404, content={"error": "角色不存在"})
    return {"status": "deleted"}


@router.get("/models")
async def api_list_all_models():
    """获取所有可用的模型（跨所有供应商）"""
    models = await list_models(status="active")
    return {
        "models": [
            {
                "id": m.id,
                "provider_id": m.provider_id,
                "model_name": m.model_name,
                "display_name": m.display_name,
            }
            for m in models
        ]
    }


def _agent_response(a) -> dict:
    return {
        "id": a.id,
        "name": a.name,
        "display_name": a.display_name,
        "description": a.description,
        "system_prompt": a.system_prompt,
        "personality_tone": a.personality_tone,
        "personality_traits": a.personality_traits,
        "personality_constraints": a.personality_constraints,
        "model_id": a.model_id,
    }
