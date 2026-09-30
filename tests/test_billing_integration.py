"""
StructuralBot - Billing Integration Tests

Tests the application-facing billing facade.

This file focuses specifically on:
    billing.integration.BillingIntegration

It does NOT replace:
    tests/test_billing.py
    tests/test_billing_flow.py

Those files test the lower-level billing infrastructure and
commercial flow. This file tests the stable API that bot
handlers will eventually consume.
"""

from __future__ import annotations

from datetime import datetime, timezone


# ============================================================
# HELPERS
# ============================================================


def _value(obj, name, default=None):
    """Read an attribute from an object or dictionary."""

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


# ============================================================
# IMPORT
# ============================================================


def test_billing_integration_import():
    """
    Integration facade must import successfully.
    """

    from billing.integration import BillingIntegration

    assert BillingIntegration is not None


def test_billing_integration_initialization():
    """
    BillingIntegration must initialize using the default
    billing managers.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    assert integration is not None

    assert integration.subscription_manager is not None
    assert integration.credit_manager is not None
    assert integration.entitlement_manager is not None
    assert integration.order_manager is not None
    assert integration.invoice_manager is not None
    assert integration.product_catalog is not None


# ============================================================
# USER VALIDATION
# ============================================================


def test_user_id_validation():
    """
    Valid user IDs must be normalized.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    assert (
        integration.validate_user_id(123456)
        == "123456"
    )

    assert (
        integration.validate_user_id("  user-1  ")
        == "user-1"
    )


def test_empty_user_id_rejected():
    """
    Empty user IDs must not silently enter billing logic.
    """

    import pytest

    from billing.integration import (
        BillingIntegration,
        BillingUserError,
    )

    integration = BillingIntegration()

    with pytest.raises(BillingUserError):
        integration.validate_user_id("")


# ============================================================
# FREE USER
# ============================================================


def test_new_user_defaults_to_free_plan():
    """
    A user without an active subscription must resolve to
    the free plan.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    user_id = "integration-free-user"

    plan_code = integration.get_plan_code(
        user_id
    )

    assert plan_code == "free"


def test_new_user_has_no_active_subscription():
    """
    New user should not be considered subscribed.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    user_id = "integration-new-user"

    assert (
        integration.has_active_subscription(
            user_id
        )
        is False
    )


# ============================================================
# USER SUMMARY
# ============================================================


def test_user_summary_for_free_user():
    """
    Free user summary must contain stable commercial fields.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    user_id = "integration-summary-free"

    summary = integration.user_summary(
        user_id
    )

    assert summary is not None

    assert summary.user_id == user_id
    assert summary.plan_code == "free"
    assert summary.subscription_active is False
    assert summary.credits >= 0


def test_user_summary_serialization():
    """
    BillingUserSummary.to_dict() must produce UI-safe data.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    summary = integration.user_summary(
        "integration-summary-dict"
    )

    data = summary.to_dict()

    assert isinstance(data, dict)

    assert "user_id" in data
    assert "plan_code" in data
    assert "plan_name" in data
    assert "subscription_active" in data
    assert "credits" in data


# ============================================================
# SUBSCRIPTION
# ============================================================


def test_professional_subscription_visible_through_facade():
    """
    Subscription created through the manager must be visible
    through BillingIntegration.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    user_id = "integration-professional-user"

    integration.subscription_manager.activate(
        user_id=user_id,
        plan_code="professional",
        duration_days=30,
    )

    assert (
        integration.has_active_subscription(
            user_id
        )
        is True
    )

    assert (
        integration.get_plan_code(
            user_id
        )
        == "professional"
    )


def test_subscription_summary_updates():
    """
    User summary must reflect an active subscription.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    user_id = "integration-summary-paid"

    integration.subscription_manager.activate(
        user_id=user_id,
        plan_code="professional",
        duration_days=30,
    )

    summary = integration.user_summary(
        user_id
    )

    assert summary.plan_code == "professional"
    assert summary.subscription_active is True
    assert summary.days_remaining >= 29


# ============================================================
# CREDITS
# ============================================================


def test_credit_balance_facade():
    """
    Credit balance must be accessible through the facade.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    user_id = "integration-credit-user"

    before = integration.get_credit_balance(
        user_id
    )

    integration.credit_manager.add_credits(
        user_id=user_id,
        amount=250,
        description="Integration test credits",
    )

    after = integration.get_credit_balance(
        user_id
    )

    assert after == before + 250


def test_consume_credits_facade():
    """
    consume_credits() must return a normalized result.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    user_id = "integration-consume-user"

    integration.credit_manager.add_credits(
        user_id=user_id,
        amount=100,
        description="Consumption test",
    )

    result = integration.consume_credits(
        user_id=user_id,
        amount=30,
        description="Calculation",
    )

    assert result is not None
    assert result.success is True
    assert result.operation == "consume_credits"

    assert (
        integration.get_credit_balance(
            user_id
        )
        == 70
    )


def test_consume_insufficient_credits():
    """
    Insufficient credits must return a failed normalized
    result instead of silently consuming.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    user_id = "integration-insufficient-user"

    result = integration.consume_credits(
        user_id=user_id,
        amount=100,
        description="Should fail",
    )

    assert result.success is False
    assert result.error == "insufficient_credits"


# ============================================================
# PRODUCTS
# ============================================================


def test_products_facade():
    """
    Product catalog must be exposed through the facade.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    products = integration.products()

    assert isinstance(products, list)


