"""Agent Router —— 角色路由

根据 ParsedCommand 决定使用哪个角色、哪个适配器。
优先从数据库读取角色信息。
"""

from __future__ import annotations

from src.core.command_parser import ParsedCommand, CommandType
from src.data.repositories.agent_repo import get_agent_by_name, list_agents


async def resolve_agent(cmd: ParsedCommand) -> str:
    """从命令中解析出目标角色名"""
    if cmd.target_agent:
        return cmd.target_agent

    # 检查角色名是否直接作为输入（无前缀，但匹配已知角色名）
    agents = [a.name for a in await __gen_agents()]
    if cmd.content in agents:
        return cmd.content

    # 返回默认角色
    agents_list = await list_agents(status="active")
    if agents_list:
        return agents_list[0].name
    return "promoter"


async def __gen_agents():
    return await list_agents(status="active")


def is_discuss_command(cmd: ParsedCommand) -> bool:
    """判断是否为讨论模式命令"""
    return cmd.type == CommandType.DISCUSS


def is_stop_command(cmd: ParsedCommand) -> bool:
    """判断是否为停止命令"""
    return cmd.type == CommandType.STOP
