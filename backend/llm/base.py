"""
Base classes and protocols for LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional, Any


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""

    provider: str  # "openai" | "anthropic" | "deepseek" | "google" | "custom"
    api_key: str
    model: str
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """A single message in a chat conversation."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    """Standardized response from an LLM provider."""

    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)  # {"prompt_tokens": N, "completion_tokens": N}
    finish_reason: str = "stop"
    raw: Any = None


@dataclass
class StreamChunk:
    """A single chunk from a streaming response."""

    content: str = ""
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    async def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """Send a chat completion request (non-streaming)."""
        ...

    @abstractmethod
    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncIterator[StreamChunk]:
        """Send a chat completion request and stream the response."""
        ...

    @staticmethod
    def build_system_prompt(agent_role: str, agent_capabilities: List[str], domain: str = "") -> str:
        """Build a standard system prompt for agent execution."""
        parts = []
        if agent_role:
            parts.append(agent_role)
        if domain:
            parts.append(f"\nDomain: {domain}")
        if agent_capabilities:
            parts.append("\nCapabilities:\n- " + "\n- ".join(agent_capabilities))
        parts.append(
            "\n\nProvide detailed, technically accurate analysis with specific references "
            "to automotive standards. Include code examples where applicable. "
            "Structure output with clear markdown headings."
        )
        return "\n".join(parts)

    @staticmethod
    def build_user_prompt(
        task_description: str,
        context_files: List[str] = None,
        user_instruction: str = "",
        step_name: str = "",
    ) -> str:
        """Build a user prompt from task + context."""
        parts = []
        if step_name:
            parts.append(f"## Current Step: {step_name}\n")
        if task_description:
            parts.append(task_description)
        if context_files:
            parts.append("\n## Context Files\n")
            for f in context_files:
                parts.append(f"- {f}")
        if user_instruction:
            parts.append(f"\n## User Instruction\n{user_instruction}")
        return "\n".join(parts)
