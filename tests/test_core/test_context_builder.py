"""Context Builder 测试"""

from src.core.context_builder import build_system_message, build_messages
from src.data.models import Message, MessageRole


class TestContextBuilder:
    def test_build_system_message(self):
        msg = build_system_message("promoter")
        assert msg.role == "system"
        assert "创业" in msg.content or "决策" in msg.content

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
                agent_name="promoter",
                content="你好！",
            ),
        ]
        messages = build_messages("promoter", history)
        # 第一个应该是 system
        assert messages[0].role == "system"
        # 应该有 3 条（system + user + assistant）
        assert len(messages) == 3
        # assistant 消息带角色标签
        assert "[promoter]" in messages[2].content

    def test_build_messages_empty_history(self):
        messages = build_messages("promoter", [])
        assert len(messages) == 1
        assert messages[0].role == "system"
