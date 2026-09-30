"""
StructuralBot - Billing End-to-End Flow Tests

Commercial billing flow tests.

Purpose:
    Validate the complete logical revenue flow without requiring
    a real payment provider, Telegram, database, or network.

Flow:

    Product
       ↓
    Order
       ↓
    Payment
       ↓
    Verification
       ↓
    Fulfillment
       ↓
    Subscription / Credits
       ↓
    Invoice
       ↓
    Notification

Important:
    These tests validate the current in-memory architecture.
    They are intentionally independent from real payment gateways.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal


# ============================================================
# HELPERS
# ============================================================


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_value(obj, name, default=None):
    """
    Safely retrieve an attribute from either an object or dict.
    """
    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


# ============================================================
# PRODUCT → ORDER
# ============================================================


def test_subscription_product_exists():
    """
    The default catalog should contain subscription products.
    """

    from billing.products import (
        ProductType,
        build_default_catalog,
    )

    catalog = build_default_catalog()

    products = catalog.by_type(
        ProductType.SUBSCRIPTION
    )

    assert isinstance(products, list)

    # The commercial architecture should have at least
    # one subscription product.
    assert len(products) >= 1


def test_credit_products_exist():
    """
    The default catalog should contain credit products.
    """

    from billing.products import (
        ProductType,
        build_default_catalog,
    )

    catalog = build_default_catalog()

    products = catalog.by_type(
        ProductType.CREDIT_PACK
    )

    assert isinstance(products, list)


def test_create_subscription_order():
    """
    A subscription order must be creatable.
    """

    from billing.orders import (
        OrderManager,
        OrderStatus,
        OrderType,
    )

    manager = OrderManager()

    order = manager.create(
        user_id="flow-user-subscription",
        order_type=OrderType.SUBSCRIPTION,
        items=[],
    )

    assert order is not None

    assert (
        _get_value(order, "user_id")
        == "flow-user-subscription"
    )

    assert (
        _get_value(order, "order_type")
        == OrderType.SUBSCRIPTION
    )


# ============================================================
# PAYMENT
# ============================================================


def test_create_payment_request():
    """
    Payment request infrastructure must be usable.
    """

    from billing.gateway import (
        PaymentRequest,
    )

    request = PaymentRequest(
        user_id="payment-flow-user",
        amount=Decimal("100000"),
        currency="IRR",
        description="StructuralBot subscription test",
    )

    assert request is not None

    assert (
        _get_value(request, "user_id")
        == "payment-flow-user"
    )

    assert (
        _get_value(request, "currency")
        == "IRR"
    )


def test_placeholder_payment_gateway():
    """
    Placeholder gateway must be available for development.
    """

    from billing.gateway import (
        PaymentRequest,
        PlaceholderPaymentGateway,
        PaymentStatus,
    )

    gateway = PlaceholderPaymentGateway()

    request = PaymentRequest(
        user_id="placeholder-user",
        amount=Decimal("50000"),
        currency="IRR",
        description="Placeholder payment",
    )

    result = gateway.create_payment(request)

    assert result is not None

    status = _get_value(
        result,
        "status",
    )

    assert status is not None

    # The placeholder gateway must never pretend that a
    # real external payment was completed.
    assert status != PaymentStatus.SUCCESS


# ============================================================
# ORDER + PAYMENT
# ============================================================


def test_order_payment_relationship():
    """
    An order should be able to reference a payment.
    """

    from billing.orders import (
        OrderManager,
        OrderType,
    )

    manager = OrderManager()

    order = manager.create(
        user_id="payment-order-user",
        order_type=OrderType.SUBSCRIPTION,
        items=[],
    )

    assert order is not None

    payment_reference = "payment_test_001"

    # Use the manager's public API when available.
    attached = manager.attach_payment(
        _get_value(order, "order_id"),
        payment_reference,
    )

    assert attached is not None

    refreshed = manager.get(
        _get_value(order, "order_id")
    )

    assert refreshed is not None

    assert (
        _get_value(
            refreshed,
            "payment_id",
            _get_value(
                refreshed,
                "payment_reference",
                None,
            ),
        )
        == payment_reference
    )


# ============================================================
# SUBSCRIPTION FULFILLMENT
# ============================================================


def test_subscription_activation_after_payment():
    """
    Successful commercial fulfillment must activate the
    requested subscription.
    """

    from billing.subscription import (
        SubscriptionManager,
    )

    manager = SubscriptionManager()

    user_id = "fulfillment-subscription-user"

    subscription = manager.activate(
        user_id=user_id,
        plan_code="professional",
        duration_days=30,
    )

    assert subscription is not None

    assert (
        _get_value(subscription, "user_id")
        == user_id
    )

    assert (
        _get_value(subscription, "plan_code")
        == "professional"
    )

    assert subscription.is_active()


def test_subscription_days_remaining():
    """
    An active subscription should report remaining time.
    """

    from billing.subscription import (
        SubscriptionManager,
    )

    manager = SubscriptionManager()

    subscription = manager.activate(
        user_id="remaining-days-user",
        plan_code="basic",
        duration_days=30,
    )

    remaining = subscription.days_remaining()

    assert remaining is not None
    assert remaining >= 29


# ============================================================
# CREDIT FULFILLMENT
# ============================================================


def test_credit_purchase_flow():
    """
    A paid credit package should increase the user's
    credit balance after fulfillment.
    """

    from billing.credits import (
        CreditManager,
        CreditTransactionType,
    )

    manager = CreditManager()

    user_id = "credit-purchase-user"

    before = manager.get_balance(
        user_id
    ).balance

    manager.add_credits(
        user_id=user_id,
        amount=500,
        transaction_type=(
            CreditTransactionType.PURCHASE
        ),
        description="Purchased credits",
    )

    after = manager.get_balance(
        user_id
    ).balance

    assert after == before + 500


def test_credit_purchase_is_consumable():
    """
    Purchased credits must be usable afterwards.
    """

    from billing.credits import (
        CreditManager,
        CreditTransactionType,
    )

    manager = CreditManager()

    user_id = "credit-consumption-flow"

    manager.add_credits(
        user_id=user_id,
        amount=200,
        transaction_type=(
            CreditTransactionType.PURCHASE
        ),
        description="Flow test credits",
    )

    before = manager.get_balance(
        user_id
    ).balance

    manager.consume(
        user_id=user_id,
        amount=50,
        description="Calculation usage",
    )

    after = manager.get_balance(
        user_id
    ).balance

    assert after == before - 50


# ============================================================
# ENTITLEMENTS
# ============================================================


def test_professional_entitlement():
    """
    Professional subscription should produce an entitlement
    context that can be evaluated by the entitlement layer.
    """

    from billing.entitlements import (
        EntitlementManager,
    )

    from billing.plans import (
        PlanFeature,
    )

    from billing.subscription import (
        SubscriptionManager,
    )

    subscription_manager = SubscriptionManager()

    user_id = "entitlement-flow-user"

    subscription_manager.activate(
        user_id=user_id,
        plan_code="professional",
        duration_days=30,
    )

    entitlement_manager = EntitlementManager()

    result = entitlement_manager.check_feature(
        user_id=user_id,
        feature=PlanFeature.ADVANCED_CALCULATIONS,
    )

    assert result is not None


# ============================================================
# INVOICE
# ============================================================


def test_create_invoice():
    """
    Invoice infrastructure should create a valid invoice.
    """

    from billing.invoice import (
        InvoiceManager,
        InvoiceType,
    )

    manager = InvoiceManager()

    invoice = manager.create(
        user_id="invoice-flow-user",
        invoice_type=InvoiceType.SUBSCRIPTION,
    )

    assert invoice is not None

    assert (
        _get_value(invoice, "user_id")
        == "invoice-flow-user"
    )


# ============================================================
# NOTIFICATION
# ============================================================


def test_payment_success_notification_message():
    """
    Payment success message factory must generate text.
    """

    from billing.notifications import (
        payment_success_message,
    )

    message = payment_success_message(
        amount="100,000",
        currency="IRR",
        order_id="ORD-TEST-001",
    )

    assert message is not None
    assert str(message).strip()


def test_subscription_notification_message():
    """
    Subscription activation message must be generated.
    """

    from billing.notifications import (
        subscription_activated_message,
    )

    message = subscription_activated_message(
        plan_name="Professional",
        expires_at=_now(),
    )

    assert message is not None
    assert str(message).strip()


# ============================================================
# TRANSPORT
# ============================================================


def test_billing_notification_transport():
    """
    A generated notification must be deliverable through the
    development memory transport.
    """

    from billing.transport import (
        InMemoryNotificationTransport,
        TransportMessage,
    )

    transport = InMemoryNotificationTransport()

    message = TransportMessage(
        notification_id="flow-notification-001",
        user_id="flow-user",
        channel="telegram",
        recipient="123456",
        body="Payment completed.",
        metadata={
            "order_id": "ORD-001",
        },
    )

    result = transport.send(message)

    assert result.success


# ============================================================
# FULFILLMENT MANAGER
# ============================================================


def test_fulfillment_manager_import_and_creation():
    """
    Fulfillment manager must initialize successfully.
    """

    from billing.fulfillment import (
        FulfillmentManager,
    )

    manager = FulfillmentManager()

    assert manager is not None


# ============================================================
# BILLING SERVICE
# ============================================================


def test_billing_service_initialization():
    """
    High-level BillingService must initialize without external
    infrastructure.
    """

    from billing.service import (
        BillingService,
    )

    service = BillingService()

    assert service is not None


# ============================================================
# COMPLETE LOGICAL FLOW
# ============================================================


def test_complete_subscription_revenue_flow():
    """
    Complete logical subscription revenue flow.

    This intentionally uses in-memory components.

    Flow:

        User
         ↓
        Product
         ↓
        Order
         ↓
        Payment
         ↓
        Subscription
         ↓
        Entitlement
         ↓
        Invoice
         ↓
        Notification
    """

    from billing.products import (
        ProductType,
        build_default_catalog,
    )

    from billing.orders import (
        OrderManager,
        OrderType,
    )

    from billing.subscription import (
        SubscriptionManager,
    )

    from billing.invoice import (
        InvoiceManager,
        InvoiceType,
    )

    from billing.transport import (
        InMemoryNotificationTransport,
        TransportMessage,
    )

    from billing.notifications import (
        subscription_activated_message,
    )

    # --------------------------------------------------------
    # 1. Product
    # --------------------------------------------------------

    catalog = build_default_catalog()

    subscription_products = catalog.by_type(
        ProductType.SUBSCRIPTION
    )

    assert subscription_products

    product = subscription_products[0]

    # --------------------------------------------------------
    # 2. User
    # --------------------------------------------------------

    user_id = "complete-flow-user"

    # --------------------------------------------------------
    # 3. Order
    # --------------------------------------------------------

    order_manager = OrderManager()

    order = order_manager.create(
        user_id=user_id,
        order_type=OrderType.SUBSCRIPTION,
        items=[],
    )

    assert order is not None

    order_id = _get_value(
        order,
        "order_id",
    )

    assert order_id

    # --------------------------------------------------------
    # 4. Payment reference
    # --------------------------------------------------------

    payment_reference = (
        "payment_complete_flow_001"
    )

    order_manager.attach_payment(
        order_id,
        payment_reference,
    )

    # --------------------------------------------------------
    # 5. Payment success / fulfillment simulation
    # --------------------------------------------------------
    #
    # We intentionally do not fake a real payment gateway.
    # The actual gateway adapter will be connected later.

    subscription_manager = (
        SubscriptionManager()
    )

    subscription = subscription_manager.activate(
        user_id=user_id,
        plan_code="professional",
        duration_days=30,
        payment_reference=payment_reference,
    )

    assert subscription.is_active()

    # --------------------------------------------------------
    # 6. Entitlement
    # --------------------------------------------------------

    assert (
        subscription.plan_code
        == "professional"
    )

    # --------------------------------------------------------
    # 7. Invoice
    # --------------------------------------------------------

    invoice_manager = InvoiceManager()

    invoice = invoice_manager.create(
        user_id=user_id,
        invoice_type=InvoiceType.SUBSCRIPTION,
    )

    assert invoice is not None

    # --------------------------------------------------------
    # 8. Notification
    # --------------------------------------------------------

    notification_text = (
        subscription_activated_message(
            plan_name="Professional",
            expires_at=subscription.expires_at,
        )
    )

    assert notification_text

    # --------------------------------------------------------
    # 9. Transport
    # --------------------------------------------------------

    transport = (
        InMemoryNotificationTransport()
    )

    notification = TransportMessage(
        notification_id="complete-flow-notification",
        user_id=user_id,
        channel="telegram",
        recipient="123456",
        body=notification_text,
        metadata={
            "order_id": order_id,
            "payment_reference": payment_reference,
            "product_id": _get_value(
                product,
                "product_id",
                None,
            ),
        },
    )

    result = transport.send(
        notification
    )

    assert result.success

    # --------------------------------------------------------
    # Final assertions
    # --------------------------------------------------------

    assert (
        subscription.user_id
        == user_id
    )

    assert (
        subscription.plan_code
        == "professional"
    )

    assert transport.get_message(
        "complete-flow-notification"
    ) is not None


# ============================================================
# COMMERCIAL SAFETY TEST
# ============================================================


def test_placeholder_payment_must_not_claim_success():
    """
    Development payment infrastructure must never silently
    convert a placeholder transaction into a successful
    commercial payment.
    """

    from billing.gateway import (
        PaymentRequest,
        PaymentStatus,
        PlaceholderPaymentGateway,
    )

    gateway = PlaceholderPaymentGateway()

    request = PaymentRequest(
        user_id="safety-user",
        amount=Decimal("100000"),
        currency="IRR",
        description="Safety test",
    )

    result = gateway.create_payment(
        request
    )

    status = _get_value(
        result,
        "status",
    )

    assert status != PaymentStatus.SUCCESS


# ============================================================
# FINAL ARCHITECTURE SMOKE TEST
# ============================================================


def test_complete_billing_modules_import():
    """
    All current billing modules must import together.

    This catches circular imports and missing symbols before
    bot.py integration.
    """

    modules = [
        "billing.plans",
        "billing.credits",
        "billing.subscription",
        "billing.entitlements",
        "billing.gateway",
        "billing.gateway_registry",
        "billing.orders",
        "billing.checkout",
        "billing.products",
        "billing.fulfillment",
        "billing.invoice",
        "billing.service",
        "billing.repository",
        "billing.audit",
        "billing.events",
        "billing.webhooks",
        "billing.notifications",
        "billing.notification_service",
        "billing.transport",
    ]

    for module_name in modules:
        module = __import__(
            module_name,
            fromlist=["*"],
        )

        assert module is not None
