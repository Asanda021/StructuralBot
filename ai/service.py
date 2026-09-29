"""
StructuralBot - AI Service Layer

This module provides a provider-independent interface for the AI assistant.

Important:
- Telegram handlers must not call an AI provider directly.
- Provider-specific implementations will be connected later.
- Engineering calculations remain the responsibility of the calculation engine.
- AI can explain, review, summarize, and assist, but must not silently replace
  deterministic engineering calculations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


# ---------------------------------------------------------
# EXCEPTIONS
# ---------------------------------------------------------


class AIError(Exception):
    """Base exception for AI-related errors."""


class AIConfigurationError(AIError):
    """Raised when AI configuration is missing or invalid."""


class AIProviderError(AIError):
    """Raised when an AI provider fails."""


# ---------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------


@dataclass
class AIRequest:
    """
    Standard request sent to the AI service.
    """

    message: str

    mode: str = "assistant"

    language: str = "fa"

    user_id: Optional[int] = None

    project_id: Optional[str] = None

    context: Dict[str, Any] = field(default_factory=dict)

    system_prompt: Optional[str] = None

    temperature: float = 0.2

    max_tokens: Optional[int] = None


@dataclass
class AIResponse:
    """
    Standard AI response returned to the application.
    """

    text: str

    provider: str = "placeholder"

    model: Optional[str] = None

    usage: Dict[str, Any] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    success: bool = True

    error: Optional[str] = None


# ---------------------------------------------------------
# PROVIDER PROTOCOL
# ---------------------------------------------------------


class AIProvider(Protocol):
    """
    Provider interface.

    Any future AI provider must implement this method.
    """

    name: str

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        ...


# ---------------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------------


class EngineeringPromptBuilder:
    """
    Builds safe and structured prompts for engineering assistance.
    """

    BASE_SYSTEM_PROMPT = """
You are an engineering assistant inside StructuralBot.

Your role is to assist civil and structural engineering workflows.

Rules:
1. Be technically clear and concise.
2. Distinguish calculated results from explanations or assumptions.
3. Never invent missing engineering input values.
4. If required data is missing, explicitly request it.
5. Do not claim that a calculation is code-compliant unless the selected
   design code and required inputs have actually been checked.
6. Do not replace deterministic calculation modules with guessed AI output.
7. When reviewing a result, identify possible issues and explain why.
8. Keep units explicit.
9. Mention assumptions when they materially affect the result.
10. For safety-critical engineering decisions, recommend verification by
    a qualified engineer when appropriate.
"""

    MODE_INSTRUCTIONS = {
        "assistant": """
Provide practical engineering assistance and answer the user's question.
""",
        "explain": """
Explain the supplied calculation, formula, engineering concept, or result
in a clear step-by-step manner.
""",
        "review": """
Review the supplied engineering information for missing inputs,
inconsistencies, suspicious values, unit problems, and possible issues.
Do not invent a final design result.
""",
        "project": """
Analyze the supplied project context and help organize the engineering
workflow, inputs, calculations, outputs, and possible next steps.
""",
        "report": """
