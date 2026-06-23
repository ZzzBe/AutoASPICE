"""
Factory for creating LLM provider instances from configuration.

Also handles reading API keys from localStorage-style config (passed from frontend).
"""

from typing import Dict, Optional

from llm.base import LLMConfig, LLMProvider
from llm.providers.openai import OpenAIProvider
from llm.providers.anthropic import AnthropicProvider
from llm.providers.deepseek import DeepSeekProvider
from llm.providers.google import GoogleProvider
from llm.providers.custom import CustomProvider

# Default models for each provider
DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-6",
    "deepseek": "deepseek-chat",
    "google": "gemini-2.5-flash",
    "custom": "",
}

# Well-known models per provider (for UI dropdowns)
PROVIDER_MODELS = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4-turbo",
        "o4-mini",
        "o3",
    ],
    "anthropic": [
        "claude-opus-4-8",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
        "claude-fable-5",
    ],
    "deepseek": [
        "deepseek-chat",
        "deepseek-reasoner",
    ],
    "google": [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
    ],
    "custom": [],  # User types model name freely
}


def create_provider(
    provider: str,
    api_key: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    **extra,
) -> LLMProvider:
    """
    Create an LLM provider instance.

    Args:
        provider: "openai" | "anthropic" | "deepseek" | "google" | "custom"
        api_key: API key for the provider
        model: Model name (uses default if not specified)
        base_url: Override the default API endpoint
        temperature: Sampling temperature (0.0 - 2.0)
        max_tokens: Maximum tokens in the response
        **extra: Additional provider-specific parameters

    Returns:
        An LLMProvider instance

    Raises:
        ValueError: If provider is unknown or required config is missing
    """
    provider = provider.lower().strip()

    if not api_key:
        raise ValueError(f"API key is required for provider '{provider}'")

    if model is None:
        model = DEFAULT_MODELS.get(provider, "")
    if not model:
        raise ValueError(f"Model must be specified for provider '{provider}'")

    config = LLMConfig(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        extra=extra,
    )

    if provider == "openai":
        return OpenAIProvider(config)
    elif provider == "anthropic":
        return AnthropicProvider(config)
    elif provider == "deepseek":
        return DeepSeekProvider(config)
    elif provider == "google":
        return GoogleProvider(config)
    elif provider == "custom":
        return CustomProvider(config)
    else:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Supported: openai, anthropic, deepseek, google, custom"
        )


def get_provider_for_agent(
    provider: str,
    api_key: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LLMProvider:
    """
    Convenience function to get a provider with agent-execution defaults.
    Uses lower temperature (0.3) and higher max_tokens (8192) suitable for
    structured technical analysis.
    """
    return create_provider(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        temperature=0.3,
        max_tokens=8192,
    )
