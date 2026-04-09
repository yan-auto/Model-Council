"""种子数据 —— 启动时从 YAML 和环境变量导入初始数据"""

from __future__ import annotations

from src.config import get_settings
from src.data.models import ProviderType, ProviderCreate, ModelCreate, AgentCreate
from src.data.repositories.provider_repo import create_provider, list_providers
from src.data.repositories.model_repo import create_model, list_models
from src.data.repositories.agent_repo import count_agents, create_agent
from src.core.agent_loader import load_all_agents


async def seed_initial_data() -> None:
    """初始化供应商和角色数据（仅在为空时）"""
    settings = get_settings()

    # ── 供应商 ────────────────────────────────────
    existing = await list_providers()
    if not existing:
        # DeepSeek 供应商（从环境变量）
        if settings.deepseek_api_key:
            p = await create_provider(
                ProviderCreate(
                    name="DeepSeek",
                    provider_type=ProviderType.OPENAI_COMPATIBLE,
                    api_key=settings.deepseek_api_key,
                    base_url=settings.deepseek_base_url or "https://api.deepseek.com/v1",
                )
            )
            await create_model(ModelCreate(
                provider_id=p.id,
                model_name="deepseek-chat",
                display_name="DeepSeek Chat",
            ))

        # OpenAI 供应商（从环境变量）
        if settings.openai_api_key:
            p2 = await create_provider(
                ProviderCreate(
                    name="OpenAI",
                    provider_type=ProviderType.OPENAI_COMPATIBLE,
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url or "https://api.openai.com/v1",
                )
            )
            for mname, dname in [
                ("gpt-4o", "GPT-4o"),
                ("gpt-4o-mini", "GPT-4o Mini"),
                ("o3-mini", "o3 Mini"),
            ]:
                await create_model(ModelCreate(
                    provider_id=p2.id,
                    model_name=mname,
                    display_name=dname,
                ))

        # Anthropic 供应商（从环境变量）
        if settings.anthropic_api_key:
            p3 = await create_provider(
                ProviderCreate(
                    name="Anthropic",
                    provider_type=ProviderType.ANTHROPIC,
                    api_key=settings.anthropic_api_key,
                    base_url="https://api.anthropic.com",
                )
            )
            for mname, dname in [
                ("claude-sonnet-4-7-20250514", "Claude Sonnet 4"),
                ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet"),
                ("claude-3-5-haiku-20241022", "Claude 3.5 Haiku"),
            ]:
                await create_model(ModelCreate(
                    provider_id=p3.id,
                    model_name=mname,
                    display_name=dname,
                ))

    # ── 角色 ───────────────────────────────────────
    if await count_agents() == 0:
        yaml_agents = load_all_agents()
        for ya in yaml_agents:
            await create_agent(AgentCreate(
                name=ya.name,
                display_name=_yaml_name_to_display(ya.name),
                description=ya.description,
                system_prompt=ya.system_prompt,
                personality_tone=ya.personality.tone,
                personality_traits=ya.personality.traits,
                personality_constraints=ya.personality.constraints,
            ))


def _yaml_name_to_display(name: str) -> str:
    mapping = {
        "promoter": "推进者",
        "perspectivist": "透视",
        "strategist": "军师",
        "supervisor": "监工",
        "social_coach": "读心",
    }
    return mapping.get(name, name)
