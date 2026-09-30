"""
Central AI orchestration manager for StructuralBot.

This module connects the AI subsystems:

    config
        ↓
    usage limits
        ↓
    safety inspection
        ↓
    engineering context
        ↓
    prompt builder
        ↓
    AI provider
        ↓
    output safety inspection
        ↓
    usage recording

The manager is intentionally provider-independent.

Engineering calculations remain deterministic and are NOT delegated
to the AI model. AI is used for explanation, review, assistance,
summaries, and controlled engineering interaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence

from .config import (
    AIConfig,
    get_ai_config,
    ai_is_ready,
    trim_ai_context,
)

from .context import (
    context_to_text,
    merge_contexts,
    filter_context_for_mode,
)

from .prompts import PromptBuilder

from .safety import (
    SafetyResult,
    prepare_ai_input,
    inspect_output,
    engineering_verification_note,
)

from .service import (
    AIError,
    AIRequest,
    AIResponse,
    AIService,
    get_ai_service,
)

from .usage import (
    AIUsageLimitError,
    AIInsufficientCreditsError,
    check_ai_usage,
    record_ai_success,
    record_ai_failure,
)


# ============================================================
# EXCEPTIONS
# ============================================================

class AIManagerError(AIError):
    """Base exception for AI manager errors."""


class AIManagerConfigurationError(AIManagerError):
    """AI manager configuration problem."""


class AIManagerSafetyError(AIManagerError):
    """AI input/output failed a safety requirement."""


# ============================================================
# MANAGER REQUEST
# ============================================================

@dataclass
class AIManagerRequest:
    """
    High-level AI request.

    This is the preferred request object for handlers.
    """

    message: str

    user_id: str

    mode: str = "assistant"

    language: str = "fa"

    plan: str = "free"

    project_id: Optional[str] = None

    context: Optional[Mapping[str, Any]] = None

    format: str = "normal"

    specialty: Optional[str] = None

    system_prompt: Optional[str] = None

    temperature: Optional[float] = None

    max_tokens: Optional[int] = None

    estimated_credits: float = 0.0

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# MANAGER RESPONSE
# ============================================================

@dataclass
class AIManagerResponse:
    """
    High-level AI response.

    Contains both the user-facing AI response and
    internal metadata required by the application.
    """

    text: str

    success: bool = True

    provider: str = "unknown"

    model: str = "unknown"

    usage: Dict[str, Any] = field(
        default_factory=dict
    )

    safety: Optional[SafetyResult] = None

    verification_note: str = ""

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "success": self.success,
            "provider": self.provider,
            "model": self.model,
            "usage": self.usage,
            "verification_note": self.verification_note,
            "error": self.error,
            "metadata": self.metadata,
        }


# ============================================================
# AI MANAGER
# ============================================================

class AIManager:
    """
    Main AI orchestration layer.

    Handlers should preferably call this class instead of
    directly interacting with providers.
    """

    def __init__(
        self,
        *,
        service: Optional[AIService] = None,
        config: Optional[AIConfig] = None,
        prompt_builder: Optional[PromptBuilder] = None,
    ) -> None:

        self.service = service or get_ai_service()

        self.config = config or get_ai_config()

        self.prompt_builder = (
            prompt_builder
            or PromptBuilder()
        )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def refresh_config(self) -> AIConfig:
        """Reload configuration from environment."""

        self.config = get_ai_config()

        return self.config

    def is_available(self) -> bool:
        """
        Return whether the AI system is configured and enabled.

        The provider may still be unavailable at runtime.
        """

        try:
            return bool(
                self.config.enabled
                and ai_is_ready()
            )
        except Exception:
            return False

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_messages(
        self,
        request: AIManagerRequest,
        context: Mapping[str, Any],
    ) -> Sequence[Mapping[str, str]]:
        """
        Build provider messages using the central prompt builder.
        """

        system_prompt = (
            request.system_prompt
            if request.system_prompt
            else self.prompt_builder.build_system_prompt(
                language=request.language,
                mode=request.mode,
                format=request.format,
                specialty=request.specialty,
            )
        )

        context_text = context_to_text(context)

        user_message = request.message.strip()

        if context_text:
            user_message = (
                f"{user_message}\n\n"
                "ENGINEERING CONTEXT:\n"
                f"{context_text}"
            )

        return self.prompt_builder.build_messages(
            system_prompt=system_prompt,
            user_message=user_message,
        )

    # ========================================================
    # CONTEXT
    # ========================================================

    def _prepare_context(
        self,
        request: AIManagerRequest,
    ) -> Dict[str, Any]:

        raw_context: Dict[str, Any] = dict(
            request.context or {}
        )

        filtered = filter_context_for_mode(
            raw_context,
            request.mode,
        )

        merged = merge_contexts(
            filtered,
        )

        text = context_to_text(merged)

        trimmed = trim_ai_context(
            text,
            max_chars=self.config.max_context_chars,
        )

        if trimmed != text:
            return {
                "context": trimmed,
                "context_trimmed": True,
            }

        return merged

    # ========================================================
    # INPUT SAFETY
    # ========================================================

    def _prepare_input(
        self,
        request: AIManagerRequest,
        context: Mapping[str, Any],
    ):
        """
        Run safety preprocessing.

        Returns the sanitized text/context package.
        """

        combined_context = context_to_text(
            context
        )

        result = prepare_ai_input(
            user_text=request.message,
            context_text=combined_context,
        )

        return result

    # ========================================================
    # USAGE
    # ========================================================

    def _check_usage(
        self,
        request: AIManagerRequest,
    ) -> None:

        check_ai_usage(
            user_id=request.user_id,
            plan=request.plan,
            estimated_credits=request.estimated_credits,
        )

    # ========================================================
    # REQUEST
    # ========================================================

    def generate(
        self,
        request: AIManagerRequest,
    ) -> AIManagerResponse:
        """
        Execute one complete AI request.

        Flow:

        1. Validate request
        2. Check usage
        3. Prepare context
        4. Inspect input safety
        5. Build prompt
        6. Call AI service/provider
        7. Inspect output
        8. Record usage
        9. Return response
        """

        if not isinstance(
            request,
            AIManagerRequest,
        ):
            raise TypeError(
                "request must be AIManagerRequest"
            )

        if not request.message.strip():
            return AIManagerResponse(
                text="پیام ورودی خالی است.",
                success=False,
                error="empty_message",
            )

        # ----------------------------------------------------
        # Configuration
        # ----------------------------------------------------

        if not self.config.enabled:
            return AIManagerResponse(
                text=(
                    "دستیار هوشمند در حال حاضر "
                    "فعال نشده است."
                ),
                success=False,
                error="ai_disabled",
            )

        # ----------------------------------------------------
        # Usage
        # ----------------------------------------------------

        try:
            self._check_usage(request)

        except (
            AIUsageLimitError,
            AIInsufficientCreditsError,
        ) as exc:

            return AIManagerResponse(
                text=str(exc),
                success=False,
                error="usage_limit",
            )

        # ----------------------------------------------------
        # Context
        # ----------------------------------------------------

        context = self._prepare_context(
            request
        )

        # ----------------------------------------------------
        # Safety
        # ----------------------------------------------------

        try:
            prepared = self._prepare_input(
                request,
                context,
            )

        except Exception as exc:

            record_ai_failure(
                user_id=request.user_id,
            )

            return AIManagerResponse(
                text=(
                    "ورودی برای پردازش هوش مصنوعی "
                    "قابل استفاده نیست."
                ),
                success=False,
                error=f"safety_error: {exc}",
            )

        if isinstance(prepared, tuple):
            sanitized_message = prepared[0]
            sanitized_context = (
                prepared[1]
                if len(prepared) > 1
                else ""
            )
        else:
            sanitized_message = request.message
            sanitized_context = context_to_text(
                context
            )

        # ----------------------------------------------------
        # Prompt
        # ----------------------------------------------------

        prompt_context = {
            "context": sanitized_context
        }

        effective_request = AIManagerRequest(
            message=sanitized_message,
            user_id=request.user_id,
            mode=request.mode,
            language=request.language,
            plan=request.plan,
            project_id=request.project_id,
            context=prompt_context,
            format=request.format,
            specialty=request.specialty,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            estimated_credits=request.estimated_credits,
            metadata=dict(request.metadata),
        )

        try:
            messages = self._build_messages(
                effective_request,
                prompt_context,
            )

        except Exception as exc:

            record_ai_failure(
                user_id=request.user_id,
            )

            return AIManagerResponse(
                text=(
                    "خطا در آماده‌سازی درخواست "
                    "هوش مصنوعی."
                ),
                success=False,
                error=f"prompt_error: {exc}",
            )

        # ----------------------------------------------------
        # AI service request
        # ----------------------------------------------------

        ai_request = AIRequest(
            message=sanitized_message,
            mode=request.mode,
            language=request.language,
            user_id=request.user_id,
            project_id=request.project_id,
            context=prompt_context,
            system_prompt=request.system_prompt,
            temperature=(
                request.temperature
                if request.temperature is not None
                else self.config.temperature
            ),
            max_tokens=(
                request.max_tokens
                if request.max_tokens is not None
                else self.config.max_tokens
            ),
        )

        # Attach generated messages as metadata when supported.
        ai_request_metadata = {
            "messages": list(messages),
            "manager": "AIManager",
            "mode": request.mode,
            "format": request.format,
            "specialty": request.specialty,
        }

        # ----------------------------------------------------
        # Provider execution
        # ----------------------------------------------------

        try:

            response = self.service.generate(
                ai_request
            )

        except Exception as exc:

            record_ai_failure(
                user_id=request.user_id,
            )

            return AIManagerResponse(
                text=(
                    "در ارتباط با سرویس هوش مصنوعی "
                    "خطایی رخ داد."
                ),
                success=False,
                error=str(exc),
                metadata=ai_request_metadata,
            )

        # ----------------------------------------------------
        # Normalize response
        # ----------------------------------------------------

        if not isinstance(
            response,
            AIResponse,
        ):
            record_ai_failure(
                user_id=request.user_id,
            )

            return AIManagerResponse(
                text="پاسخ نامعتبر از سرویس AI دریافت شد.",
                success=False,
                error="invalid_ai_response",
                metadata=ai_request_metadata,
            )

        if not response.success:

            record_ai_failure(
                user_id=request.user_id,
            )

            return AIManagerResponse(
                text=(
                    response.text
                    or "پاسخی از سرویس AI دریافت نشد."
                ),
                success=False,
                provider=response.provider,
                model=response.model,
                usage=response.usage or {},
                error=response.error,
                metadata={
                    **ai_request_metadata,
                    **(response.metadata or {}),
                },
            )

        # ----------------------------------------------------
        # Output safety
        # ----------------------------------------------------

        output_text = (
            response.text
            or ""
        ).strip()

        try:

            output_safety = inspect_output(
                output_text
            )

        except Exception:
            output_safety = None

        if (
            output_safety is not None
            and not output_safety.safe
        ):

            record_ai_failure(
                user_id=request.user_id,
            )

            return AIManagerResponse(
                text=(
                    "پاسخ تولیدشده نیاز به بررسی "
                    "ایمنی و فنی دارد و مستقیماً "
                    "نمایش داده نشد."
                ),
                success=False,
                provider=response.provider,
                model=response.model,
                safety=output_safety,
                error="unsafe_output",
                metadata={
                    **ai_request_metadata,
                    **(response.metadata or {}),
                },
            )

        # ----------------------------------------------------
        # Usage extraction
        # ----------------------------------------------------

        usage = response.usage or {}

        input_tokens = self._extract_token_count(
            usage,
            "input_tokens",
            "prompt_tokens",
        )

        output_tokens = self._extract_token_count(
            usage,
            "output_tokens",
            "completion_tokens",
        )

        total_tokens = self._extract_token_count(
            usage,
            "total_tokens",
        )

        if total_tokens <= 0:
            total_tokens = (
                input_tokens + output_tokens
            )

        credits = self._calculate_credits(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

        record_ai_success(
            user_id=request.user_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            credits=credits,
        )

        # ----------------------------------------------------
        # Verification note
        # ----------------------------------------------------

        verification_note = (
            engineering_verification_note(
                mode=request.mode
            )
        )

        # ----------------------------------------------------
        # Final response
        # ----------------------------------------------------

        return AIManagerResponse(
            text=output_text,
            success=True,
            provider=response.provider,
            model=response.model,
            usage={
                **usage,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "credits": credits,
            },
            safety=output_safety,
            verification_note=verification_note,
            metadata={
                **ai_request_metadata,
                **(response.metadata or {}),
            },
        )

    # ========================================================
    # TOKEN HELPERS
    # ========================================================

    @staticmethod
    def _extract_token_count(
        usage: Mapping[str, Any],
        *keys: str,
    ) -> int:

        for key in keys:

            value = usage.get(key)

            if value is None:
                continue

            try:
                return max(
                    0,
                    int(value),
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

        return 0

    # ========================================================
    # CREDIT CALCULATION
    # ========================================================

    @staticmethod
    def _calculate_credits(
        *,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
    ) -> float:
        """
        Internal normalized credit calculation.

        This is intentionally NOT tied to a provider price.

        Later billing.py can map actual provider costs
        to commercial credits.
        """

        if total_tokens <= 0:
            return 0.0

        # Temporary normalized unit:
        # 1 credit per 1,000 tokens.
        #
        # This is a usage unit, NOT a monetary price.
        return round(
            total_tokens / 1000.0,
            4,
        )

    # ========================================================
    # CONVENIENCE METHODS
    # ========================================================

    def ask(
        self,
        *,
        message: str,
        user_id: str,
        language: str = "fa",
        plan: str = "free",
        mode: str = "assistant",
        context: Optional[Mapping[str, Any]] = None,
        project_id: Optional[str] = None,
        format: str = "normal",
        specialty: Optional[str] = None,
    ) -> AIManagerResponse:

        request = AIManagerRequest(
            message=message,
            user_id=str(user_id),
            language=language,
            plan=plan,
            mode=mode,
            context=context,
            project_id=project_id,
            format=format,
            specialty=specialty,
        )

        return self.generate(request)

    def explain(
        self,
        *,
        message: str,
        user_id: str,
        language: str = "fa",
        plan: str = "free",
        context: Optional[Mapping[str, Any]] = None,
        project_id: Optional[str] = None,
        specialty: Optional[str] = None,
    ) -> AIManagerResponse:

        return self.ask(
            message=message,
            user_id=user_id,
            language=language,
            plan=plan,
            mode="explain",
            context=context,
            project_id=project_id,
            specialty=specialty,
        )

    def review(
        self,
        *,
        message: str,
        user_id: str,
        language: str = "fa",
        plan: str = "free",
        context: Optional[Mapping[str, Any]] = None,
        project_id: Optional[str] = None,
        specialty: Optional[str] = None,
    ) -> AIManagerResponse:

        return self.ask(
            message=message,
            user_id=user_id,
            language=language,
            plan=plan,
            mode="review",
            context=context,
            project_id=project_id,
            specialty=specialty,
        )

    def project(
        self,
        *,
        message: str,
        user_id: str,
        language: str = "fa",
        plan: str = "free",
        context: Optional[Mapping[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> AIManagerResponse:

        return self.ask(
            message=message,
            user_id=user_id,
            language=language,
            plan=plan,
            mode="project",
            context=context,
            project_id=project_id,
        )

    def report(
        self,
        *,
        message: str,
        user_id: str,
        language: str = "fa",
        plan: str = "free",
        context: Optional[Mapping[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> AIManagerResponse:

        return self.ask(
            message=message,
            user_id=user_id,
            language=language,
            plan=plan,
            mode="report",
            context=context,
            project_id=project_id,
        )


# ============================================================
# GLOBAL MANAGER
# ============================================================

_default_ai_manager: Optional[AIManager] = None


def get_ai_manager() -> AIManager:
    """Return the global AI manager."""

    global _default_ai_manager

    if _default_ai_manager is None:
        _default_ai_manager = AIManager()

    return _default_ai_manager


def set_ai_manager(
    manager: AIManager,
) -> None:
    """Replace the global AI manager."""

    global _default_ai_manager

    _default_ai_manager = manager


# ============================================================
# GLOBAL CONVENIENCE FUNCTION
# ============================================================

def ask_ai_manager(
    *,
    message: str,
    user_id: str,
    language: str = "fa",
    plan: str = "free",
    mode: str = "assistant",
    context: Optional[Mapping[str, Any]] = None,
    project_id: Optional[str] = None,
    format: str = "normal",
    specialty: Optional[str] = None,
) -> AIManagerResponse:

    return get_ai_manager().ask(
        message=message,
        user_id=user_id,
        language=language,
        plan=plan,
        mode=mode,
        context=context,
        project_id=project_id,
        format=format,
        specialty=specialty,
    )


__all__ = [
    "AIManagerError",
    "AIManagerConfigurationError",
    "AIManagerSafetyError",
    "AIManagerRequest",
    "AIManagerResponse",
    "AIManager",
    "get_ai_manager",
    "set_ai_manager",
    "ask_ai_manager",
]
