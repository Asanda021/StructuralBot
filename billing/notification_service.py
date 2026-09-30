"""
StructuralBot - Billing Notification Service

High-level notification service for billing events.

Responsibilities:
- Convert billing events into user notifications
- Keep notification generation independent from Telegram
- Provide consistent notification templates
- Support future Telegram/email/SMS/push adapters
- Handle billing lifecycle notifications
- Avoid duplicate notifications through idempotency keys

This module does not send messages directly.
Transport-specific delivery belongs to external adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from billing.notifications import (
    BillingNotification,
    NotificationChannel,
    NotificationManager,
    NotificationType,
    credits_added_message,
    get_notification_manager,
    invoice_issued_message,
    payment_failed_message,
    payment_success_message,
    report_ready_message,
    subscription_activated_message,
)


# ---------------------------------------------------------------------------
# ERRORS
# ---------------------------------------------------------------------------


class NotificationServiceError(Exception):
    """Base notification service error."""


class NotificationTemplateError(NotificationServiceError):
    """Notification template could not be generated."""


# ---------------------------------------------------------------------------
# REQUEST
# ---------------------------------------------------------------------------


@dataclass
class NotificationRequest:
    """
    Generic request for creating a billing notification.
    """

    notification_type: NotificationType

    user_id: Optional[str] = None

    channel: NotificationChannel = NotificationChannel.INTERNAL

    title: str = ""

    message: str = ""

    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    product_code: Optional[str] = None

    amount: Optional[float] = None
    currency: Optional[str] = None

    metadata: Optional[Dict[str, Any]] = None

    idempotency_key: Optional[str] = None

    correlation_id: Optional[str] = None


# ---------------------------------------------------------------------------
# SERVICE
# ---------------------------------------------------------------------------


class BillingNotificationService:
    """
    High-level notification facade.

    Billing modules should use this service instead of directly
    constructing Telegram messages.
    """

    def __init__(
        self,
        manager: Optional[NotificationManager] = None,
    ) -> None:
        self.manager = (
            manager
            if manager is not None
            else get_notification_manager()
        )

    # ------------------------------------------------------------------
    # GENERIC
    # ------------------------------------------------------------------

    def create(
        self,
        request: NotificationRequest,
    ) -> BillingNotification:
        """
        Create a notification from a generic request.
        """

        if not request.user_id:
            raise NotificationServiceError(
                "user_id is required for a user notification."
            )

        return self.manager.create(
            request.notification_type,
            user_id=request.user_id,
            channel=request.channel,
            title=request.title,
            message=request.message,
            order_id=request.order_id,
            payment_id=request.payment_id,
            subscription_id=request.subscription_id,
            invoice_id=request.invoice_id,
            product_code=request.product_code,
            amount=request.amount,
            currency=request.currency,
            metadata=request.metadata,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
        )

    # ------------------------------------------------------------------
    # SUBSCRIPTION
    # ------------------------------------------------------------------

    def subscription_activated(
        self,
        *,
        user_id: str,
        plan_name: str,
        expires_text: Optional[str] = None,
        subscription_id: Optional[str] = None,
        product_code: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingNotification:
        """
        Create subscription activation notification.
        """

        title, message = subscription_activated_message(
            plan_name=plan_name,
            expires_text=expires_text,
        )

        return self.manager.create(
            NotificationType.SUBSCRIPTION_ACTIVATED,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            subscription_id=subscription_id,
            product_code=product_code,
            metadata=metadata,
            idempotency_key=idempotency_key,
        )

    def subscription_renewed(
        self,
        *,
        user_id: str,
        plan_name: str,
        expires_text: Optional[str] = None,
        subscription_id: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        title = "اشتراک تمدید شد"

        message = (
            f"اشتراک «{plan_name}» با موفقیت تمدید شد."
        )

        if expires_text:
            message += (
                f"\nاعتبار تا: {expires_text}"
            )

        return self.manager.create(
            NotificationType.SUBSCRIPTION_RENEWED,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            subscription_id=subscription_id,
            idempotency_key=idempotency_key,
        )

    def subscription_expiring(
        self,
        *,
        user_id: str,
        plan_name: str,
        days_remaining: int,
        subscription_id: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        title = "اشتراک در حال اتمام است"

        message = (
            f"اشتراک «{plan_name}» "
            f"{days_remaining} روز دیگر منقضی می‌شود."
        )

        return self.manager.create(
            NotificationType.SUBSCRIPTION_EXPIRING,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            subscription_id=subscription_id,
            idempotency_key=idempotency_key,
        )

    def subscription_expired(
        self,
        *,
        user_id: str,
        plan_name: str,
        subscription_id: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        title = "اشتراک منقضی شد"

        message = (
            f"اشتراک «{plan_name}» منقضی شده است."
        )

        return self.manager.create(
            NotificationType.SUBSCRIPTION_EXPIRED,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            subscription_id=subscription_id,
            idempotency_key=idempotency_key,
        )

    def subscription_cancelled(
        self,
        *,
        user_id: str,
        plan_name: str,
        subscription_id: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        title = "اشتراک لغو شد"

        message = (
            f"اشتراک «{plan_name}» لغو شد."
        )

        return self.manager.create(
            NotificationType.SUBSCRIPTION_CANCELLED,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            subscription_id=subscription_id,
            idempotency_key=idempotency_key,
        )

    # ------------------------------------------------------------------
    # PAYMENT
    # ------------------------------------------------------------------

    def payment_success(
        self,
        *,
        user_id: str,
        amount_text: str,
        product_name: Optional[str] = None,
        payment_id: Optional[str] = None,
        order_id: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        """
        Create successful payment notification.
        """

        title, message = payment_success_message(
            amount_text=amount_text,
            product_name=product_name,
        )

        return self.manager.create(
            NotificationType.PAYMENT_SUCCESS,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            payment_id=payment_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
        )

    def payment_failed(
        self,
        *,
        user_id: str,
        reason: Optional[str] = None,
        payment_id: Optional[str] = None,
        order_id: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        """
        Create failed payment notification.
        """

        title, message = payment_failed_message(
            reason=reason,
        )

        return self.manager.create(
            NotificationType.PAYMENT_FAILED,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            payment_id=payment_id,
            order_id=order_id,
            idempotency_key=idempotency_key,
        )

    def payment_pending(
        self,
        *,
        user_id: str,
        payment_id: Optional[str] = None,
        order_id: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        title = "پرداخت در انتظار تأیید"

        message = (
            "پرداخت شما دریافت شده و در انتظار تأیید نهایی است."
        )

        return self.manager.create(
            NotificationType.PAYMENT_PENDING,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            payment_id=payment_id,
            order_id=order_id,
            idempotency_key=idempotency_key,
        )

    def payment_refunded(
        self,
        *,
        user_id: str,
        amount_text: str,
        payment_id: Optional[str] = None,
        order_id: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        title = "مبلغ بازپرداخت شد"

        message = (
            f"مبلغ {amount_text} به‌عنوان بازپرداخت ثبت شد."
        )

        return self.manager.create(
            NotificationType.PAYMENT_REFUNDED,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            payment_id=payment_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
        )

    # ------------------------------------------------------------------
    # CREDITS
    # ------------------------------------------------------------------

    def credits_added(
        self,
        *,
        user_id: str,
        credits: float,
        balance: Optional[float] = None,
        order_id: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        """
        Notify user that credits were added.
        """

        title, message = credits_added_message(
            credits=credits,
            balance=balance,
        )

        return self.manager.create(
            NotificationType.CREDITS_PURCHASED,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            order_id=order_id,
            amount=credits,
            idempotency_key=idempotency_key,
        )

    def credits_granted(
        self,
        *,
        user_id: str,
        credits: float,
        balance: Optional[float] = None,
        reason: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        title = "اعتبار هدیه دریافت کردید"

        message = (
            f"{credits:g} اعتبار به حساب شما اضافه شد."
        )

        if balance is not None:
            message += (
                f"\nموجودی فعلی: {balance:g}"
            )

        if reason:
            message += (
                f"\nدلیل: {reason}"
            )

        return self.manager.create(
            NotificationType.CREDITS_GRANTED,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            amount=credits,
            idempotency_key=idempotency_key,
        )

    def credits_low(
        self,
        *,
        user_id: str,
        balance: float,
        threshold: float,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        title = "اعتبار حساب کم است"

        message = (
            f"موجودی اعتبار شما {balance:g} است "
            f"و به حد هشدار {threshold:g} رسیده است."
        )

        return self.manager.create(
            NotificationType.CREDITS_LOW,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            amount=balance,
            idempotency_key=idempotency_key,
        )

    # ------------------------------------------------------------------
    # INVOICE
    # ------------------------------------------------------------------

    def invoice_issued(
        self,
        *,
        user_id: str,
        invoice_number: str,
        amount_text: str,
        invoice_id: Optional[str] = None,
        order_id: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        """
        Notify user about issued invoice.
        """

        title, message = invoice_issued_message(
            invoice_number=invoice_number,
            amount_text=amount_text,
        )

        return self.manager.create(
            NotificationType.INVOICE_ISSUED,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            invoice_id=invoice_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
        )

    def invoice_paid(
        self,
        *,
        user_id: str,
        invoice_number: str,
        amount_text: str,
        invoice_id: Optional[str] = None,
        order_id: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        title = "فاکتور پرداخت شد"

        message = (
            f"فاکتور {invoice_number} پرداخت شد."
            f"\nمبلغ: {amount_text}"
        )

        return self.manager.create(
            NotificationType.INVOICE_PAID,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            invoice_id=invoice_id,
            order_id=order_id,
            idempotency_key=idempotency_key,
        )

    # ------------------------------------------------------------------
    # REPORT
    # ------------------------------------------------------------------

    def report_ready(
        self,
        *,
        user_id: str,
        report_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        """
        Notify user that a report is ready.
        """

        title, message = report_ready_message(
            report_name=report_name,
        )

        return self.manager.create(
            NotificationType.REPORT_READY,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            metadata=metadata,
            idempotency_key=idempotency_key,
        )

    def report_failed(
        self,
        *,
        user_id: str,
        report_name: str,
        reason: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        title = "ساخت گزارش ناموفق بود"

        message = (
            f"ساخت گزارش «{report_name}» با مشکل مواجه شد."
        )

        if reason:
            message += (
                f"\nعلت: {reason}"
            )

        return self.manager.create(
            NotificationType.REPORT_FAILED,
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            idempotency_key=idempotency_key,
        )

    # ------------------------------------------------------------------
    # GENERAL BILLING ERROR
    # ------------------------------------------------------------------

    def billing_error(
        self,
        *,
        user_id: Optional[str],
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        channel: NotificationChannel = NotificationChannel.INTERNAL,
        idempotency_key: Optional[str] = None,
    ) -> BillingNotification:
        """
        Create a user-safe billing error notification.

        Internal exception details should not be exposed here.
        """

        return self.manager.create(
            NotificationType.BILLING_ERROR,
            user_id=user_id,
            channel=channel,
            title="خطا در بخش مالی",
            message=message,
            metadata=metadata,
            idempotency_key=idempotency_key,
        )

    # ------------------------------------------------------------------
    # DELIVERY HELPERS
    # ------------------------------------------------------------------

    def queue(
        self,
        notification_id: str,
    ) -> BillingNotification:
        return self.manager.queue(notification_id)

    def start_sending(
        self,
        notification_id: str,
    ) -> BillingNotification:
        return self.manager.start_sending(notification_id)

    def mark_sent(
        self,
        notification_id: str,
    ) -> BillingNotification:
        return self.manager.mark_sent(notification_id)

    def mark_failed(
        self,
        notification_id: str,
        error: str,
    ) -> BillingNotification:
        return self.manager.mark_failed(
            notification_id,
            error,
        )

    # ------------------------------------------------------------------
    # QUERY
    # ------------------------------------------------------------------

    def user_inbox(
        self,
        user_id: str,
        *,
        limit: Optional[int] = None,
    ) -> list[BillingNotification]:
        return self.manager.user_inbox(
            user_id,
            limit=limit,
        )

    def pending(
        self,
        *,
        channel: Optional[NotificationChannel] = None,
        limit: Optional[int] = None,
    ) -> list[BillingNotification]:
        return self.manager.pending(
            channel=channel,
            limit=limit,
        )

    def summary(
        self,
        *,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.manager.summary(
            user_id=user_id,
        )


# ---------------------------------------------------------------------------
# GLOBAL SERVICE
# ---------------------------------------------------------------------------


_default_notification_service = BillingNotificationService()


def get_notification_service() -> BillingNotificationService:
    """
    Return the global billing notification service.
    """

    return _default_notification_service


# ---------------------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# ---------------------------------------------------------------------------


def notify_subscription_activated(
    *,
    user_id: str,
    plan_name: str,
    expires_text: Optional[str] = None,
    subscription_id: Optional[str] = None,
    channel: NotificationChannel = NotificationChannel.INTERNAL,
    idempotency_key: Optional[str] = None,
) -> BillingNotification:
    return _default_notification_service.subscription_activated(
        user_id=user_id,
        plan_name=plan_name,
        expires_text=expires_text,
        subscription_id=subscription_id,
        channel=channel,
        idempotency_key=idempotency_key,
    )


def notify_payment_success(
    *,
    user_id: str,
    amount_text: str,
    product_name: Optional[str] = None,
    payment_id: Optional[str] = None,
    order_id: Optional[str] = None,
    channel: NotificationChannel = NotificationChannel.INTERNAL,
    idempotency_key: Optional[str] = None,
) -> BillingNotification:
    return _default_notification_service.payment_success(
        user_id=user_id,
        amount_text=amount_text,
        product_name=product_name,
        payment_id=payment_id,
        order_id=order_id,
        channel=channel,
        idempotency_key=idempotency_key,
    )


def notify_payment_failed(
    *,
    user_id: str,
    reason: Optional[str] = None,
    payment_id: Optional[str] = None,
    order_id: Optional[str] = None,
    channel: NotificationChannel = NotificationChannel.INTERNAL,
    idempotency_key: Optional[str] = None,
) -> BillingNotification:
    return _default_notification_service.payment_failed(
        user_id=user_id,
        reason=reason,
        payment_id=payment_id,
        order_id=order_id,
        channel=channel,
        idempotency_key=idempotency_key,
    )


def notify_credits_added(
    *,
    user_id: str,
    credits: float,
    balance: Optional[float] = None,
    order_id: Optional[str] = None,
    channel: NotificationChannel = NotificationChannel.INTERNAL,
    idempotency_key: Optional[str] = None,
) -> BillingNotification:
    return _default_notification_service.credits_added(
        user_id=user_id,
        credits=credits,
        balance=balance,
        order_id=order_id,
        channel=channel,
        idempotency_key=idempotency_key,
    )


def notify_invoice_issued(
    *,
    user_id: str,
    invoice_number: str,
    amount_text: str,
    invoice_id: Optional[str] = None,
    order_id: Optional[str] = None,
    channel: NotificationChannel = NotificationChannel.INTERNAL,
    idempotency_key: Optional[str] = None,
) -> BillingNotification:
    return _default_notification_service.invoice_issued(
        user_id=user_id,
        invoice_number=invoice_number,
        amount_text=amount_text,
        invoice_id=invoice_id,
        order_id=order_id,
        channel=channel,
        idempotency_key=idempotency_key,
    )


def notify_report_ready(
    *,
    user_id: str,
    report_name: str,
    metadata: Optional[Dict[str, Any]] = None,
    channel: NotificationChannel = NotificationChannel.INTERNAL,
    idempotency_key: Optional[str] = None,
) -> BillingNotification:
    return _default_notification_service.report_ready(
        user_id=user_id,
        report_name=report_name,
        metadata=metadata,
        channel=channel,
        idempotency_key=idempotency_key,
    )


__all__ = [
    "NotificationServiceError",
    "NotificationTemplateError",
    "NotificationRequest",
    "BillingNotificationService",
    "get_notification_service",
    "notify_subscription_activated",
    "notify_payment_success",
    "notify_payment_failed",
    "notify_credits_added",
    "notify_invoice_issued",
    "notify_report_ready",
]
