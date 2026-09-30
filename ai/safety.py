from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass(frozen=True)
class SafetyResult:
    allowed: bool
    sanitized_text: str
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# These patterns are intentionally broad.
# They are not treated as proof of malicious intent; they are signals that
# the text should not be allowed to override the AI system instructions.
_PROMPT_INJECTION_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore the system prompt",
    "forget your instructions",
    "override your instructions",
    "reveal your system prompt",
    "show me your system prompt",
    "developer message",
    "system message",
    "jailbreak",
    "bypass safety",
    "disable safety",
)


def _normalize(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def detect_prompt_injection(text: str) -> List[str]:
    normalized = _normalize(text)
    found: List[str] = []

    for pattern in _PROMPT_INJECTION_PATTERNS:
        if pattern in normalized:
            found.append(pattern)

    return found


def check_input_safety(
    text: str,
    *,
    max_chars: int = 12000,
) -> SafetyResult:
    value = (text or "").strip()
    reasons: List[str] = []
    warnings: List[str] = []

    if not value:
        return SafetyResult(
            allowed=False,
            sanitized_text="",
            reasons=["Input is empty."],
        )

    if max_chars < 1:
        max_chars = 12000

    if len(value) > max_chars:
        value = value[:max_chars]
        warnings.append(
            f"Input was truncated to {max_chars} characters."
        )

    injections = detect_prompt_injection(value)

    if injections:
        warnings.append(
            "Prompt-injection-like instructions were detected and will "
            "not be treated as system instructions."
        )

    return SafetyResult(
        allowed=True,
        sanitized_text=value,
        reasons=reasons,
        warnings=warnings,
    )


def check_output_safety(
    text: str,
    *,
    max_chars: int = 12000,
) -> SafetyResult:
    value = (text or "").strip()
    reasons: List[str] = []
    warnings: List[str] = []

    if not value:
        return SafetyResult(
            allowed=False,
            sanitized_text="",
            reasons=["AI output is empty."],
        )

    if max_chars < 1:
        max_chars = 12000

    if len(value) > max_chars:
        value = value[:max_chars]
        warnings.append(
            f"Output was truncated to {max_chars} characters."
        )

    # The AI must not claim that its response is an approved structural
    # design. We flag explicit approval-style language for downstream review.
    approval_phrases = (
        "approved structural design",
        "structurally approved",
        "no engineer review is required",
        "does not need engineer approval",
    )

    normalized = _normalize(value)

    if any(phrase in normalized for phrase in approval_phrases):
        warnings.append(
            "Output contains language suggesting engineering approval."
        )

    return SafetyResult(
        allowed=True,
        sanitized_text=value,
        reasons=reasons,
        warnings=warnings,
    )


def sanitize_for_prompt(
    text: str,
    *,
    max_chars: int = 12000,
) -> str:
    result = check_input_safety(
        text,
        max_chars=max_chars,
    )

    if not result.allowed:
        return ""

    return result.sanitized_text


def combine_safety_results(
    results: Iterable[SafetyResult],
) -> SafetyResult:
    results = list(results)

    if not results:
        return SafetyResult(
            allowed=True,
            sanitized_text="",
        )

    allowed = all(item.allowed for item in results)

    reasons: List[str] = []
    warnings: List[str] = []

    for item in results:
        reasons.extend(item.reasons)
        warnings.extend(item.warnings)

    sanitized = next(
        (
            item.sanitized_text
            for item in results
            if item.sanitized_text
        ),
        "",
    )

    return SafetyResult(
        allowed=allowed,
        sanitized_text=sanitized,
        reasons=list(dict.fromkeys(reasons)),
        warnings=list(dict.fromkeys(warnings)),
    )


__all__ = [
    "SafetyResult",
    "detect_prompt_injection",
    "check_input_safety",
    "check_output_safety",
    "sanitize_for_prompt",
    "combine_safety_results",
]
