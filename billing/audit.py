"""
StructuralBot - Billing Audit Trail

Audit and event tracking for the billing subsystem.

Responsibilities:
- Record billing-related events
- Track order/payment/subscription/credit changes
- Preserve actor and reference information
- Support troubleshooting and administrative review
- Provide a stable event model for future database persistence

This module intentionally remains storage-agnostic.
The default implementation uses in-memory storage and can later
be replaced or backed by a persistent repository/database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional
import uuid


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------


class AuditEventType(str, Enum):
    """
    High-level categories of billing audit events.
    """

    SYSTEM = "system"

    PRODUCT = "product"

    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    ORDER_PAID = "order_paid"
    ORDER_COMPLETED = "order_completed"
    ORDER_FAILED = "order_failed"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REFUNDED = "order_refunded"
    ORDER_EXPIRED = "order_expired"

    PAYMENT_CREATED = "payment_created"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_CANCELLED = "payment_cancelled"
    PAYMENT_REFUNDED = "payment_refunded"

    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_ACTIVATED = "subscription_activated"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    SUBSCRIPTION_SUSPENDED = "subscription_suspended"
    SUBSCRIPTION_RESTORED = "subscription_restored"

    CREDIT_PURCHASED = "credit_purchased"
    CREDIT_GRANTED = "credit_granted"
    CREDIT_CONSUMED = "credit_consumed"
    CREDIT_REFUNDED = "credit_refunded"
    CREDIT_EXPIRED = "credit_expired"
    CREDIT_ADJUSTED = "credit_adjusted"

    FULFILLMENT_STARTED = "fulfillment_started"
    FULFILLMENT_COMPLETED = "fulfillment_completed"
    FULFILLMENT_FAILED = "fulfillment_failed"
    FULFILLMENT_SKIPPED = "fulfillment_skipped"

    INVOICE_CREATED = "invoice_created"
    INVOICE_ISSUED = "invoice_issued"
    INVOICE_PAID = "invoice_paid"
    INVOICE_VOIDED = "invoice_voided"
    INVOICE_REFUNDED = "invoice_refunded"

    ADMIN_ACTION = "admin_action"
    SECURITY = "security"
    ERROR = "error"


class AuditActorType(str, Enum):
    """
    Who or what caused the event.
    """

    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
    PAYMENT_GATEWAY = "payment_gateway"
    BOT = "bot"
    API = "api"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_copy_metadata(
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create a shallow, serialization-friendly metadata copy.

    Sensitive payment secrets should never be placed in audit metadata.
    """
    if not metadata:
        return {}

    result: Dict[str, Any] = {}

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

    for key, value in metadata.items():
        normalized = str(key).strip().lower()

        if normalized in sensitive_keys:
            result[str(key)] = "[REDACTED]"
            continue

        result[str(key)] = value

    return result


# ---------------------------------------------------------------------------
# AUDIT EVENT
# ---------------------------------------------------------------------------


