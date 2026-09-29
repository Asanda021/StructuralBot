"""
StructuralBot - AI Configuration

Central configuration for the AI subsystem.

AI configuration is kept separate from Telegram handlers and
engineering calculation logic.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------
# ENVIRONMENT HELPERS
# ---------------------------------------------------------


def _env(
    name: str,
    default: Optional[str] = None,
) -> Optional[str]:
    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip()

    return value if value else default


def _env_bool(
    name: str,
    default: bool = False,
) -> bool:

    value = _env(name)

    if value is None:
        return default

    return value.lower() in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


def _env_float(
    name: str,
    default: float,
) -> float:

    value = _env(name)

    if value is None:
        return default

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def _env_int(
    name: str,
    default: int,
) -> int:

    value = _env(name)

    if value is None:
        return default

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------
# AI CONFIGURATION
# ---------------------------------------------------------


@dataclass
class AIConfig:
    """
    Global AI configuration.
    """

    provider: str = "placeholder"

    api_key: Optional[str] = None

    base_url: str = "https://api.openai.com/v1"

    model: Optional[str] = None

    timeout: float = 60.0

    temperature: float = 0.2

    max_tokens: int = 2000

    enabled: bool = False

    daily_limit_free: int = 10

    daily_limit_basic: int = 50

    daily_limit_professional: int = 200

    daily_limit_business: int = 1000

    max_context_chars: int = 20000

    allow_project_context: bool = True

    allow_calculation_context: bool = True

    allow_report_context: bool = True

    log_requests: bool = False

    redact_sensitive_data: bool = True


# ---------------------------------------------------------
# LOAD CONFIGURATION
# ---------------------------------------------------------


def load_ai_config() -> AIConfig:
    """
    Load AI configuration from environment variables.
    """

    provider = (
        _env(
            "AI_PROVIDER",
            "placeholder",
        )
        or "placeholder"
    ).lower()

    api_key = (
        _env("AI_API_KEY")
        or _env("OPENAI_API_KEY")
    )

    base_url = (
        _env(
            "AI_BASE_URL",
            "https://api.openai.com/v1",
        )
        or "https://api.openai.com/v1"
    )

    model = _env("AI_MODEL")

    timeout = _env_float(
        "AI_TIMEOUT",
        60.0,
    )

    temperature = _env_float(
        "AI_TEMPERATURE",
        0.2,
    )

    max_tokens = _env_int(
        "AI_MAX_TOKENS",
        2000,
    )

    enabled = _env_bool(
        "AI_ENABLED",
        False,
    )

    daily_limit_free = _env_int(
        "AI_DAILY_LIMIT_FREE",
        10,
    )

    daily_limit_basic = _env_int(
        "AI_DAILY_LIMIT_BASIC",
        50,
    )

    daily_limit_professional = _env_int(
        "AI_DAILY_LIMIT_PROFESSIONAL",
        200,
    )

    daily_limit_business = _env_int(
        "AI_DAILY_LIMIT_BUSINESS",
        1000,
    )

    max_context_chars = _env_int(
        "AI_MAX_CONTEXT_CHARS",
        20000,
    )

    allow_project_context = _env_bool(
        "AI_ALLOW_PROJECT_CONTEXT",
        True,
    )

    allow_calculation_context = _env_bool(
        "AI_ALLOW_CALCULATION_CONTEXT",
        True,
    )

    allow_report_context = _env_bool(
        "AI_ALLOW_REPORT_CONTEXT",
        True,
    )

    log_requests = _env_bool(
        "AI_LOG_REQUESTS",
        False,
    )

    redact_sensitive_data = _env_bool(
        "AI_REDACT_SENSITIVE_DATA",
        True,
    )

    return AIConfig(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout=timeout,
        temperature=temperature,
        max_tokens=max_tokens,
        enabled=enabled,
        daily_limit_free=daily_limit_free,
        daily_limit_basic=daily_limit_basic,
        daily_limit_professional=daily_limit_professional,
        daily_limit_business=daily_limit_business,
        max_context_chars=max_context_chars,
        allow_project_context=allow_project_context,
        allow_calculation_context=allow_calculation_context,
        allow_report_context=allow_report_context,
        log_requests=log_requests,
        redact_sensitive_data=redact_sensitive_data,
    )


# ---------------------------------------------------------
# GLOBAL CONFIG
# ---------------------------------------------------------


_ai_config: Optional[AIConfig] = None


def get_ai_config() -> AIConfig:
    """
    Return the shared AI configuration.
    """

    global _ai_config

    if _ai_config is None:
        _ai_config = load_ai_config()

    return _ai_config


def reload_ai_config() -> AIConfig:
    """
    Reload configuration from environment variables.
    """

    global _ai_config

    _ai_config = load_ai_config()

    return _ai_config


def set_ai_config(
    config: AIConfig,
) -> None:
    """
    Replace the current AI configuration.
    """

    global _ai_config

    if not isinstance(config, AIConfig):
        raise TypeError(
            "config must be an AIConfig instance."
        )

    _ai_config = config


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------


def validate_ai_config(
    config: Optional[AIConfig] = None,
) -> list[str]:
    """
    Return configuration problems.

    An empty list means the configuration is valid for the
    selected provider.
    """

    config = config or get_ai_config()

    errors: list[str] = []

    if not config.provider:
        errors.append(
            "AI provider is not specified."
        )

    if config.timeout <= 0:
        errors.append(
            "AI timeout must be greater than zero."
        )

    if not 0 <= config.temperature <= 2:
        errors.append(
            "AI temperature must be between 0 and 2."
        )

    if config.max_tokens <= 0:
        errors.append(
            "AI max tokens must be greater than zero."
        )

    if config.max_context_chars <= 0:
        errors.append(
            "AI maximum context length must be greater than zero."
        )

    limits = [
        config.daily_limit_free,
        config.daily_limit_basic,
        config.daily_limit_professional,
        config.daily_limit_business,
    ]

    if any(limit < 0 for limit in limits):
        errors.append(
            "AI daily limits cannot be negative."
        )

    provider = config.provider.lower()

    if provider not in {
        "placeholder",
        "none",
        "disabled",
        "openai",
        "openai-compatible",
        "openai_compatible",
    }:
        errors.append(
            f"Unsupported AI provider: {config.provider}"
        )

    if (
        config.enabled
        and provider not in {
            "placeholder",
            "none",
            "disabled",
        }
    ):
        if not config.api_key:
            errors.append(
                "AI API key is required when AI is enabled."
            )

        if not config.model:
            errors.append(
                "AI model is required when AI is enabled."
            )

    return errors


def ai_is_ready(
    config: Optional[AIConfig] = None,
) -> bool:
    """
    Check whether AI is ready for real execution.
    """

    config = config or get_ai_config()

    errors = validate_ai_config(config)

    return (
        config.enabled
        and not errors
        and config.provider.lower()
        not in {
            "placeholder",
            "none",
            "disabled",
        }
    )


# ---------------------------------------------------------
# PLAN LIMITS
# ---------------------------------------------------------


PLAN_LIMITS = {
    "free": "daily_limit_free",
    "basic": "daily_limit_basic",
    "professional": "daily_limit_professional",
    "business": "daily_limit_business",
}


def get_plan_daily_limit(
    plan: str,
    config: Optional[AIConfig] = None,
) -> int:
    """
    Return the daily AI request limit for a subscription plan.
    """

    config = config or get_ai_config()

    normalized = (
        plan or "free"
    ).strip().lower()

    attribute = PLAN_LIMITS.get(
        normalized,
        "daily_limit_free",
    )

    return int(
        getattr(
            config,
            attribute,
            config.daily_limit_free,
        )
    )


# ---------------------------------------------------------
# CONTEXT LIMIT
# ---------------------------------------------------------


def trim_ai_context(
    text: str,
    config: Optional[AIConfig] = None,
) -> str:
    """
    Limit context size before sending it to an AI provider.

    Keeps the beginning and end so that both project information
    and recent calculation/output information can remain visible.
    """

    config = config or get_ai_config()

    if not text:
        return ""

    max_chars = max(
        1000,
        config.max_context_chars,
    )

    if len(text) <= max_chars:
        return text

    first_size = max_chars // 2

    last_size = max_chars - first_size

    return (
        text[:first_size]
        + "\n\n"
        + "[... context trimmed ...]"
        + "\n\n"
        + text[-last_size:]
    )


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------


__all__ = [
    "AIConfig",
    "PLAN_LIMITS",
    "load_ai_config",
    "get_ai_config",
    "reload_ai_config",
    "set_ai_config",
    "validate_ai_config",
    "ai_is_ready",
    "get_plan_daily_limit",
    "trim_ai_context",
]
