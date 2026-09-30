"""
StructuralBot - Billing Notifications

Notification infrastructure for the billing subsystem.

Responsibilities:
- Define billing notification types
- Build user/admin notification messages
- Keep billing logic independent from Telegram
- Support future Telegram/email/SMS/push channels
- Provide notification history and delivery state
- Prevent duplicate notification delivery

The actual Telegram/API transport must remain outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Dict, List, Optional
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
    Remove obvious secret fields from notification metadata.
    """

    if not metadata:
        return {}

    sensitive = {
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

        if key_text.lower().strip() in sensitive:
            result[key_text] = "[REDACTED]"
        else:
            result[key_text] = value

    return result


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------


class NotificationType(str, Enum):
    """
    Billing notification categories.
    """

    # Subscription
    SUBSCRIPTION_ACTIVATED = "subscription_activated"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    SUBSCRIPTION_EXPIRING = "subscription_expiring"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    SUBSCRIPTION_SUSPENDED = "subscription_suspended"
    SUBSCRIPTION_RESTORED = "subscription_restored"

    # Payment
    PAYMENT_CREATED = "payment_created"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_CANCELLED = "payment_cancelled"
    PAYMENT_REFUNDED = "payment_refunded"

    # Order
    ORDER_CREATED = "order_created"
    ORDER_PAID = "order_paid"
    ORDER_COMPLETED = "order_completed"
    ORDER_FAILED = "order_failed"
    ORDER_CANCELLED = "order_cancelled"

    # Credits
    CREDITS_PURCHASED = "credits_purchased"
    CREDITS_GRANTED = "credits_granted"
    CREDITS_REFUNDED = "credits_refunded"
    CREDITS_LOW = "credits_low"
    CREDITS_EXPIRED = "credits_expired"

    # Invoice
    INVOICE_CREATED = "invoice_created"
    INVOICE_ISSUED = "invoice_issued"
    INVOICE_PAID = "invoice_paid"
    INVOICE_REFUNDED = "invoice_refunded"

    # Reports / files
    REPORT_READY = "report_ready"
    REPORT_FAILED = "report_failed"

    # System
    SECURITY_ALERT = "security_alert"
    BILLING_ERROR = "billing_error"
    GENERAL = "general"


class NotificationChannel(str, Enum):
    """
    Delivery channels.

    The current billing layer only prepares and tracks notifications.
    Transport adapters are added separately.
    """

    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    INTERNAL = "internal"


class NotificationStatus(str, Enum):
    """
    Notification lifecycle.
    """

    CREATED = "created"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


# ---------------------------------------------------------------------------
# NOTIFICATION
# ---------------------------------------------------------------------------


@dataclass
class BillingNotification:
    """
    A channel-independent notification.
    """

    notification_id: str

    notification_type: NotificationType

    user_id: Optional[str] = None

    channel: NotificationChannel = NotificationChannel.INTERNAL

    status: NotificationStatus = NotificationStatus.CREATED

    title: str = ""

    message: str = ""

    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    product_code: Optional[str] = None

    amount: Optional[float] = None
    currency: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=_utc_now)

    queued_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    attempts: int = 0

    error_message: Optional[str] = None

    idempotency_key: Optional[str] = None

    correlation_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        notification_type: NotificationType,
        *,
        user_id: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        title: str = "",
        message: str = "",
        order_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        product_code: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> "BillingNotification":
        """
        Create a billing notification.
        """

        correlation = _normalize(correlation_id)

        if correlation is None:
            correlation = f"corr_{uuid.uuid4().hex}"

        return cls(
            notification_id=f"notif_{uuid.uuid4().hex}",
            notification_type=notification_type,
            user_id=_normalize(user_id),
            channel=channel,
            title=str(title or ""),
            message=str(message or ""),
            order_id=_normalize(order_id),
            payment_id=_normalize(payment_id),
            subscription_id=_normalize(subscription_id),
            invoice_id=_normalize(invoice_id),
            product_code=_normalize(product_code),
            amount=float(amount) if amount is not None else None,
            currency=_normalize(currency),
            metadata=_safe_metadata(metadata),
            idempotency_key=_normalize(idempotency_key),
            correlation_id=correlation,
        )

    def mark_queued(self) -> None:
        self.status = NotificationStatus.QUEUED
        self.queued_at = _utc_now()

    def mark_sending(self) -> None:
        self.status = NotificationStatus.SENDING
        self.attempts += 1

    def mark_sent(self) -> None:
        self.status = NotificationStatus.SENT
        self.sent_at = _utc_now()
        self.error_message = None

    def mark_failed(self, error: str) -> None:
        self.status = NotificationStatus.FAILED
        self.failed_at = _utc_now()
        self.error_message = str(error)

    def mark_cancelled(self) -> None:
        self.status = NotificationStatus.CANCELLED

    def mark_skipped(self, reason: Optional[str] = None) -> None:
        self.status = NotificationStatus.SKIPPED

        if reason:
            self.error_message = str(reason)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "notification_type": self.notification_type.value,
            "user_id": self.user_id,
            "channel": self.channel.value,
            "status": self.status.value,
            "title": self.title,
            "message": self.message,
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "subscription_id": self.subscription_id,
            "invoice_id": self.invoice_id,
            "product_code": self.product_code,
            "amount": self.amount,
            "currency": self.currency,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "queued_at": (
                self.queued_at.isoformat()
                if self.queued_at
                else None
            ),
            "sent_at": (
                self.sent_at.isoformat()
                if self.sent_at
                else None
            ),
            "failed_at": (
                self.failed_at.isoformat()
                if self.failed_at
                else None
            ),
            "attempts": self.attempts,
            "error_message": self.error_message,
            "idempotency_key": self.idempotency_key,
            "correlation_id": self.correlation_id,
        }


