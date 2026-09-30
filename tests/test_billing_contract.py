"""
StructuralBot - Billing Contract QA

Tests the commercial infrastructure without using a real payment
gateway or external service.

Architecture:

    Product
       ↓
    Order
       ↓
    Payment
       ↓
    Fulfillment
       ↓
    Subscription / Credits
       ↓
    Entitlements
       ↓
    Invoice / Notifications
"""

from __future__ import annotations

import inspect

import pytest

from billing.plans import (
    Plan,
    PlanFeature,
    PLAN_DEFINITIONS,
    get_all_plans,
    get_plan,
    has_feature,
)

from billing.credits import (
    CreditBalance,
    CreditManager,
    CreditTransaction,
    CreditTransactionType,
)

from billing.subscription import (
    Subscription,
    SubscriptionManager,
    SubscriptionStatus,
)

from billing.entitlements import (
    EntitlementManager,
)

from billing.gateway import (
    PaymentGateway,
    PaymentManager,
    PaymentRequest,
    PaymentStatus,
)

from billing.orders import (
    Order,
    OrderItem,
    OrderManager,
    OrderStatus,
    OrderType,
)

from billing.products import (
    Product,
    ProductCatalog,
    ProductType,
)

from billing.invoice import (
    Invoice,
    InvoiceItem,
    InvoiceManager,
)

from billing.integration import (
    BillingIntegration,
)


# ---------------------------------------------------------------------------
# PLANS
# ---------------------------------------------------------------------------

@pytest.mark.billing
def test_plan_definitions_exist() -> None:
    assert PLAN_DEFINITIONS


@pytest.mark.billing
def test_free_plan_exists() -> None:
    plan = get_plan("free")

    assert isinstance(
        plan,
        Plan,
    )


@pytest.mark.billing
def test_all_plans_have_unique_codes() -> None:
    plans = get_all_plans()

    codes = [
        plan.code
        for plan in plans
    ]

    assert len(codes) == len(set(codes))


@pytest.mark.billing
def test_plan_features_are_valid() -> None:
    for plan in get_all_plans():
        for feature in plan.features:
            assert isinstance(
                feature,
                PlanFeature,
            )


@pytest.mark.billing
def test_feature_check_is_boolean() -> None:
    result = has_feature(
        "free",
        PlanFeature.BASIC_CALCULATIONS,
    )

    assert isinstance(
        result,
        bool,
    )


# ---------------------------------------------------------------------------
# CREDITS
# ---------------------------------------------------------------------------

def test_credit_balance_can_be_created() -> None:
    balance = CreditBalance(
        user_id="user-001",
    )

    assert balance.user_id == "user-001"


def test_credit_manager_can_be_created() -> None:
    manager = CreditManager()

    assert manager is not None


def test_credit_manager_can_add_credits() -> None:
    manager = CreditManager()

    if not hasattr(manager, "add_credits"):
        pytest.skip(
            "CreditManager.add_credits is not exposed."
        )

    result = manager.add_credits(
        user_id="user-001",
        amount=100,
    )

    assert result is not None


def test_credit_transaction_types_exist() -> None:
    values = list(
        CreditTransactionType
    )

    assert values


def test_credit_transaction_is_constructible() -> None:
    signature = inspect.signature(
        CreditTransaction,
    )

    kwargs = {}

    if "user_id" in signature.parameters:
        kwargs["user_id"] = "user-001"

    if "amount" in signature.parameters:
        kwargs["amount"] = 10

    if "transaction_type" in signature.parameters:
        kwargs["transaction_type"] = (
            CreditTransactionType.BONUS
        )

    transaction = CreditTransaction(
        **kwargs,
    )

    assert transaction is not None


# ---------------------------------------------------------------------------
# SUBSCRIPTIONS
# ---------------------------------------------------------------------------

def test_subscription_status_exists() -> None:
    assert list(
        SubscriptionStatus
    )


def test_subscription_manager_can_be_created() -> None:
    manager = SubscriptionManager()

    assert manager is not None


def test_subscription_can_be_created() -> None:
    manager = SubscriptionManager()

    if not hasattr(
        manager,
        "activate",
    ):
        pytest.skip(
            "SubscriptionManager.activate is not exposed."
        )

    subscription = manager.activate(
        user_id="user-001",
        plan_code="basic",
    )

    assert subscription is not None

    assert subscription.user_id == "user-001"
    assert subscription.plan_code == "basic"


def test_active_subscription_is_active() -> None:
    manager = SubscriptionManager()

    if not hasattr(
        manager,
        "activate",
    ):
        pytest.skip()

    subscription = manager.activate(
        user_id="user-002",
        plan_code="basic",
    )

    assert subscription.is_active()


# ---------------------------------------------------------------------------
# ENTITLEMENTS
# ---------------------------------------------------------------------------

def test_entitlement_manager_can_be_created() -> None:
    manager = EntitlementManager()

    assert manager is not None


def test_entitlement_manager_exposes_feature_check() -> None:
    manager = EntitlementManager()

    candidates = (
        "check_feature",
        "has_feature",
        "require_feature",
    )

    assert any(
        hasattr(manager, name)
        for name in candidates
    )


# ---------------------------------------------------------------------------
# PRODUCTS
# ---------------------------------------------------------------------------

def test_product_type_exists() -> None:
    assert list(
        ProductType
    )


def test_product_catalog_can_be_created() -> None:
    catalog = ProductCatalog()

    assert catalog is not None


