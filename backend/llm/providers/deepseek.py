"""
DeepSeek provider — uses OpenAI-compatible API at api.deepseek.com.
"""

from llm.base import LLMConfig
from llm.providers.openai import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    """LLM provider for DeepSeek (OpenAI-compatible API)."""

    def __init__(self, config: LLMConfig):
        if not config.base_url:
            config.base_url = "https://api.deepseek.com/v1"
        super().__init__(config)
