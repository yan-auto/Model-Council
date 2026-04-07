"""Anthropic 适配器

支持 Claude 系列模型，SSE 流式输出。
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from src.adapters.base import (
    LLMAdapter,
    ChatMessage,
    ChatResponse,
    StreamChunk,
)


class AnthropicAdapter(LLMAdapter):
    """Anthropic Claude 适配器"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com",
        default_model: str = "claude-sonnet-4-7-20250514",
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model

    def is_available(self) -> bool:
        return bool(self._api_key)

    def _build_payload(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> tuple[str, list[dict], str | None]:
        """分离 system prompt 和对话消息，返回 (model, messages, system)"""
        system_prompt = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})
        return model or self._default_model, chat_messages, system_prompt

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[StreamChunk]:
        model, chat_messages, system_prompt = self._build_payload(
            messages, model, temperature, max_tokens
        )
        url = f"{self._base_url}/v1/messages"
        payload: dict = {
            "model": model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    import json
                    try:
                        event = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type", "")

                    if event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        token = delta.get("text", "")
                        if token:
                            yield StreamChunk(token=token)

                    elif event_type == "message_stop":
                        yield StreamChunk(token="", finish_reason="stop")
                        return

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        model, chat_messages, system_prompt = self._build_payload(
            messages, model, temperature, max_tokens
        )
        url = f"{self._base_url}/v1/messages"
        payload: dict = {
            "model": model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content_blocks = data.get("content", [])
            content = "".join(b.get("text", "") for b in content_blocks)
            usage = data.get("usage", {})
            return ChatResponse(content=content, usage=usage)
