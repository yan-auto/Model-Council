"""Orchestrator —— 讨论编排器

管理多角色讨论的全流程：
1. 接收讨论配置（参与角色、主题、最大轮次）
2. 顺序调度每个角色发言（轮流发言制）
3. 最后一轮转为投票轮（support / oppose / neutral + 理由）
4. 汇总投票结果并广播
5. 通过 Event Bus 发送事件
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.agent_loader import load_agent as yaml_load_agent
from src.core.context_builder import build_messages
from src.core.event_bus import Event, EventType, get_event_bus
from src.data.models import Message, MessageRole
from src.data.repositories import message_repo
from src.data.repositories.agent_repo import get_agent_by_name
from src.data.repositories.model_repo import get_model, list_models as list_all_models
from src.services.model_router import get_default_adapter, get_default_model_config


@dataclass
class DiscussionState:
    """讨论状态"""
    conversation_id: str
    agent_names: list[str]
    topic: str
    max_rounds: int
    current_round: int = 0
    current_agent_index: int = 0
    status: str = "running"  # running / stopped / consensus
    full_transcript: list[Message] = field(default_factory=list)
    votes: dict[str, dict[str, str]] = field(default_factory=dict)  # agent → {stance, reason}
    vote_result_shown: bool = False


@dataclass
class VoteResult:
    """投票结果汇总"""
    topic: str
    support: list[str]
    oppose: list[str]
    neutral: list[str]
    consensus: str  # "support" | "oppose" | "neutral" | "split"


class DiscussionOrchestrator:
    """讨论编排器"""

    def __init__(self, state: DiscussionState):
        self.state = state
        self._stop_requested = False
        self._event_bus = get_event_bus()

    async def run(self) -> list[Message]:
        """运行完整讨论（含投票轮），返回所有消息"""
        topic = self.state.topic or "请讨论以下问题"

        # 发布开始事件
        await self._event_bus.publish(Event(
            type=EventType.DISCUSSION_STARTED,
            data={
                "topic": topic,
                "agents": self.state.agent_names,
                "max_rounds": self.state.max_rounds,
            },
        ))

        # 注入话题作为首条用户消息
        topic_msg = Message(
            conversation_id=self.state.conversation_id,
            role=MessageRole.USER,
            content=topic,
        )
        self.state.full_transcript.append(topic_msg)

        adapter = await get_default_adapter()
        if adapter is None:
            raise RuntimeError("没有可用的 LLM 适配器，请检查 API 配置")

        # ── 讨论轮 ──────────────────────────────
        for round_num in range(1, self.state.max_rounds):
            if self._stop_requested:
                break
            self.state.current_round = round_num
            is_last = (round_num == self.state.max_rounds - 1)

            # 发布轮次开始（用于前端进度条）
            await self._event_bus.publish(Event(
                type=EventType.DISCUSSION_ROUND_DONE,
                data={
                    "round": round_num,
                    "total": self.state.max_rounds - 1,
                    "is_last": is_last,
                },
            ))

            # 每个角色轮流发言
            for i, agent_name in enumerate(self.state.agent_names):
                if self._stop_requested:
                    break
                self.state.current_agent_index = i
                await self._agent_speak(agent_name, adapter, round_num, is_last)

            if self._stop_requested:
                break

        # ── 投票轮（最后一轮） ──────────────────
        if not self._stop_requested and not self.state.vote_result_shown:
            await self._run_voting_round(adapter)

        self.state.status = "stopped" if self._stop_requested else "consensus"
        await self._event_bus.publish(Event(
            type=EventType.DISCUSSION_CONSENSUS,
            data={
                "status": self.state.status,
                "rounds": self.state.current_round,
                "votes": self.state.votes,
            },
        ))
        return self.state.full_transcript

    async def _agent_speak(
        self,
        agent_name: str,
        adapter,
        round_num: int,
        is_last: bool = False,
    ) -> Message:
        """单个角色发言——分三个阶段发事件：thinking → token流 → done"""
        # 获取 system prompt
        agent_db = await get_agent_by_name(agent_name)
        system_prompt = ""
        if agent_db and agent_db.system_prompt:
            system_prompt = agent_db.system_prompt
        else:
            try:
                system_prompt = yaml_load_agent(agent_name).system_prompt
            except FileNotFoundError:
                system_prompt = "你是一个有帮助的AI助手。"

        # 获取模型
        model_name = ""
        if agent_db and agent_db.model_id:
            model = await get_model(agent_db.model_id)
            if model:
                model_name = model.model_name
        if not model_name:
            all_models = await list_all_models(status="active")
            if all_models:
                model_name = all_models[0].model_name
        provider_cfg = get_default_model_config()

        # ── 阶段 1：thinking ─────────────────────
        await self._event_bus.publish(Event(
            type=EventType.DISCUSSION_AGENT_THINKING,
            data={
                "agent": agent_name,
                "round": round_num,
                "is_last": is_last,
            },
        ))

        # ── 阶段 2：token 流 ───────────────────
        history = [
            m for m in self.state.full_transcript
            if m.role in (MessageRole.USER, MessageRole.ASSISTANT)
        ]
        messages = await build_messages(agent_name, history)

        # 发开始事件（含 agent 元信息，方便前端初始化气泡）
        await self._event_bus.publish(Event(
            type=EventType.DISCUSSION_AGENT_TURN,
            data={
                "agent": agent_name,
                "round": round_num,
                "is_last": is_last,
                "phase": "start",
                "content": "",
            },
        ))

        collected = []
        async for chunk in adapter.chat_stream(
            messages,
            model=model_name or provider_cfg.get("model", ""),
            temperature=provider_cfg.get("temperature", 0.7),
            max_tokens=provider_cfg.get("max_tokens", 2048),
        ):
            if self._stop_requested:
                break
            collected.append(chunk.token)
            # 每个 token 单独发事件（前端按 agent+round 合并）
            await self._event_bus.publish(Event(
                type=EventType.DISCUSSION_AGENT_TURN,
                data={
                    "agent": agent_name,
                    "round": round_num,
                    "is_last": is_last,
                    "phase": "token",
                    "token": chunk.token,
                    "content": "".join(collected),
                },
            ))

        content = "".join(collected)

        # 发完成事件
        await self._event_bus.publish(Event(
            type=EventType.DISCUSSION_AGENT_DONE,
            data={
                "agent": agent_name,
                "round": round_num,
                "is_last": is_last,
                "content": content,
            },
        ))

        # 持久化
        msg = Message(
            conversation_id=self.state.conversation_id,
            role=MessageRole.ASSISTANT,
            agent_name=agent_name,
            content=content,
        )
        self.state.full_transcript.append(msg)
        await message_repo.create_message(
            conversation_id=self.state.conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            agent_name=agent_name,
        )
        return msg

    async def _run_voting_round(self, adapter) -> None:
        """最后一轮：投票——让每个角色给出立场 + 理由"""
        self.state.vote_result_shown = True

        # 发布投票开始
        await self._event_bus.publish(Event(
            type=EventType.DISCUSSION_VOTE_START,
            data={"agents": self.state.agent_names},
        ))

        for agent_name in self.state.agent_names:
            if self._stop_requested:
                break

            # 每个角色生成投票
            vote_content = await self._generate_vote(agent_name, adapter)
            self.state.votes[agent_name] = vote_content

            await self._event_bus.publish(Event(
                type=EventType.DISCUSSION_VOTE,
                data={
                    "agent": agent_name,
                    **vote_content,
                },
            ))

        # 汇总结果
        result = self._aggregate_votes()
        await self._event_bus.publish(Event(
            type=EventType.DISCUSSION_VOTE_RESULT,
            data=result,
        ))

    async def _generate_vote(self, agent_name: str, adapter) -> dict[str, str]:
        """让角色生成一张投票：立场 + 简短理由"""
        history = [
            m for m in self.state.full_transcript
            if m.role in (MessageRole.USER, MessageRole.ASSISTANT)
        ]
        messages = await build_messages(
            agent_name,
            history,
            extra_system="你现在的任务是：对之前的讨论给出你的最终立场。"
            "请用以下 JSON 格式回复（不要有其他内容）：\n"
            '{"stance": "support|oppose|neutral", "reason": "不超过30字的简短理由"}'
        )

        provider_cfg = get_default_model_config()
        model_name = ""
        agent_db = await get_agent_by_name(agent_name)
        if agent_db and agent_db.model_id:
            model = await get_model(agent_db.model_id)
            if model:
                model_name = model.model_name
        if not model_name:
            all_models = await list_all_models(status="active")
            if all_models:
                model_name = all_models[0].model_name

        collected = []
        async for chunk in adapter.chat_stream(
            messages,
            model=model_name or provider_cfg.get("model", ""),
            temperature=0.3,
            max_tokens=128,
        ):
            if self._stop_requested:
                break
            collected.append(chunk.token)

        content = "".join(collected).strip()

        # 解析 JSON
        stance, reason = self._parse_vote(content)
        return {"stance": stance, "reason": reason}

    def _parse_vote(self, raw: str) -> tuple[str, str]:
        """从 LLM 输出中提取 stance 和 reason"""
        import re, json
        raw = raw.strip()

        # 尝试直接解析 JSON
        m = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group())
                stance = obj.get("stance", "neutral")
                reason = obj.get("reason", "")
                if stance not in ("support", "oppose", "neutral"):
                    stance = "neutral"
                return stance, reason[:40]
            except Exception:
                pass

        # 降级：按关键词猜
        lower = raw.lower()
        if "support" in lower or "赞" in raw or "同意" in raw:
            stance = "support"
        elif "oppose" in lower or "反" in raw or "反对" in raw:
            stance = "oppose"
        else:
            stance = "neutral"
        reason = raw[:40]
        return stance, reason

    def _aggregate_votes(self) -> dict[str, Any]:
        """汇总投票，返回结果字典"""
        support = []
        oppose = []
        neutral = []
        for agent, vote in self.state.votes.items():
            stance = vote.get("stance", "neutral")
            if stance == "support":
                support.append(agent)
            elif stance == "oppose":
                oppose.append(agent)
            else:
                neutral.append(agent)

        n = len(self.state.agent_names)
        if len(support) > n // 2:
            consensus = "support"
        elif len(oppose) > n // 2:
            consensus = "oppose"
        elif len(support) == len(oppose) == n // 2:
            consensus = "split"
        else:
            consensus = "neutral"

        return {
            "topic": self.state.topic,
            "support": support,
            "oppose": oppose,
            "neutral": neutral,
            "consensus": consensus,
            "votes": self.state.votes,
        }

    def stop(self) -> None:
        """请求停止讨论"""
        self._stop_requested = True

    @property
    def is_stopped(self) -> bool:
        return self._stop_requested
