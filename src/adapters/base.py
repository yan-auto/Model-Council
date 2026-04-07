"""LLM 适配器抽象基类

所有模型提供商的适配器必须实现此接口。
核心引擎只依赖这个抽象，不知道具体用的是哪家 API。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from collections.abc import AsyncIterator

from src.data.models import Message


@dataclass
class ChatMessage:
    """发送给 LLM 的消息格式"""
    role: str  # system / user / assistant
    content: str


@dataclass
class StreamChunk:
    """流式返回的单个 chunk"""
    token: str
    finish_reason: str | None = None


@dataclass
class ChatResponse:
    """非流式完整回复（备用）"""
    content: str
    usage: dict = field(default_factory=dict)


class LLMAdapter(ABC):
    """LLM 适配器抽象基类"""

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[StreamChunk]:
        """流式对话，逐 token 返回"""
        ...
        # 让 yield 检查器知道这是生成器
        if False:
            yield  # type: ignore[misc]

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        """非流式对话，等待完整回复"""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """检查当前适配器是否可用（API key 是否配置）"""
        ...
