"""
Anthropic provider — uses the Anthropic Messages API.
"""

import json
from typing import AsyncIterator, List, Optional

import httpx

from llm.base import ChatMessage, ChatResponse, LLMConfig, LLMProvider, StreamChunk


class AnthropicProvider(LLMProvider):
    """LLM provider for Anthropic Claude models."""

    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._base_url = (config.base_url or "https://api.anthropic.com").rstrip("/")
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "x-api-key": config.api_key,
                "anthropic-version": self.ANTHROPIC_VERSION,
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(120.0),
        )

    async def close(self):
        await self._http.aclose()

    def _convert_messages(self, messages: List[ChatMessage]) -> tuple:
        """Convert ChatMessages to Anthropic format. Returns (system, msgs)."""
        system_parts = []
        msgs = []
        for m in messages:
            if m.role == "system":
                system_parts.append(m.content)
            else:
                role = "assistant" if m.role == "assistant" else "user"
                msgs.append({"role": role, "content": m.content})
        system = "\n".join(system_parts) if system_parts else None
        return system, msgs

    async def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        system, msgs = self._convert_messages(messages)
        body = {
            "model": self.config.model,
            "messages": msgs,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        if system:
            body["system"] = system
        body.update(self.config.extra)

        resp = await self._http.post("/v1/messages", json=body)
        resp.raise_for_status()
        data = resp.json()

        content_blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")

        return ChatResponse(
            content=text,
            model=data.get("model", self.config.model),
            usage={
                "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
            },
            finish_reason=data.get("stop_reason", "stop"),
            raw=data,
        )

    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncIterator[StreamChunk]:
        system, msgs = self._convert_messages(messages)
        body = {
            "model": self.config.model,
            "messages": msgs,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": True,
        }
        if system:
            body["system"] = system
        body.update(self.config.extra)

        async with self._http.stream("POST", "/v1/messages", json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if not data_str:
                    continue
                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type", "")

                if event_type == "content_block_delta":
                    delta = event.get("delta", {})
                    yield StreamChunk(
                        content=delta.get("text", ""),
                    )
                elif event_type == "message_delta":
                    usage = event.get("usage", {})
                    finish = event.get("delta", {}).get("stop_reason")
                    yield StreamChunk(
                        finish_reason=finish,
                        usage={
                            "prompt_tokens": usage.get("input_tokens", 0),
                            "completion_tokens": usage.get("output_tokens", 0),
                        } if usage else None,
                    )
                elif event_type == "message_stop":
                    break