def test_available_products_facade():
    """
    Available product list must be accessible.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    products = integration.available_products()

    assert isinstance(products, list)


# ============================================================
# FEATURE ACCESS
# ============================================================


def test_feature_access_returns_normalized_result():
    """
    check_feature() must always return BillingAccess rather
    than leaking internal entitlement implementation.
    """

    from billing.entitlements import (
        EntitlementManager,
    )

    from billing.integration import (
        BillingAccess,
        BillingIntegration,
    )

    from billing.plans import (
        PlanFeature,
    )

    integration = BillingIntegration(
        entitlement_manager=EntitlementManager()
    )

    result = integration.check_feature(
        "integration-feature-user",
        PlanFeature.BASIC_CALCULATIONS,
    )

    assert isinstance(
        result,
        BillingAccess,
    )

    assert result.user_id == (
        "integration-feature-user"
    )

    assert isinstance(
        result.allowed,
        bool,
    )


def test_feature_access_with_paid_user():
    """
    Feature access should be evaluated using the user's
    current subscription state.
    """

    from billing.entitlements import (
        EntitlementManager,
    )

    from billing.integration import (
        BillingIntegration,
    )

    from billing.plans import (
        PlanFeature,
    )

    from billing.subscription import (
        SubscriptionManager,
    )

    subscriptions = SubscriptionManager()

    user_id = "integration-feature-paid"

    subscriptions.activate(
        user_id=user_id,
        plan_code="professional",
        duration_days=30,
    )

    integration = BillingIntegration(
        subscription_manager=subscriptions,
        entitlement_manager=EntitlementManager(),
    )

    result = integration.check_feature(
        user_id,
        PlanFeature.ADVANCED_CALCULATIONS,
    )

    assert result is not None
    assert isinstance(
        result.allowed,
        bool,
    )


# ============================================================
# ORDER
# ============================================================


def test_create_order_facade():
    """
    Order creation through the facade must return a normalized
    BillingOperationResult.
    """

    from billing.integration import (
        BillingIntegration,
        BillingOperationResult,
    )

    from billing.orders import (
        OrderType,
    )

    integration = BillingIntegration()

    result = integration.create_order(
        user_id="integration-order-user",
        order_type=OrderType.SUBSCRIPTION,
        items=[],
    )

    assert isinstance(
        result,
        BillingOperationResult,
    )

    assert result.success is True
    assert result.operation == "create_order"

    assert "order" in result.data


# ============================================================
# INVOICE
# ============================================================


def test_invoice_lookup():
    """
    Invoice lookup through the facade should safely return
    None for unknown invoices.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    invoice = integration.get_invoice(
        "invoice-that-does-not-exist"
    )

    assert invoice is None


# ============================================================
# COMMERCIAL SUMMARY
# ============================================================


def test_commercial_summary():
    """
    commercial_summary() must provide a bot-friendly
    dictionary.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    data = integration.commercial_summary(
        "integration-commercial-user"
    )

    assert isinstance(
        data,
        dict,
    )

    assert "user_id" in data
    assert "plan" in data
    assert "credits" in data
    assert "products_available" in data

    assert isinstance(
        data["plan"],
        dict,
    )


# ============================================================
# GLOBAL FACADE
# ============================================================


def test_global_billing_integration():
    """
    Global facade helper must return a usable instance.
    """

    from billing.integration import (
        BillingIntegration,
        get_billing_integration,
    )

    integration = (
        get_billing_integration()
    )

    assert isinstance(
        integration,
        BillingIntegration,
    )


def test_global_user_summary_helper():
    """
    Global summary helper must work.
    """

    from billing.integration import (
        get_user_billing_summary,
    )

    summary = get_user_billing_summary(
        "integration-global-user"
    )

    assert summary is not None
    assert (
        summary.user_id
        == "integration-global-user"
    )


def test_global_plan_helper():
    """
    Global plan helper must default to free for a new user.
    """

    from billing.integration import (
        get_user_plan,
    )

    assert (
        get_user_plan(
            "integration-global-plan-user"
        )
        == "free"
    )


def test_global_credit_helper():
    """
    Global credit helper must return a numeric balance.
    """

    from billing.integration import (
        get_user_credit_balance,
    )

    balance = get_user_credit_balance(
        "integration-global-credit-user"
    )

    assert isinstance(
        balance,
        int,
    )


# ============================================================
# RESULT SERIALIZATION
# ============================================================


def test_billing_operation_result_serialization():
    """
    BillingOperationResult must serialize cleanly.
    """

    from billing.integration import (
        BillingOperationResult,
    )

    result = BillingOperationResult(
        success=True,
        operation="test",
        user_id="serialization-user",
        message="OK",
        data={
            "value": 123,
        },
    )

    data = result.to_dict()

    assert isinstance(
        data,
        dict,
    )

    assert data["success"] is True
    assert data["operation"] == "test"
    assert data["user_id"] == (
        "serialization-user"
    )

    assert isinstance(
        data["created_at"],
        str,
    )


# ============================================================
# BOT-SAFETY TEST
# ============================================================


def test_integration_does_not_require_telegram():
    """
    BillingIntegration must remain independent from Telegram.

    This is important because:
    - billing can be tested independently
    - future web/app clients can reuse billing
    - payment logic remains separate from Telegram
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    summary = integration.user_summary(
        "telegram-independent-user"
    )

    assert summary is not None
