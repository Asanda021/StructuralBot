"""
StructuralBot - AI Safety Layer

Controls AI input/output boundaries.

This module does not perform structural calculations.
It helps prevent:
- unsafe fabricated engineering values;
- accidental exposure of secrets;
- prompt injection through project data;
- unsupported claims of code compliance;
- uncontrolled AI output size.

The deterministic calculation engine remains the source of truth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from ai.config import get_ai_config, trim_ai_context


# ---------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------


@dataclass
class SafetyIssue:
    """
    A detected safety or quality issue.
    """

    code: str
    severity: str
    message: str
    category: str = "general"
    details: Optional[str] = None


@dataclass
class SafetyResult:
    """
    Result of safety inspection.
    """

    safe: bool

    text: str

    issues: List[SafetyIssue] = field(
        default_factory=list
    )

    blocked: bool = False

    modified: bool = False


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------


MAX_INPUT_CHARS = 30000
MAX_OUTPUT_CHARS = 30000

BLOCKED_SECRET_PATTERNS = [
    r"(?i)\bapi[_-]?key\s*[:=]\s*\S+",
    r"(?i)\bsecret\s*[:=]\s*\S+",
    r"(?i)\bpassword\s*[:=]\s*\S+",
    r"(?i)\bbearer\s+[A-Za-z0-9._\-]+",
    r"(?i)\btoken\s*[:=]\s*\S+",
]

PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)ignore\s+(the\s+)?system\s+prompt",
    r"(?i)disregard\s+(all\s+)?previous\s+instructions",
    r"(?i)reveal\s+(the\s+)?system\s+prompt",
    r"(?i)show\s+(me\s+)?your\s+hidden\s+instructions",
    r"(?i)developer\s+message",
    r"(?i)system\s+message",
]

UNSUPPORTED_CERTAINTY_PATTERNS = [
    r"(?i)\b100%\s*(safe|correct|compliant)\b",
    r"(?i)\bguaranteed\s+(safe|correct|compliant)\b",
    r"(?i)\bdefinitely\s+code[- ]compliant\b",
]

UNSAFE_AUTOMATION_PATTERNS = [
    r"(?i)\bskip\s+(engineering|structural)\s+check",
    r"(?i)\bskip\s+code\s+check",
    r"(?i)\bno\s+(need|necessity)\s+for\s+(engineer|verification)",
]


# ---------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------


def normalize_text(
    text: Any,
) -> str:
    """
    Normalize arbitrary input into safe text.
    """

    if text is None:
        return ""

    text = str(text)

    text = text.replace("\x00", "")

    return text.strip()


# ---------------------------------------------------------
# SECRET REDACTION
# ---------------------------------------------------------


def redact_secrets(
    text: str,
) -> Tuple[str, List[SafetyIssue]]:
    """
    Remove common API keys, tokens and credentials.
    """

    text = normalize_text(text)

    issues: List[SafetyIssue] = []

    for pattern in BLOCKED_SECRET_PATTERNS:

        new_text, count = re.subn(
            pattern,
            "[REDACTED_SECRET]",
            text,
        )

        if count:
            text = new_text

            issues.append(
                SafetyIssue(
                    code="SECRET_REDACTED",
                    severity="high",
                    category="privacy",
                    message=(
                        "A possible secret or credential "
                        "was removed from the AI input."
                    ),
                )
            )

    return text, issues


# ---------------------------------------------------------
# PROMPT INJECTION DETECTION
# ---------------------------------------------------------


def detect_prompt_injection(
    text: str,
) -> List[SafetyIssue]:
    """
    Detect common attempts to override application instructions.

    Detection does not automatically mean malicious intent.
    It marks the content for controlled handling.
    """

    text = normalize_text(text)

    issues: List[SafetyIssue] = []

    for pattern in PROMPT_INJECTION_PATTERNS:

        if re.search(pattern, text):

            issues.append(
                SafetyIssue(
                    code="PROMPT_INJECTION",
                    severity="medium",
                    category="security",
                    message=(
                        "The input contains text that may attempt "
                        "to override AI instructions."
                    ),
                )
            )

            break

    return issues


# ---------------------------------------------------------
# UNSAFE AUTOMATION DETECTION
# ---------------------------------------------------------


def detect_unsafe_automation(
    text: str,
) -> List[SafetyIssue]:
    """
    Detect requests that attempt to bypass engineering verification.
    """

    text = normalize_text(text)

    issues: List[SafetyIssue] = []

    for pattern in UNSAFE_AUTOMATION_PATTERNS:

        if re.search(pattern, text):

            issues.append(
                SafetyIssue(
                    code="UNSAFE_AUTOMATION",
                    severity="high",
                    category="engineering_safety",
                    message=(
                        "The request appears to bypass an engineering "
                        "or code verification step."
                    ),
                )
            )

    return issues


# ---------------------------------------------------------
# CERTAINTY CLAIM DETECTION
# ---------------------------------------------------------


def detect_unsupported_certainty(
    text: str,
) -> List[SafetyIssue]:
    """
    Detect overly certain engineering claims.
    """

    text = normalize_text(text)

    issues: List[SafetyIssue] = []

    for pattern in UNSUPPORTED_CERTAINTY_PATTERNS:

        if re.search(pattern, text):

            issues.append(
                SafetyIssue(
                    code="UNSUPPORTED_CERTAINTY",
                    severity="medium",
                    category="engineering_safety",
                    message=(
                        "The text contains an absolute engineering "
                        "certainty claim."
                    ),
                )
            )

    return issues


# ---------------------------------------------------------
# CODE COMPLIANCE CLAIMS
# ---------------------------------------------------------


def detect_code_compliance_claim(
    text: str,
) -> List[SafetyIssue]:
    """
    Detect statements that may claim code compliance without context.
    """

    text = normalize_text(text)

    patterns = [
        r"(?i)\bcode[- ]compliant\b",
        r"(?i)\bfully\s+complies\s+with\b",
        r"(?i)\bکاملاً\s+مطابق\s+آیین.?نامه\b",
        r"(?i)\bمطابق\s+آیین.?نامه\s+است\b",
    ]

    for pattern in patterns:

        if re.search(pattern, text):

            return [
                SafetyIssue(
                    code="CODE_COMPLIANCE_CLAIM",
                    severity="medium",
                    category="engineering_safety",
                    message=(
                        "A code-compliance claim was detected. "
                        "It requires verification against the selected "
                        "code and actual calculation inputs."
                    ),
                )
            ]

    return []


# ---------------------------------------------------------
# INPUT INSPECTION
# ---------------------------------------------------------


def inspect_input(
    text: str,
) -> SafetyResult:
    """
    Inspect user input before sending it to an AI provider.
    """

    text = normalize_text(text)

    issues: List[SafetyIssue] = []

    if not text:

        return SafetyResult(
            safe=False,
            text="",
            issues=[
                SafetyIssue(
                    code="EMPTY_INPUT",
                    severity="medium",
                    message="AI input is empty.",
                )
            ],
            blocked=True,
        )

    if len(text) > MAX_INPUT_CHARS:

        return SafetyResult(
            safe=False,
            text=text[:MAX_INPUT_CHARS],
            issues=[
                SafetyIssue(
                    code="INPUT_TOO_LARGE",
                    severity="medium",
                    message=(
                        "AI input exceeded the maximum allowed size."
                    ),
                )
            ],
            blocked=True,
        )

    text, secret_issues = redact_secrets(text)

    issues.extend(secret_issues)

    issues.extend(
        detect_prompt_injection(text)
    )

    issues.extend(
        detect_unsafe_automation(text)
    )

    blocked = any(
        issue.severity == "high"
        and issue.code == "UNSAFE_AUTOMATION"
        for issue in issues
    )

    return SafetyResult(
        safe=not blocked,
        text=text,
        issues=issues,
        blocked=blocked,
        modified=text != normalize_text(
            text
        ),
    )


# ---------------------------------------------------------
# OUTPUT INSPECTION
# ---------------------------------------------------------


def inspect_output(
    text: str,
) -> SafetyResult:
    """
    Inspect AI output before returning it to the user.
    """

    text = normalize_text(text)

    if not text:

        return SafetyResult(
            safe=False,
            text="",
            blocked=True,
            issues=[
                SafetyIssue(
                    code="EMPTY_OUTPUT",
                    severity="medium",
                    message="AI provider returned empty output.",
                )
            ],
        )

    issues: List[SafetyIssue] = []

    if len(text) > MAX_OUTPUT_CHARS:

        text = text[:MAX_OUTPUT_CHARS]

        issues.append(
            SafetyIssue(
                code="OUTPUT_TRUNCATED",
                severity="low",
                category="quality",
                message=(
                    "AI output exceeded the maximum allowed length."
                ),
            )
        )

    issues.extend(
        detect_unsupported_certainty(text)
    )

    issues.extend(
        detect_code_compliance_claim(text)
    )

    return SafetyResult(
        safe=True,
        text=text,
        issues=issues,
        blocked=False,
        modified=bool(
            any(
                issue.code == "OUTPUT_TRUNCATED"
                for issue in issues
            )
        ),
    )


# ---------------------------------------------------------
# CONTEXT SAFETY
# ---------------------------------------------------------


def sanitize_context(
    context: Any,
) -> Any:
    """
    Sanitize context recursively.

    This protects against accidental credential exposure and
    converts unsupported objects into simple representations.
    """

    if context is None:
        return None

    if isinstance(context, Mapping):

        result: Dict[str, Any] = {}

        for key, value in context.items():

            key_text = str(key)

            if key_text.lower() in {
                "password",
                "token",
                "api_key",
                "secret",
                "authorization",
                "telegram_token",
            }:
                result[key_text] = "[REDACTED_SECRET]"
                continue

            result[key_text] = sanitize_context(
                value
            )

        return result

    if isinstance(context, list):

        return [
            sanitize_context(item)
            for item in context
        ]

    if isinstance(context, tuple):

        return tuple(
            sanitize_context(item)
            for item in context
        )

    if isinstance(
        context,
        (str, int, float, bool),
    ):
        return context

    return str(context)


# ---------------------------------------------------------
# SAFE CONTEXT TEXT
# ---------------------------------------------------------


def sanitize_context_text(
    text: str,
) -> SafetyResult:
    """
    Sanitize textual engineering context.
    """

    text = normalize_text(text)

    config = get_ai_config()

    text = trim_ai_context(
        text,
        config,
    )

    inspected = inspect_input(text)

    return inspected


# ---------------------------------------------------------
# SAFE ENGINEERING DISCLAIMER
# ---------------------------------------------------------


def engineering_verification_note(
    language: str = "fa",
) -> str:
    """
    Return a concise verification note.
    """

    notes = {
        "fa": (
            "⚠️ نتایج تولیدشده توسط AI باید در صورت استفاده "
            "در تصمیم مهندسی با محاسبات و ضوابط مربوطه تطبیق داده شوند."
        ),
        "en": (
            "⚠️ AI-generated information should be verified against "
            "the relevant calculations and design requirements before "
            "being used for engineering decisions."
        ),
        "tr": (
            "⚠️ Yapay zekâ tarafından üretilen bilgiler, mühendislik "
            "kararlarında kullanılmadan önce ilgili hesaplarla "
            "doğrulanmalıdır."
        ),
        "ar": (
            "⚠️ يجب التحقق من المعلومات التي ينتجها الذكاء الاصطناعي "
            "مقابل الحسابات والمتطلبات الهندسية ذات الصلة."
        ),
        "ru": (
            "⚠️ Информацию, созданную ИИ, необходимо проверить "
            "по соответствующим расчетам и нормативным требованиям."
        ),
        "de": (
            "⚠️ KI-generierte Informationen sollten vor einer "
            "ingenieurtechnischen Entscheidung anhand der relevanten "
            "Berechnungen und Anforderungen überprüft werden."
        ),
        "zh-CN": (
            "⚠️ 在用于工程决策之前，应根据相关计算和设计要求 "
            "核验 AI 生成的信息。"
        ),
    }

    return notes.get(
        language,
        notes["en"],
    )


# ---------------------------------------------------------
# SAFE AI PIPELINE
# ---------------------------------------------------------


def prepare_ai_input(
    message: str,
    *,
    context: Optional[Any] = None,
) -> SafetyResult:
    """
    Prepare complete AI input.

    Steps:
    1. Inspect user message.
    2. Sanitize context.
    3. Limit context size.
    """

    input_result = inspect_input(message)

    if input_result.blocked:
        return input_result

    if context is not None:

        safe_context = sanitize_context(
            context
        )

        context_text = str(
            safe_context
        )

        context_result = sanitize_context_text(
            context_text
        )

        combined_issues = (
            input_result.issues
            + context_result.issues
        )

        combined_text = (
            input_result.text
            + "\n\n"
            + context_result.text
        )

        return SafetyResult(
            safe=(
                input_result.safe
                and context_result.safe
            ),
            text=combined_text,
            issues=combined_issues,
            blocked=(
                input_result.blocked
                or context_result.blocked
            ),
            modified=(
                input_result.modified
                or context_result.modified
            ),
        )

    return input_result


# ---------------------------------------------------------
# SAFETY SUMMARY
# ---------------------------------------------------------


def safety_summary(
    result: SafetyResult,
) -> Dict[str, Any]:
    """
    Convert a safety result into a serializable summary.
    """

    return {
        "safe": result.safe,
        "blocked": result.blocked,
        "modified": result.modified,
        "issue_count": len(result.issues),
        "issues": [
            {
                "code": issue.code,
                "severity": issue.severity,
                "category": issue.category,
                "message": issue.message,
                "details": issue.details,
            }
            for issue in result.issues
        ],
    }


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

__all__ = [
    "SafetyIssue",
    "SafetyResult",
    "normalize_text",
    "redact_secrets",
    "detect_prompt_injection",
    "detect_unsafe_automation",
    "detect_unsupported_certainty",
    "detect_code_compliance_claim",
    "inspect_input",
    "inspect_output",
    "sanitize_context",
    "sanitize_context_text",
    "engineering_verification_note",
    "prepare_ai_input",
    "safety_summary",
]
