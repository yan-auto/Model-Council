"""Agent 配置加载器

从 config/agents/*.yaml 加载角色定义，Pydantic 校验。
"""

from __future__ import annotations

from pathlib import Path

import yaml

from src.config import PROJECT_ROOT
from src.data.models import AgentDefinition, AgentInfo


def load_agent(name: str) -> AgentDefinition:
    """加载单个角色定义"""
    agents_dir = PROJECT_ROOT / "config" / "agents"
    yaml_path = agents_dir / f"{name}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"角色 {name} 不存在: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return AgentDefinition(**raw)


def load_all_agents() -> list[AgentDefinition]:
    """加载所有可用角色"""
    agents_dir = PROJECT_ROOT / "config" / "agents"
    agents = []
    for yaml_path in sorted(agents_dir.glob("*.yaml")):
        name = yaml_path.stem
        try:
            agents.append(load_agent(name))
        except Exception as e:
            # 启动时警告，但不阻塞
            import warnings
            warnings.warn(f"加载角色 {name} 失败: {e}")
    return agents


def list_agent_infos() -> list[AgentInfo]:
    """返回可用角色列表（用于 API）"""
    return [AgentInfo(name=a.name, description=a.description) for a in load_all_agents()]


def get_default_agent_name() -> str:
    """返回默认角色名（按字母顺序第一个）"""
    agents = load_all_agents()
    if not agents:
        return "strategist"
    return sorted(a.name for a in agents)[0]
