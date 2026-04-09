"""Chat API —— SSE 流式聊天端点"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from src.data.models import (
    MessageCreate,
    MessageRole,
    ConversationCreate,
    StreamEvent,
    StreamEventType,
)
from src.adapters.base import ChatMessage
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
async def list_conversations(limit: int = 50, offset: int = 0, status: str | None = None):
    """列出对话，支持按 status 过滤（active / archived）"""
    convs = await conversation_repo.list_conversations(limit, offset, status)
    return [
        {"id": c.id, "title": c.title, "status": c.status.value, "updated_at": c.updated_at}
        for c in convs
    ]


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    """获取对话详情 + 消息"""
    conv = await conversation_repo.get_conversation(conv_id)
    if conv is None:
        return JSONResponse(status_code=404, content={"error": "对话不存在"})
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
                "image_data": m.image_data,
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
        return JSONResponse(status_code=404, content={"error": "对话不存在"})
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
        conv = await conversation_repo.create_conversation(ConversationCreate())
        conv_id = conv.id

    # 解析指令
    try:
        cmd = parse_command(data.content)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    # ── 指令分发 ──────────────────────────────

    if cmd.type == CommandType.DISCUSS:
        return JSONResponse(content={
            "mode": "discussion",
            "conversation_id": conv_id,
            "topic": cmd.content,
            "message": "讨论模式请使用 WebSocket: ws://host/ws/discuss",
        })

    if cmd.type == CommandType.STOP:
        return JSONResponse(content={"status": "stopped", "message": "讨论已停止"})

    if cmd.type == CommandType.ADD_AGENT:
        return await _handle_add_agent(cmd)

    if cmd.type == CommandType.REMOVE_AGENT:
        return await _handle_remove_agent(cmd)

    if cmd.type == CommandType.LIST_AGENTS:
        return await _handle_list_agents()

    if cmd.type == CommandType.MEMORY:
        return await _handle_memory(conv_id)

    if cmd.type == CommandType.SAVE:
        return await _handle_save(conv_id)

    if cmd.type == CommandType.CHANGE_MODEL:
        return await _handle_change_model(cmd)

    # ── @all：依次发给所有活跃角色 ─────────────
    if cmd.type == CommandType.CHAT_ALL:
        return await _handle_chat_all(cmd, conv_id, image_data=data.image_data)

    # ── 普通聊天（单角色） ──────────────────────
    return await _handle_single_chat(cmd, conv_id, data.content, image_data=data.image_data)


async def _handle_single_chat(cmd, conv_id, raw_content, image_data=None):
    """单角色聊天"""
    agent_name = await resolve_agent(cmd)

    # 保存用户消息
    await message_repo.create_message(
        conversation_id=conv_id,
        role=MessageRole.USER,
        content=raw_content,
        image_data=image_data,
    )

    # 获取上下文
    history = await get_context_messages(conv_id)

    # 构建当前用户消息（含可选图片）
    if image_data:
        user_msg_content: str | list = [
            {"type": "text", "text": raw_content},
            {"type": "image_url", "image_url": {"url": image_data}},
        ]
    else:
        user_msg_content = raw_content

    messages = await build_messages(agent_name, history)
    # 将当前用户消息追加进去（build_messages 不含当前这条）
    messages.append(ChatMessage(role="user", content=user_msg_content))

    # 获取适配器
    from src.services.model_router import get_adapter_for_agent, get_default_model_config
    adapter, model_cfg = await get_adapter_for_agent(agent_name)
    if adapter is None:
        adapter = await get_default_adapter()
    if adapter is None:
        return JSONResponse(status_code=503, content={"error": "没有可用的 LLM 适配器，请在设置中配置供应商"})

    default_cfg = get_default_model_config()
    model_name = model_cfg["model"] if model_cfg else default_cfg.get("model", "")
    temperature = default_cfg.get("temperature", 0.7)
    max_tokens = default_cfg.get("max_tokens", 2048)

    async def event_generator():
        collected_tokens = []
        agent_name_resolved = agent_name
        try:
            async for chunk in adapter.chat_stream(
                messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                if chunk.token:
                    collected_tokens.append(chunk.token)
                    event = StreamEvent(
                        type=StreamEventType.TOKEN,
                        data={"token": chunk.token},
                        agent_name=agent_name_resolved,
                    )
                    yield {"event": "message", "data": event.model_dump_json()}

                if chunk.finish_reason:
                    full_content = "".join(collected_tokens)
                    await message_repo.create_message(
                        conversation_id=conv_id,
                        role=MessageRole.ASSISTANT,
                        content=full_content,
                        agent_name=agent_name_resolved,
                    )
                    # 自动检测行动项和决策
                    from src.services.memory_service import check_and_track_actions
                    await check_and_track_actions(conv_id, agent_name_resolved, full_content)
                    event = StreamEvent(
                        type=StreamEventType.MESSAGE_DONE,
                        data={"content": full_content, "conversation_id": conv_id},
                        agent_name=agent_name_resolved,
                    )
                    yield {"event": "done", "data": event.model_dump_json()}
        except ConnectionError:
            event = StreamEvent(
                type=StreamEventType.ERROR,
                data={"error": "连接 LLM 服务失败，请检查网络或 API Key 配置"},
            )
            yield {"event": "error", "data": event.model_dump_json()}
        except TimeoutError:
            event = StreamEvent(
                type=StreamEventType.ERROR,
                data={"error": "LLM 响应超时，请稍后重试"},
            )
            yield {"event": "error", "data": event.model_dump_json()}
        except Exception as e:
            error_msg = str(e)
            # 对常见错误给出友好提示
            if "401" in error_msg or "Unauthorized" in error_msg:
                friendly = "API Key 无效或已过期，请在设置中检查供应商配置"
            elif "429" in error_msg or "rate_limit" in error_msg.lower():
                friendly = "请求太频繁，请稍等几秒再试"
            elif "403" in error_msg or "Forbidden" in error_msg:
                friendly = "API Key 没有权限访问该模型，请检查配置"
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                friendly = "LLM 服务暂时不可用，请稍后重试"
            else:
                friendly = f"生成回复时出错：{error_msg[:200]}"
            event = StreamEvent(
                type=StreamEventType.ERROR,
                data={"error": friendly},
            )
            yield {"event": "error", "data": event.model_dump_json()}

    return EventSourceResponse(event_generator())


async def _handle_chat_all(cmd, conv_id, image_data=None):
    """@all：依次发给所有活跃角色"""
    from src.data.repositories.agent_repo import list_agents
    from src.services.model_router import get_adapter_for_agent, get_default_model_config

    active_agents = await list_agents(status="active")
    if not active_agents:
        return JSONResponse(status_code=400, content={"error": "没有活跃的角色"})

    agent_names = [a.name for a in active_agents]

    # 保存用户消息
    await message_repo.create_message(
        conversation_id=conv_id,
        role=MessageRole.USER,
        content=cmd.raw,
        image_data=image_data,
    )

    # 为每个角色构建上下文
    history = await get_context_messages(conv_id)

    # 构建当前用户消息（含可选图片）
    if image_data:
        user_msg_content: str | list = [
            {"type": "text", "text": cmd.raw},
            {"type": "image_url", "image_url": {"url": image_data}},
        ]
    else:
        user_msg_content = cmd.raw

    default_cfg = get_default_model_config()

    async def event_generator():
        for agent_name in agent_names:
            messages = await build_messages(agent_name, history)
            messages.append(ChatMessage(role="user", content=user_msg_content))

            adapter, model_cfg = await get_adapter_for_agent(agent_name)
            if adapter is None:
                adapter = await get_default_adapter()
            if adapter is None:
                continue

            model_name = model_cfg["model"] if model_cfg else default_cfg.get("model", "")

            # 发送角色切换事件
            switch_event = StreamEvent(
                type=StreamEventType.TOKEN,
                data={"token": "", "agent_switch": agent_name},
                agent_name=agent_name,
            )
            yield {"event": "agent_switch", "data": switch_event.model_dump_json()}

            collected_tokens = []
            try:
                async for chunk in adapter.chat_stream(
                    messages, model=model_name,
                    temperature=default_cfg.get("temperature", 0.7),
                    max_tokens=default_cfg.get("max_tokens", 2048),
                ):
                    if chunk.token:
                        collected_tokens.append(chunk.token)
                        event = StreamEvent(
                            type=StreamEventType.TOKEN,
                            data={"token": chunk.token},
                            agent_name=agent_name,
                        )
                        yield {"event": "message", "data": event.model_dump_json()}

                    if chunk.finish_reason:
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
                        yield {"event": "done", "data": event.model_dump_json()}
                        # 更新 history 供下一个角色看到
                        from src.data.models import Message
                        history.append(Message(
                            conversation_id=conv_id,
                            role=MessageRole.ASSISTANT,
                            agent_name=agent_name,
                            content=full_content,
                        ))
            except Exception:
                continue

    return EventSourceResponse(event_generator())


async def _handle_add_agent(cmd):
    """/add <角色名>"""
    from src.data.repositories.agent_repo import get_agent_by_name, list_agents
    if not cmd.target_agent:
        # 列出可添加的角色
        agents = await list_agents(status="active")
        return {
            "message": "用法：/add <角色名>",
            "available": [a.name for a in agents],
        }
    agent = await get_agent_by_name(cmd.target_agent)
    if not agent:
        return JSONResponse(status_code=404, content={"error": f"角色 {cmd.target_agent} 不存在"})
    return {"status": "ok", "action": "add", "agent": cmd.target_agent, "message": f"已添加角色 {cmd.target_agent}"}


async def _handle_remove_agent(cmd):
    """/remove <角色名>"""
    from src.data.repositories.agent_repo import get_agent_by_name
    if not cmd.target_agent:
        return JSONResponse(content={"message": "用法：/remove <角色名>"})
    agent = await get_agent_by_name(cmd.target_agent)
    if not agent:
        return JSONResponse(status_code=404, content={"error": f"角色 {cmd.target_agent} 不存在"})
    return {"status": "ok", "action": "remove", "agent": cmd.target_agent, "message": f"已移除角色 {cmd.target_agent}"}


async def _handle_list_agents():
    """/list"""
    from src.data.repositories.agent_repo import list_agents
    agents = await list_agents(status="active")
    return {
        "agents": [
            {"name": a.name, "display_name": a.display_name, "description": a.description}
            for a in agents
        ],
    }


async def _handle_memory(conv_id):
    """/memory"""
    from src.services.memory_service import get_context_messages
    history = await get_context_messages(conv_id, max_messages=10)
    return {
        "conversation_id": conv_id,
        "short_term_count": len(history),
        "messages": [
            {"role": m.role.value, "agent_name": m.agent_name, "content": m.content[:100]}
            for m in history[-5:]
        ],
        "note": "长期记忆（跨对话摘要）和语义记忆（向量检索）尚未实现",
    }


async def _handle_save(conv_id):
    """/save"""
    # 目前记忆自动保存到数据库，这里返回确认
    return {
        "status": "ok",
        "message": "当前对话已保存到数据库",
        "conversation_id": conv_id,
    }


async def _handle_change_model(cmd):
    """/model <角色名> <模型名>"""
    from src.data.repositories.agent_repo import get_agent_by_name, update_agent_model
    from src.data.repositories.model_repo import get_model_by_name
    target = cmd.target_agent
    if not target:
        return JSONResponse(status_code=400, content={"error": "用法：/model <角色名> <模型名>"})
    agent_db = await get_agent_by_name(target)
    if not agent_db:
        return JSONResponse(status_code=404, content={"error": f"角色 {target} 不存在"})
    model_db = await get_model_by_name(cmd.content)
    if not model_db:
        return JSONResponse(status_code=404, content={"error": f"模型 {cmd.content} 不存在"})
    await update_agent_model(agent_db.id, model_db.id)
    return {"status": "ok", "agent": target, "model": model_db.model_name}
