"""WebSocket 讨论 API

多角色讨论走 WebSocket，支持：
- 实时接收每个角色的 token 流（thinking → token → done）
- 最后一轮自动投票
- 客户端中途 /stop 停止讨论
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.agent_loader import load_all_agents
from src.core.event_bus import Event, EventType, get_event_bus
from src.core.orchestrator import DiscussionOrchestrator, DiscussionState
from src.data.models import MessageRole
from src.data.repositories import conversation_repo, message_repo

router = APIRouter(tags=["discussion"])

# 当前活跃的讨论（conv_id → orchestrator）
_active_discussions: dict[str, DiscussionOrchestrator] = {}

# 需要订阅的所有讨论事件类型
_DISCUSSION_EVENTS = [
    EventType.DISCUSSION_STARTED,
    EventType.DISCUSSION_AGENT_THINKING,
    EventType.DISCUSSION_AGENT_TURN,
    EventType.DISCUSSION_AGENT_DONE,
    EventType.DISCUSSION_ROUND_DONE,
    EventType.DISCUSSION_VOTE_START,
    EventType.DISCUSSION_VOTE,
    EventType.DISCUSSION_VOTE_RESULT,
    EventType.DISCUSSION_CONSENSUS,
]


@router.websocket("/ws/discuss")
async def websocket_discuss(websocket: WebSocket):
    await websocket.accept()
    conv_id = None

    try:
        # 等待客户端发送讨论配置
        raw = await websocket.receive_text()
        config = json.loads(raw)

        topic = config.get("topic", "")
        agent_names = config.get("agents", [])
        max_rounds = config.get("max_rounds", 3)
        conv_id = config.get("conversation_id")

        # 验证角色存在
        all_agents = {a.name for a in load_all_agents()}
        agent_names = [n for n in agent_names if n in all_agents]
        if not agent_names:
            agent_names = [a.name for a in load_all_agents()[:3]]

        # 确保有对话
        if not conv_id:
            from src.data.models import ConversationCreate
            conv = await conversation_repo.create_conversation(
                ConversationCreate(title=f"讨论: {topic[:30]}")
            )
            conv_id = conv.id

        # 保存用户消息
        await message_repo.create_message(
            conversation_id=conv_id,
            role=MessageRole.USER,
            content=f"[讨论] {topic}",
        )

        # 创建编排器
        state = DiscussionState(
            conversation_id=conv_id,
            agent_names=agent_names,
            topic=topic,
            max_rounds=max_rounds,
        )
        orchestrator = DiscussionOrchestrator(state)
        _active_discussions[conv_id] = orchestrator

        # 订阅事件，转发给 WebSocket
        event_bus = get_event_bus()

        async def on_event(event: Event):
            """将 Event Bus 事件转发给 WebSocket 客户端"""
            try:
                payload = {
                    "type": event.type.value if hasattr(event.type, "value") else str(event.type),
                    "data": event.data,
                    "source": event.source,
                }
                await websocket.send_text(json.dumps(payload, ensure_ascii=False))
            except Exception:
                pass

        for et in _DISCUSSION_EVENTS:
            event_bus.subscribe(et, on_event)

        # 运行讨论（阻塞直到完成）
        await orchestrator.run()

        # 清理
        _active_discussions.pop(conv_id, None)
        for et in _DISCUSSION_EVENTS:
            event_bus.unsubscribe(et, on_event)

    except WebSocketDisconnect:
        if conv_id and conv_id in _active_discussions:
            _active_discussions[conv_id].stop()
    except json.JSONDecodeError:
        await websocket.send_text(json.dumps({"type": "error", "data": {"error": "无效的 JSON"}}))
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "data": {"error": str(e)}}))
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