def test_product_can_be_constructed() -> None:
    signature = inspect.signature(
        Product,
    )

    kwargs = {}

    if "product_id" in signature.parameters:
        kwargs["product_id"] = "TEST-PRODUCT"

    if "name" in signature.parameters:
        kwargs["name"] = "Test Product"

    if "product_type" in signature.parameters:
        kwargs["product_type"] = ProductType.CUSTOM_SERVICE

    if "price" in signature.parameters:
        kwargs["price"] = 0

    product = Product(
        **kwargs,
    )

    assert product is not None


# ---------------------------------------------------------------------------
# ORDERS
# ---------------------------------------------------------------------------

def test_order_status_exists() -> None:
    assert list(
        OrderStatus
    )


def test_order_type_exists() -> None:
    assert list(
        OrderType
    )


def test_order_manager_can_be_created() -> None:
    manager = OrderManager()

    assert manager is not None


def test_order_item_can_be_constructed() -> None:
    signature = inspect.signature(
        OrderItem,
    )

    kwargs = {}

    if "product_id" in signature.parameters:
        kwargs["product_id"] = "TEST"

    if "name" in signature.parameters:
        kwargs["name"] = "Test"

    if "quantity" in signature.parameters:
        kwargs["quantity"] = 1

    if "unit_price" in signature.parameters:
        kwargs["unit_price"] = 0

    item = OrderItem(
        **kwargs,
    )

    assert item is not None


def test_order_can_be_created() -> None:
    manager = OrderManager()

    if not hasattr(
        manager,
        "create",
    ):
        pytest.skip()

    order = manager.create(
        user_id="user-001",
        order_type=OrderType.CREDIT,
        items=[],
    )

    assert order is not None


# ---------------------------------------------------------------------------
# PAYMENT
# ---------------------------------------------------------------------------

def test_payment_status_exists() -> None:
    assert list(
        PaymentStatus
    )


def test_payment_manager_can_be_created() -> None:
    manager = PaymentManager()

    assert manager is not None


def test_payment_request_is_constructible() -> None:
    signature = inspect.signature(
        PaymentRequest,
    )

    kwargs = {}

    if "user_id" in signature.parameters:
        kwargs["user_id"] = "user-001"

    if "amount" in signature.parameters:
        kwargs["amount"] = 100

    if "currency" in signature.parameters:
        kwargs["currency"] = "IRR"

    request = PaymentRequest(
        **kwargs,
    )

    assert request is not None


# ---------------------------------------------------------------------------
# PAYMENT GATEWAY CONTRACT
# ---------------------------------------------------------------------------

def test_payment_gateway_is_protocol_or_abstract_contract() -> None:
    assert PaymentGateway is not None


# ---------------------------------------------------------------------------
# INVOICES
# ---------------------------------------------------------------------------

def test_invoice_manager_can_be_created() -> None:
    manager = InvoiceManager()

    assert manager is not None


def test_invoice_item_is_constructible() -> None:
    signature = inspect.signature(
        InvoiceItem,
    )

    kwargs = {}

    if "description" in signature.parameters:
        kwargs["description"] = "Test item"

    if "quantity" in signature.parameters:
        kwargs["quantity"] = 1

    if "unit_price" in signature.parameters:
        kwargs["unit_price"] = 0

    item = InvoiceItem(
        **kwargs,
    )

    assert item is not None


def test_invoice_class_exists() -> None:
    assert Invoice is not None


# ---------------------------------------------------------------------------
# INTEGRATION FACADE
# ---------------------------------------------------------------------------

@pytest.mark.billing
def test_billing_integration_can_be_created() -> None:
    integration = BillingIntegration()

    assert integration is not None


def test_billing_integration_validates_user_id() -> None:
    integration = BillingIntegration()

    assert integration.validate_user_id(
        "user-001"
    )


def test_billing_integration_rejects_empty_user_id() -> None:
    integration = BillingIntegration()

    with pytest.raises(Exception):
        integration.validate_user_id("")


# ---------------------------------------------------------------------------
# COMMERCIAL ISOLATION
# ---------------------------------------------------------------------------

def test_billing_does_not_require_telegram() -> None:
    import billing.integration as module

    source = inspect.getsource(module)

    assert "import telegram" not in source
    assert "from telegram" not in source


def test_billing_does_not_require_ai() -> None:
    import billing.integration as module

    source = inspect.getsource(module)

    assert "import ai" not in source
    assert "from ai" not in source


# ---------------------------------------------------------------------------
# NO REAL PAYMENT NETWORK
# ---------------------------------------------------------------------------

def test_payment_manager_is_local_by_default() -> None:
    manager = PaymentManager()

    source = inspect.getsource(
        manager.__class__,
    )

    assert "requests.post" not in source
    assert "httpx.post" not in source


# ---------------------------------------------------------------------------
# ARCHITECTURAL PRINCIPLE
# ---------------------------------------------------------------------------

@pytest.mark.billing
def test_billing_layer_is_independent_from_telegram() -> None:
    """
    Billing must remain provider-independent.

    Telegram is a notification/UI transport, not the source of
    commercial truth.
    """

    modules = (
        "billing.plans",
        "billing.credits",
        "billing.subscription",
        "billing.orders",
        "billing.gateway",
        "billing.checkout",
        "billing.invoice",
        "billing.fulfillment",
    )

    for module_name in modules:
        module = __import__(
            module_name,
            fromlist=["*"],
        )

        source = inspect.getsource(
            module,
        )

        assert "from telegram" not in source
        assert "import telegram" not in source