@dataclass
class AuditEvent:
    """
    Immutable-style representation of one billing audit event.

    The object is not technically frozen because metadata may need
    controlled normalization before persistence.
    """

    event_id: str
    event_type: AuditEventType

    actor_type: AuditActorType = AuditActorType.SYSTEM
    actor_id: Optional[str] = None

    user_id: Optional[str] = None

    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    fulfillment_id: Optional[str] = None
    product_code: Optional[str] = None

    description: str = ""

    amount: Optional[float] = None
    currency: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        event_type: AuditEventType,
        *,
        actor_type: AuditActorType = AuditActorType.SYSTEM,
        actor_id: Optional[str] = None,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        fulfillment_id: Optional[str] = None,
        product_code: Optional[str] = None,
        description: str = "",
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AuditEvent":
        """
        Create a new audit event.
        """

        return cls(
            event_id=f"audit_{uuid.uuid4().hex}",
            event_type=event_type,
            actor_type=actor_type,
            actor_id=str(actor_id) if actor_id is not None else None,
            user_id=str(user_id) if user_id is not None else None,
            order_id=str(order_id) if order_id is not None else None,
            payment_id=str(payment_id) if payment_id is not None else None,
            subscription_id=(
                str(subscription_id)
                if subscription_id is not None
                else None
            ),
            invoice_id=str(invoice_id) if invoice_id is not None else None,
            fulfillment_id=(
                str(fulfillment_id)
                if fulfillment_id is not None
                else None
            ),
            product_code=(
                str(product_code)
                if product_code is not None
                else None
            ),
            description=str(description or ""),
            amount=float(amount) if amount is not None else None,
            currency=str(currency) if currency else None,
            metadata=_safe_copy_metadata(metadata),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the event into a JSON-friendly dictionary.
        """

        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "actor_type": self.actor_type.value,
            "actor_id": self.actor_id,
            "user_id": self.user_id,
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "subscription_id": self.subscription_id,
            "invoice_id": self.invoice_id,
            "fulfillment_id": self.fulfillment_id,
            "product_code": self.product_code,
            "description": self.description,
            "amount": self.amount,
            "currency": self.currency,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# AUDIT MANAGER
# ---------------------------------------------------------------------------


class AuditManager:
    """
    Thread-safe in-memory audit event manager.

    Designed so the storage implementation can later be replaced
    with a database/repository without changing billing business logic.
    """

    def __init__(self) -> None:
        self._events: Dict[str, AuditEvent] = {}
        self._lock = RLock()

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def record(
        self,
        event_type: AuditEventType,
        *,
        actor_type: AuditActorType = AuditActorType.SYSTEM,
        actor_id: Optional[str] = None,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        fulfillment_id: Optional[str] = None,
        product_code: Optional[str] = None,
        description: str = "",
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Record a billing audit event.
        """

        event = AuditEvent.create(
            event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            user_id=user_id,
            order_id=order_id,
            payment_id=payment_id,
            subscription_id=subscription_id,
            invoice_id=invoice_id,
            fulfillment_id=fulfillment_id,
            product_code=product_code,
            description=description,
            amount=amount,
            currency=currency,
            metadata=metadata,
        )

        with self._lock:
            self._events[event.event_id] = event

        return event

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def get(self, event_id: str) -> Optional[AuditEvent]:
        with self._lock:
            return self._events.get(str(event_id))

    def require(self, event_id: str) -> AuditEvent:
        event = self.get(event_id)

        if event is None:
            raise KeyError(f"Audit event not found: {event_id}")

        return event

    # ------------------------------------------------------------------
    # LIST
    # ------------------------------------------------------------------

    def list_events(
        self,
        *,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        fulfillment_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor_type: Optional[AuditActorType] = None,
        limit: Optional[int] = None,
        newest_first: bool = True,
    ) -> List[AuditEvent]:
        """
        Return filtered audit events.
        """

        with self._lock:
            events = list(self._events.values())

        if user_id is not None:
            user_id = str(user_id)
            events = [e for e in events if e.user_id == user_id]

        if order_id is not None:
            order_id = str(order_id)
            events = [e for e in events if e.order_id == order_id]

        if payment_id is not None:
            payment_id = str(payment_id)
            events = [e for e in events if e.payment_id == payment_id]

        if subscription_id is not None:
            subscription_id = str(subscription_id)
            events = [
                e
                for e in events
                if e.subscription_id == subscription_id
            ]

        if invoice_id is not None:
            invoice_id = str(invoice_id)
            events = [e for e in events if e.invoice_id == invoice_id]

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        if actor_type is not None:
            events = [e for e in events if e.actor_type == actor_type]

        events.sort(
            key=lambda e: e.created_at,
            reverse=newest_first,
        )

        if limit is not None:
            limit = max(0, int(limit))
            events = events[:limit]

        return events

    # ------------------------------------------------------------------
    # CONVENIENCE FILTERS
    # ------------------------------------------------------------------

    def user_history(
        self,
        user_id: str,
        *,
        limit: Optional[int] = None,
    ) -> List[AuditEvent]:
        return self.list_events(
            user_id=user_id,
            limit=limit,
        )

    def order_history(
        self,
        order_id: str,
        *,
        limit: Optional[int] = None,
    ) -> List[AuditEvent]:
        return self.list_events(
            order_id=order_id,
            limit=limit,
        )

    def payment_history(
        self,
        payment_id: str,
        *,
        limit: Optional[int] = None,
    ) -> List[AuditEvent]:
        return self.list_events(
            payment_id=payment_id,
            limit=limit,
        )

    def subscription_history(
        self,
        subscription_id: str,
        *,
        limit: Optional[int] = None,
    ) -> List[AuditEvent]:
        return self.list_events(
            subscription_id=subscription_id,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------

    def search(
        self,
        text: str,
        *,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[AuditEvent]:
        """
        Search descriptions and selected metadata values.
        """

        query = str(text or "").strip().lower()

        if not query:
            return []

        events = self.user_history(
            user_id,
            limit=None,
        ) if user_id is not None else self.list_events(
            limit=None,
        )

        matched: List[AuditEvent] = []

        for event in events:
            haystack_parts = [
                event.description,
                event.event_id,
                event.order_id or "",
                event.payment_id or "",
                event.subscription_id or "",
                event.invoice_id or "",
                event.product_code or "",
            ]

            haystack_parts.extend(
                str(value)
                for value in event.metadata.values()
            )

            haystack = " ".join(haystack_parts).lower()

            if query in haystack:
                matched.append(event)

        if limit is not None:
            matched = matched[: max(0, int(limit))]

        return matched

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------

    def summary(
        self,
        *,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return a compact audit summary.
        """

        events = (
            self.user_history(user_id)
            if user_id is not None
            else self.list_events()
        )

        by_type: Dict[str, int] = {}

        for event in events:
            key = event.event_type.value
            by_type[key] = by_type.get(key, 0) + 1

        return {
            "total_events": len(events),
            "by_type": by_type,
            "latest_event": (
                events[0].to_dict()
                if events
                else None
            ),
        }

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    def to_dicts(
        self,
        events: Optional[Iterable[AuditEvent]] = None,
    ) -> List[Dict[str, Any]]:
        if events is None:
            events = self.list_events()

        return [
            event.to_dict()
            for event in events
        ]

    # ------------------------------------------------------------------
    # MAINTENANCE
    # ------------------------------------------------------------------

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


# ---------------------------------------------------------------------------
# GLOBAL MANAGER
# ---------------------------------------------------------------------------


_default_audit_manager = AuditManager()


def get_audit_manager() -> AuditManager:
    """
    Return the global audit manager.
    """

    return _default_audit_manager


# ---------------------------------------------------------------------------
# CONVENIENCE FUNCTION
# ---------------------------------------------------------------------------


def record_audit_event(
    event_type: AuditEventType,
    *,
    actor_type: AuditActorType = AuditActorType.SYSTEM,
    actor_id: Optional[str] = None,
    user_id: Optional[str] = None,
    order_id: Optional[str] = None,
    payment_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    invoice_id: Optional[str] = None,
    fulfillment_id: Optional[str] = None,
    product_code: Optional[str] = None,
    description: str = "",
    amount: Optional[float] = None,
    currency: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """
    Convenience wrapper around the global AuditManager.
    """

    return _default_audit_manager.record(
        event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        user_id=user_id,
        order_id=order_id,
        payment_id=payment_id,
        subscription_id=subscription_id,
        invoice_id=invoice_id,
        fulfillment_id=fulfillment_id,
        product_code=product_code,
        description=description,
        amount=amount,
        currency=currency,
        metadata=metadata,
    )


__all__ = [
    "AuditEventType",
    "AuditActorType",
    "AuditEvent",
    "AuditManager",
    "get_audit_manager",
    "record_audit_event",
]
