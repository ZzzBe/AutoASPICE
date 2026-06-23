"""
LLM Adapter Layer — unified interface for multiple LLM providers.

Supports: OpenAI, Anthropic, DeepSeek, Google AI, and Custom (OpenAI-compatible).
Provides both streaming and non-streaming chat completion.
"""

from llm.base import LLMProvider, LLMConfig, ChatMessage, ChatResponse, StreamChunk
from llm.factory import create_provider, get_provider_for_agent

__all__ = [
    "LLMProvider",
    "LLMConfig",
    "ChatMessage",
    "ChatResponse",
    "StreamChunk",
    "create_provider",
    "get_provider_for_agent",
]
