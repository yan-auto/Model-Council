"""Orchestrator —— 讨论编排器

管理多角色讨论的全流程：
1. 接收讨论配置（参与角色、主题、最大轮次）
2. 顺序调度每个角色发言
3. 管理讨论状态（轮次、停止条件）
4. 通过 Event Bus 广播事件
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from src.core.agent_loader import load_agent
from src.core.context_builder import build_system_message, build_messages
from src.core.event_bus import Event, EventType, get_event_bus
from src.data.models import Message, MessageRole
from src.data.repositories import message_repo
from src.services.model_router import get_default_adapter, get_provider_config


@dataclass
class DiscussionState:
    """讨论状态"""
    conversation_id: str
    agent_names: list[str]
    topic: str
    max_rounds: int
    current_round: int = 0
    current_agent_index: int = 0
    status: str = "running"  # running / stopped / consensus
    full_transcript: list[Message] = field(default_factory=list)


class DiscussionOrchestrator:
    """讨论编排器"""

    def __init__(self, state: DiscussionState):
        self.state = state
        self._stop_requested = False
        self._event_bus = get_event_bus()

    async def run(self) -> list[Message]:
        """
        运行完整讨论，返回所有消息。
        yield 事件流由外部通过 Event Bus 消费。
        """
        topic = self.state.topic or "请讨论以下问题"
        # 发布开始事件
        await self._event_bus.publish(Event(
            type=EventType.DISCUSSION_STARTED,
            data={"topic": topic, "agents": self.state.agent_names},
        ))

        # 把用户的问题作为第一条消息注入
        topic_msg = Message(
            conversation_id=self.state.conversation_id,
            role=MessageRole.USER,
            content=topic,
        )
        self.state.full_transcript.append(topic_msg)

        adapter = get_default_adapter()
        if adapter is None:
            raise RuntimeError("没有可用的 LLM 适配器，请检查 API 配置")

        for round_num in range(1, self.state.max_rounds + 1):
            if self._stop_requested:
                break
            self.state.current_round = round_num

            await self._event_bus.publish(Event(
                type=EventType.DISCUSSION_ROUND_DONE,
                data={"round": round_num - 1},
            ))

            # 每个角色轮流发言
            for i, agent_name in enumerate(self.state.agent_names):
                if self._stop_requested:
                    break
                self.state.current_agent_index = i
                msg = await self._agent_speak(agent_name, adapter)
                self.state.full_transcript.append(msg)

        self.state.status = "stopped" if self._stop_requested else "consensus"
        await self._event_bus.publish(Event(
            type=EventType.DISCUSSION_CONSENSUS,
            data={"status": self.state.status, "rounds": self.state.current_round},
        ))
        return self.state.full_transcript

    async def _agent_speak(
        self,
        agent_name: str,
        adapter,
    ) -> Message:
        """单个角色发言"""
        agent = load_agent(agent_name)
        provider_cfg = get_provider_config("openai")  # TODO: 按角色配置 provider

        # 发布角色轮次事件
        await self._event_bus.publish(Event(
            type=EventType.DISCUSSION_AGENT_TURN,
            data={"agent": agent_name, "round": self.state.current_round},
        ))

        # 构建上下文（排除 system prompt 本身不计入历史）
        from src.data.models import MessageRole as MR
        history = [
            m for m in self.state.full_transcript
            if m.role in (MR.USER, MR.ASSISTANT)
        ]
        messages = build_messages(agent_name, history)

        # 流式生成
        from src.adapters.base import StreamChunk
        collected = []
        async for chunk in adapter.chat_stream(
            messages,
            model=provider_cfg["model"],
            temperature=provider_cfg["temperature"],
            max_tokens=provider_cfg["max_tokens"],
        ):
            if self._stop_requested:
                break
            collected.append(chunk.token)
            await self._event_bus.publish(Event(
                type=EventType.DISCUSSION_AGENT_TURN,
                data={
                    "agent": agent_name,
                    "token": chunk.token,
                    "round": self.state.current_round,
                },
            ))

        content = "".join(collected)
        msg = Message(
            conversation_id=self.state.conversation_id,
            role=MessageRole.ASSISTANT,
            agent_name=agent_name,
            content=content,
        )
        # 持久化
        await message_repo.create_message(
            conversation_id=self.state.conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            agent_name=agent_name,
        )
        return msg

    def stop(self) -> None:
        """请求停止讨论（可从外部调用）"""
        self._stop_requested = True
