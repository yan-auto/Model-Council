"""Event Bus —— asyncio 事件总线

模块之间通过事件通信，不直接调用。
支持同步订阅者和异步订阅者。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class EventType(str, Enum):
    # 消息事件
    MESSAGE_CREATED = "message.created"
    MESSAGE_STREAMING = "message.streaming"
    # 讨论事件
    DISCUSSION_STARTED = "discussion.started"
    DISCUSSION_AGENT_THINKING = "discussion.agent_thinking"
    DISCUSSION_AGENT_TURN = "discussion.agent_turn"
    DISCUSSION_AGENT_DONE = "discussion.agent_done"
    DISCUSSION_ROUND_DONE = "discussion.round_done"
    DISCUSSION_VOTE_START = "discussion.vote_start"
    DISCUSSION_VOTE = "discussion.vote"
    DISCUSSION_VOTE_RESULT = "discussion.vote_result"
    DISCUSSION_STOPPED = "discussion.stopped"
    DISCUSSION_CONSENSUS = "discussion.consensus"
    # 系统事件
    AGENT_LOADED = "agent.loaded"
    ERROR = "error"


@dataclass
class Event:
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    source: str = ""


# 订阅者类型
Subscriber = Callable[[Event], Any]  # sync or async


class EventBus:
    """简单的事件总线"""

    def __init__(self):
        self._subscribers: dict[EventType, list[Subscriber]] = {}

    def subscribe(self, event_type: EventType, handler: Subscriber) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: EventType, handler: Subscriber) -> None:
        if handler in self._subscribers.get(event_type, []):
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: Event) -> None:
        handlers = self._subscribers.get(event.type, [])
        for handler in handlers:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result


# 全局 EventBus 单例
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
