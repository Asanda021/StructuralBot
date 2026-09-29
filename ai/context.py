"""
StructuralBot - AI Context

Builds structured context for the AI assistant.

The AI layer must receive only the information that is relevant
to the current request. This module provides a controlled boundary
between engineering data and the AI provider.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

from ai.config import get_ai_config, trim_ai_context


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

CONTEXT_VERSION = "1.0"

SENSITIVE_KEYS = {
    "password",
    "token",
    "api_key",
    "secret",
    "authorization",
    "phone",
    "email",
    "national_id",
    "telegram_token",
}


# ---------------------------------------------------------
# BASIC SERIALIZATION
# ---------------------------------------------------------


def _serialize(value: Any) -> Any:
    """
    Convert common Python objects into JSON-like structures.
    """

    if value is None:
        return None

    if is_dataclass(value):
        return {
            key: _serialize(item)
            for key, item in asdict(value).items()
        }

    if isinstance(value, Mapping):
        return {
            str(key): _serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _serialize(item)
            for item in value
        ]

    if hasattr(value, "value"):
        try:
            return value.value
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return {
                str(key): _serialize(item)
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        except Exception:
            pass

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


# ---------------------------------------------------------
# SENSITIVE DATA REDACTION
# ---------------------------------------------------------


def redact_sensitive_data(
    data: Any,
) -> Any:
    """
    Remove or mask sensitive values before AI processing.
    """

    if isinstance(data, Mapping):

        result: Dict[str, Any] = {}

        for key, value in data.items():

            normalized_key = str(key).lower()

            if normalized_key in SENSITIVE_KEYS:
                result[str(key)] = "[REDACTED]"
                continue

            result[str(key)] = redact_sensitive_data(
                value
            )

        return result

    if isinstance(data, list):
        return [
            redact_sensitive_data(item)
            for item in data
        ]

    if isinstance(data, tuple):
        return tuple(
            redact_sensitive_data(item)
            for item in data
        )

    return data


# ---------------------------------------------------------
# PROJECT CONTEXT
# ---------------------------------------------------------


def build_project_context(
    project: Any,
) -> Dict[str, Any]:
    """
    Convert a project object into AI-safe context.
    """

    if project is None:
        return {}

    data = _serialize(project)

    if not isinstance(data, dict):
        data = {
            "project": data,
        }

    result = {
        "context_version": CONTEXT_VERSION,
        "type": "project",
        "project": data,
    }

    config = get_ai_config()

    if config.redact_sensitive_data:
        result = redact_sensitive_data(result)

    return result


# ---------------------------------------------------------
# MEMBER CONTEXT
# ---------------------------------------------------------


def build_member_context(
    member: Any,
) -> Dict[str, Any]:
    """
    Convert a structural member into AI context.
    """

    if member is None:
        return {}

    data = _serialize(member)

    result = {
        "context_version": CONTEXT_VERSION,
        "type": "structural_member",
        "member": data,
    }

    config = get_ai_config()

    if config.redact_sensitive_data:
        result = redact_sensitive_data(result)

    return result


# ---------------------------------------------------------
# CALCULATION CONTEXT
# ---------------------------------------------------------


def build_calculation_context(
    calculation: Any,
) -> Dict[str, Any]:
    """
    Convert a calculation request/result into AI context.
    """

    if calculation is None:
        return {}

    data = _serialize(calculation)

    result = {
        "context_version": CONTEXT_VERSION,
        "type": "calculation",
        "calculation": data,
    }

    config = get_ai_config()

    if config.redact_sensitive_data:
        result = redact_sensitive_data(result)

    return result


# ---------------------------------------------------------
# REPORT CONTEXT
# ---------------------------------------------------------


def build_report_context(
    report: Any,
) -> Dict[str, Any]:
    """
    Convert report information into AI context.
    """

    if report is None:
        return {}

    data = _serialize(report)

    result = {
        "context_version": CONTEXT_VERSION,
        "type": "report",
        "report": data,
    }

    config = get_ai_config()

    if config.redact_sensitive_data:
        result = redact_sensitive_data(result)

    return result


# ---------------------------------------------------------
# REINFORCEMENT CONTEXT
# ---------------------------------------------------------


def build_reinforcement_context(
    reinforcement: Any,
) -> Dict[str, Any]:
    """
    Convert reinforcement/BBS/Cut List data into AI context.
    """

    if reinforcement is None:
        return {}

    data = _serialize(reinforcement)

    result = {
        "context_version": CONTEXT_VERSION,
        "type": "reinforcement",
        "reinforcement": data,
    }

    config = get_ai_config()

    if config.redact_sensitive_data:
        result = redact_sensitive_data(result)

    return result


# ---------------------------------------------------------
# QUANTITY CONTEXT
# ---------------------------------------------------------


def build_quantity_context(
    quantities: Any,
) -> Dict[str, Any]:
    """
    Convert quantity takeoff information into AI context.
    """

    if quantities is None:
        return {}

    data = _serialize(quantities)

    result = {
        "context_version": CONTEXT_VERSION,
        "type": "quantities",
        "quantities": data,
    }

    config = get_ai_config()

    if config.redact_sensitive_data:
        result = redact_sensitive_data(result)

    return result


# ---------------------------------------------------------
# MERGE CONTEXT
# ---------------------------------------------------------


def merge_contexts(
    *contexts: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    """
    Merge multiple context dictionaries.

    Nested dictionaries are merged recursively.
    """

    result: Dict[str, Any] = {
        "context_version": CONTEXT_VERSION,
    }

    def merge_dict(
        target: Dict[str, Any],
        source: Mapping[str, Any],
    ) -> None:

        for key, value in source.items():

            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, Mapping)
            ):
                merge_dict(
                    target[key],
                    value,
                )
            else:
                target[key] = _serialize(value)

    for context in contexts:

        if not context:
            continue

        merge_dict(
            result,
            context,
        )

    config = get_ai_config()

    if config.redact_sensitive_data:
        result = redact_sensitive_data(result)

    return result


# ---------------------------------------------------------
# CONTEXT SUMMARY
# ---------------------------------------------------------


def context_to_text(
    context: Mapping[str, Any],
) -> str:
    """
    Convert structured context into readable text.

    This is intended for AI prompts and logs.
    """

    lines: List[str] = []

    def walk(
        value: Any,
        prefix: str = "",
    ) -> None:

        if isinstance(value, Mapping):

            for key, item in value.items():

                next_prefix = (
                    f"{prefix}.{key}"
                    if prefix
                    else str(key)
                )

                walk(
                    item,
                    next_prefix,
                )

            return

        if isinstance(value, list):

            if not value:
                lines.append(
                    f"{prefix}: []"
                )
                return

            for index, item in enumerate(value):
                walk(
                    item,
                    f"{prefix}[{index}]",
                )

            return

        lines.append(
            f"{prefix}: {value}"
        )

    walk(context)

    text = "\n".join(lines)

    return trim_ai_context(text)


# ---------------------------------------------------------
# ENGINEERING SNAPSHOT
# ---------------------------------------------------------


def build_engineering_snapshot(
    *,
    project: Any = None,
    member: Any = None,
    calculation: Any = None,
    reinforcement: Any = None,
    quantities: Any = None,
    report: Any = None,
) -> Dict[str, Any]:
    """
    Build a complete but controlled engineering snapshot.

    Only non-empty components are included.
    """

    contexts: List[Mapping[str, Any]] = []

    if project is not None:
        contexts.append(
            build_project_context(project)
        )

    if member is not None:
        contexts.append(
            build_member_context(member)
        )

    if calculation is not None:
        contexts.append(
            build_calculation_context(calculation)
        )

    if reinforcement is not None:
        contexts.append(
            build_reinforcement_context(reinforcement)
        )

    if quantities is not None:
        contexts.append(
            build_quantity_context(quantities)
        )

    if report is not None:
        contexts.append(
            build_report_context(report)
        )

    return merge_contexts(*contexts)


# ---------------------------------------------------------
# CONTEXT FILTERING
# ---------------------------------------------------------


def filter_context_for_mode(
    context: Mapping[str, Any],
    mode: str,
) -> Dict[str, Any]:
    """
    Restrict context according to AI mode and configuration.

    Modes:
        assistant
        explain
        review
        project
        report
    """

    config = get_ai_config()

    normalized_mode = (
        mode or "assistant"
    ).strip().lower()

    source = _serialize(context)

    if not isinstance(source, dict):
        return {}

    allowed: Dict[str, Any] = {
        "context_version": source.get(
            "context_version",
            CONTEXT_VERSION,
        ),
    }

    if normalized_mode in {
        "assistant",
        "review",
        "explain",
    }:
        if config.allow_calculation_context:
            if "calculation" in source:
                allowed["calculation"] = source[
                    "calculation"
                ]

        if "reinforcement" in source:
            allowed["reinforcement"] = source[
                "reinforcement"
            ]

        if "quantities" in source:
            allowed["quantities"] = source[
                "quantities"
            ]

        if "structural_member" in source:
            allowed["structural_member"] = source[
                "structural_member"
            ]

    if normalized_mode == "project":
        if config.allow_project_context:
            if "project" in source:
                allowed["project"] = source[
                    "project"
                ]

        if "structural_member" in source:
            allowed["structural_member"] = source[
                "structural_member"
            ]

        if config.allow_calculation_context:
            if "calculation" in source:
                allowed["calculation"] = source[
                    "calculation"
                ]

    if normalized_mode == "report":
        if config.allow_report_context:
            if "report" in source:
                allowed["report"] = source[
                    "report"
                ]

        if config.allow_calculation_context:
            if "calculation" in source:
                allowed["calculation"] = source[
                    "calculation"
                ]

        if "quantities" in source:
            allowed["quantities"] = source[
                "quantities"
            ]

        if "reinforcement" in source:
            allowed["reinforcement"] = source[
                "reinforcement"
            ]

    if config.redact_sensitive_data:
        allowed = redact_sensitive_data(
            allowed
        )

    return allowed


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------


__all__ = [
    "CONTEXT_VERSION",
    "redact_sensitive_data",
    "build_project_context",
    "build_member_context",
    "build_calculation_context",
    "build_report_context",
    "build_reinforcement_context",
    "build_quantity_context",
    "merge_contexts",
    "context_to_text",
    "build_engineering_snapshot",
    "filter_context_for_mode",
]
