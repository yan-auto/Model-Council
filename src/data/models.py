"""Pydantic 数据模型 —— 贯穿全层的数据结构

安全提示：
- API 密钥应该使用加密存储（在 Repository 层处理）
- 不应该在 API 响应中返回完整密钥
- 属于敏感信息，不应该在日志中打印
"""

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


# ── 供应商 ──────────────────────────────────────────

class ProviderType(str, Enum):
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"
    MINIMAX = "minimax"


class Provider(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    provider_type: ProviderType = ProviderType.OPENAI_COMPATIBLE
    api_key: str = ""
    base_url: str = ""
    group_id: str = ""
    status: str = "active"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class ProviderCreate(BaseModel):
    name: str
    provider_type: ProviderType = ProviderType.OPENAI_COMPATIBLE
    api_key: str
    base_url: str = ""
    group_id: str = ""


class ProviderUpdate(BaseModel):
    name: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    group_id: str | None = None


# ── 模型 ──────────────────────────────────────────

class Model(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    provider_id: str
    model_name: str
    display_name: str = ""
    status: str = "active"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class ModelCreate(BaseModel):
    provider_id: str
    model_name: str
    display_name: str = ""


# ── 角色（数据库版） ──────────────────────────────

class Agent(BaseModel):
    """角色完整定义，从数据库加载"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    display_name: str = ""
    description: str = ""
    system_prompt: str = ""
    model_id: str | None = None
    personality_tone: str = ""
    personality_traits: list[str] = Field(default_factory=list)
    personality_constraints: str = ""
    status: str = "active"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class AgentCreate(BaseModel):
    name: str
    display_name: str = ""
    description: str = ""
    system_prompt: str = ""
    model_id: str | None = None
    personality_tone: str = ""
    personality_traits: list[str] = Field(default_factory=list)
    personality_constraints: str = ""


class AgentUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    model_id: str | None = None
    personality_tone: str | None = None
    personality_traits: list[str] | None = None
    personality_constraints: str | None = None


class AgentModelUpdate(BaseModel):
    model_id: str | None = None


# ── 用户档案 ──────────────────────────────────────

class UserProfile(BaseModel):
    """用户个人档案（单行）"""
    id: str = "default"
    name: str = ""
    background: str = ""
    goals: str = ""
    constraints: str = ""
    financial_baseline: str = ""
    current_projects: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class UserProfileUpdate(BaseModel):
    """更新用户档案请求"""
    name: str | None = None
    background: str | None = None
    goals: str | None = None
    constraints: str | None = None
    financial_baseline: str | None = None
    current_projects: list[str] | None = None


# ── 对话摘要 ──────────────────────────────────────

class ConversationSummary(BaseModel):
    """对话摘要（长期记忆）"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    conversation_id: str
    content: str = ""
    key_decisions: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


# ── 角色记忆 ──────────────────────────────────────

class AgentMemory(BaseModel):
    """角色记住的关于用户的信息"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    agent_name: str
    memory_type: str = "fact"  # fact / decision / pattern / preference
    key: str = ""
    value: str = ""
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


# ── 待办承诺 ──────────────────────────────────────

class ActionItem(BaseModel):
    """待办行动项"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    conversation_id: str | None = None
    agent_name: str
    content: str
    status: str = "pending"  # pending / done / skipped
    created_at: float = Field(default_factory=time.time)
    completed_at: float | None = None


# ── 消息 ────────────��─────────────────────────────

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
    image_data: str | None = None  # base64 图片数据，data:image/...;base64,...
    created_at: float = Field(default_factory=time.time)


class MessageCreate(BaseModel):
    """创建消息的请求体"""
    content: str
    conversation_id: str | None = None  # 不传则自动创建新对话
    agent_name: str | None = None  # 指定路由到哪个角色，None 则走默认
    image_data: str | None = None  # base64 图片数据


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
