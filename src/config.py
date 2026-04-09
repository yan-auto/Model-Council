"""Council 配置加载，支持 YAML + 环境变量"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── 项目根目录 ──────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AppConfig(BaseSettings):
    """应用级配置，从 config/settings.yaml 加载"""

    name: str = "Council"
    version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def app_static_dir(self) -> Path:
        """前端静态文件目录（Docker 部署用）"""
        return PROJECT_ROOT / "web" / "dist"


class DataConfig(BaseSettings):
    db_path: str = "data/db/council.db"
    vectors_path: str = "data/vectors"


class MemoryConfig(BaseSettings):
    short_term_max_tokens: int = 8000
    long_term_enabled: bool = True


class ProviderConfig(BaseSettings):
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2048


class ModelRoutingConfig(BaseSettings):
    default: str = "openai"
    openai: ProviderConfig = ProviderConfig(model="gpt-4o-mini")
    anthropic: ProviderConfig = ProviderConfig(model="claude-sonnet-4-7-20250514")
    deepseek: ProviderConfig = ProviderConfig(model="deepseek-chat")


class StreamConfig(BaseSettings):
    timeout: int = 300
    heartbeat_interval: int = 30


class RateLimitConfig(BaseSettings):
    requests_per_minute: int = 60
    burst: int = 10


class Settings(BaseSettings):
    """顶层设置，合并所有子配置"""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app: AppConfig = AppConfig()
    data: DataConfig = DataConfig()
    memory: MemoryConfig = MemoryConfig()
    model_routing: ModelRoutingConfig = ModelRoutingConfig()
    stream: StreamConfig = StreamConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()

    # 环境变量注入
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com/v1", alias="DEEPSEEK_BASE_URL")
    council_auth_token: str = Field(default="council-local", alias="COUNCIL_AUTH_TOKEN")


def _load_yaml() -> dict:
    """加载 config/settings.yaml"""
    yaml_path = PROJECT_ROOT / "config" / "settings.yaml"
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取全局配置单例"""
    yaml_data = _load_yaml()
    return Settings(**yaml_data)
