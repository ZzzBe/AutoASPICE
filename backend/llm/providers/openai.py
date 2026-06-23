"""
OpenAI provider — uses the standard chat/completions API.
Also works as base for OpenAI-compatible providers (DeepSeek, Custom).
"""

import json
from typing import AsyncIterator, List, Optional

import httpx

from llm.base import ChatMessage, ChatResponse, LLMConfig, LLMProvider, StreamChunk


class OpenAIProvider(LLMProvider):
    """LLM provider for OpenAI and OpenAI-compatible APIs."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._base_url = (config.base_url or "https://api.openai.com/v1").rstrip("/")
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(120.0),
        )

    async def close(self):
        await self._http.aclose()

    async def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        body = {
            "model": self.config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            **self.config.extra,
        }

        resp = await self._http.post("/chat/completions", json=body)
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        return ChatResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.config.model),
            usage={
                "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
            },
            finish_reason=choice.get("finish_reason", "stop"),
            raw=data,
        )

    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncIterator[StreamChunk]:
        body = {
            "model": self.config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
            **self.config.extra,
        }

        async with self._http.stream("POST", "/chat/completions", json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                choice = chunk.get("choices", [{}])[0]
                delta = choice.get("delta", {})
                finish = choice.get("finish_reason")

                yield StreamChunk(
                    content=delta.get("content", ""),
                    finish_reason=finish,
                    usage=chunk.get("usage"),
                )
