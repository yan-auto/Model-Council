"""WebSocket 讨论 API

多角色讨论走 WebSocket，支持：
- 实时接收每个角色的 token 流
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


@router.websocket("/ws/discuss")
async def websocket_discuss(websocket: WebSocket):
    await websocket.accept()

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
            agent_names = [a.name for a in load_all_agents()[:3]]  # 默认前3个

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
            try:
                await websocket.send_text(event.model_dump_json())
            except Exception:
                pass

        event_bus.subscribe(EventType.DISCUSSION_STARTED, on_event)
        event_bus.subscribe(EventType.DISCUSSION_AGENT_TURN, on_event)
        event_bus.subscribe(EventType.DISCUSSION_ROUND_DONE, on_event)
        event_bus.subscribe(EventType.DISCUSSION_CONSENSUS, on_event)

        # 运行讨论
        await orchestrator.run()

        # 清理
        _active_discussions.pop(conv_id, None)
        event_bus.unsubscribe(EventType.DISCUSSION_STARTED, on_event)
        event_bus.unsubscribe(EventType.DISCUSSION_AGENT_TURN, on_event)
        event_bus.unsubscribe(EventType.DISCUSSION_ROUND_DONE, on_event)
        event_bus.unsubscribe(EventType.DISCUSSION_CONSENSUS, on_event)

    except WebSocketDisconnect:
        # 客户端断开，停止讨论
        if conv_id and conv_id in _active_discussions:
            _active_discussions[conv_id].stop()
    except json.JSONDecodeError:
        await websocket.send_text(json.dumps({"error": "无效的 JSON"}))
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
