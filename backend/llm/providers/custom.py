"""
Custom provider — for OpenAI-compatible self-hosted or third-party APIs.
"""

from llm.base import LLMConfig
from llm.providers.openai import OpenAIProvider


class CustomProvider(OpenAIProvider):
    """LLM provider for custom OpenAI-compatible endpoints (e.g. vLLM, Ollama, LiteLLM)."""

    def __init__(self, config: LLMConfig):
        # Custom provider requires an explicit base_url
        if not config.base_url:
            raise ValueError("Custom provider requires base_url in config")
        super().__init__(config)
