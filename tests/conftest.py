"""pytest 全局配置和 fixtures"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 测试环境变量
os.environ.setdefault("COUNCIL_AUTH_TOKEN", "test-token")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def sample_agent_yaml():
    """测试用的角色 YAML 数据"""
    return {
        "name": "test_agent",
        "description": "测试角色",
        "personality": {
            "tone": "测试",
            "traits": ["test"],
            "constraints": "仅用于测试",
        },
        "system_prompt": "你是一个测试角色。",
    }


@pytest.fixture
def sample_messages():
    """测试用的消息列表"""
    from src.data.models import Message, MessageRole
    return [
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
            content="你好！有什么我可以帮你的？",
        ),
    ]


@pytest.fixture
def mock_llm_adapter():
    """模拟 LLM 适配器"""
    from src.adapters.base import LLMAdapter, StreamChunk, ChatResponse

    adapter = AsyncMock(spec=LLMAdapter)
    adapter.is_available.return_value = True

    async def fake_stream(*args, **kwargs):
        tokens = ["你好", "，", "这是", "测试", "回复"]
        for t in tokens:
            yield StreamChunk(token=t)
        yield StreamChunk(token="", finish_reason="stop")

    adapter.chat_stream.side_effect = fake_stream
    adapter.chat.return_value = ChatResponse(content="测试回复", usage={})
    return adapter
