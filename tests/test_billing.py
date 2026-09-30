"""
StructuralBot - Billing Integration Tests

Tests the commercial/billing layer without requiring:
- Telegram
- Real payment gateway
- Database
- External network

These tests verify that the current billing architecture
can work together before integration with bot.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal


# ============================================================
# TEST HELPERS
# ============================================================


def test_import_billing_package():
    """Billing package must import successfully."""

    import billing

    assert billing is not None


def test_plans_available():
    """Plan definitions must be available."""

    from billing.plans import (
        PLAN_DEFINITIONS,
        get_all_plans,
        get_plan,
    )

    assert isinstance(PLAN_DEFINITIONS, dict)

    plans = get_all_plans()

    assert plans

    for plan in plans:
        assert plan.code
        assert plan.name

        loaded = get_plan(plan.code)

        assert loaded is not None
        assert loaded.code == plan.code


def test_plan_features():
    """Plan feature system must work."""

    from billing.plans import (
        PlanFeature,
        get_plan,
        has_feature,
    )

    free_plan = get_plan("free")

    assert free_plan is not None

    # The helper must return a boolean rather than
    # raising an exception for a valid plan.
    result = has_feature(
        "free",
        PlanFeature.BASIC_CALCULATIONS,
    )

    assert isinstance(result, bool)


def test_credit_manager():
    """Credit manager must support balance and consumption."""

    from billing.credits import (
        CreditManager,
        CreditTransactionType,
    )

    manager = CreditManager()

    user_id = "test-user-credits"

    balance = manager.get_balance(user_id)

    assert balance is not None

    initial = balance.balance

    manager.add_credits(
        user_id=user_id,
        amount=100,
        transaction_type=(
            CreditTransactionType.BONUS
        ),
        description="Test bonus",
    )

    updated = manager.get_balance(user_id)

    assert updated.balance >= initial + 100


def test_credit_consumption():
    """Credits must be consumable."""

    from billing.credits import (
        CreditManager,
        CreditTransactionType,
    )

    manager = CreditManager()

    user_id = "test-user-consume"

    manager.add_credits(
        user_id=user_id,
        amount=100,
        transaction_type=(
            CreditTransactionType.BONUS
        ),
        description="Initial test balance",
    )

    before = manager.get_balance(user_id).balance

    result = manager.consume(
        user_id=user_id,
        amount=25,
        description="Test consumption",
    )

    assert result is not None

    after = manager.get_balance(user_id).balance

    assert after == before - 25


def test_subscription_creation():
    """Subscription manager must create subscriptions."""

    from billing.subscription import (
        SubscriptionManager,
        SubscriptionStatus,
    )

    manager = SubscriptionManager()

    user_id = "test-user-subscription"

    subscription = manager.activate(
        user_id=user_id,
        plan_code="basic",
        duration_days=30,
    )

    assert subscription is not None
    assert subscription.user_id == user_id
    assert subscription.plan_code == "basic"

    assert subscription.status in {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.TRIAL,
    }


def test_subscription_access():
    """Active subscription must expose access state."""

    from billing.subscription import (
        SubscriptionManager,
    )

    manager = SubscriptionManager()

    user_id = "test-user-access"

    manager.activate(
        user_id=user_id,
        plan_code="professional",
        duration_days=30,
    )

    subscription = manager.get_subscription(
        user_id
    )

    assert subscription is not None
    assert subscription.is_active()


def test_subscription_expiration():
    """Expired subscriptions must no longer be active."""

    from billing.subscription import (
        Subscription,
        SubscriptionStatus,
    )

    now = datetime.now(timezone.utc)

    subscription = Subscription(
        subscription_id="sub_test_expired",
        user_id="expired-user",
        plan_code="basic",
        status=SubscriptionStatus.ACTIVE,
        started_at=now - timedelta(days=60),
        expires_at=now - timedelta(days=1),
    )

    assert subscription.is_expired()


def test_gateway_registry():
    """Gateway registry must register and select gateways."""

    from billing.gateway_registry import (
        GatewayCapabilities,
        PaymentGatewayRegistry,
    )

    class TestGateway:
        name = "test"

        def health_check(self):
            return True

        def create_payment(self, request):
            return None

        def verify_payment(self, payment):
            return None

    registry = PaymentGatewayRegistry()

    registry.register(
        TestGateway(),
        capabilities=GatewayCapabilities(
            currencies=frozenset({"IRR"}),
            supports_subscription=True,
            supports_credit_purchase=True,
            supports_report_purchase=True,
            supports_verification=True,
        ),
        priority=10,
    )

    selected = registry.select(
        currency="IRR",
        order_type="subscription",
    )

    assert selected.name == "test"


def test_gateway_selection_by_currency():
    """Gateway selection must respect currency."""

    from billing.gateway_registry import (
        GatewayCapabilities,
        PaymentGatewayRegistry,
        GatewaySelectionError,
    )

    class DollarGateway:
        name = "usd_gateway"

        def health_check(self):
            return True

        def create_payment(self, request):
            return None

        def verify_payment(self, payment):
            return None

    registry = PaymentGatewayRegistry()

    registry.register(
        DollarGateway(),
        capabilities=GatewayCapabilities(
            currencies=frozenset({"USD"}),
        ),
    )

    try:
        registry.select(
            currency="IRR",
        )
    except GatewaySelectionError:
        return

    raise AssertionError(
        "Gateway registry selected an incompatible currency gateway."
    )


def test_transport_memory():
    """In-memory notification transport must work."""

    from billing.transport import (
        InMemoryNotificationTransport,
        TransportMessage,
        TransportStatus,
    )

    transport = InMemoryNotificationTransport()

    message = TransportMessage(
        notification_id="notification-test",
        user_id="user-test",
        channel="telegram",
        recipient="123456789",
        body="Test notification",
    )

    result = transport.send(message)

    assert result.status == TransportStatus.SENT
    assert result.success

    stored = transport.get_message(
        "notification-test"
    )

    assert stored is not None
    assert stored.body == "Test notification"


def test_transport_manager():
    """Transport manager must select a channel-compatible adapter."""

    from billing.transport import (
        InMemoryNotificationTransport,
        NotificationTransportManager,
        NotificationTransportRegistry,
        TransportMessage,
    )

    registry = NotificationTransportRegistry()

    registry.register(
        InMemoryNotificationTransport()
    )

    manager = NotificationTransportManager(
        registry=registry
    )

    message = TransportMessage(
        notification_id="transport-manager-test",
        user_id="user-test",
        channel="telegram",
        recipient="123456",
        body="Transport test",
    )

    result = manager.send(message)

    assert result.success


def test_order_creation():
    """Order manager must create a valid order."""

    from billing.orders import (
        OrderManager,
        OrderType,
    )

    manager = OrderManager()

    order = manager.create(
        user_id="order-test-user",
        order_type=OrderType.SUBSCRIPTION,
        items=[],
    )

    assert order is not None
    assert order.user_id == "order-test-user"


def test_product_catalog():
    """Default product catalog must be constructible."""

    from billing.products import (
        build_default_catalog,
    )

    catalog = build_default_catalog()

    assert catalog is not None

    products = catalog.all()

    assert isinstance(products, list)


def test_invoice_manager_import():
    """Invoice infrastructure must be importable."""

    from billing.invoice import (
        InvoiceManager,
        InvoiceStatus,
        InvoiceType,
    )

    manager = InvoiceManager()

    assert manager is not None
    assert InvoiceStatus
    assert InvoiceType


def test_audit_manager():
    """Audit manager must record events."""

    from billing.audit import (
        AuditActorType,
        AuditEventType,
        AuditManager,
    )

    manager = AuditManager()

    event = manager.record(
        event_type=AuditEventType.SYSTEM,
        actor_type=AuditActorType.SYSTEM,
        actor_id="test",
        action="billing_test",
        metadata={
            "source": "test_billing"
        },
    )

    assert event is not None
    assert event.action == "billing_test"


def test_event_bus():
    """Billing event bus must publish events."""

    from billing.events import (
        BillingEventBus,
        BillingEventSource,
        BillingEventType,
    )

    bus = BillingEventBus()

    event = bus.publish(
        event_type=BillingEventType.SYSTEM,
        source=BillingEventSource.SYSTEM,
        user_id="event-test-user",
        metadata={
            "test": True
        },
    )

    assert event is not None

    events = bus.list()

    assert len(events) >= 1


def test_webhook_manager_import():
    """Webhook infrastructure must be available."""

    from billing.webhooks import (
        WebhookManager,
        WebhookStatus,
        WebhookEventType,
    )

    manager = WebhookManager()

    assert manager is not None
    assert WebhookStatus
    assert WebhookEventType


def test_notification_manager_import():
    """Notification infrastructure must be available."""

    from billing.notifications import (
        NotificationManager,
        NotificationChannel,
        NotificationType,
    )

    manager = NotificationManager()

    assert manager is not None
    assert NotificationChannel
    assert NotificationType


def test_billing_service_import():
    """High-level billing service must import."""

    from billing.service import (
        BillingService,
    )

    service = BillingService()

    assert service is not None


def test_repository():
    """Generic repository must support basic CRUD."""

    from billing.repository import (
        InMemoryRepository,
    )

    repository = InMemoryRepository()

    item = {
        "id": "repo-test-1",
        "name": "Test",
    }

    repository.add(
        "repo-test-1",
        item,
    )

    assert repository.exists(
        "repo-test-1"
    )

    loaded = repository.get(
        "repo-test-1"
    )

    assert loaded == item

    repository.delete(
        "repo-test-1"
    )

    assert not repository.exists(
        "repo-test-1"
    )


# ============================================================
# OPTIONAL FULL-SMOKE TEST
# ============================================================


def test_billing_smoke_imports():
    """
    Final lightweight smoke test.

    This deliberately imports all major billing modules.
    It catches circular imports and missing symbols early.
    """

    import billing.plans
    import billing.credits
    import billing.subscription
    import billing.entitlements
    import billing.gateway
    import billing.gateway_registry
    import billing.orders
    import billing.checkout
    import billing.products
    import billing.fulfillment
    import billing.invoice
    import billing.service
    import billing.repository
    import billing.audit
    import billing.events
    import billing.webhooks
    import billing.notifications
    import billing.notification_service
    import billing.transport

    assert True
