"""
StructuralBot - AI Providers

Provider implementations for the AI service layer.

The application communicates with providers through a common interface.
This makes it possible to connect different AI services later without
changing Telegram handlers or engineering calculation modules.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from ai.service import (
    AIConfigurationError,
    AIProviderError,
    AIRequest,
    AIResponse,
    EngineeringPromptBuilder,
)


# ---------------------------------------------------------
# GENERIC HTTP PROVIDER INTERFACE
# ---------------------------------------------------------


class BaseAIProvider:
    """
    Base provider interface.

    Concrete providers should implement generate().
    """

    name = "base"

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        raise NotImplementedError


# ---------------------------------------------------------
# OPENAI-COMPATIBLE PROVIDER
# ---------------------------------------------------------


class OpenAICompatibleProvider(BaseAIProvider):
    """
    Provider for APIs that expose an OpenAI-compatible chat interface.

    The actual HTTP client is intentionally not imported here yet.
    This keeps the core project lightweight until a provider is selected.

    Expected configuration:

        AI_API_KEY
        AI_BASE_URL
        AI_MODEL

    Example base URL:

        https://api.openai.com/v1

    The provider can later be connected to any compatible service.
    """

    name = "openai-compatible"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:

        self.api_key = (
            api_key
            or os.getenv("AI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )

        self.base_url = (
            base_url
            or os.getenv("AI_BASE_URL")
            or os.getenv(
                "OPENAI_BASE_URL",
                "https://api.openai.com/v1",
            )
        )

        self.model = (
            model
            or os.getenv("AI_MODEL")
        )

        self.timeout = timeout

    def validate_configuration(self) -> None:
        """
        Validate provider configuration.
        """

        if not self.api_key:
            raise AIConfigurationError(
                "AI API key is not configured."
            )

        if not self.base_url:
            raise AIConfigurationError(
                "AI base URL is not configured."
            )

        if not self.model:
            raise AIConfigurationError(
                "AI model is not configured."
            )

    def build_payload(
        self,
        request: AIRequest,
    ) -> Dict[str, Any]:
        """
        Build a provider-neutral OpenAI-compatible payload.

        This method does not perform network communication.
        """

        self.validate_configuration()

        messages = EngineeringPromptBuilder.build(
            request
        )

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": request.temperature,
        }

        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        return payload

    def build_headers(self) -> Dict[str, str]:
        """
        Build HTTP authorization headers.
        """

        self.validate_configuration()

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def endpoint(self) -> str:
        """
        Return chat completion endpoint.
        """

        self.validate_configuration()

        return (
            self.base_url.rstrip("/")
            + "/chat/completions"
        )

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        """
        Generate an AI response.

        Network transport is intentionally separated from this first
        provider definition. A dedicated HTTP implementation can be added
        without changing the rest of StructuralBot.
        """

        self.validate_configuration()

        raise AIProviderError(
            "AI HTTP transport is not connected yet. "
            "Provider configuration is ready, but network execution "
            "must be implemented before production use."
        )


# ---------------------------------------------------------
# FACTORY
# ---------------------------------------------------------


def create_ai_provider(
    provider_name: Optional[str] = None,
) -> BaseAIProvider:
    """
    Create an AI provider from configuration.

    Supported values:

        placeholder
        openai
        openai-compatible
    """

    name = (
        provider_name
        or os.getenv("AI_PROVIDER")
        or "placeholder"
    ).strip().lower()

    if name in {
        "placeholder",
        "none",
        "disabled",
    }:
        from ai.service import PlaceholderAIProvider

        return PlaceholderAIProvider()

    if name in {
        "openai",
        "openai-compatible",
        "openai_compatible",
    }:
        return OpenAICompatibleProvider()

    raise AIConfigurationError(
        f"Unsupported AI provider: {name}"
    )


# ---------------------------------------------------------
# CONFIGURATION HELPERS
# ---------------------------------------------------------


def ai_provider_is_configured() -> bool:
    """
    Check whether enough configuration exists for a real AI provider.

    This does not make a network request.
    """

    provider_name = (
        os.getenv("AI_PROVIDER")
        or "placeholder"
    ).strip().lower()

    if provider_name in {
        "placeholder",
        "none",
        "disabled",
    }:
        return False

    api_key = (
        os.getenv("AI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

    model = os.getenv("AI_MODEL")

    return bool(api_key and model)


def get_ai_provider_name() -> str:
    """
    Return the configured provider name.
    """

    return (
        os.getenv("AI_PROVIDER")
        or "placeholder"
    ).strip().lower()


__all__ = [
    "BaseAIProvider",
    "OpenAICompatibleProvider",
    "create_ai_provider",
    "ai_provider_is_configured",
    "get_ai_provider_name",
]
