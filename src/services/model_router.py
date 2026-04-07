"""Model Router —— 模型路由

根据配置和可用性选择适配器，支持按角色指定模型。
"""

from __future__ import annotations

from src.adapters.base import LLMAdapter
from src.adapters.openai_adapter import OpenAIAdapter
from src.adapters.anthropic_adapter import AnthropicAdapter
from src.config import get_settings


# 适配器单例
_openai_adapter: OpenAIAdapter | None = None
_anthropic_adapter: AnthropicAdapter | None = None


def get_openai_adapter() -> OpenAIAdapter:
    global _openai_adapter
    if _openai_adapter is None:
        settings = get_settings()
        _openai_adapter = OpenAIAdapter(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            default_model=settings.model_routing.openai.model,
        )
    return _openai_adapter


def get_anthropic_adapter() -> AnthropicAdapter:
    global _anthropic_adapter
    if _anthropic_adapter is None:
        settings = get_settings()
        _anthropic_adapter = AnthropicAdapter(
            api_key=settings.anthropic_api_key,
            default_model=settings.model_routing.anthropic.model,
        )
    return _anthropic_adapter


def get_adapter_for_provider(provider: str) -> LLMAdapter | None:
    """根据 provider 名称返回对应适配器"""
    if provider == "openai":
        adapter = get_openai_adapter()
        return adapter if adapter.is_available() else None
    if provider == "anthropic":
        adapter = get_anthropic_adapter()
        return adapter if adapter.is_available() else None
    if provider == "deepseek":
        settings = get_settings()
        if settings.deepseek_api_key:
            return OpenAIAdapter(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                default_model=settings.model_routing.deepseek.model,
            )
    return None


def get_default_adapter() -> LLMAdapter | None:
    """按配置优先级返回第一个可用的适配器"""
    settings = get_settings()
    routing = settings.model_routing
    providers = ["openai", "anthropic", "deepseek"]
    for p in providers:
        adapter = get_adapter_for_provider(p)
        if adapter is not None and adapter.is_available():
            return adapter
    return None


def get_provider_config(provider: str) -> dict:
    """获取指定 provider 的模型配置"""
    settings = get_settings()
    routing = settings.model_routing
    cfg_map = {
        "openai": routing.openai,
        "anthropic": routing.anthropic,
        "deepseek": routing.deepseek,
    }
    cfg = cfg_map.get(provider)
    if cfg is None:
        cfg = routing.openai  # fallback
    return {"model": cfg.model, "temperature": cfg.temperature, "max_tokens": cfg.max_tokens}
