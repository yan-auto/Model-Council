"""Pydantic 数据模型 —— 贯穿全层的数据结构"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from pydantic import BaseModel, Field


# ── 角色 ──────────────────────────────────────────

class AgentPersonality(BaseModel):
    tone: str = ""
    traits: list[str] = []
    constraints: str = ""


class AgentDefinition(BaseModel):
    """一个 AI 角色的完整定义，从 YAML 加载"""
    name: str
    description: str = ""
    personality: AgentPersonality = AgentPersonality()
    system_prompt: str = ""


class AgentInfo(BaseModel):
    """API 返回的角色摘要"""
    name: str
    description: str


# ── 消息 ──────────────────────────────────────────

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """一条对话消息"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    conversation_id: str
    role: MessageRole
    agent_name: str | None = None  # assistant 消息标记来自哪个角色
    content: str
    created_at: float = Field(default_factory=time.time)


class MessageCreate(BaseModel):
    """创建消息的请求体"""
    content: str
    conversation_id: str | None = None  # 不传则自动创建新对话
    agent_name: str | None = None  # 指定路由到哪个角色，None 则走默认


# ── 对话 ──────────────────────────────────────────

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Conversation(BaseModel):
    """一次对话会话"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    title: str = "新对话"
    status: ConversationStatus = ConversationStatus.ACTIVE
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class ConversationCreate(BaseModel):
    """创建对话请求"""
    title: str = "新对话"


# ── 讨论 ──────────────────────────────────────────

class DiscussionStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    CONSENSUS = "consensus"


class DiscussionConfig(BaseModel):
    """讨论模式配置"""
    agent_names: list[str]           # 参与讨论的角色
    max_rounds: int = 3              # 最大轮次
    topic: str = ""                  # 讨论主题


# ── 流式事件（统一抽象） ──────────────────────────

class StreamEventType(str, Enum):
    # 单角色对话
    TOKEN = "token"                  # 流式 token
    MESSAGE_DONE = "message_done"    # 一条完整消息结束
    # 讨论模式
    DISCUSSION_START = "discussion_start"
    DISCUSSION_TOKEN = "discussion_token"
    DISCUSSION_AGENT_TURN = "discussion_agent_turn"  # 轮到某角色
    DISCUSSION_DONE = "discussion_done"
    # 通用
    ERROR = "error"


class StreamEvent(BaseModel):
    """统一流式事件，SSE 和 WebSocket 共用"""
    type: StreamEventType
    data: dict = {}
    agent_name: str | None = None
