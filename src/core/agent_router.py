"""Agent Router —— 角色路由

根据 ParsedCommand 决定使用哪个角色、哪个适配器。
"""

from __future__ import annotations

from src.core.agent_loader import get_default_agent_name, load_all_agents
from src.core.command_parser import ParsedCommand, CommandType


def resolve_agent(cmd: ParsedCommand) -> str:
    """从命令中解析出目标角色名"""
    if cmd.target_agent:
        return cmd.target_agent

    # 检查角色名是否直接作为输入（无前缀，但匹配已知角色名）
    agents = {a.name for a in load_all_agents()}
    if cmd.content in agents:
        return cmd.content

    return get_default_agent_name()


def is_discuss_command(cmd: ParsedCommand) -> bool:
    """判断是否为讨论模式命令"""
    return cmd.type == CommandType.DISCUSS


def is_stop_command(cmd: ParsedCommand) -> bool:
    """判断是否为停止命令"""
    return cmd.type == CommandType.STOP
