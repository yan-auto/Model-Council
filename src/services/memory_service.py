"""记忆服务

三层记忆：
1. 短期记忆（当前对话）—— Context Builder 直接加载
2. 长期记忆（对话摘要）—— 每次对话结束自动生成
3. 角色记忆（共享知识）—— 角色学到的关于用户的信息
"""

from __future__ import annotations

import json
import re

from src.data.models import Message
from src.data.repositories import memory_repo


async def get_context_messages(
    conversation_id: str,
    max_messages: int = 50,
) -> list[Message]:
    """获取上下文窗口内的消息（短期记忆）"""
    from src.data.repositories.message_repo import get_recent_messages
    return await get_recent_messages(conversation_id, limit=max_messages)


# ── 用户档案 ──────────────────────────────────────

async def get_profile_context() -> str:
    """获取格式化的用户档案文本，注入 system prompt"""
    profile = await memory_repo.get_profile()
    if not profile:
        return ""
    if not any(profile.get(k) for k in ("name", "background", "goals", "constraints", "financial_baseline")):
        return ""

    parts = ["## 用户档案"]
    if profile.get("name"):
        parts.append(f"姓名：{profile['name']}")
    if profile.get("background"):
        parts.append(f"背景：{profile['background']}")
    if profile.get("goals"):
        parts.append(f"目标：{profile['goals']}")
    if profile.get("constraints"):
        parts.append(f"约束：{profile['constraints']}")
    if profile.get("financial_baseline"):
        parts.append(f"财务基准：{profile['financial_baseline']}")

    # 当前项目
    projects = profile.get("current_projects", "[]")
    if isinstance(projects, str):
        try:
            projects = json.loads(projects)
        except (json.JSONDecodeError, TypeError):
            projects = []
    if projects:
        parts.append(f"当前项目：{', '.join(projects)}")

    return "\n".join(parts)


async def get_profile() -> dict:
    """获取原始档案数据"""
    profile = await memory_repo.get_profile()
    if not profile:
        return {}
    # 解析 JSON 字段
    if isinstance(profile.get("current_projects"), str):
        try:
            profile["current_projects"] = json.loads(profile["current_projects"])
        except (json.JSONDecodeError, TypeError):
            profile["current_projects"] = []
    return profile


async def update_profile(data: dict) -> dict:
    """更新用户档案"""
    return await memory_repo.upsert_profile(data)


# ── 对话摘要 ──────────────────────────────────────

async def save_conversation_summary(
    conversation_id: str,
    messages: list[Message] | None = None,
) -> str | None:
    """
    为对话生成摘要并保存。
    如果有 messages 参数，用简单规则提取摘要（不调 LLM，零成本）。
    返回摘要 ID。
    """
    # 检查是否已有摘要
    existing = await memory_repo.get_summary(conversation_id)
    if existing:
        return existing["id"]

    if not messages:
        return None

    # 从消息中提取关键信息
    assistant_msgs = [m for m in messages if m.role.value == "assistant"]
    user_msgs = [m for m in messages if m.role.value == "user"]
    if not assistant_msgs:
        return None

    # 简单摘要：取用户第一条消息作为主题 + 最后一条助手消息的要点
    topic = user_msgs[0].content[:100] if user_msgs else ""
    last_reply = assistant_msgs[-1].content[:200] if assistant_msgs else ""

    # 提取决策和行动项
    decisions = []
    actions = []
    for msg in assistant_msgs:
        content = msg.content
        # 检测决策关键词
        if any(kw in content for kw in ["决定", "选择", "下一步：", "行动："]):
            # 取包含关键词的那一行
            for line in content.split("\n"):
                line = line.strip()
                if any(kw in line for kw in ["决定", "选择", "下一步", "行动"]):
                    if len(line) > 10:
                        decisions.append(line[:80])
                    break

        # 检测行动项
        action_match = re.findall(r"(?:下一步|行动|接下来)[：:]\s*(.+)", content)
        actions.extend(a[:60] for a in action_match[:3])

    summary_parts = []
    if topic:
        summary_parts.append(f"讨论主题：{topic}")
    summary_parts.append(f"助手回复次数：{len(assistant_msgs)}")
    if last_reply:
        summary_parts.append(f"最后要点：{last_reply}")

    content = "\n".join(summary_parts)
    return await memory_repo.create_summary(
        conversation_id=conversation_id,
        content=content,
        key_decisions=decisions[:5],
        action_items=actions[:5],
    )


