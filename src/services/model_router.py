"""Model Router —— 模型路由

从数据库读取供应商和模型配置，动态创建适配器。
"""

from __future__ import annotations

from src.adapters.base import LLMAdapter
from src.adapters.openai_adapter import OpenAIAdapter
from src.adapters.anthropic_adapter import AnthropicAdapter
from src.data.models import ProviderType

# 适配器缓存（provider_id → adapter）
_adapter_cache: dict[str, LLMAdapter] = {}


def _create_adapter(provider, api_key: str, base_url: str, model: str = "") -> LLMAdapter:
    """根据供应商类型创建适配器"""
    if provider.provider_type == ProviderType.ANTHROPIC:
        return AnthropicAdapter(api_key=api_key, base_url=base_url, default_model=model)
    # OpenAI 兼容（OpenAI、DeepSeek、MiniMax、自定义）
    return OpenAIAdapter(api_key=api_key, base_url=base_url, default_model=model)


async def get_adapter_for_agent(agent_name: str) -> tuple[LLMAdapter | None, dict | None]:
    """获取角色对应的适配器 + 模型配置，返回 (adapter, model_config)"""
    from src.data.repositories.agent_repo import get_agent_by_name
    from src.data.repositories.model_repo import get_model
    from src.data.repositories.provider_repo import get_provider

    agent = await get_agent_by_name(agent_name)
    if not agent:
        return None, None

    # 角色绑定了特定模型
    if agent.model_id:
        model = await get_model(agent.model_id)
        if model:
            provider = await get_provider(model.provider_id)
            if provider and provider.api_key:
                adapter = _get_or_create_adapter(provider, model.model_name)
                if adapter:
                    return adapter, {"model": model.model_name}

    # 没绑定模型或绑定失败，用默认适配器
    adapter = await get_default_adapter()
    return adapter, None


async def get_default_adapter() -> LLMAdapter | None:
    """返回第一个可用的适配器"""
    from src.data.repositories.provider_repo import list_providers
    from src.data.repositories.model_repo import list_models

    providers = await list_providers(status="active")
    for p in providers:
        if not p.api_key:
            continue
        models = await list_models(provider_id=p.id, status="active")
        model_name = models[0].model_name if models else ""
        adapter = _get_or_create_adapter(p, model_name)
        if adapter and adapter.is_available():
            return adapter
    return None


def _get_or_create_adapter(provider, model_name: str = "") -> LLMAdapter | None:
    """获取或创建适配器（按 provider_id 缓存）"""
    pid = provider.id
    if pid in _adapter_cache:
        return _adapter_cache[pid]
    if not provider.api_key:
        return None
    adapter = _create_adapter(provider, provider.api_key, provider.base_url, model_name)
    _adapter_cache[pid] = adapter
    return adapter


def clear_adapter_cache() -> None:
    """清除适配器缓存（供应商配置更新时调用）"""
    _adapter_cache.clear()


def get_default_model_config() -> dict:
    """默认模型参数"""
    return {"temperature": 0.7, "max_tokens": 2048}


# 向后兼容
def get_provider_config(provider: str) -> dict:
    """兼容旧代码的 provider config"""
    from src.config import get_settings
    settings = get_settings()
    routing = settings.model_routing
    cfg_map = {
        "openai": routing.openai,
        "anthropic": routing.anthropic,
        "deepseek": routing.deepseek,
    }
    cfg = cfg_map.get(provider, routing.openai)
    return {"model": cfg.model, "temperature": cfg.temperature, "max_tokens": cfg.max_tokens}
