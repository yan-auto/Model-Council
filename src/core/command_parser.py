"""Command Parser —— 指令解析层

解析 @角色名、@all、/discuss、/stop 等指令。
这些指令不走 LLM，纯规则匹配。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from src.core.agent_loader import load_all_agents, get_default_agent_name


class CommandType(str, Enum):
    CHAT = "chat"          # 普通聊天（单个角色）
    CHAT_ALL = "chat_all"  # 发给所有活跃角色
    DISCUSS = "discuss"     # 开启讨论
    STOP = "stop"          # 停止讨论
    ADD_AGENT = "add_agent"     # 添加角色
    REMOVE_AGENT = "remove_agent"  # 移除角色
    LIST_AGENTS = "list_agents"    # 列出所有角色
    MEMORY = "memory"       # 查看记忆状态
    SAVE = "save"           # 手动保存记忆
    CHANGE_MODEL = "change_model"  # 换模型


@dataclass
class ParsedCommand:
    type: CommandType
    raw: str
    content: str           # 去掉指令前缀后的实际内容
    target_agent: str | None = None  # @角色名 指定的目标角色
    # 附加参数（不同指令类型用不同字段）
    extra: dict = field(default_factory=dict)


def parse_command(raw: str) -> ParsedCommand:
    """
    解析用户输入，返回 ParsedCommand。

    规则：
    - /stop → 停止讨论
    - /discuss → 讨论模式
    - /add <角色> → 添加角色
    - /remove <角色> → 移除角色
    - /list → 列出所有角色
    - /memory → 查看记忆状态
    - /save → 保存记忆
    - /model <角色> <模型> → 换模型
    - @all → 发给所有活跃角色
    - @角色名 → 发给指定角色
    - 其他 → 普通聊天（默认角色）
    """
    text = raw.strip()
    agents = {a.name: a.name for a in load_all_agents()}
    default_agent = get_default_agent_name()

    # /stop 优先
    if text.lower().startswith("/stop"):
        return ParsedCommand(
            type=CommandType.STOP,
            raw=raw,
            content=text[5:].strip(),
        )

    # /discuss
    if text.lower().startswith("/discuss"):
        return ParsedCommand(
            type=CommandType.DISCUSS,
            raw=raw,
            content=text[8:].strip(),
        )

    # /add <角色>
    if text.lower().startswith("/add"):
        rest = text[4:].strip()
        return ParsedCommand(
            type=CommandType.ADD_AGENT,
            raw=raw,
            content=rest,
            target_agent=rest or None,
        )

    # /remove <角色>
    if text.lower().startswith("/remove"):
        rest = text[7:].strip()
        return ParsedCommand(
            type=CommandType.REMOVE_AGENT,
            raw=raw,
            content=rest,
            target_agent=rest or None,
        )

    # /list
    if text.lower().startswith("/list"):
        return ParsedCommand(
            type=CommandType.LIST_AGENTS,
            raw=raw,
            content="",
        )

    # /memory
    if text.lower().startswith("/memory"):
        return ParsedCommand(
            type=CommandType.MEMORY,
            raw=raw,
            content="",
        )

    # /save
    if text.lower().startswith("/save"):
        return ParsedCommand(
            type=CommandType.SAVE,
            raw=raw,
            content="",
        )

    # /model <agent_name> <model_name>
    if text.lower().startswith("/model"):
        parts = text[6:].strip().split(maxsplit=1)
        if len(parts) == 2:
            return ParsedCommand(
                type=CommandType.CHANGE_MODEL,
                raw=raw,
                content=parts[1],        # model_name
                target_agent=parts[0],   # agent_name
            )
        elif len(parts) == 1:
            return ParsedCommand(
                type=CommandType.CHANGE_MODEL,
                raw=raw,
                content=parts[0],
                target_agent=None,
            )
        else:
            raise ValueError("/model 需要参数：/model <角色名> <模型名>")

    # @all → 发给所有活跃角色
    if text.startswith("@all"):
        rest = text[4:].strip()
        if not rest:
            raise ValueError("@all 后面需要有问题内容")
        return ParsedCommand(
            type=CommandType.CHAT_ALL,
            raw=raw,
            content=rest,
            target_agent=None,
        )

    # @角色名
    matched_agent = None
    for name in sorted(agents.keys(), key=len, reverse=True):
        if text.startswith(f"@{name}"):
            matched_agent = name
            rest = text[len(name) + 1:].strip()
            if rest:
                return ParsedCommand(
                    type=CommandType.CHAT,
                    raw=raw,
                    content=rest,
                    target_agent=matched_agent,
                )
            else:
                raise ValueError(f"@{name} 后面需要有问题内容")

    # 普通聊天，默认角色
    return ParsedCommand(
        type=CommandType.CHAT,
        raw=raw,
        content=text,
        target_agent=None,
    )
