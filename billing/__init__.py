"""
StructuralBot - Billing Package

Commercial and subscription infrastructure for StructuralBot.

Responsibilities:
- Subscription plans
- User entitlements
- Credits
- Usage limits
- Feature access
- Billing state

Payment-provider integrations must remain outside the core
billing models so the application can later support multiple
payment gateways without changing business logic.
"""

from billing.plans import (
    Plan,
    PlanFeature,
    PLAN_DEFINITIONS,
    get_plan,
    get_all_plans,
    has_feature,
)

from billing.credits import (
    CreditBalance,
    CreditTransaction,
    CreditManager,
    get_credit_manager,
)

from billing.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionManager,
    get_subscription_manager,
)


__all__ = [
    # Plans
    "Plan",
    "PlanFeature",
    "PLAN_DEFINITIONS",
    "get_plan",
    "get_all_plans",
    "has_feature",

    # Credits
    "CreditBalance",
    "CreditTransaction",
    "CreditManager",
    "get_credit_manager",

    # Subscription
    "Subscription",
    "SubscriptionStatus",
    "SubscriptionManager",
    "get_subscription_manager",
]
