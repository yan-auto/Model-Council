"""Context Builder 测试"""

import pytest
import asyncio

from src.core.context_builder import build_system_message, build_messages
from src.data.models import Message, MessageRole


@pytest.fixture(autouse=True)
async def setup_db():
    """确保有 agent 数据"""
    from src.data.database import reset_db
    await reset_db()
    # 种子数据
    from src.data.seed import seed_initial_data
    await seed_initial_data()


def run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestContextBuilder:
    def test_build_system_message(self):
        msg = run(build_system_message("strategist"))
        assert msg.role == "system"
        assert "决策" in msg.content or "行动" in msg.content

    def test_build_messages_with_history(self):
        history = [
            Message(
                id="m1",
                conversation_id="conv1",
                role=MessageRole.USER,
                content="你好",
            ),
            Message(
                id="m2",
                conversation_id="conv1",
                role=MessageRole.ASSISTANT,
                agent_name="strategist",
                content="你好！",
            ),
        ]
        messages = run(build_messages("strategist", history))
        # 第一个应该是 system
        assert messages[0].role == "system"
        # 应该有 3 条（system + user + assistant）
        assert len(messages) == 3
        # assistant 消息带角色标签
        assert "[strategist]" in messages[2].content

    def test_build_messages_empty_history(self):
        messages = run(build_messages("promoter", []))
        assert len(messages) == 1
        assert messages[0].role == "system"
