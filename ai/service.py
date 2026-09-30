from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol


@dataclass
class AIRequest:
    user_id: Optional[str]
    message: str
    system_prompt: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)
    temperature: float = 0.2
    max_tokens: int = 1500


@dataclass
class AIResponse:
    text: str
    provider: str = "placeholder"
    model: Optional[str] = None
    usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class AIProvider(Protocol):
    name: str

    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        ...


class PlaceholderAIProvider:
    name = "placeholder"

    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        return AIResponse(
            text=(
                "دستیار هوشمند در حال حاضر در حالت آزمایشی است. "
                "برای محاسبات سازه‌ای، نتیجه موتور محاسبات "
                "و کنترل آیین‌نامه‌ای منبع اصلی پاسخ است."
            ),
            provider=self.name,
            model=None,
            usage={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        )


class AIService:
    def __init__(
        self,
        provider: Optional[AIProvider] = None,
    ):
        self.provider = provider or PlaceholderAIProvider()

    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        if not isinstance(request, AIRequest):
            raise TypeError("request must be AIRequest")

        message = str(request.message).strip()

        if not message:
            raise ValueError("AI request message cannot be empty.")

        if request.temperature < 0:
            request.temperature = 0.0

        if request.temperature > 2:
            request.temperature = 2.0

        if request.max_tokens < 1:
            request.max_tokens = 1

        return self.provider.generate(request)

    def ask(
        self,
        message: str,
        *,
        user_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> AIResponse:
        request = AIRequest(
            user_id=user_id,
            message=message,
            system_prompt=system_prompt,
            context=context or {},
        )
        return self.generate(request)


_default_service = AIService()


def get_ai_service() -> AIService:
    return _default_service


def ask_ai(
    message: str,
    *,
    user_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
    context: Optional[dict[str, Any]] = None,
) -> AIResponse:
    return _default_service.ask(
        message,
        user_id=user_id,
        system_prompt=system_prompt,
        context=context,
    )


__all__ = [
    "AIRequest",
    "AIResponse",
    "AIProvider",
    "PlaceholderAIProvider",
    "AIService",
    "get_ai_service",
    "ask_ai",
]
