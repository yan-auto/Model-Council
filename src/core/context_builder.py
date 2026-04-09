"""Context Builder —— 上下文构建器

把 system prompt + 用户档案 + 角色记忆 + 待办 + 历史摘要 + 对话历史
拼成 LLM 可用的 messages。
"""

from __future__ import annotations

from src.adapters.base import ChatMessage
from src.data.models import Message, MessageRole
from src.services import memory_service


async def _get_agent_system_prompt(agent_name: str) -> str:
    """从数据库获取角色的 system prompt"""
    from src.data.repositories.agent_repo import get_agent_by_name
    agent = await get_agent_by_name(agent_name)
    if agent and agent.system_prompt:
        return agent.system_prompt
    # Fallback 到 YAML
    from src.core.agent_loader import load_agent
    try:
        yaml_agent = load_agent(agent_name)
        return yaml_agent.system_prompt
    except FileNotFoundError:
        return "你是一个有帮助的AI助手。"


async def build_system_message(agent_name: str) -> ChatMessage:
    """构建角色的 system prompt（含记忆注入）"""
    prompt = await _get_agent_system_prompt(agent_name)
    prompt = await _inject_memory(prompt, agent_name)
    return ChatMessage(role="system", content=prompt)


async def build_messages(
    agent_name: str,
    history: list[Message],
    *,
    extra_system: str = "",
) -> list[ChatMessage]:
    """
    构建发给 LLM 的完整消息列表。

    注入顺序：
    1. system prompt（角色设定）
    2. extra_system（投票等额外指令）
    3. 用户档案（profile）
    4. 角色记忆（agent memory）
    5. 待办承诺（pending actions）
    6. 相关历史摘要（relevant summaries）
    7. 当前对话历史（conversation history）
    """
    prompt = await _get_agent_system_prompt(agent_name)

    if extra_system:
        prompt = f"{prompt}\n\n{extra_system}"

    prompt = await _inject_memory(prompt, agent_name)

    messages = [ChatMessage(role="system", content=prompt)]
    for msg in history:
        role = "assistant" if msg.role == MessageRole.ASSISTANT else "user"
        agent_tag = f"[{msg.agent_name}] " if msg.agent_name else ""
        if msg.image_data:
            # Vision 消息：内容为多模态数组
            content: str | list = [
                {"type": "text", "text": agent_tag + msg.content},
                {"type": "image_url", "image_url": {"url": msg.image_data}},
            ]
        else:
            content = agent_tag + msg.content
        messages.append(ChatMessage(role=role, content=content))
    return messages


async def _inject_memory(prompt: str, agent_name: str) -> str:
    """将用户档案、角色记忆、待办承诺、历史摘要注入 prompt"""
    # 1. 用户档案
    profile_ctx = await memory_service.get_profile_context()
    if profile_ctx:
        prompt = f"{prompt}\n\n{profile_ctx}"

    # 2. 角色记忆
    agent_mem = await memory_service.get_agent_memory(agent_name)
    if agent_mem:
        prompt = f"{prompt}\n\n{agent_mem}"

    # 3. 待办承诺
    actions = await memory_service.get_pending_actions()
    if actions:
        actions_text = memory_service.format_actions(actions)
        prompt = f"{prompt}\n\n{actions_text}"

    # 4. 相关历史摘要（取最近几条）
    summaries = await memory_service.get_relevant_summaries(agent_name, limit=3)
    if summaries:
        summaries_text = memory_service.format_summaries(summaries)
        prompt = f"{prompt}\n\n{summaries_text}"

    return prompt
