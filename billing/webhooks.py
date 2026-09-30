"""
StructuralBot - Billing Webhooks

Webhook and callback processing layer for payment providers.

Responsibilities:
- Normalize external payment callbacks
- Validate webhook payloads
- Prevent duplicate processing
- Track webhook processing state
- Provide a provider-agnostic interface
- Connect future payment gateways to billing business logic

Important:
This module does not trust external webhook data blindly.

A real payment provider adapter must:
1. Verify authenticity/signature.
2. Verify transaction status with the provider when required.
3. Normalize the result.
4. Pass the normalized event to this module.

The current implementation is storage-agnostic and uses in-memory
state so it can later be migrated to a persistent database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Dict, List, Optional
import hashlib
import json
import uuid


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize(value: Any) -> Optional[str]:
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def _safe_metadata(
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Remove obvious secrets from stored webhook metadata.
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
        "signature",
        "sign",
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


def _stable_payload_hash(payload: Dict[str, Any]) -> str:
    """
    Generate a stable hash for duplicate webhook detection.

    This is not a security signature.
    It is only an idempotency/deduplication helper.
    """

    normalized = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------


class WebhookStatus(str, Enum):
    """
    Processing state of an incoming webhook.
    """

    RECEIVED = "received"
    VALIDATED = "validated"
    PROCESSING = "processing"
    PROCESSED = "processed"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    FAILED = "failed"


class WebhookEventType(str, Enum):
    """
    Normalized provider-independent payment events.
    """

    PAYMENT_CREATED = "payment_created"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_CANCELLED = "payment_cancelled"
    PAYMENT_REFUNDED = "payment_refunded"
    PAYMENT_EXPIRED = "payment_expired"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# ERRORS
# ---------------------------------------------------------------------------


class WebhookError(Exception):
    """Base webhook error."""


class WebhookValidationError(WebhookError):
    """Webhook payload failed validation."""


class WebhookDuplicateError(WebhookError):
    """Webhook has already been processed."""


class WebhookProcessingError(WebhookError):
    """Webhook processing failed."""


# ---------------------------------------------------------------------------
# NORMALIZED WEBHOOK
# ---------------------------------------------------------------------------


@dataclass
class PaymentWebhook:
    """
    Provider-independent representation of an incoming payment webhook.
    """

    webhook_id: str

    provider: str

    event_type: WebhookEventType

    provider_event_id: Optional[str] = None

    payment_id: Optional[str] = None

    provider_payment_id: Optional[str] = None

    order_id: Optional[str] = None

    user_id: Optional[str] = None

    amount: Optional[float] = None

    currency: Optional[str] = None

    status: WebhookStatus = WebhookStatus.RECEIVED

    payload: Dict[str, Any] = field(default_factory=dict)

    headers: Dict[str, Any] = field(default_factory=dict)

    received_at: datetime = field(default_factory=_utc_now)

    processed_at: Optional[datetime] = None

    error_message: Optional[str] = None

    correlation_id: Optional[str] = None

    payload_hash: Optional[str] = None

    @classmethod
    def create(
        cls,
        *,
        provider: str,
        event_type: WebhookEventType,
        provider_event_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        provider_payment_id: Optional[str] = None,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> "PaymentWebhook":
        """
        Create a normalized webhook object.
        """

        normalized_payload = dict(payload or {})

        correlation = _normalize(correlation_id)

        if correlation is None:
            correlation = f"corr_{uuid.uuid4().hex}"

        return cls(
            webhook_id=f"wh_{uuid.uuid4().hex}",
            provider=str(provider).strip().lower(),
            event_type=event_type,
            provider_event_id=_normalize(provider_event_id),
            payment_id=_normalize(payment_id),
            provider_payment_id=_normalize(provider_payment_id),
            order_id=_normalize(order_id),
            user_id=_normalize(user_id),
            amount=float(amount) if amount is not None else None,
            currency=_normalize(currency),
            payload=_safe_metadata(normalized_payload),
            headers=_safe_metadata(dict(headers or {})),
            correlation_id=correlation,
            payload_hash=_stable_payload_hash(normalized_payload),
        )

    def mark_validated(self) -> None:
        self.status = WebhookStatus.VALIDATED

    def mark_processing(self) -> None:
        self.status = WebhookStatus.PROCESSING

    def mark_processed(self) -> None:
        self.status = WebhookStatus.PROCESSED
        self.processed_at = _utc_now()
        self.error_message = None

    def mark_duplicate(self) -> None:
        self.status = WebhookStatus.DUPLICATE
        self.processed_at = _utc_now()

    def mark_rejected(self, reason: str) -> None:
        self.status = WebhookStatus.REJECTED
        self.error_message = str(reason)

    def mark_failed(self, reason: str) -> None:
        self.status = WebhookStatus.FAILED
        self.error_message = str(reason)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "webhook_id": self.webhook_id,
            "provider": self.provider,
            "event_type": self.event_type.value,
            "provider_event_id": self.provider_event_id,
            "payment_id": self.payment_id,
            "provider_payment_id": self.provider_payment_id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "payload": dict(self.payload),
            "headers": dict(self.headers),
            "received_at": self.received_at.isoformat(),
            "processed_at": (
                self.processed_at.isoformat()
                if self.processed_at
                else None
            ),
            "error_message": self.error_message,
            "correlation_id": self.correlation_id,
            "payload_hash": self.payload_hash,
        }


# ---------------------------------------------------------------------------
# WEBHOOK PROCESSING RESULT
# ---------------------------------------------------------------------------


@dataclass
class WebhookResult:
    """
    Result returned after webhook processing.
    """

    success: bool

    webhook_id: str

    status: WebhookStatus

    message: str = ""

    duplicate: bool = False

    payment_id: Optional[str] = None

    order_id: Optional[str] = None

    user_id: Optional[str] = None

    event_type: Optional[WebhookEventType] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_webhook(
        cls,
        webhook: PaymentWebhook,
        *,
        success: bool,
        message: str = "",
        duplicate: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "WebhookResult":
        return cls(
            success=success,
            webhook_id=webhook.webhook_id,
            status=webhook.status,
            message=message,
            duplicate=duplicate,
            payment_id=webhook.payment_id,
            order_id=webhook.order_id,
            user_id=webhook.user_id,
            event_type=webhook.event_type,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "webhook_id": self.webhook_id,
            "status": self.status.value,
            "message": self.message,
            "duplicate": self.duplicate,
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "event_type": (
                self.event_type.value
                if self.event_type
                else None
            ),
            "metadata": dict(self.metadata),
        }


# ---------------------------------------------------------------------------
# WEBHOOK MANAGER
# ---------------------------------------------------------------------------


class WebhookManager:
    """
    Thread-safe webhook registry and idempotency manager.
    """

    def __init__(self) -> None:
        self._webhooks: Dict[str, PaymentWebhook] = {}

        # Provider event IDs are the strongest idempotency key when
        # available.
        self._provider_event_index: Dict[str, str] = {}

        # Payload hashes provide a secondary deduplication mechanism.
        self._payload_hash_index: Dict[str, str] = {}

        self._lock = RLock()

    # ------------------------------------------------------------------
    # REGISTER
    # ------------------------------------------------------------------

    def receive(
        self,
        webhook: PaymentWebhook,
    ) -> PaymentWebhook:
        """
        Register an incoming webhook.

        Raises WebhookDuplicateError if the same provider event or
        payload has already been registered.
        """

        with self._lock:
            if webhook.provider_event_id:
                key = (
                    f"{webhook.provider}:"
                    f"{webhook.provider_event_id}"
                )

                if key in self._provider_event_index:
                    existing_id = self._provider_event_index[key]

                    existing = self._webhooks.get(existing_id)

                    if existing is not None:
                        raise WebhookDuplicateError(
                            "Duplicate provider event."
                        )

            if webhook.payload_hash:
                key = (
                    f"{webhook.provider}:"
                    f"{webhook.payload_hash}"
                )

                if key in self._payload_hash_index:
                    raise WebhookDuplicateError(
                        "Duplicate webhook payload."
                    )

            self._webhooks[webhook.webhook_id] = webhook

            if webhook.provider_event_id:
                key = (
                    f"{webhook.provider}:"
                    f"{webhook.provider_event_id}"
                )

                self._provider_event_index[key] = (
                    webhook.webhook_id
                )

            if webhook.payload_hash:
                key = (
                    f"{webhook.provider}:"
                    f"{webhook.payload_hash}"
                )

                self._payload_hash_index[key] = (
                    webhook.webhook_id
                )

        return webhook

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def get(
        self,
        webhook_id: str,
    ) -> Optional[PaymentWebhook]:
        with self._lock:
            return self._webhooks.get(str(webhook_id))

    def require(
        self,
        webhook_id: str,
    ) -> PaymentWebhook:
        webhook = self.get(webhook_id)

        if webhook is None:
            raise KeyError(
                f"Webhook not found: {webhook_id}"
            )

        return webhook

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def validate(
        self,
        webhook: PaymentWebhook,
    ) -> PaymentWebhook:
        """
        Perform structural validation.

        Cryptographic verification must happen inside the specific
        payment gateway adapter before this method is considered
        sufficient for production payment confirmation.
        """

        if not webhook.provider:
            webhook.mark_rejected(
                "Payment provider is required."
            )

            raise WebhookValidationError(
                "Payment provider is required."
            )

        if webhook.event_type == WebhookEventType.UNKNOWN:
            webhook.mark_rejected(
                "Unknown webhook event type."
            )

            raise WebhookValidationError(
                "Unknown webhook event type."
            )

        if not webhook.payment_id and not webhook.order_id:
            webhook.mark_rejected(
                "Webhook must contain payment_id or order_id."
            )

            raise WebhookValidationError(
                "Webhook must contain payment_id or order_id."
            )

        webhook.mark_validated()

        return webhook

    # ------------------------------------------------------------------
    # PROCESS
    # ------------------------------------------------------------------

    def process(
        self,
        webhook: PaymentWebhook,
        *,
        handler: Optional[Any] = None,
    ) -> WebhookResult:
        """
        Process a validated webhook.

        `handler` is intentionally generic.

        Expected handler signature:

            handler(webhook) -> Any

        The actual handler can later call:
            - PaymentManager
            - OrderManager
            - CheckoutManager
            - FulfillmentManager
            - InvoiceManager
            - AuditManager
        """

        try:
            self.validate(webhook)

            webhook.mark_processing()

            if handler is not None:
                handler(webhook)

            webhook.mark_processed()

            return WebhookResult.from_webhook(
                webhook,
                success=True,
                message="Webhook processed successfully.",
            )

        except WebhookDuplicateError:
            webhook.mark_duplicate()

            return WebhookResult.from_webhook(
                webhook,
                success=True,
                duplicate=True,
                message="Webhook was already processed.",
            )

        except WebhookValidationError as exc:
            webhook.mark_rejected(str(exc))

            return WebhookResult.from_webhook(
                webhook,
                success=False,
                message=str(exc),
            )

        except Exception as exc:
            webhook.mark_failed(str(exc))

            return WebhookResult.from_webhook(
                webhook,
                success=False,
                message=str(exc),
            )

    # ------------------------------------------------------------------
    # LOOKUPS
    # ------------------------------------------------------------------

    def list_webhooks(
        self,
        *,
        provider: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
        event_type: Optional[WebhookEventType] = None,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[PaymentWebhook]:
        with self._lock:
            webhooks = list(self._webhooks.values())

        if provider is not None:
            provider = str(provider).strip().lower()

            webhooks = [
                webhook
                for webhook in webhooks
                if webhook.provider == provider
            ]

        if status is not None:
            webhooks = [
                webhook
                for webhook in webhooks
                if webhook.status == status
            ]

        if event_type is not None:
            webhooks = [
                webhook
                for webhook in webhooks
                if webhook.event_type == event_type
            ]

        if user_id is not None:
            user_id = str(user_id)

            webhooks = [
                webhook
                for webhook in webhooks
                if webhook.user_id == user_id
            ]

        if order_id is not None:
            order_id = str(order_id)

            webhooks = [
                webhook
                for webhook in webhooks
                if webhook.order_id == order_id
            ]

        if payment_id is not None:
            payment_id = str(payment_id)

            webhooks = [
                webhook
                for webhook in webhooks
                if webhook.payment_id == payment_id
            ]

        webhooks.sort(
            key=lambda webhook: webhook.received_at,
            reverse=True,
        )

        if limit is not None:
            webhooks = webhooks[: max(0, int(limit))]

        return webhooks

    # ------------------------------------------------------------------
    # STATUS HELPERS
    # ------------------------------------------------------------------

    def is_processed(
        self,
        webhook_id: str,
    ) -> bool:
        webhook = self.get(webhook_id)

        return bool(
            webhook
            and webhook.status == WebhookStatus.PROCESSED
        )

    def is_duplicate(
        self,
        webhook_id: str,
    ) -> bool:
        webhook = self.get(webhook_id)

        return bool(
            webhook
            and webhook.status == WebhookStatus.DUPLICATE
        )

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        webhooks = self.list_webhooks()

        by_status: Dict[str, int] = {}
        by_provider: Dict[str, int] = {}
        by_event: Dict[str, int] = {}

        for webhook in webhooks:
            status_key = webhook.status.value
            provider_key = webhook.provider
            event_key = webhook.event_type.value

            by_status[status_key] = (
                by_status.get(status_key, 0) + 1
            )

            by_provider[provider_key] = (
                by_provider.get(provider_key, 0) + 1
            )

            by_event[event_key] = (
                by_event.get(event_key, 0) + 1
            )

        return {
            "total": len(webhooks),
            "by_status": by_status,
            "by_provider": by_provider,
            "by_event": by_event,
        }

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    def to_dicts(
        self,
        webhooks: Optional[List[PaymentWebhook]] = None,
    ) -> List[Dict[str, Any]]:
        if webhooks is None:
            webhooks = self.list_webhooks()

        return [
            webhook.to_dict()
            for webhook in webhooks
        ]

    # ------------------------------------------------------------------
    # MAINTENANCE
    # ------------------------------------------------------------------

    def count(self) -> int:
        with self._lock:
            return len(self._webhooks)

    def clear(self) -> None:
        with self._lock:
            self._webhooks.clear()
            self._provider_event_index.clear()
            self._payload_hash_index.clear()


# ---------------------------------------------------------------------------
# GLOBAL MANAGER
# ---------------------------------------------------------------------------


_default_webhook_manager = WebhookManager()


def get_webhook_manager() -> WebhookManager:
    """
    Return the global webhook manager.
    """

    return _default_webhook_manager


# ---------------------------------------------------------------------------
# FACTORY
# ---------------------------------------------------------------------------


def create_payment_webhook(
    *,
    provider: str,
    event_type: WebhookEventType,
    payment_id: Optional[str] = None,
    provider_payment_id: Optional[str] = None,
    provider_event_id: Optional[str] = None,
    order_id: Optional[str] = None,
    user_id: Optional[str] = None,
    amount: Optional[float] = None,
    currency: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> PaymentWebhook:
    """
    Convenience factory for normalized payment webhooks.
    """

    return PaymentWebhook.create(
        provider=provider,
        event_type=event_type,
        provider_event_id=provider_event_id,
        payment_id=payment_id,
        provider_payment_id=provider_payment_id,
        order_id=order_id,
        user_id=user_id,
        amount=amount,
        currency=currency,
        payload=payload,
        headers=headers,
        correlation_id=correlation_id,
    )


__all__ = [
    "WebhookStatus",
    "WebhookEventType",
    "WebhookError",
    "WebhookValidationError",
    "WebhookDuplicateError",
    "WebhookProcessingError",
    "PaymentWebhook",
    "WebhookResult",
    "WebhookManager",
    "get_webhook_manager",
    "create_payment_webhook",
]
