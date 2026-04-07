"""Context Builder —— 上下文构建器

把 system prompt + 历史消息 + 记忆 拼成 LLM 可用的 messages。
"""

from __future__ import annotations

from src.adapters.base import ChatMessage
from src.data.models import Message, MessageRole
from src.core.agent_loader import load_agent


def build_system_message(agent_name: str) -> ChatMessage:
    """构建角色的 system prompt"""
    agent = load_agent(agent_name)
    return ChatMessage(role="system", content=agent.system_prompt)


def build_messages(
    agent_name: str,
    history: list[Message],
) -> list[ChatMessage]:
    """
    构建发给 LLM 的完整消息列表。
    格式：[system_prompt, ...history_messages]
    """
    messages = [build_system_message(agent_name)]
    for msg in history:
        role = "assistant" if msg.role == MessageRole.ASSISTANT else "user"
        agent_tag = f"[{msg.agent_name}] " if msg.agent_name else ""
        messages.append(ChatMessage(
            role=role,
            content=agent_tag + msg.content,
        ))
    return messages
