from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class AIConfig:
    enabled: bool = False
    provider: str = "placeholder"
    model: str = "placeholder"
    api_key: str = ""
    base_url: str = ""
    timeout: float = 30.0
    temperature: float = 0.2
    max_tokens: int = 1200

    max_input_chars: int = 12000
    max_output_chars: int = 12000

    daily_request_limit: int = 50
    monthly_request_limit: int = 1000

    allow_engineering_advice: bool = True
    require_disclaimer: bool = True

    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "AIConfig":
        provider = os.getenv("AI_PROVIDER", "placeholder").strip()
        model = os.getenv("AI_MODEL", "placeholder").strip()

        return cls(
            enabled=_env_bool("AI_ENABLED", False),
            provider=provider or "placeholder",
            model=model or "placeholder",
            api_key=os.getenv("AI_API_KEY", "").strip(),
            base_url=os.getenv("AI_BASE_URL", "").strip(),
            timeout=max(1.0, _env_float("AI_TIMEOUT", 30.0)),
            temperature=min(
                2.0,
                max(0.0, _env_float("AI_TEMPERATURE", 0.2)),
            ),
            max_tokens=max(
                1,
                _env_int("AI_MAX_TOKENS", 1200),
            ),
            max_input_chars=max(
                100,
                _env_int("AI_MAX_INPUT_CHARS", 12000),
            ),
            max_output_chars=max(
                100,
                _env_int("AI_MAX_OUTPUT_CHARS", 12000),
            ),
            daily_request_limit=max(
                0,
                _env_int("AI_DAILY_REQUEST_LIMIT", 50),
            ),
            monthly_request_limit=max(
                0,
                _env_int("AI_MONTHLY_REQUEST_LIMIT", 1000),
            ),
            allow_engineering_advice=_env_bool(
                "AI_ALLOW_ENGINEERING_ADVICE",
                True,
            ),
            require_disclaimer=_env_bool(
                "AI_REQUIRE_DISCLAIMER",
                True,
            ),
        )

    def is_usable(self) -> bool:
        if not self.enabled:
            return False

        if self.provider.strip().lower() == "placeholder":
            return False

        return True

    def sanitized(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_input_chars": self.max_input_chars,
            "max_output_chars": self.max_output_chars,
            "daily_request_limit": self.daily_request_limit,
            "monthly_request_limit": self.monthly_request_limit,
            "allow_engineering_advice": self.allow_engineering_advice,
            "require_disclaimer": self.require_disclaimer,
        }


_config: AIConfig | None = None


def get_ai_config(refresh: bool = False) -> AIConfig:
    global _config

    if _config is None or refresh:
        _config = AIConfig.from_env()

    return _config


def set_ai_config(config: AIConfig) -> None:
    global _config
    _config = config


__all__ = [
    "AIConfig",
    "get_ai_config",
    "set_ai_config",
]
