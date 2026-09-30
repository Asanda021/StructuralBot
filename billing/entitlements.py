"""
StructuralBot - Entitlements

Feature-access control based on subscription plans.

Responsibilities:
- Determine whether a user can access a feature
- Check project limits
- Check team/member limits
- Check AI limits
- Provide entitlement summaries
- Keep feature-access logic outside Telegram handlers

This module does not perform payment processing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from billing.plans import (
    Plan,
    PlanFeature,
    get_plan,
    has_feature,
)

from billing.subscription import (
    SubscriptionManager,
    get_subscription_manager,
)


# ============================================================
# ENTITLEMENT RESULT
# ============================================================

@dataclass(frozen=True)
class EntitlementResult:
    """
    Result of an access-control check.
    """

    allowed: bool

    feature: Optional[str] = None

    plan_code: str = "free"

    reason: str = ""

    limit: Optional[int] = None

    current: Optional[int] = None

    remaining: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "feature": self.feature,
            "plan_code": self.plan_code,
            "reason": self.reason,
            "limit": self.limit,
            "current": self.current,
            "remaining": self.remaining,
        }


# ============================================================
# ENTITLEMENT MANAGER
# ============================================================

class EntitlementManager:
    """
    Central access-control service.

    Handlers should ask this class whether an operation is
    permitted instead of checking subscription details directly.
    """

    def __init__(
        self,
        subscription_manager: Optional[
            SubscriptionManager
        ] = None,
    ) -> None:

        self.subscription_manager = (
            subscription_manager
            or get_subscription_manager()
        )

    # ========================================================
    # PLAN
    # ========================================================

    def get_plan(
        self,
        user_id: str,
    ) -> Plan:

        return self.subscription_manager.get_plan(
            user_id
        )

    def get_plan_code(
        self,
        user_id: str,
    ) -> str:

        return self.get_plan(
            user_id
        ).code

    # ========================================================
    # FEATURE
    # ========================================================

    def check_feature(
        self,
        user_id: str,
        feature: PlanFeature | str,
    ) -> EntitlementResult:
        """
        Check whether a user has access to a feature.
        """

        plan = self.get_plan(
            user_id
        )

        if isinstance(
            feature,
            PlanFeature,
        ):
            feature_name = feature.value
            feature_value = feature
        else:
            feature_name = str(
                feature
            ).strip().lower()

            try:
                feature_value = PlanFeature(
                    feature_name
                )
            except ValueError:

                return EntitlementResult(
                    allowed=False,
                    feature=feature_name,
                    plan_code=plan.code,
                    reason=(
                        "Unknown feature."
                    ),
                )

        allowed = has_feature(
            plan.code,
            feature_value,
        )

        if allowed:

            return EntitlementResult(
                allowed=True,
                feature=feature_name,
                plan_code=plan.code,
                reason=(
                    "Feature is available "
                    "for the current plan."
                ),
            )

        return EntitlementResult(
            allowed=False,
            feature=feature_name,
            plan_code=plan.code,
            reason=(
                "This feature is not available "
                "for the current plan."
            ),
        )

    def can_use(
        self,
        user_id: str,
        feature: PlanFeature | str,
    ) -> bool:

        return self.check_feature(
            user_id,
            feature,
        ).allowed

    # ========================================================
    # PROJECT LIMIT
    # ========================================================

    def check_project_limit(
        self,
        user_id: str,
        current_projects: int,
    ) -> EntitlementResult:

        plan = self.get_plan(
            user_id
        )

        limit = plan.max_projects

        if limit is None:

            return EntitlementResult(
                allowed=True,
                feature="projects",
                plan_code=plan.code,
                reason=(
                    "Unlimited projects."
                ),
                limit=None,
                current=current_projects,
                remaining=None,
            )

        remaining = max(
            0,
            limit - current_projects,
        )

        allowed = (
            current_projects < limit
        )

        return EntitlementResult(
            allowed=allowed,
            feature="projects",
            plan_code=plan.code,
            reason=(
                "Project limit available."
                if allowed
                else
                "Project limit reached."
            ),
            limit=limit,
            current=current_projects,
            remaining=remaining,
        )

    # ========================================================
    # PROJECT MEMBER LIMIT
    # ========================================================

    def check_project_member_limit(
        self,
        user_id: str,
        current_members: int,
    ) -> EntitlementResult:

        plan = self.get_plan(
            user_id
        )

        limit = plan.max_project_members

        if limit is None:

            return EntitlementResult(
                allowed=True,
                feature="project_members",
                plan_code=plan.code,
                reason=(
                    "Unlimited project members."
                ),
                limit=None,
                current=current_members,
                remaining=None,
            )

        remaining = max(
            0,
            limit - current_members,
        )

        allowed = (
            current_members < limit
        )

        return EntitlementResult(
            allowed=allowed,
            feature="project_members",
            plan_code=plan.code,
            reason=(
                "Project member slot available."
                if allowed
                else
                "Project member limit reached."
            ),
            limit=limit,
            current=current_members,
            remaining=remaining,
        )

    # ========================================================
    # AI REQUEST LIMIT
    # ========================================================

    def check_ai_daily_limit(
        self,
        user_id: str,
        current_requests: int,
    ) -> EntitlementResult:

        plan = self.get_plan(
            user_id
        )

        limit = plan.ai_daily_requests

        if limit is None:

            return EntitlementResult(
                allowed=True,
                feature="ai_daily_requests",
                plan_code=plan.code,
                reason=(
                    "Unlimited daily AI requests."
                ),
                limit=None,
                current=current_requests,
                remaining=None,
            )

        remaining = max(
            0,
            limit - current_requests,
        )

        allowed = (
            current_requests < limit
        )

        return EntitlementResult(
            allowed=allowed,
            feature="ai_daily_requests",
            plan_code=plan.code,
            reason=(
                "Daily AI request available."
                if allowed
                else
                "Daily AI request limit reached."
            ),
            limit=limit,
            current=current_requests,
            remaining=remaining,
        )

    # ========================================================
    # AI CREDIT LIMIT
    # ========================================================

    def check_ai_daily_credits(
        self,
        user_id: str,
        current_credits: float,
    ) -> EntitlementResult:

        plan = self.get_plan(
            user_id
        )

        limit = plan.ai_daily_credits

        if limit is None:

            return EntitlementResult(
                allowed=True,
                feature="ai_daily_credits",
                plan_code=plan.code,
                reason=(
                    "Unlimited daily AI credits."
                ),
                limit=None,
                current=int(
                    current_credits
                ),
                remaining=None,
            )

        remaining = max(
            0.0,
            float(limit) - float(
                current_credits
            ),
        )

        allowed = (
            float(current_credits)
            < float(limit)
        )

        return EntitlementResult(
            allowed=allowed,
            feature="ai_daily_credits",
            plan_code=plan.code,
            reason=(
                "Daily AI credits available."
                if allowed
                else
                "Daily AI credit limit reached."
            ),
            limit=int(limit),
            current=int(
                current_credits
            ),
            remaining=int(
                remaining
            ),
        )

    # ========================================================
    # GENERIC LIMIT
    # ========================================================

    def check_limit(
        self,
        user_id: str,
        limit_name: str,
        current: int | float,
    ) -> EntitlementResult:

        plan = self.get_plan(
            user_id
        )

        normalized = str(
            limit_name
        ).strip().lower()

        mapping = {
            "projects": plan.max_projects,
            "project_members": (
                plan.max_project_members
            ),
            "ai_daily_requests": (
                plan.ai_daily_requests
            ),
            "ai_daily_credits": (
                plan.ai_daily_credits
            ),
        }

        if normalized not in mapping:

            return EntitlementResult(
                allowed=False,
                feature=normalized,
                plan_code=plan.code,
                reason=(
                    "Unknown entitlement limit."
                ),
            )

        limit = mapping[
            normalized
        ]

        if limit is None:

            return EntitlementResult(
                allowed=True,
                feature=normalized,
                plan_code=plan.code,
                reason="Unlimited.",
                limit=None,
                current=int(
                    current
                ),
                remaining=None,
            )

        remaining = max(
            0,
            int(limit) - int(current),
        )

        allowed = (
            current < limit
        )

        return EntitlementResult(
            allowed=allowed,
            feature=normalized,
            plan_code=plan.code,
            reason=(
                "Limit available."
                if allowed
                else
                "Limit reached."
            ),
            limit=int(limit),
            current=int(
                current
            ),
            remaining=remaining,
        )

    # ========================================================
    # PLAN SUMMARY
    # ========================================================

    def summary(
        self,
        user_id: str,
    ) -> Dict[str, Any]:

        plan = self.get_plan(
            user_id
        )

        features = [
            feature.value
            for feature in PlanFeature
            if has_feature(
                plan.code,
                feature,
            )
        ]

        return {
            "user_id": str(
                user_id
            ),
            "plan_code": plan.code,
            "plan_name": plan.name,
            "features": features,
            "limits": {
                "max_projects": (
                    plan.max_projects
                ),
                "max_project_members": (
                    plan.max_project_members
                ),
                "ai_daily_requests": (
                    plan.ai_daily_requests
                ),
                "ai_daily_credits": (
                    plan.ai_daily_credits
                ),
            },
        }

    # ========================================================
    # REQUIRE FEATURE
    # ========================================================

    def require_feature(
        self,
        user_id: str,
        feature: PlanFeature | str,
    ) -> None:
        """
        Raise PermissionError when feature is unavailable.

        Useful for service-layer code where a simple boolean
        is not enough.
        """

        result = self.check_feature(
            user_id,
            feature,
        )

        if not result.allowed:

            raise PermissionError(
                result.reason
            )


# ============================================================
# GLOBAL MANAGER
# ============================================================

_default_entitlement_manager: Optional[
    EntitlementManager
] = None


def get_entitlement_manager() -> EntitlementManager:

    global _default_entitlement_manager

    if _default_entitlement_manager is None:

        _default_entitlement_manager = (
            EntitlementManager()
        )

    return _default_entitlement_manager


def set_entitlement_manager(
    manager: EntitlementManager,
) -> None:

    global _default_entitlement_manager

    _default_entitlement_manager = manager


# ============================================================
# CONVENIENCE HELPERS
# ============================================================

def user_can_use(
    user_id: str,
    feature: PlanFeature | str,
) -> bool:

    return get_entitlement_manager().can_use(
        user_id,
        feature,
    )


def check_user_feature(
    user_id: str,
    feature: PlanFeature | str,
) -> EntitlementResult:

    return get_entitlement_manager().check_feature(
        user_id,
        feature,
    )


def check_user_project_limit(
    user_id: str,
    current_projects: int,
) -> EntitlementResult:

    return get_entitlement_manager().check_project_limit(
        user_id,
        current_projects,
    )


def check_user_member_limit(
    user_id: str,
    current_members: int,
) -> EntitlementResult:

    return get_entitlement_manager().check_project_member_limit(
        user_id,
        current_members,
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "EntitlementResult",
    "EntitlementManager",
    "get_entitlement_manager",
    "set_entitlement_manager",
    "user_can_use",
    "check_user_feature",
    "check_user_project_limit",
    "check_user_member_limit",
]
