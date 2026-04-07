"""记忆服务

分三层：
1. 短期记忆（当前对话上下文窗口内）—— 已在 Context Builder 处理
2. 长期记忆（跨对话摘要）—— SQLite 存储
3. 语义记忆（向量检索）—— ChromaDB，Phase 2 再实现
"""

from __future__ import annotations

from src.data.models import Message
from src.data.repositories.message_repo import get_recent_messages


async def get_context_messages(
    conversation_id: str,
    max_messages: int = 50,
) -> list[Message]:
    """获取上下文窗口内的消息（短期记忆）"""
    return await get_recent_messages(conversation_id, limit=max_messages)


# TODO: 长期记忆 —— 跨对话摘要
# - 对话结束时生成摘要存入 conversation_summaries 表
# - 新对话开始时检索相关摘要注入 system prompt

# TODO: 语义记忆 —— ChromaDB 向量检索
# - 消息嵌入存入 ChromaDB
# - 新消息进来时检索相关历史消息作为额外上下文
