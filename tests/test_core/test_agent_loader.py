"""Agent 加载器测试"""

import pytest
import yaml
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.agent_loader import load_agent, load_all_agents, list_agent_infos, get_default_agent_name


class TestAgentLoader:
    def test_load_promoter(self):
        """加载内置角色：推进者"""
        agent = load_agent("promoter")
        assert agent.name == "promoter"
        assert agent.description != ""
        assert agent.system_prompt != ""
        assert len(agent.personality.traits) > 0

    def test_load_perspectivist(self):
        """加载内置角色：透视者"""
        agent = load_agent("perspectivist")
        assert agent.name == "perspectivist"
        assert "分析" in agent.personality.traits

    def test_load_nonexistent(self):
        """加载不存在的角色应抛出异常"""
        with pytest.raises(FileNotFoundError):
            load_agent("nonexistent_agent")

    def test_load_all_agents(self):
        """加载所有角色"""
        agents = load_all_agents()
        names = [a.name for a in agents]
        assert "promoter" in names
        assert "perspectivist" in names

    def test_list_agent_infos(self):
        """角色摘要列表"""
        infos = list_agent_infos()
        assert len(infos) >= 2
        assert all(hasattr(i, "name") for i in infos)

    def test_default_agent_name(self):
        """默认角色名"""
        name = get_default_agent_name()
        assert name != ""
        assert isinstance(name, str)