# ---------------------------------------------------------------------------
# NOTIFICATION MANAGER
# ---------------------------------------------------------------------------


class NotificationManager:
    """
    Thread-safe notification manager.

    It stores notification state but does not know how to send a message.
    """

    def __init__(self) -> None:
        self._notifications: Dict[str, BillingNotification] = {}

        self._idempotency_index: Dict[str, str] = {}

        self._lock = RLock()

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def create(
        self,
        notification_type: NotificationType,
        *,
        user_id: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        title: str = "",
        message: str = "",
        order_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        product_code: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> BillingNotification:
        """
        Create and store a notification.

        If an idempotency key already exists, the existing notification
        is returned instead of creating a duplicate.
        """

        with self._lock:
            if idempotency_key:
                existing_id = self._idempotency_index.get(
                    str(idempotency_key)
                )

                if existing_id:
                    existing = self._notifications.get(existing_id)

                    if existing is not None:
                        return existing

            notification = BillingNotification.create(
                notification_type,
                user_id=user_id,
                channel=channel,
                title=title,
                message=message,
                order_id=order_id,
                payment_id=payment_id,
                subscription_id=subscription_id,
                invoice_id=invoice_id,
                product_code=product_code,
                amount=amount,
                currency=currency,
                metadata=metadata,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            )

            self._notifications[
                notification.notification_id
            ] = notification

            if notification.idempotency_key:
                self._idempotency_index[
                    notification.idempotency_key
                ] = notification.notification_id

            return notification

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def get(
        self,
        notification_id: str,
    ) -> Optional[BillingNotification]:
        with self._lock:
            return self._notifications.get(
                str(notification_id)
            )

    def require(
        self,
        notification_id: str,
    ) -> BillingNotification:
        notification = self.get(notification_id)

        if notification is None:
            raise KeyError(
                f"Notification not found: {notification_id}"
            )

        return notification

    # ------------------------------------------------------------------
    # QUEUE
    # ------------------------------------------------------------------

    def queue(
        self,
        notification_id: str,
    ) -> BillingNotification:
        notification = self.require(notification_id)

        with self._lock:
            notification.mark_queued()

        return notification

    # ------------------------------------------------------------------
    # SEND LIFECYCLE
    # ------------------------------------------------------------------

    def start_sending(
        self,
        notification_id: str,
    ) -> BillingNotification:
        notification = self.require(notification_id)

        with self._lock:
            notification.mark_sending()

        return notification

    def mark_sent(
        self,
        notification_id: str,
    ) -> BillingNotification:
        notification = self.require(notification_id)

        with self._lock:
            notification.mark_sent()

        return notification

    def mark_failed(
        self,
        notification_id: str,
        error: str,
    ) -> BillingNotification:
        notification = self.require(notification_id)

        with self._lock:
            notification.mark_failed(error)

        return notification

    def cancel(
        self,
        notification_id: str,
    ) -> BillingNotification:
        notification = self.require(notification_id)

        with self._lock:
            notification.mark_cancelled()

        return notification

    def skip(
        self,
        notification_id: str,
        reason: Optional[str] = None,
    ) -> BillingNotification:
        notification = self.require(notification_id)

        with self._lock:
            notification.mark_skipped(reason)

        return notification

    # ------------------------------------------------------------------
    # LIST
    # ------------------------------------------------------------------

    def list_notifications(
        self,
        *,
        user_id: Optional[str] = None,
        channel: Optional[NotificationChannel] = None,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        order_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[BillingNotification]:
        with self._lock:
            notifications = list(
                self._notifications.values()
            )

        if user_id is not None:
            user_id = str(user_id)

            notifications = [
                item
                for item in notifications
                if item.user_id == user_id
            ]

        if channel is not None:
            notifications = [
                item
                for item in notifications
                if item.channel == channel
            ]

        if status is not None:
            notifications = [
                item
                for item in notifications
                if item.status == status
            ]

        if notification_type is not None:
            notifications = [
                item
                for item in notifications
                if item.notification_type == notification_type
            ]

        if order_id is not None:
            order_id = str(order_id)

            notifications = [
                item
                for item in notifications
                if item.order_id == order_id
            ]

        if payment_id is not None:
            payment_id = str(payment_id)

            notifications = [
                item
                for item in notifications
                if item.payment_id == payment_id
            ]

        if subscription_id is not None:
            subscription_id = str(subscription_id)

            notifications = [
                item
                for item in notifications
                if item.subscription_id == subscription_id
            ]

        notifications.sort(
            key=lambda item: item.created_at,
            reverse=True,
        )

        if limit is not None:
            notifications = notifications[
                : max(0, int(limit))
            ]

        return notifications

    # ------------------------------------------------------------------
    # USER INBOX
    # ------------------------------------------------------------------

    def user_inbox(
        self,
        user_id: str,
        *,
        limit: Optional[int] = None,
    ) -> List[BillingNotification]:
        """
        Return notifications intended for a user.
        """

        return self.list_notifications(
            user_id=user_id,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # PENDING
    # ------------------------------------------------------------------

    def pending(
        self,
        *,
        channel: Optional[NotificationChannel] = None,
        limit: Optional[int] = None,
    ) -> List[BillingNotification]:
        """
        Return notifications ready for delivery.
        """

        notifications = self.list_notifications(
            channel=channel,
            status=NotificationStatus.QUEUED,
            limit=limit,
        )

        return notifications

    # ------------------------------------------------------------------
    # FAILED
    # ------------------------------------------------------------------

    def failed(
        self,
        *,
        channel: Optional[NotificationChannel] = None,
        limit: Optional[int] = None,
    ) -> List[BillingNotification]:
        return self.list_notifications(
            channel=channel,
            status=NotificationStatus.FAILED,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------

    def summary(
        self,
        *,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        notifications = (
            self.user_inbox(user_id)
            if user_id is not None
            else self.list_notifications()
        )

        by_status: Dict[str, int] = {}
        by_channel: Dict[str, int] = {}
        by_type: Dict[str, int] = {}

        for notification in notifications:
            status_key = notification.status.value
            channel_key = notification.channel.value
            type_key = notification.notification_type.value

            by_status[status_key] = (
                by_status.get(status_key, 0) + 1
            )

            by_channel[channel_key] = (
                by_channel.get(channel_key, 0) + 1
            )

            by_type[type_key] = (
                by_type.get(type_key, 0) + 1
            )

        return {
            "total": len(notifications),
            "by_status": by_status,
            "by_channel": by_channel,
            "by_type": by_type,
        }

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    def to_dicts(
        self,
        notifications: Optional[
            List[BillingNotification]
        ] = None,
    ) -> List[Dict[str, Any]]:
        if notifications is None:
            notifications = self.list_notifications()

        return [
            notification.to_dict()
            for notification in notifications
        ]

    # ------------------------------------------------------------------
    # MAINTENANCE
    # ------------------------------------------------------------------

    def count(self) -> int:
        with self._lock:
            return len(self._notifications)

    def clear(self) -> None:
        with self._lock:
            self._notifications.clear()
            self._idempotency_index.clear()


# ---------------------------------------------------------------------------
# MESSAGE FACTORIES
# ---------------------------------------------------------------------------


def subscription_activated_message(
    *,
    plan_name: str,
    expires_text: Optional[str] = None,
) -> tuple[str, str]:
    title = "اشتراک فعال شد"

    message = (
        f"اشتراک «{plan_name}» با موفقیت فعال شد."
    )

    if expires_text:
        message += (
            f"\nاعتبار تا: {expires_text}"
        )

    return title, message


def payment_success_message(
    *,
    amount_text: str,
    product_name: Optional[str] = None,
) -> tuple[str, str]:
    title = "پرداخت موفق"

    message = (
        f"پرداخت شما به مبلغ {amount_text} با موفقیت ثبت شد."
    )

    if product_name:
        message += (
            f"\nمحصول: {product_name}"
        )

    return title, message


def payment_failed_message(
    *,
    reason: Optional[str] = None,
) -> tuple[str, str]:
    title = "پرداخت ناموفق"

    message = (
        "پرداخت با موفقیت تکمیل نشد."
    )

    if reason:
        message += (
            f"\nعلت: {reason}"
        )

    return title, message


def credits_added_message(
    *,
    credits: float,
    balance: Optional[float] = None,
) -> tuple[str, str]:
    title = "اعتبار اضافه شد"

    message = (
        f"{credits:g} اعتبار به حساب شما اضافه شد."
    )

    if balance is not None:
        message += (
            f"\nموجودی فعلی: {balance:g}"
        )

    return title, message


def invoice_issued_message(
    *,
    invoice_number: str,
    amount_text: str,
) -> tuple[str, str]:
    title = "فاکتور صادر شد"

    message = (
        f"فاکتور {invoice_number} صادر شد."
        f"\nمبلغ: {amount_text}"
    )

    return title, message


def report_ready_message(
    *,
    report_name: str,
) -> tuple[str, str]:
    title = "گزارش آماده است"

    message = (
        f"گزارش «{report_name}» آماده دریافت است."
    )

    return title, message


# ---------------------------------------------------------------------------
# GLOBAL MANAGER
# ---------------------------------------------------------------------------


_default_notification_manager = NotificationManager()


def get_notification_manager() -> NotificationManager:
    """
    Return the global notification manager.
    """

    return _default_notification_manager


# ---------------------------------------------------------------------------
# CONVENIENCE FACTORY
# ---------------------------------------------------------------------------


def create_billing_notification(
    notification_type: NotificationType,
    *,
    user_id: Optional[str] = None,
    channel: NotificationChannel = NotificationChannel.INTERNAL,
    title: str = "",
    message: str = "",
    order_id: Optional[str] = None,
    payment_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    invoice_id: Optional[str] = None,
    product_code: Optional[str] = None,
    amount: Optional[float] = None,
    currency: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> BillingNotification:
    """
    Create and store a billing notification using the global manager.
    """

    return _default_notification_manager.create(
        notification_type,
        user_id=user_id,
        channel=channel,
        title=title,
        message=message,
        order_id=order_id,
        payment_id=payment_id,
        subscription_id=subscription_id,
        invoice_id=invoice_id,
        product_code=product_code,
        amount=amount,
        currency=currency,
        metadata=metadata,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


__all__ = [
    "NotificationType",
    "NotificationChannel",
    "NotificationStatus",
    "BillingNotification",
    "NotificationManager",
    "get_notification_manager",
    "create_billing_notification",
    "subscription_activated_message",
    "payment_success_message",
    "payment_failed_message",
    "credits_added_message",
    "invoice_issued_message",
    "report_ready_message",
]
