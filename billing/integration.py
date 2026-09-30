"""
StructuralBot - Billing Integration Layer

Application-facing bridge between the Telegram bot and the
commercial billing infrastructure.

Responsibilities:
- Provide a small stable API for bot handlers
- Hide internal billing manager complexity
- Check user access/features
- Manage subscription state
- Manage credits
- Create commercial orders
- Expose billing summaries
- Prepare notification-friendly results

Important:
    This module does not contain Telegram-specific code.
    Telegram handlers should call this layer instead of
    directly coordinating multiple billing managers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional


# ============================================================
# HELPERS
# ============================================================


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


# ============================================================
# ERRORS
# ============================================================


class BillingIntegrationError(Exception):
    """Base integration error."""


class BillingAccessError(BillingIntegrationError):
    """User does not have access to requested feature."""


class BillingUserError(BillingIntegrationError):
    """Invalid or missing user information."""


class BillingOperationError(BillingIntegrationError):
    """Commercial operation failed."""


# ============================================================
# RESULT MODELS
# ============================================================


@dataclass
class BillingAccess:
    """
    Normalized access result for bot handlers.
    """

    user_id: str

    allowed: bool

    feature: Optional[str] = None

    plan_code: str = "free"

    reason: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "allowed": self.allowed,
            "feature": self.feature,
            "plan_code": self.plan_code,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


@dataclass
class BillingUserSummary:
    """
    Stable commercial summary suitable for bot UI.
    """

    user_id: str

    plan_code: str = "free"

    plan_name: str = "Free"

    subscription_active: bool = False

    expires_at: Optional[datetime] = None

    days_remaining: int = 0

    credits: int = 0

    projects: int = 0

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "plan_code": self.plan_code,
            "plan_name": self.plan_name,
            "subscription_active": (
                self.subscription_active
            ),
            "expires_at": (
                self.expires_at.isoformat()
                if self.expires_at
                else None
            ),
            "days_remaining": self.days_remaining,
            "credits": self.credits,
            "projects": self.projects,
            "metadata": dict(self.metadata),
        }


@dataclass
class BillingOperationResult:
    """
    Generic normalized result returned by integration
    operations.
    """

    success: bool

    operation: str

    user_id: str

    message: str = ""

    data: Dict[str, Any] = field(
        default_factory=dict
    )

    error: Optional[str] = None

    created_at: datetime = field(
        default_factory=_utcnow
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "operation": self.operation,
            "user_id": self.user_id,
            "message": self.message,
            "data": dict(self.data),
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================
# BILLING INTEGRATION
# ============================================================


class BillingIntegration:
    """
    Application-level facade for StructuralBot billing.

    Bot handlers should preferably use this class rather than
    directly coordinating:

        plans
        subscriptions
        credits
        entitlements
        orders
        checkout
        invoices
        notifications
    """

    def __init__(
        self,
        *,
        subscription_manager: Any = None,
        credit_manager: Any = None,
        entitlement_manager: Any = None,
        order_manager: Any = None,
        checkout_manager: Any = None,
        invoice_manager: Any = None,
        product_catalog: Any = None,
        billing_service: Any = None,
    ) -> None:

        from billing.credits import (
            get_credit_manager,
        )

        from billing.entitlements import (
            get_entitlement_manager,
        )

        from billing.invoice import (
            get_invoice_manager,
        )

        from billing.orders import (
            get_order_manager,
        )

        from billing.products import (
            get_product_catalog,
        )

        from billing.service import (
            get_billing_service,
        )

        from billing.subscription import (
            get_subscription_manager,
        )

        self.subscription_manager = (
            subscription_manager
            or get_subscription_manager()
        )

        self.credit_manager = (
            credit_manager
            or get_credit_manager()
        )

        self.entitlement_manager = (
            entitlement_manager
            or get_entitlement_manager()
        )

        self.order_manager = (
            order_manager
            or get_order_manager()
        )

        self.checkout_manager = (
            checkout_manager
        )

        self.invoice_manager = (
            invoice_manager
            or get_invoice_manager()
        )

        self.product_catalog = (
            product_catalog
            or get_product_catalog()
        )

        self.billing_service = (
            billing_service
            or get_billing_service()
        )

    # ========================================================
    # USER VALIDATION
    # ========================================================

    @staticmethod
    def validate_user_id(
        user_id: Any,
    ) -> str:

        normalized = _safe_str(user_id)

        if not normalized:
            raise BillingUserError(
                "user_id is required."
            )

        return normalized

    # ========================================================
    # SUBSCRIPTION
    # ========================================================

    def get_subscription(
        self,
        user_id: Any,
    ) -> Any:

        user_id = self.validate_user_id(
            user_id
        )

        return self.subscription_manager.get_subscription(
            user_id
        )

    def get_plan_code(
        self,
        user_id: Any,
    ) -> str:

        subscription = self.get_subscription(
            user_id
        )

        if subscription is None:
            return "free"

        if hasattr(
            subscription,
            "is_active",
        ):
            if not subscription.is_active():
                return "free"

        return _safe_str(
            getattr(
                subscription,
                "plan_code",
                "free",
            )
        ) or "free"

    def has_active_subscription(
        self,
        user_id: Any,
    ) -> bool:

        subscription = self.get_subscription(
            user_id
        )

        if subscription is None:
            return False

        try:
            return bool(
                subscription.is_active()
            )
        except Exception:
            return False

    # ========================================================
    # CREDITS
    # ========================================================

    def get_credit_balance(
        self,
        user_id: Any,
    ) -> int:

        user_id = self.validate_user_id(
            user_id
        )

        balance = self.credit_manager.get_balance(
            user_id
        )

        if balance is None:
            return 0

        value = getattr(
            balance,
            "balance",
            0,
        )

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0

    def consume_credits(
        self,
        user_id: Any,
        amount: int,
        *,
        description: str = "",
    ) -> BillingOperationResult:

        user_id = self.validate_user_id(
            user_id
        )

        try:
            amount = int(amount)
        except (
            TypeError,
            ValueError,
        ):
            raise BillingOperationError(
                "Credit amount must be an integer."
            )

        if amount <= 0:
            raise BillingOperationError(
                "Credit amount must be greater than zero."
            )

        current = self.get_credit_balance(
            user_id
        )

        if current < amount:
            return BillingOperationResult(
                success=False,
                operation="consume_credits",
                user_id=user_id,
                message="Insufficient credits.",
                error="insufficient_credits",
                data={
                    "required": amount,
                    "available": current,
                },
            )

        try:
            result = self.credit_manager.consume(
                user_id=user_id,
                amount=amount,
                description=description,
            )

            return BillingOperationResult(
                success=True,
                operation="consume_credits",
                user_id=user_id,
                message="Credits consumed successfully.",
                data={
                    "amount": amount,
                    "remaining": (
                        self.get_credit_balance(
                            user_id
                        )
                    ),
                    "transaction": result,
                },
            )

        except Exception as exc:
            return BillingOperationResult(
                success=False,
                operation="consume_credits",
                user_id=user_id,
                message="Credit consumption failed.",
                error=str(exc),
            )

    # ========================================================
    # FEATURE ACCESS
    # ========================================================

    def check_feature(
        self,
        user_id: Any,
        feature: Any,
    ) -> BillingAccess:

        user_id = self.validate_user_id(
            user_id
        )

        plan_code = self.get_plan_code(
            user_id
        )

        try:

            result = (
                self.entitlement_manager.check_feature(
                    user_id=user_id,
                    feature=feature,
                )
            )

            allowed = bool(
                getattr(
                    result,
                    "allowed",
                    result
                    if isinstance(
                        result,
                        bool,
                    )
                    else False,
                )
            )

            reason = _safe_str(
                getattr(
                    result,
                    "reason",
                    "",
                )
            )

            return BillingAccess(
                user_id=user_id,
                allowed=allowed,
                feature=_safe_str(
                    feature
                ),
                plan_code=plan_code,
                reason=reason,
                metadata={
                    "entitlement_result": result,
                },
            )

        except Exception as exc:

            return BillingAccess(
                user_id=user_id,
                allowed=False,
                feature=_safe_str(
                    feature
                ),
                plan_code=plan_code,
                reason=str(exc),
            )

    def require_feature(
        self,
        user_id: Any,
        feature: Any,
    ) -> BillingAccess:

        access = self.check_feature(
            user_id,
            feature,
        )

        if not access.allowed:
            raise BillingAccessError(
                access.reason
                or (
                    "This feature is not "
                    "available on the current plan."
                )
            )

        return access

    # ========================================================
    # USER SUMMARY
    # ========================================================

    def user_summary(
        self,
        user_id: Any,
    ) -> BillingUserSummary:

        user_id = self.validate_user_id(
            user_id
        )

        subscription = self.get_subscription(
            user_id
        )

        plan_code = "free"
        plan_name = "Free"
        active = False
        expires_at = None
        days_remaining = 0

        if subscription is not None:

            plan_code = _safe_str(
                getattr(
                    subscription,
                    "plan_code",
                    "free",
                )
            ) or "free"

            active = bool(
                subscription.is_active()
            )

            expires_at = getattr(
                subscription,
                "expires_at",
                None,
            )

            try:
                days_remaining = int(
                    subscription.days_remaining()
                )
            except Exception:
                days_remaining = 0

            try:
                from billing.plans import (
                    get_plan,
                )

                plan = get_plan(
                    plan_code
                )

                if plan is not None:
                    plan_name = _safe_str(
                        getattr(
                            plan,
                            "name",
                            plan_code,
                        )
                    ) or plan_code

            except Exception:
                plan_name = plan_code

        return BillingUserSummary(
            user_id=user_id,
            plan_code=plan_code,
            plan_name=plan_name,
            subscription_active=active,
            expires_at=expires_at,
            days_remaining=max(
                0,
                days_remaining,
            ),
            credits=self.get_credit_balance(
                user_id
            ),
        )

    # ========================================================
    # ORDER
    # ========================================================

    def create_order(
        self,
        *,
        user_id: Any,
        order_type: Any,
        items: Optional[list] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> BillingOperationResult:

        user_id = self.validate_user_id(
            user_id
        )

        try:

            order = self.order_manager.create(
                user_id=user_id,
                order_type=order_type,
                items=items or [],
                metadata=dict(
                    metadata or {}
                ),
            )

            return BillingOperationResult(
                success=True,
                operation="create_order",
                user_id=user_id,
                message="Order created successfully.",
                data={
                    "order": order,
                    "order_id": getattr(
                        order,
                        "order_id",
                        None,
                    ),
                },
            )

        except TypeError:
            # Compatibility fallback for older OrderManager
            # implementations that do not yet accept metadata.

            try:

                order = self.order_manager.create(
                    user_id=user_id,
                    order_type=order_type,
                    items=items or [],
                )

                return BillingOperationResult(
                    success=True,
                    operation="create_order",
                    user_id=user_id,
                    message="Order created successfully.",
                    data={
                        "order": order,
                        "order_id": getattr(
                            order,
                            "order_id",
                            None,
                        ),
                    },
                )

            except Exception as exc:

                return BillingOperationResult(
                    success=False,
                    operation="create_order",
                    user_id=user_id,
                    message="Order creation failed.",
                    error=str(exc),
                )

        except Exception as exc:

            return BillingOperationResult(
                success=False,
                operation="create_order",
                user_id=user_id,
                message="Order creation failed.",
                error=str(exc),
            )

    # ========================================================
    # PRODUCTS
    # ========================================================

    def products(
        self,
    ) -> list:

        try:
            return list(
                self.product_catalog.all()
            )
        except Exception:
            return []

    def available_products(
        self,
    ) -> list:

        try:
            return list(
                self.product_catalog.available()
            )
        except Exception:
            return self.products()

    # ========================================================
    # INVOICE
    # ========================================================

    def get_invoice(
        self,
        invoice_id: str,
    ) -> Any:

        invoice_id = _safe_str(
            invoice_id
        )

        if not invoice_id:
            return None

        try:
            return self.invoice_manager.get(
                invoice_id
            )
        except Exception:
            return None

    # ========================================================
    # COMMERCIAL SUMMARY
    # ========================================================

    def commercial_summary(
        self,
        user_id: Any,
    ) -> Dict[str, Any]:

        summary = self.user_summary(
            user_id
        )

        return {
            "user_id": summary.user_id,
            "plan": {
                "code": summary.plan_code,
                "name": summary.plan_name,
                "active": summary.subscription_active,
                "expires_at": (
                    summary.expires_at.isoformat()
                    if summary.expires_at
                    else None
                ),
                "days_remaining": (
                    summary.days_remaining
                ),
            },
            "credits": summary.credits,
            "products_available": len(
                self.available_products()
            ),
        }


# ============================================================
# GLOBAL INSTANCE
# ============================================================


_default_billing_integration = (
    BillingIntegration()
)


# ============================================================
# PUBLIC HELPERS
# ============================================================


def get_billing_integration() -> BillingIntegration:
    return _default_billing_integration


def get_user_billing_summary(
    user_id: Any,
) -> BillingUserSummary:

    return _default_billing_integration.user_summary(
        user_id
    )


def check_billing_feature(
    user_id: Any,
    feature: Any,
) -> BillingAccess:

    return _default_billing_integration.check_feature(
        user_id,
        feature,
    )


def get_user_credit_balance(
    user_id: Any,
) -> int:

    return _default_billing_integration.get_credit_balance(
        user_id
    )


def get_user_plan(
    user_id: Any,
) -> str:

    return _default_billing_integration.get_plan_code(
        user_id
    )


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "BillingIntegrationError",
    "BillingAccessError",
    "BillingUserError",
    "BillingOperationError",

    "BillingAccess",
    "BillingUserSummary",
    "BillingOperationResult",

    "BillingIntegration",

    "get_billing_integration",
    "get_user_billing_summary",
    "check_billing_feature",
    "get_user_credit_balance",
    "get_user_plan",
]
