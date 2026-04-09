"""Profile API —— 用户档案 + 待办管理"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.data.models import UserProfileUpdate
from src.data.repositories import memory_repo
from src.services import memory_service

router = APIRouter(prefix="/api", tags=["memory"])


# ── 用户档案 ──────────────────────────────────

@router.get("/profile")
async def api_get_profile():
    """获取用户档案"""
    profile = await memory_service.get_profile()
    return profile or {"name": "", "background": "", "goals": ""}


@router.put("/profile")
async def api_update_profile(data: UserProfileUpdate):
    """更新用户档案"""
    update_data = data.model_dump(exclude_none=True)
    profile = await memory_service.update_profile(update_data)
    return profile


# ── 待��承诺 ──────────────────────────────────

@router.get("/actions")
async def api_list_actions(status: str = ""):
    """获取待办列表"""
    if status == "pending":
        actions = await memory_service.get_pending_actions()
    else:
        actions = await memory_repo.get_all_actions()
    return {"actions": actions}


@router.put("/actions/{action_id}")
async def api_update_action(action_id: str, status: str = "done"):
    """更新待办状态"""
    if status not in ("done", "skipped"):
        return JSONResponse(status_code=400, content={"error": "状态必须是 done 或 skipped"})
    if status == "done":
        await memory_service.complete_action(action_id)
    else:
        await memory_service.skip_action(action_id)
    return {"status": "ok"}


@router.delete("/actions/{action_id}")
async def api_delete_action(action_id: str):
    """删除待办"""
    await memory_repo.delete_action(action_id)
    return {"status": "deleted"}


# ── 角色记忆 ──────────────────────────────────

@router.get("/agents/{agent_name}/memory")
async def api_get_agent_memory(agent_name: str):
    """获取某角色的记忆"""
    memories = await memory_repo.get_agent_memories(agent_name)
    return {"memories": memories}


@router.get("/summaries")
async def api_list_summaries(limit: int = 10):
    """获取对话摘要列表"""
    summaries = await memory_repo.get_summaries(limit)
    return {"summaries": summaries}


@router.post("/conversations/{conv_id}/summarize")
async def api_summarize_conversation(conv_id: str):
    """手动触发对话摘要"""
    from src.data.repositories.message_repo import get_messages
    messages = await get_messages(conv_id)
    summary_id = await memory_service.save_conversation_summary(conv_id, messages)
    if not summary_id:
        return JSONResponse(status_code=400, content={"error": "无法生成摘要"})
    return {"id": summary_id}