Help prepare or explain an engineering report using only the supplied
project and calculation information.
""",
    }

    @classmethod
    def build(
        cls,
        request: AIRequest,
    ) -> List[Dict[str, str]]:
        """
        Build provider-independent chat messages.
        """

        mode = request.mode.lower().strip()

        mode_instruction = cls.MODE_INSTRUCTIONS.get(
            mode,
            cls.MODE_INSTRUCTIONS["assistant"],
        )

        language_instruction = (
            "Respond in Persian."
            if request.language == "fa"
            else f"Respond in language code: {request.language}."
        )

        system_parts = [
            cls.BASE_SYSTEM_PROMPT.strip(),
            mode_instruction.strip(),
            language_instruction,
        ]

        if request.system_prompt:
            system_parts.append(
                request.system_prompt.strip()
            )

        if request.context:
            context_text = cls._format_context(
                request.context
            )

            system_parts.append(
                "\nEngineering context:\n"
                + context_text
            )

        return [
            {
                "role": "system",
                "content": "\n\n".join(system_parts),
            },
            {
                "role": "user",
                "content": request.message.strip(),
            },
        ]

    @staticmethod
    def _format_context(
        context: Dict[str, Any],
    ) -> str:
        """
        Convert structured engineering context into readable text.
        """

        lines: List[str] = []

        for key, value in context.items():
            if value is None:
                continue

            if isinstance(value, dict):
                lines.append(
                    f"{key}: {value}"
                )
            elif isinstance(value, list):
                lines.append(
                    f"{key}: {value}"
                )
            else:
                lines.append(
                    f"{key}: {value}"
                )

        return "\n".join(lines)


# ---------------------------------------------------------
# PLACEHOLDER PROVIDER
# ---------------------------------------------------------


class PlaceholderAIProvider:
    """
    Temporary provider used until a real AI API is connected.

    This intentionally does NOT pretend to perform real AI inference.
    """

    name = "placeholder"

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        return AIResponse(
            text=(
                "🤖 دستیار هوشمند هنوز به سرویس AI متصل نشده است.\n\n"
                "ساختار درخواست شما دریافت شد و موتور AI پروژه "
                "آماده اتصال به Provider واقعی است."
            ),
            provider=self.name,
            model=None,
            success=True,
            metadata={
                "mode": request.mode,
                "language": request.language,
                "project_id": request.project_id,
            },
        )


# ---------------------------------------------------------
# AI SERVICE
# ---------------------------------------------------------


class AIService:
    """
    Main application-level AI service.

    The rest of StructuralBot communicates only with this class.
    """

    def __init__(
        self,
        provider: Optional[AIProvider] = None,
    ) -> None:

        self.provider = provider or PlaceholderAIProvider()

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        """
        Generate an AI response.
        """

        self._validate_request(request)

        try:
            return await self.provider.generate(
                request
            )

        except AIError:
            raise

        except Exception as exc:
            raise AIProviderError(
                f"AI provider error: {exc}"
            ) from exc

    async def ask(
        self,
        message: str,
        *,
        language: str = "fa",
        mode: str = "assistant",
        user_id: Optional[int] = None,
        project_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AIResponse:
        """
        Convenience method for simple requests.
        """

        request = AIRequest(
            message=message,
            mode=mode,
            language=language,
            user_id=user_id,
            project_id=project_id,
            context=context or {},
        )

        return await self.generate(request)

    def build_messages(
        self,
        request: AIRequest,
    ) -> List[Dict[str, str]]:
        """
        Build messages that can be passed to an external AI provider.
        """

        self._validate_request(request)

        return EngineeringPromptBuilder.build(
            request
        )

    def set_provider(
        self,
        provider: AIProvider,
    ) -> None:
        """
        Replace the current AI provider.
        """

        if provider is None:
            raise AIConfigurationError(
                "AI provider cannot be None."
            )

        self.provider = provider

    @staticmethod
    def _validate_request(
        request: AIRequest,
    ) -> None:

        if not isinstance(request, AIRequest):
            raise AIConfigurationError(
                "request must be an AIRequest instance."
            )

        if not request.message or not request.message.strip():
            raise AIConfigurationError(
                "AI request message cannot be empty."
            )

        if request.mode not in {
            "assistant",
            "explain",
            "review",
            "project",
            "report",
        }:
            raise AIConfigurationError(
                f"Unsupported AI mode: {request.mode}"
            )

        if not request.language:
            raise AIConfigurationError(
                "AI request language is required."
            )

        if request.temperature < 0:
            raise AIConfigurationError(
                "Temperature cannot be negative."
            )

        if request.max_tokens is not None:
            if request.max_tokens <= 0:
                raise AIConfigurationError(
                    "max_tokens must be greater than zero."
                )


# ---------------------------------------------------------
# GLOBAL SERVICE
# ---------------------------------------------------------


_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """
    Return the shared AI service instance.
    """

    global _ai_service

    if _ai_service is None:
        _ai_service = AIService()

    return _ai_service


def set_ai_service(
    service: AIService,
) -> None:
    """
    Replace the global AI service.

    Useful for tests and future provider configuration.
    """

    global _ai_service

    if not isinstance(service, AIService):
        raise AIConfigurationError(
            "service must be an AIService instance."
        )

    _ai_service = service


# ---------------------------------------------------------
# SIMPLE PUBLIC API
# ---------------------------------------------------------


async def ask_ai(
    message: str,
    *,
    language: str = "fa",
    mode: str = "assistant",
    user_id: Optional[int] = None,
    project_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> AIResponse:
    """
    Application-level helper.
    """

    service = get_ai_service()

    return await service.ask(
        message,
        language=language,
        mode=mode,
        user_id=user_id,
        project_id=project_id,
        context=context,
    )


__all__ = [
    "AIError",
    "AIConfigurationError",
    "AIProviderError",
    "AIRequest",
    "AIResponse",
    "AIProvider",
    "EngineeringPromptBuilder",
    "PlaceholderAIProvider",
    "AIService",
    "get_ai_service",
    "set_ai_service",
    "ask_ai",
]
