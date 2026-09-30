"""
StructuralBot - Billing Plans

Defines commercial subscription plans and their feature access.

This module contains business rules only.
Payment gateway logic must not be placed here.

Plan hierarchy:

FREE
BASIC
PROFESSIONAL
BUSINESS

The definitions are intentionally provider-independent so the
same plan system can later be connected to:
- Iranian payment gateways
- international payment gateways
- Telegram payments
- organizational billing
- promotional plans
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional


# ============================================================
# PLAN FEATURES
# ============================================================

class PlanFeature(str, Enum):
    """
    Features that can be enabled or disabled for each plan.
    """

    BASIC_CALCULATIONS = "basic_calculations"

    ADVANCED_CALCULATIONS = "advanced_calculations"

    PROJECTS = "projects"

    REINFORCEMENT = "reinforcement"

    REBAR_EQUIVALENCY = "rebar_equivalency"

    BBS = "bbs"

    CUT_LIST = "cut_list"

    QUANTITIES = "quantities"

    PDF_REPORT = "pdf_report"

    EXCEL_REPORT = "excel_report"

    AI_ASSISTANT = "ai_assistant"

    AI_EXPLANATION = "ai_explanation"

    AI_REVIEW = "ai_review"

    AI_PROJECT_ANALYSIS = "ai_project_analysis"

    AI_REPORT_ASSISTANCE = "ai_report_assistance"

    MULTI_PROJECT = "multi_project"

    TEAM_WORKSPACE = "team_workspace"

    API_ACCESS = "api_access"

    WHITE_LABEL = "white_label"

    PRIORITY_SUPPORT = "priority_support"


# ============================================================
# PLAN
# ============================================================

@dataclass(frozen=True)
class Plan:
    """
    Commercial plan definition.

    Prices are represented as integer currency units and are
    intentionally not tied to a specific currency.

    The billing layer can later interpret the amount as:
        IRR
        USD
        EUR
        etc.
    """

    code: str

    name: str

    description: str

    price: int = 0

    currency: str = "IRR"

    duration_days: Optional[int] = None

    ai_daily_requests: Optional[int] = None

    ai_daily_credits: Optional[float] = None

    max_projects: Optional[int] = None

    max_project_members: Optional[int] = None

    features: frozenset = field(
        default_factory=frozenset
    )

    active: bool = True

    trial: bool = False

    metadata: dict = field(
        default_factory=dict
    )

    def has_feature(
        self,
        feature: PlanFeature | str,
    ) -> bool:
        """
        Check whether this plan contains a feature.
        """

        if isinstance(feature, PlanFeature):
            feature_code = feature.value
        else:
            feature_code = str(feature)

        return feature_code in {
            (
                item.value
                if isinstance(item, PlanFeature)
                else str(item)
            )
            for item in self.features
        }

    def allows_ai(self) -> bool:
        """Return whether AI is available."""

        return (
            self.has_feature(
                PlanFeature.AI_ASSISTANT
            )
            and (
                self.ai_daily_requests is None
                or self.ai_daily_requests > 0
            )
        )

    def allows_projects(
        self,
        current_projects: int = 0,
    ) -> bool:
        """Check project creation entitlement."""

        if not self.has_feature(
            PlanFeature.PROJECTS
        ):
            return False

        if self.max_projects is None:
            return True

        return current_projects < self.max_projects

    def allows_members(
        self,
        current_members: int = 0,
    ) -> bool:
        """Check project/team member entitlement."""

        if self.max_project_members is None:
            return True

        return (
            current_members
            < self.max_project_members
        )

    def to_dict(self) -> dict:
        """Serialize plan."""

        return {
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "currency": self.currency,
            "duration_days": self.duration_days,
            "ai_daily_requests": self.ai_daily_requests,
            "ai_daily_credits": self.ai_daily_credits,
            "max_projects": self.max_projects,
            "max_project_members": self.max_project_members,
            "features": sorted(
                [
                    (
                        item.value
                        if isinstance(item, PlanFeature)
                        else str(item)
                    )
                    for item in self.features
                ]
            ),
            "active": self.active,
            "trial": self.trial,
            "metadata": dict(self.metadata),
        }


# ============================================================
# PLAN DEFINITIONS
# ============================================================

FREE_PLAN = Plan(
    code="free",
    name="رایگان",
    description=(
        "دسترسی پایه برای آشنایی با StructuralBot"
    ),
    price=0,
    currency="IRR",
    duration_days=None,
    ai_daily_requests=10,
    ai_daily_credits=None,
    max_projects=1,
    max_project_members=1,
    features=frozenset(
        {
            PlanFeature.BASIC_CALCULATIONS,
            PlanFeature.PROJECTS,
            PlanFeature.REINFORCEMENT,
            PlanFeature.REBAR_EQUIVALENCY,
            PlanFeature.QUANTITIES,
        }
    ),
    active=True,
    trial=False,
)


BASIC_PLAN = Plan(
    code="basic",
    name="پایه",
    description=(
        "امکانات بیشتر برای استفاده شخصی و پروژه‌های کوچک"
    ),
    price=0,
    currency="IRR",
    duration_days=30,
    ai_daily_requests=50,
    ai_daily_credits=None,
    max_projects=5,
    max_project_members=1,
    features=frozenset(
        {
            PlanFeature.BASIC_CALCULATIONS,
            PlanFeature.ADVANCED_CALCULATIONS,
            PlanFeature.PROJECTS,
            PlanFeature.REINFORCEMENT,
            PlanFeature.REBAR_EQUIVALENCY,
            PlanFeature.BBS,
            PlanFeature.CUT_LIST,
            PlanFeature.QUANTITIES,
            PlanFeature.PDF_REPORT,
            PlanFeature.EXCEL_REPORT,
            PlanFeature.AI_ASSISTANT,
            PlanFeature.AI_EXPLANATION,
        }
    ),
    active=True,
    trial=False,
)


PROFESSIONAL_PLAN = Plan(
    code="professional",
    name="حرفه‌ای",
    description=(
        "امکانات کامل محاسبات، گزارش و دستیار هوشمند"
    ),
    price=0,
    currency="IRR",
    duration_days=30,
    ai_daily_requests=200,
    ai_daily_credits=None,
    max_projects=50,
    max_project_members=1,
    features=frozenset(
        {
            PlanFeature.BASIC_CALCULATIONS,
            PlanFeature.ADVANCED_CALCULATIONS,
            PlanFeature.PROJECTS,
            PlanFeature.REINFORCEMENT,
            PlanFeature.REBAR_EQUIVALENCY,
            PlanFeature.BBS,
            PlanFeature.CUT_LIST,
            PlanFeature.QUANTITIES,
            PlanFeature.PDF_REPORT,
            PlanFeature.EXCEL_REPORT,
            PlanFeature.AI_ASSISTANT,
            PlanFeature.AI_EXPLANATION,
            PlanFeature.AI_REVIEW,
            PlanFeature.AI_PROJECT_ANALYSIS,
            PlanFeature.AI_REPORT_ASSISTANCE,
            PlanFeature.MULTI_PROJECT,
            PlanFeature.PRIORITY_SUPPORT,
        }
    ),
    active=True,
    trial=False,
)


BUSINESS_PLAN = Plan(
    code="business",
    name="سازمانی",
    description=(
        "برای شرکت‌ها، تیم‌های مهندسی و استفاده سازمانی"
    ),
    price=0,
    currency="IRR",
    duration_days=30,
    ai_daily_requests=1000,
    ai_daily_credits=None,
    max_projects=None,
    max_project_members=20,
    features=frozenset(
        {
            PlanFeature.BASIC_CALCULATIONS,
            PlanFeature.ADVANCED_CALCULATIONS,
            PlanFeature.PROJECTS,
            PlanFeature.REINFORCEMENT,
            PlanFeature.REBAR_EQUIVALENCY,
            PlanFeature.BBS,
            PlanFeature.CUT_LIST,
            PlanFeature.QUANTITIES,
            PlanFeature.PDF_REPORT,
            PlanFeature.EXCEL_REPORT,
            PlanFeature.AI_ASSISTANT,
            PlanFeature.AI_EXPLANATION,
            PlanFeature.AI_REVIEW,
            PlanFeature.AI_PROJECT_ANALYSIS,
            PlanFeature.AI_REPORT_ASSISTANCE,
            PlanFeature.MULTI_PROJECT,
            PlanFeature.TEAM_WORKSPACE,
            PlanFeature.API_ACCESS,
            PlanFeature.WHITE_LABEL,
            PlanFeature.PRIORITY_SUPPORT,
        }
    ),
    active=True,
    trial=False,
)


# ============================================================
# PLAN REGISTRY
# ============================================================

PLAN_DEFINITIONS: Dict[str, Plan] = {
    FREE_PLAN.code: FREE_PLAN,
    BASIC_PLAN.code: BASIC_PLAN,
    PROFESSIONAL_PLAN.code: PROFESSIONAL_PLAN,
    BUSINESS_PLAN.code: BUSINESS_PLAN,
}


# ============================================================
# PLAN HELPERS
# ============================================================

def normalize_plan_code(
    plan_code: Optional[str],
) -> str:
    """
    Normalize a plan code.

    Unknown/empty values fall back to free.
    """

    if not plan_code:
        return "free"

    normalized = str(
        plan_code
    ).strip().lower()

    aliases = {
        "free": "free",
        " رایگان": "free",
        "رایگان": "free",

        "basic": "basic",
        "پایه": "basic",

        "pro": "professional",
        "professional": "professional",
        "حرفه‌ای": "professional",
        "حرفه ای": "professional",

        "business": "business",
        "enterprise": "business",
        "سازمانی": "business",
        "سازمان": "business",
    }

    return aliases.get(
        normalized,
        "free",
    )


def get_plan(
    plan_code: Optional[str],
) -> Plan:
    """
    Get a plan definition.

    Unknown plans return FREE.
    """

    normalized = normalize_plan_code(
        plan_code
    )

    return PLAN_DEFINITIONS.get(
        normalized,
        FREE_PLAN,
    )


def get_all_plans(
    active_only: bool = True,
) -> List[Plan]:
    """Return available plan definitions."""

    plans = list(
        PLAN_DEFINITIONS.values()
    )

    if active_only:
        plans = [
            plan
            for plan in plans
            if plan.active
        ]

    return plans


def has_feature(
    plan_code: Optional[str],
    feature: PlanFeature | str,
) -> bool:
    """
    Check feature availability for a plan.
    """

    return get_plan(
        plan_code
    ).has_feature(feature)


def get_plan_features(
    plan_code: Optional[str],
) -> List[str]:
    """Return sorted feature codes."""

    plan = get_plan(
        plan_code
    )

    return sorted(
        [
            (
                feature.value
                if isinstance(
                    feature,
                    PlanFeature,
                )
                else str(feature)
            )
            for feature in plan.features
        ]
    )


def get_plan_price(
    plan_code: Optional[str],
) -> int:
    """Return plan price."""

    return get_plan(
        plan_code
    ).price


def get_plan_duration(
    plan_code: Optional[str],
) -> Optional[int]:
    """Return duration in days."""

    return get_plan(
        plan_code
    ).duration_days


def get_ai_daily_limit(
    plan_code: Optional[str],
) -> Optional[int]:
    """Return daily AI request limit."""

    return get_plan(
        plan_code
    ).ai_daily_requests


def get_max_projects(
    plan_code: Optional[str],
) -> Optional[int]:
    """Return maximum project count."""

    return get_plan(
        plan_code
    ).max_projects


def get_max_project_members(
    plan_code: Optional[str],
) -> Optional[int]:
    """Return maximum team member count."""

    return get_plan(
        plan_code
    ).max_project_members


# ============================================================
# FEATURE GROUPS
# ============================================================

CALCULATION_FEATURES = frozenset(
    {
        PlanFeature.BASIC_CALCULATIONS,
        PlanFeature.ADVANCED_CALCULATIONS,
    }
)

REPORT_FEATURES = frozenset(
    {
        PlanFeature.PDF_REPORT,
        PlanFeature.EXCEL_REPORT,
    }
)

AI_FEATURES = frozenset(
    {
        PlanFeature.AI_ASSISTANT,
        PlanFeature.AI_EXPLANATION,
        PlanFeature.AI_REVIEW,
        PlanFeature.AI_PROJECT_ANALYSIS,
        PlanFeature.AI_REPORT_ASSISTANCE,
    }
)

REBAR_FEATURES = frozenset(
    {
        PlanFeature.REINFORCEMENT,
        PlanFeature.REBAR_EQUIVALENCY,
        PlanFeature.BBS,
        PlanFeature.CUT_LIST,
    }
)


# ============================================================
# ACCESS HELPERS
# ============================================================

def can_use_calculations(
    plan_code: Optional[str],
    advanced: bool = False,
) -> bool:
    """
    Check calculation access.
    """

    feature = (
        PlanFeature.ADVANCED_CALCULATIONS
        if advanced
        else PlanFeature.BASIC_CALCULATIONS
    )

    return has_feature(
        plan_code,
        feature,
    )


def can_use_reports(
    plan_code: Optional[str],
    *,
    excel: bool = False,
) -> bool:

    feature = (
        PlanFeature.EXCEL_REPORT
        if excel
        else PlanFeature.PDF_REPORT
    )

    return has_feature(
        plan_code,
        feature,
    )


def can_use_ai(
    plan_code: Optional[str],
    mode: str = "assistant",
) -> bool:

    mode_map = {
        "assistant": PlanFeature.AI_ASSISTANT,
        "explain": PlanFeature.AI_EXPLANATION,
        "review": PlanFeature.AI_REVIEW,
        "project": PlanFeature.AI_PROJECT_ANALYSIS,
        "report": PlanFeature.AI_REPORT_ASSISTANCE,
    }

    feature = mode_map.get(
        str(mode).lower(),
        PlanFeature.AI_ASSISTANT,
    )

    return has_feature(
        plan_code,
        feature,
    )


def can_use_rebar_tools(
    plan_code: Optional[str],
    *,
    bbs: bool = False,
    cut_list: bool = False,
) -> bool:

    if bbs:
        return has_feature(
            plan_code,
            PlanFeature.BBS,
        )

    if cut_list:
        return has_feature(
            plan_code,
            PlanFeature.CUT_LIST,
        )

    return has_feature(
        plan_code,
        PlanFeature.REINFORCEMENT,
    )


# ============================================================
# DISPLAY HELPERS
# ============================================================

def plan_to_display_dict(
    plan_code: Optional[str],
) -> dict:
    """
    Return a Telegram/UI-friendly plan representation.
    """

    plan = get_plan(
        plan_code
    )

    return {
        "code": plan.code,
        "name": plan.name,
        "description": plan.description,
        "price": plan.price,
        "currency": plan.currency,
        "duration_days": plan.duration_days,
        "ai_daily_requests": plan.ai_daily_requests,
        "max_projects": plan.max_projects,
        "max_project_members": plan.max_project_members,
        "features": get_plan_features(
            plan.code
        ),
        "active": plan.active,
        "trial": plan.trial,
    }


def plans_to_display_list() -> List[dict]:
    """Return all active plans for UI."""

    return [
        plan_to_display_dict(
            plan.code
        )
        for plan in get_all_plans()
    ]


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "PlanFeature",
    "Plan",
    "FREE_PLAN",
    "BASIC_PLAN",
    "PROFESSIONAL_PLAN",
    "BUSINESS_PLAN",
    "PLAN_DEFINITIONS",
    "CALCULATION_FEATURES",
    "REPORT_FEATURES",
    "AI_FEATURES",
    "REBAR_FEATURES",
    "normalize_plan_code",
    "get_plan",
    "get_all_plans",
    "has_feature",
    "get_plan_features",
    "get_plan_price",
    "get_plan_duration",
    "get_ai_daily_limit",
    "get_max_projects",
    "get_max_project_members",
    "can_use_calculations",
    "can_use_reports",
    "can_use_ai",
    "can_use_rebar_tools",
    "plan_to_display_dict",
    "plans_to_display_list",
]
