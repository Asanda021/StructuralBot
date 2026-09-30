"""
StructuralBot - AI Package

AI services for:
- Engineering assistance
- Calculation explanation
- Result review
- Project analysis
- Report assistance

The Telegram handler must not contain provider-specific AI logic.

Provider integrations are implemented under this package.
"""

# ============================================================
# CORE AI SERVICE
# ============================================================

from ai.service import (
    AIError,
    AIConfigurationError,
    AIProviderError,
    AIResponse,
    AIRequest,
    AIService,
    get_ai_service,
    set_ai_service,
    ask_ai,
)


# ============================================================
# AI CONFIGURATION
# ============================================================

from ai.config import (
    AIConfig,
    get_ai_config,
    reload_ai_config,
    set_ai_config,
    validate_ai_config,
    ai_is_ready,
    ai_is_enabled,
    get_plan_daily_limit,
    trim_ai_context,
)


# ============================================================
# AI PROVIDERS
# ============================================================

from ai.providers import (
    BaseAIProvider,
    OpenAICompatibleProvider,
    create_ai_provider,
    ai_provider_is_configured,
    get_ai_provider_name,
)


# ============================================================
# AI CONTEXT
# ============================================================

from ai.context import (
    redact_sensitive_data,
    build_project_context,
    build_member_context,
    build_calculation_context,
    build_report_context,
    build_reinforcement_context,
    build_quantity_context,
    merge_contexts,
    context_to_text,
    build_engineering_snapshot,
    filter_context_for_mode,
)


# ============================================================
# AI PROMPTS
# ============================================================

from ai.prompts import (
    SYSTEM_PROMPT,
    LANGUAGE_INSTRUCTIONS,
    MODE_PROMPTS,
    SPECIALIZED_PROMPTS,
    OUTPUT_FORMATS,
    CONTEXT_INSTRUCTIONS,
    PromptBuilder,
    build_engineering_prompt,
    build_review_prompt,
    build_explanation_prompt,
    build_report_prompt,
    build_specialty_prompt,
)


# ============================================================
# AI SAFETY
# ============================================================

from ai.safety import (
    SafetyIssue,
    SafetyResult,
    normalize_text,
    redact_secrets,
    detect_prompt_injection,
    detect_unsafe_automation,
    detect_unsupported_certainty,
    detect_code_compliance_claim,
    inspect_input,
    inspect_output,
    sanitize_context,
    sanitize_context_text,
    engineering_verification_note,
    prepare_ai_input,
    safety_summary,
)


# ============================================================
# AI USAGE
# ============================================================

from ai.usage import (
    AIUsageError,
    AIUsageLimitError,
    AIInsufficientCreditsError,
    UsageRecord,
    UsageLimit,
    DEFAULT_USAGE_LIMITS,
    UsageStore,
    AIUsageManager,
    get_ai_usage_manager,
    set_ai_usage_manager,
    check_ai_usage,
    record_ai_success,
    record_ai_failure,
    get_ai_usage_summary,
)


# ============================================================
# AI MANAGER
# ============================================================

from ai.manager import (
    AIManagerError,
    AIManagerConfigurationError,
    AIManagerSafetyError,
    AIManagerRequest,
    AIManagerResponse,
    AIManager,
    get_ai_manager,
    set_ai_manager,
    ask_ai_manager,
)


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [

    # --------------------------------------------------------
    # CORE SERVICE
    # --------------------------------------------------------

    "AIError",
    "AIConfigurationError",
    "AIProviderError",
    "AIResponse",
    "AIRequest",
    "AIService",
    "get_ai_service",
    "set_ai_service",
    "ask_ai",

    # --------------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------------

    "AIConfig",
    "get_ai_config",
    "reload_ai_config",
    "set_ai_config",
    "validate_ai_config",
    "ai_is_ready",
    "ai_is_enabled",
    "get_plan_daily_limit",
    "trim_ai_context",

    # --------------------------------------------------------
    # PROVIDERS
    # --------------------------------------------------------

    "BaseAIProvider",
    "OpenAICompatibleProvider",
    "create_ai_provider",
    "ai_provider_is_configured",
    "get_ai_provider_name",

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # PROMPTS
    # --------------------------------------------------------

    "SYSTEM_PROMPT",
    "LANGUAGE_INSTRUCTIONS",
    "MODE_PROMPTS",
    "SPECIALIZED_PROMPTS",
    "OUTPUT_FORMATS",
    "CONTEXT_INSTRUCTIONS",
    "PromptBuilder",
    "build_engineering_prompt",
    "build_review_prompt",
    "build_explanation_prompt",
    "build_report_prompt",
    "build_specialty_prompt",

    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # USAGE
    # --------------------------------------------------------

    "AIUsageError",
    "AIUsageLimitError",
    "AIInsufficientCreditsError",
    "UsageRecord",
    "UsageLimit",
    "DEFAULT_USAGE_LIMITS",
    "UsageStore",
    "AIUsageManager",
    "get_ai_usage_manager",
    "set_ai_usage_manager",
    "check_ai_usage",
    "record_ai_success",
    "record_ai_failure",
    "get_ai_usage_summary",

    # --------------------------------------------------------
    # MANAGER
    # --------------------------------------------------------

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
