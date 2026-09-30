"""
StructuralBot - Billing Events

Standardized billing-domain events.

Responsibilities:
- Define stable event names
- Provide typed event payloads
- Normalize event creation
- Support future event bus / database / notification integrations
- Keep billing modules decoupled from Telegram handlers

This module does not execute business logic.
It only defines and creates billing events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_id(value: Any) -> Optional[str]:
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def _safe_metadata(
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Copy metadata while removing obvious secret fields.
    """

    if not metadata:
        return {}

    sensitive_keys = {
        "password",
        "passwd",
        "secret",
        "api_key",
        "apikey",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "card_number",
        "pan",
        "cvv",
        "cvc",
        "pin",
    }

    result: Dict[str, Any] = {}

    for key, value in metadata.items():
        key_text = str(key)
        normalized = key_text.lower().strip()

        if normalized in sensitive_keys:
            result[key_text] = "[REDACTED]"
        else:
            result[key_text] = value

    return result


# ---------------------------------------------------------------------------
# EVENT TYPES
# ---------------------------------------------------------------------------


class BillingEventType(str, Enum):
    """
    Stable domain event identifiers.

    These names should be treated as public internal API because
    future integrations may depend on them.
    """

    # Product
    PRODUCT_CREATED = "billing.product.created"
    PRODUCT_UPDATED = "billing.product.updated"
    PRODUCT_ACTIVATED = "billing.product.activated"
    PRODUCT_DEACTIVATED = "billing.product.deactivated"

    # Order
    ORDER_CREATED = "billing.order.created"
    ORDER_UPDATED = "billing.order.updated"
    ORDER_PAYMENT_PENDING = "billing.order.payment_pending"
    ORDER_PAID = "billing.order.paid"
    ORDER_PROCESSING = "billing.order.processing"
    ORDER_COMPLETED = "billing.order.completed"
    ORDER_FAILED = "billing.order.failed"
    ORDER_CANCELLED = "billing.order.cancelled"
    ORDER_REFUNDED = "billing.order.refunded"
    ORDER_EXPIRED = "billing.order.expired"

    # Payment
    PAYMENT_CREATED = "billing.payment.created"
    PAYMENT_PENDING = "billing.payment.pending"
    PAYMENT_REDIRECT_REQUIRED = "billing.payment.redirect_required"
    PAYMENT_SUCCESS = "billing.payment.success"
    PAYMENT_FAILED = "billing.payment.failed"
    PAYMENT_CANCELLED = "billing.payment.cancelled"
    PAYMENT_REFUNDED = "billing.payment.refunded"
    PAYMENT_EXPIRED = "billing.payment.expired"

    # Subscription
    SUBSCRIPTION_CREATED = "billing.subscription.created"
    SUBSCRIPTION_TRIAL_STARTED = "billing.subscription.trial_started"
    SUBSCRIPTION_ACTIVATED = "billing.subscription.activated"
    SUBSCRIPTION_RENEWED = "billing.subscription.renewed"
    SUBSCRIPTION_CANCELLED = "billing.subscription.cancelled"
    SUBSCRIPTION_EXPIRED = "billing.subscription.expired"
    SUBSCRIPTION_SUSPENDED = "billing.subscription.suspended"
    SUBSCRIPTION_RESTORED = "billing.subscription.restored"

    # Credits
    CREDIT_PURCHASED = "billing.credit.purchased"
    CREDIT_GRANTED = "billing.credit.granted"
    CREDIT_CONSUMED = "billing.credit.consumed"
    CREDIT_REFUNDED = "billing.credit.refunded"
    CREDIT_EXPIRED = "billing.credit.expired"
    CREDIT_ADJUSTED = "billing.credit.adjusted"

    # Checkout
    CHECKOUT_CREATED = "billing.checkout.created"
    CHECKOUT_VERIFIED = "billing.checkout.verified"
    CHECKOUT_FAILED = "billing.checkout.failed"
    CHECKOUT_FULFILLED = "billing.checkout.fulfilled"

    # Fulfillment
    FULFILLMENT_STARTED = "billing.fulfillment.started"
    FULFILLMENT_COMPLETED = "billing.fulfillment.completed"
    FULFILLMENT_FAILED = "billing.fulfillment.failed"
    FULFILLMENT_SKIPPED = "billing.fulfillment.skipped"

    # Invoice
    INVOICE_CREATED = "billing.invoice.created"
    INVOICE_ISSUED = "billing.invoice.issued"
    INVOICE_PAID = "billing.invoice.paid"
    INVOICE_VOIDED = "billing.invoice.voided"
    INVOICE_REFUNDED = "billing.invoice.refunded"

    # Generic
    SECURITY_ALERT = "billing.security.alert"
    SYSTEM_ERROR = "billing.system.error"


