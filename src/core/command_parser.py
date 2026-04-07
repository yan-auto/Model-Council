"""Command Parser —— 指令解析层

解析 @角色名、/discuss、/stop 等指令。
这些指令不走 LLM，纯规则匹配。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.core.agent_loader import load_all_agents, get_default_agent_name


class CommandType(str, Enum):
    CHAT = "chat"          # 普通聊天
    DISCUSS = "discuss"    # 开启讨论
    STOP = "stop"          # 停止讨论
    SWITCH = "switch"      # 切换角色


@dataclass
class ParsedCommand:
    type: CommandType
    raw: str
    content: str           # 去掉指令前缀后的实际内容
    target_agent: str | None = None  # @角色名 指定的目标角色


def parse_command(raw: str) -> ParsedCommand:
    """
    解析用户输入，返回 ParsedCommand。

    规则：
    - 以 /discuss 开头 → 讨论模式
    - 以 /stop 开头 → 停止
    - 以 @角色名 开头 → 路由到指定角色
    - 其他 → 普通聊天

    所有指令都需要有内容，纯粹的 /stop 也视为停止当前讨论。
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

    # @角色名
    # 匹配最长前缀（如 @promoter-test 不应匹配 @promoter）
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
                # 只有 @角色名 没有内容，报错
                raise ValueError(f"@{name} 后面需要有问题内容")

    # 普通聊天，默认角色
    return ParsedCommand(
        type=CommandType.CHAT,
        raw=raw,
        content=text,
        target_agent=None,  # None = 默认角色
    )
