"""数据模型测试"""

import pytest
from src.data.models import (
    AgentDefinition,
    AgentPersonality,
    AgentInfo,
    Message,
    MessageRole,
    Conversation,
    ConversationStatus,
    StreamEvent,
    StreamEventType,
    MessageCreate,
    DiscussionConfig,
)


class TestAgentDefinition:
    def test_create_from_dict(self, sample_agent_yaml):
        agent = AgentDefinition(**sample_agent_yaml)
        assert agent.name == "test_agent"
        assert agent.description == "测试角色"
        assert agent.personality.tone == "测试"
        assert "test" in agent.personality.traits
        assert agent.system_prompt == "你是一个测试角色。"

    def test_minimal(self):
        agent = AgentDefinition(name="minimal")
        assert agent.name == "minimal"
        assert agent.description == ""
        assert agent.system_prompt == ""


class TestMessage:
    def test_create_user_message(self):
        msg = Message(
            conversation_id="conv1",
            role=MessageRole.USER,
            content="测试",
        )
        assert msg.role == MessageRole.USER
        assert msg.content == "测试"
        assert msg.agent_name is None
        assert len(msg.id) == 16

    def test_create_assistant_message(self):
        msg = Message(
            conversation_id="conv1",
            role=MessageRole.ASSISTANT,
            content="回复",
            agent_name="promoter",
        )
        assert msg.agent_name == "promoter"


class TestConversation:
    def test_create(self):
        conv = Conversation(title="测试对话")
        assert conv.title == "测试对话"
        assert conv.status == ConversationStatus.ACTIVE
        assert len(conv.id) == 16


class TestStreamEvent:
    def test_token_event(self):
        event = StreamEvent(
            type=StreamEventType.TOKEN,
            data={"token": "你好"},
            agent_name="promoter",
        )
        assert event.type == StreamEventType.TOKEN
        assert event.data["token"] == "你好"
        # 可以序列化
        json_str = event.model_dump_json()
        assert "你好" in json_str

    def test_error_event(self):
        event = StreamEvent(
            type=StreamEventType.ERROR,
            data={"error": "出错了"},
        )
        assert event.type == StreamEventType.ERROR


class TestMessageCreate:
    def test_with_agent(self):
        mc = MessageCreate(content="@promoter 你好", agent_name="promoter")
        assert mc.content == "@promoter 你好"
        assert mc.conversation_id is None

    def test_with_conversation(self):
        mc = MessageCreate(content="继续", conversation_id="conv1")
        assert mc.conversation_id == "conv1"


class TestDiscussionConfig:
    def test_create(self):
        config = DiscussionConfig(
            agent_names=["promoter", "perspectivist"],
            max_rounds=3,
            topic="测试讨论",
        )
        assert len(config.agent_names) == 2
        assert config.max_rounds == 3