# ---------------------------------------------------------------------------
# EVENT SOURCE
# ---------------------------------------------------------------------------


class BillingEventSource(str, Enum):
    """
    Origin of an event.
    """

    SYSTEM = "system"
    BOT = "bot"
    USER = "user"
    ADMIN = "admin"
    API = "api"
    PAYMENT_GATEWAY = "payment_gateway"
    SCHEDULED_JOB = "scheduled_job"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# EVENT
# ---------------------------------------------------------------------------


@dataclass
class BillingEvent:
    """
    Generic billing-domain event.

    An event describes something that happened.
    It does not itself perform the operation.
    """

    event_id: str
    event_type: BillingEventType

    source: BillingEventSource = BillingEventSource.SYSTEM

    actor_id: Optional[str] = None
    user_id: Optional[str] = None

    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    fulfillment_id: Optional[str] = None

    product_code: Optional[str] = None

    amount: Optional[float] = None
    currency: Optional[str] = None

    message: str = ""

    payload: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=_utc_now)

    correlation_id: Optional[str] = None

    causation_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        event_type: BillingEventType,
        *,
        source: BillingEventSource = BillingEventSource.SYSTEM,
        actor_id: Optional[str] = None,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        fulfillment_id: Optional[str] = None,
        product_code: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        message: str = "",
        payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
    ) -> "BillingEvent":
        """
        Create a normalized billing event.
        """

        correlation = _normalize_id(correlation_id)

        if correlation is None:
            correlation = f"corr_{uuid.uuid4().hex}"

        return cls(
            event_id=f"evt_{uuid.uuid4().hex}",
            event_type=event_type,
            source=source,
            actor_id=_normalize_id(actor_id),
            user_id=_normalize_id(user_id),
            order_id=_normalize_id(order_id),
            payment_id=_normalize_id(payment_id),
            subscription_id=_normalize_id(subscription_id),
            invoice_id=_normalize_id(invoice_id),
            fulfillment_id=_normalize_id(fulfillment_id),
            product_code=_normalize_id(product_code),
            amount=float(amount) if amount is not None else None,
            currency=_normalize_id(currency),
            message=str(message or ""),
            payload=_safe_metadata(payload),
            created_at=_utc_now(),
            correlation_id=correlation,
            causation_id=_normalize_id(causation_id),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize event into JSON-friendly data.
        """

        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source.value,
            "actor_id": self.actor_id,
            "user_id": self.user_id,
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "subscription_id": self.subscription_id,
            "invoice_id": self.invoice_id,
            "fulfillment_id": self.fulfillment_id,
            "product_code": self.product_code,
            "amount": self.amount,
            "currency": self.currency,
            "message": self.message,
            "payload": dict(self.payload),
            "created_at": self.created_at.isoformat(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
        }


# ---------------------------------------------------------------------------
# EVENT FACTORIES
# ---------------------------------------------------------------------------


def order_event(
    event_type: BillingEventType,
    *,
    order_id: str,
    user_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    source: BillingEventSource = BillingEventSource.SYSTEM,
    amount: Optional[float] = None,
    currency: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    message: str = "",
    correlation_id: Optional[str] = None,
    causation_id: Optional[str] = None,
) -> BillingEvent:
    """
    Create an order-related event.
    """

    return BillingEvent.create(
        event_type,
        source=source,
        actor_id=actor_id,
        user_id=user_id,
        order_id=order_id,
        amount=amount,
        currency=currency,
        payload=payload,
        message=message,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


def payment_event(
    event_type: BillingEventType,
    *,
    payment_id: str,
    user_id: Optional[str] = None,
    order_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    source: BillingEventSource = BillingEventSource.SYSTEM,
    amount: Optional[float] = None,
    currency: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    message: str = "",
    correlation_id: Optional[str] = None,
    causation_id: Optional[str] = None,
) -> BillingEvent:
    """
    Create a payment-related event.
    """

    return BillingEvent.create(
        event_type,
        source=source,
        actor_id=actor_id,
        user_id=user_id,
        order_id=order_id,
        payment_id=payment_id,
        amount=amount,
        currency=currency,
        payload=payload,
        message=message,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


def subscription_event(
    event_type: BillingEventType,
    *,
    subscription_id: str,
    user_id: str,
    actor_id: Optional[str] = None,
    source: BillingEventSource = BillingEventSource.SYSTEM,
    product_code: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    message: str = "",
    correlation_id: Optional[str] = None,
    causation_id: Optional[str] = None,
) -> BillingEvent:
    """
    Create a subscription-related event.
    """

    return BillingEvent.create(
        event_type,
        source=source,
        actor_id=actor_id,
        user_id=user_id,
        subscription_id=subscription_id,
        product_code=product_code,
        payload=payload,
        message=message,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


def credit_event(
    event_type: BillingEventType,
    *,
    user_id: str,
    amount: float,
    actor_id: Optional[str] = None,
    source: BillingEventSource = BillingEventSource.SYSTEM,
    order_id: Optional[str] = None,
    currency: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    message: str = "",
    correlation_id: Optional[str] = None,
    causation_id: Optional[str] = None,
) -> BillingEvent:
    """
    Create a credit-related event.
    """

    return BillingEvent.create(
        event_type,
        source=source,
        actor_id=actor_id,
        user_id=user_id,
        order_id=order_id,
        amount=amount,
        currency=currency,
        payload=payload,
        message=message,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


def invoice_event(
    event_type: BillingEventType,
    *,
    invoice_id: str,
    user_id: Optional[str] = None,
    order_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    source: BillingEventSource = BillingEventSource.SYSTEM,
    amount: Optional[float] = None,
    currency: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    message: str = "",
    correlation_id: Optional[str] = None,
    causation_id: Optional[str] = None,
) -> BillingEvent:
    """
    Create an invoice-related event.
    """

    return BillingEvent.create(
        event_type,
        source=source,
        actor_id=actor_id,
        user_id=user_id,
        order_id=order_id,
        invoice_id=invoice_id,
        amount=amount,
        currency=currency,
        payload=payload,
        message=message,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


def fulfillment_event(
    event_type: BillingEventType,
    *,
    fulfillment_id: str,
    user_id: Optional[str] = None,
    order_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    source: BillingEventSource = BillingEventSource.SYSTEM,
    payload: Optional[Dict[str, Any]] = None,
    message: str = "",
    correlation_id: Optional[str] = None,
    causation_id: Optional[str] = None,
) -> BillingEvent:
    """
    Create a fulfillment-related event.
    """

    return BillingEvent.create(
        event_type,
        source=source,
        actor_id=actor_id,
        user_id=user_id,
        order_id=order_id,
        fulfillment_id=fulfillment_id,
        payload=payload,
        message=message,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


# ---------------------------------------------------------------------------
# EVENT BUS
# ---------------------------------------------------------------------------


class BillingEventBus:
    """
    Lightweight in-process event bus.

    Current implementation:
        publish -> stores event

    Future implementation can:
        - dispatch to subscribers
        - persist to database
        - send Telegram notifications
        - send email/SMS
        - trigger analytics
        - integrate webhooks
        - integrate external payment systems
    """

    def __init__(self) -> None:
        self._events: Dict[str, BillingEvent] = {}

    def publish(self, event: BillingEvent) -> BillingEvent:
        self._events[event.event_id] = event
        return event

    def get(self, event_id: str) -> Optional[BillingEvent]:
        return self._events.get(str(event_id))

    def list_events(
        self,
        *,
        event_type: Optional[BillingEventType] = None,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[BillingEvent]:
        events = list(self._events.values())

        if event_type is not None:
            events = [
                event
                for event in events
                if event.event_type == event_type
            ]

        if user_id is not None:
            user_id = str(user_id)

            events = [
                event
                for event in events
                if event.user_id == user_id
            ]

        if order_id is not None:
            order_id = str(order_id)

            events = [
                event
                for event in events
                if event.order_id == order_id
            ]

        events.sort(
            key=lambda event: event.created_at,
            reverse=True,
        )

        if limit is not None:
            events = events[: max(0, int(limit))]

        return events

    def clear(self) -> None:
        self._events.clear()

    def count(self) -> int:
        return len(self._events)


# ---------------------------------------------------------------------------
# GLOBAL EVENT BUS
# ---------------------------------------------------------------------------


_default_event_bus = BillingEventBus()


def get_event_bus() -> BillingEventBus:
    """
    Return the global billing event bus.
    """

    return _default_event_bus


def publish_event(event: BillingEvent) -> BillingEvent:
    """
    Publish an event through the global event bus.
    """

    return _default_event_bus.publish(event)


# ---------------------------------------------------------------------------
# SIMPLE EVENT FACTORY
# ---------------------------------------------------------------------------


def create_event(
    event_type: BillingEventType,
    **kwargs: Any,
) -> BillingEvent:
    """
    Generic convenience event factory.
    """

    return BillingEvent.create(
        event_type,
        **kwargs,
    )


__all__ = [
    "BillingEventType",
    "BillingEventSource",
    "BillingEvent",
    "BillingEventBus",
    "get_event_bus",
    "publish_event",
    "create_event",
    "order_event",
    "payment_event",
    "subscription_event",
    "credit_event",
    "invoice_event",
    "fulfillment_event",
]
