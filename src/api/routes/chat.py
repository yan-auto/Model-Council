"""Chat API —— SSE 流式聊天端点"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from src.data.models import (
    MessageCreate,
    MessageRole,
    ConversationCreate,
    StreamEvent,
    StreamEventType,
)
from src.data.repositories import conversation_repo, message_repo
from src.core.command_parser import parse_command, CommandType
from src.core.agent_router import resolve_agent
from src.core.context_builder import build_messages
from src.services.memory_service import get_context_messages
from src.services.model_router import get_default_adapter

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/conversations")
async def create_conversation(data: ConversationCreate | None = None):
    """创建新对话"""
    if data is None:
        data = ConversationCreate()
    conv = await conversation_repo.create_conversation(data)
    return {"id": conv.id, "title": conv.title}


@router.get("/conversations")
async def list_conversations(limit: int = 50, offset: int = 0):
    """列出所有对话"""
    convs = await conversation_repo.list_conversations(limit, offset)
    return [
        {"id": c.id, "title": c.title, "status": c.status.value, "updated_at": c.updated_at}
        for c in convs
    ]


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    """获取对话详情 + 消息"""
    conv = await conversation_repo.get_conversation(conv_id)
    if conv is None:
        return {"error": "对话不存在"}, 404
    messages = await message_repo.get_messages(conv_id)
    return {
        "id": conv.id,
        "title": conv.title,
        "status": conv.status.value,
        "messages": [
            {
                "id": m.id,
                "role": m.role.value,
                "agent_name": m.agent_name,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in messages
        ],
    }


@router.delete("/conversations/{conv_id}")
async def archive_conversation(conv_id: str):
    """归档对话"""
    ok = await conversation_repo.archive_conversation(conv_id)
    if not ok:
        return {"error": "对话不存在"}
    return {"status": "archived"}


@router.post("/chat")
async def chat(data: MessageCreate):
    """SSE 流式聊天"""
    conv_id = data.conversation_id if hasattr(data, "conversation_id") else None

    # 确保有对话
    if conv_id:
        conv = await conversation_repo.get_conversation(conv_id)
        if conv is None:
            conv_id = None

    if not conv_id:
        from src.data.models import ConversationCreate
        conv = await conversation_repo.create_conversation(ConversationCreate())
        conv_id = conv.id

    # 解析指令
    try:
        cmd = parse_command(data.content)
    except ValueError as e:
        return {"error": str(e)}

    # 如果是讨论模式，返回讨论入口（走 WebSocket）
    if cmd.type == CommandType.DISCUSS:
        return {
            "mode": "discussion",
            "conversation_id": conv_id,
            "topic": cmd.content,
            "message": "讨论模式请使用 WebSocket: ws://host/ws/discuss?token=xxx",
        }

    # 确定角色
    agent_name = resolve_agent(cmd)

    # 保存用户消息
    await message_repo.create_message(
        conversation_id=conv_id,
        role=MessageRole.USER,
        content=data.content,
    )

    # 获取上下文
    history = await get_context_messages(conv_id)
    messages = build_messages(agent_name, history)

    # 获取适配器
    adapter = get_default_adapter()
    if adapter is None:
        return {"error": "没有可用的 LLM 适配器，请检查 .env 配置"}

    # 流式返回
    from src.services.model_router import get_provider_config
    provider_cfg = get_provider_config("openai")

    async def event_generator():
        collected_tokens = []
        try:
            async for chunk in adapter.chat_stream(
                messages,
                model=provider_cfg["model"],
                temperature=provider_cfg["temperature"],
                max_tokens=provider_cfg["max_tokens"],
            ):
                if chunk.token:
                    collected_tokens.append(chunk.token)
                    event = StreamEvent(
                        type=StreamEventType.TOKEN,
                        data={"token": chunk.token},
                        agent_name=agent_name,
                    )
                    yield {
                        "event": "message",
                        "data": event.model_dump_json(),
                    }

                if chunk.finish_reason:
                    # 完整消息，存库
                    full_content = "".join(collected_tokens)
                    await message_repo.create_message(
                        conversation_id=conv_id,
                        role=MessageRole.ASSISTANT,
                        content=full_content,
                        agent_name=agent_name,
                    )
                    event = StreamEvent(
                        type=StreamEventType.MESSAGE_DONE,
                        data={"content": full_content, "conversation_id": conv_id},
                        agent_name=agent_name,
                    )
                    yield {
                        "event": "done",
                        "data": event.model_dump_json(),
                    }
        except Exception as e:
            event = StreamEvent(
                type=StreamEventType.ERROR,
                data={"error": str(e)},
            )
            yield {
                "event": "error",
                "data": event.model_dump_json(),
            }

    return EventSourceResponse(event_generator())
