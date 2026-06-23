"""
Google AI provider — uses Gemini generateContent API.
"""

import json
from typing import AsyncIterator, List

import httpx

from llm.base import ChatMessage, ChatResponse, LLMConfig, LLMProvider, StreamChunk


class GoogleProvider(LLMProvider):
    """LLM provider for Google AI (Gemini)."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._base_url = (config.base_url or "https://generativelanguage.googleapis.com").rstrip("/")
        self._http = httpx.AsyncClient(timeout=httpx.Timeout(120.0))

    async def close(self):
        await self._http.aclose()

    def _convert_messages(self, messages: List[ChatMessage]) -> dict:
        """Convert ChatMessages to Gemini format."""
        contents = []
        system_instruction = None

        for m in messages:
            if m.role == "system":
                system_instruction = {"parts": [{"text": m.content}]}
            elif m.role == "assistant":
                contents.append({"role": "model", "parts": [{"text": m.content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": m.content}]})

        return {"contents": contents, "system_instruction": system_instruction}

    async def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        converted = self._convert_messages(messages)
        body = {
            "contents": converted["contents"],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
            },
            **self.config.extra,
        }
        if converted["system_instruction"]:
            body["system_instruction"] = converted["system_instruction"]

        url = f"/v1beta/models/{self.config.model}:generateContent?key={self.config.api_key}"
        resp = await self._http.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()

        candidates = data.get("candidates", [{}])
        content_parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in content_parts)

        usage = data.get("usageMetadata", {})
        return ChatResponse(
            content=text,
            model=self.config.model,
            usage={
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
            },
            finish_reason=candidates[0].get("finishReason", "STOP").lower(),
            raw=data,
        )

    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncIterator[StreamChunk]:
        converted = self._convert_messages(messages)
        body = {
            "contents": converted["contents"],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
            },
            **self.config.extra,
        }
        if converted["system_instruction"]:
            body["system_instruction"] = converted["system_instruction"]

        url = f"/v1beta/models/{self.config.model}:streamGenerateContent?alt=sse&key={self.config.api_key}"
        async with self._http.stream("POST", url, json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if not data_str:
                    continue
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                candidates = chunk.get("candidates", [{}])
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                text = "".join(p.get("text", "") for p in parts)

                finish = candidates[0].get("finishReason")
                usage = chunk.get("usageMetadata")

                yield StreamChunk(
                    content=text,
                    finish_reason=finish.lower() if finish else None,
                    usage={
                        "prompt_tokens": usage.get("promptTokenCount", 0),
                        "completion_tokens": usage.get("candidatesTokenCount", 0),
                    } if usage else None,
                )