async def get_relevant_summaries(query: str, limit: int = 5) -> list[dict]:
    """获取相关摘要"""
    if not query.strip():
        return await memory_repo.get_summaries(limit)
    results = await memory_repo.search_summaries(query, limit)
    if not results:
        # 关键词不匹配时返回最近的
        return await memory_repo.get_summaries(limit)
    return results


def format_summaries(summaries: list[dict]) -> str:
    """格式化摘要为文本"""
    if not summaries:
        return ""
    parts = ["## 相关历史摘要"]
    for s in summaries[:3]:
        parts.append(f"- {s.get('content', '')[:100]}")
        decisions = s.get("key_decisions", "[]")
        if isinstance(decisions, str):
            try:
                decisions = json.loads(decisions)
            except (json.JSONDecodeError, TypeError):
                decisions = []
        for d in decisions[:2]:
            parts.append(f"  决策：{d}")
    return "\n".join(parts)


# ── 角色记忆 ──────────────────────────────────────

async def update_agent_memory(agent_name: str, memory_type: str, key: str, value: str) -> str:
    """更新角色记忆"""
    return await memory_repo.upsert_agent_memory(agent_name, memory_type, key, value)


async def get_agent_memory(agent_name: str) -> str:
    """获取格式化的角色记忆文本"""
    memories = await memory_repo.get_agent_memories(agent_name)
    if not memories:
        return ""
    parts = [f"## 我（{agent_name}）对用户的了解"]
    for m in memories:
        type_label = {"fact": "事实", "decision": "决策", "pattern": "模式", "preference": "偏好"}.get(
            m.get("memory_type", "fact"), "信息"
        )
        parts.append(f"- [{type_label}] {m['key']}：{m['value']}")
    return "\n".join(parts)


# ── 待办承诺 ──────────────────────────────────────

async def track_action(conversation_id: str | None, agent_name: str, content: str) -> str:
    """记录一个待办承诺"""
    return await memory_repo.create_action(conversation_id, agent_name, content)


async def get_pending_actions() -> list[dict]:
    """获取未完成的待办"""
    return await memory_repo.get_pending_actions()


async def complete_action(action_id: str) -> None:
    """标记待办为完成"""
    await memory_repo.update_action_status(action_id, "done")


async def skip_action(action_id: str) -> None:
    """标记待办为跳过"""
    await memory_repo.update_action_status(action_id, "skipped")


def format_actions(actions: list[dict]) -> str:
    """格式化待办为文本"""
    if not actions:
        return ""
    parts = ["## 待办承诺（需要跟进）"]
    for a in actions[:5]:
        agent = a.get("agent_name", "")
        parts.append(f"- [{agent}] {a.get('content', '')[:80]}")
    return "\n".join(parts)


async def check_and_track_actions(
    conversation_id: str | None,
    agent_name: str,
    content: str,
) -> list[str]:
    """
    检测消息中是否包含行动项，自动记录。
    返回检测到的行动项列表。
    """
    tracked = []

    # 检测"下一步：xxx"模式
    action_patterns = [
        r"下一步[：:]\s*(.+)",
        r"行动[：:]\s*(.+)",
        r"接下来.*?[：:]\s*(.+)",
        r"今天.*?完成[：:]\s*(.+)",
        r"你.*?要做的是[：:]?\s*(.+)",
    ]

    for pattern in action_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            action_text = match.strip()[:100]
            if len(action_text) > 5:
                await track_action(conversation_id, agent_name, action_text)
                tracked.append(action_text)

    # 检测决策模式（"决定xxx"）
    decision_patterns = [
        r"决定[了：:]?\s*(.+)",
    ]
    for pattern in decision_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            decision_text = match.strip()[:100]
            if len(decision_text) > 5:
                await update_agent_memory(agent_name, "decision", f"决策-{decision_text[:30]}", decision_text)

    return tracked
