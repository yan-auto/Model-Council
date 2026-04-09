"""OpenAI 兼容适配器

覆盖：OpenAI、DeepSeek、MiniMax 以及任何 OpenAI 兼容接口。
通过不同的 base_url + api_key 区分。
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from src.adapters.base import (
    LLMAdapter,
    ChatMessage,
    ChatResponse,
    StreamChunk,
)


class OpenAIAdapter(LLMAdapter):
    """OpenAI 兼容适配器，支持流式和非流式"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4o-mini",
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[StreamChunk]:
        model = model or self._default_model
        url = f"{self._base_url}/chat/completions"
        # 构建消息：支持 vision 格式（content 为 list）和平常文本（content 为 str）
        def build_content(msg: ChatMessage) -> str | list:
            return msg.content
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": build_content(m)} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # 去掉 "data: "
                    if data_str.strip() == "[DONE]":
                        yield StreamChunk(token="", finish_reason="stop")
                        return
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    token = delta.get("content", "")
                    finish_reason = choices[0].get("finish_reason")
                    if token:
                        yield StreamChunk(token=token, finish_reason=finish_reason)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        model = model or self._default_model
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return ChatResponse(content=content, usage=usage)
