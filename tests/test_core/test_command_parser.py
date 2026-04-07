"""Command Parser 测试"""

import pytest

from src.core.command_parser import parse_command, CommandType


class TestCommandParser:
    def test_plain_chat(self):
        """普通消息"""
        cmd = parse_command("你好，帮我分析一下")
        assert cmd.type == CommandType.CHAT
        assert cmd.content == "你好，帮我分析一下"
        assert cmd.target_agent is None

    def test_at_agent(self):
        """@角色名 路由"""
        cmd = parse_command("@promoter 这个方案怎么样")
        assert cmd.type == CommandType.CHAT
        assert cmd.target_agent == "promoter"
        assert cmd.content == "这个方案怎么样"

    def test_at_agent_no_content(self):
        """@角色名 但没有内容"""
        with pytest.raises(ValueError, match="后面需要有问题内容"):
            parse_command("@promoter")

    def test_discuss(self):
        """/discuss 指令"""
        cmd = parse_command("/discuss AI 对就业的影响")
        assert cmd.type == CommandType.DISCUSS
        assert cmd.content == "AI 对就业的影响"

    def test_discuss_case_insensitive(self):
        """/DISCUSS 大写也行"""
        cmd = parse_command("/DISCUSS 测试")
        assert cmd.type == CommandType.DISCUSS

    def test_stop(self):
        """/stop 指令"""
        cmd = parse_command("/stop")
        assert cmd.type == CommandType.STOP

    def test_stop_with_reason(self):
        """/stop 附带原因"""
        cmd = parse_command("/stop 讨论够了")
        assert cmd.type == CommandType.STOP
        assert cmd.content == "讨论够了"

    def test_whitespace_handling(self):
        """前后空格"""
        cmd = parse_command("  你好  ")
        assert cmd.content == "你好"

    def test_at_perspectivist(self):
        """@perspectivist 路由"""
        cmd = parse_command("@perspectivist 这条新闻怎么看")
        assert cmd.target_agent == "perspectivist"
        assert cmd.content == "这条新闻怎么看"
