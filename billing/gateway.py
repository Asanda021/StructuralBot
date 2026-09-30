"""
StructuralBot - Payment Gateway Abstraction

Payment gateway abstraction layer.

Responsibilities:
- Create payment requests
- Track payment intents
- Verify payments
- Normalize gateway responses
- Keep payment-provider-specific logic isolated

This module intentionally does NOT contain:
- Telegram UI
- Subscription business rules
- Credit business rules
- Engineering logic

Concrete gateways can later be implemented as adapters.
"""


from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, Optional, Protocol


# ============================================================
# PAYMENT STATUS
# ============================================================


class PaymentStatus(str, Enum):
    """
    Normalized payment lifecycle.
    """

    CREATED = "created"

    PENDING = "pending"

    REDIRECT_REQUIRED = "redirect_required"

    SUCCESS = "success"

    FAILED = "failed"

    CANCELLED = "cancelled"

    EXPIRED = "expired"

    REFUNDED = "refunded"

    UNKNOWN = "unknown"


# ============================================================
# PAYMENT ERROR
# ============================================================


class PaymentError(Exception):
    """Base payment exception."""


class PaymentConfigurationError(
    PaymentError
):
    """Gateway configuration error."""


class PaymentProviderError(
    PaymentError
):
    """External gateway/provider error."""


class PaymentVerificationError(
    PaymentError
):
    """Payment verification failure."""


class PaymentNotFoundError(
    PaymentError
):
    """Payment intent not found."""


# ============================================================
# PAYMENT REQUEST
# ============================================================


@dataclass(frozen=True)
class PaymentRequest:
    """
    Normalized request sent to a payment gateway.
    """

    user_id: str

    amount: int

    currency: str = "IRR"

    description: str = ""

    callback_url: Optional[str] = None

    order_id: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# PAYMENT RESULT
# ============================================================


@dataclass
class PaymentResult:
    """
    Normalized response from a payment gateway.
    """

    payment_id: str

    status: PaymentStatus

    amount: int

    currency: str

    authority: Optional[str] = None

    payment_url: Optional[str] = None

    gateway: Optional[str] = None

    reference_id: Optional[str] = None

    message: str = ""

    raw_data: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=lambda:
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    verified_at: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def is_successful(self) -> bool:
        return (
            self.status
            == PaymentStatus.SUCCESS
        )

    def is_pending(self) -> bool:
        return self.status in {
            PaymentStatus.CREATED,
            PaymentStatus.PENDING,
            PaymentStatus.REDIRECT_REQUIRED,
        }

    def to_dict(self) -> dict:
        return {
            "payment_id": self.payment_id,
            "status": self.status.value,
            "amount": self.amount,
            "currency": self.currency,
            "authority": self.authority,
            "payment_url": self.payment_url,
            "gateway": self.gateway,
            "reference_id": self.reference_id,
            "message": self.message,
            "raw_data": dict(
                self.raw_data
            ),
            "created_at": self.created_at,
            "verified_at": self.verified_at,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# PAYMENT INTENT
# ============================================================


@dataclass
class PaymentIntent:
    """
    Internal representation of a payment.

    A payment intent may remain pending until the external
    gateway confirms the transaction.
    """

    payment_id: str

    user_id: str

    amount: int

    currency: str

    description: str

    status: PaymentStatus = (
        PaymentStatus.CREATED
    )

    gateway: Optional[str] = None

    authority: Optional[str] = None

    payment_url: Optional[str] = None

    reference_id: Optional[str] = None

    order_id: Optional[str] = None

    created_at: str = field(
        default_factory=lambda:
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    updated_at: str = field(
        default_factory=lambda:
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    verified_at: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict:
        return {
            "payment_id": self.payment_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "status": self.status.value,
            "gateway": self.gateway,
            "authority": self.authority,
            "payment_url": self.payment_url,
            "reference_id": self.reference_id,
            "order_id": self.order_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "verified_at": self.verified_at,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# GATEWAY PROTOCOL
# ============================================================


class PaymentGateway(Protocol):
    """
    Interface implemented by payment providers.
    """

    name: str

    def create_payment(
        self,
        request: PaymentRequest,
    ) -> PaymentResult:
        ...

    def verify_payment(
        self,
        payment: PaymentIntent,
    ) -> PaymentResult:
        ...

    def refund_payment(
        self,
        payment: PaymentIntent,
    ) -> PaymentResult:
        ...


# ============================================================
# BASE GATEWAY
# ============================================================


class BasePaymentGateway:
    """
    Base class for concrete gateway adapters.
    """

    name = "base"

    def create_payment(
        self,
        request: PaymentRequest,
    ) -> PaymentResult:

        raise NotImplementedError(
            "create_payment() must be implemented "
            "by a concrete gateway."
        )

    def verify_payment(
        self,
        payment: PaymentIntent,
    ) -> PaymentResult:

        raise NotImplementedError(
            "verify_payment() must be implemented "
            "by a concrete gateway."
        )

    def refund_payment(
        self,
        payment: PaymentIntent,
    ) -> PaymentResult:

        raise NotImplementedError(
            "refund_payment() must be implemented "
            "by a concrete gateway."
        )


# ============================================================
# PLACEHOLDER GATEWAY
# ============================================================


class PlaceholderPaymentGateway(
    BasePaymentGateway
):
    """
    Development gateway.

    It never performs a real financial transaction.

    Useful while developing the bot before connecting
    a real payment provider.
    """

    name = "placeholder"

    def create_payment(
        self,
        request: PaymentRequest,
    ) -> PaymentResult:

        payment_id = (
            f"pay_placeholder_"
            f"{request.user_id}_"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        )

        return PaymentResult(
            payment_id=payment_id,
            status=(
                PaymentStatus.REDIRECT_REQUIRED
            ),
            amount=request.amount,
            currency=request.currency,
            gateway=self.name,
            payment_url=None,
            message=(
                "Placeholder payment created. "
                "No real payment was processed."
            ),
            metadata=dict(
                request.metadata
            ),
        )

    def verify_payment(
        self,
        payment: PaymentIntent,
    ) -> PaymentResult:

        return PaymentResult(
            payment_id=payment.payment_id,
            status=PaymentStatus.PENDING,
            amount=payment.amount,
            currency=payment.currency,
            gateway=self.name,
            authority=payment.authority,
            message=(
                "Placeholder gateway does not "
                "perform real verification."
            ),
            metadata=dict(
                payment.metadata
            ),
        )

    def refund_payment(
        self,
        payment: PaymentIntent,
    ) -> PaymentResult:

        return PaymentResult(
            payment_id=payment.payment_id,
            status=PaymentStatus.REFUNDED,
            amount=payment.amount,
            currency=payment.currency,
            gateway=self.name,
            reference_id=payment.reference_id,
            message=(
                "Placeholder refund recorded."
            ),
            metadata=dict(
                payment.metadata
            ),
        )


# ============================================================
# PAYMENT MANAGER
# ============================================================


class PaymentManager:
    """
    Central payment orchestration layer.

    The manager does not know how a specific gateway works.
    """

    def __init__(
        self,
        gateway: Optional[
            PaymentGateway
        ] = None,
    ) -> None:

        self._gateway = (
            gateway
            or PlaceholderPaymentGateway()
        )

        self._payments: Dict[
            str,
            PaymentIntent,
        ] = {}

        self._lock = Lock()

    # ========================================================
    # GATEWAY
    # ========================================================

    @property
    def gateway(self) -> PaymentGateway:
        return self._gateway

    def set_gateway(
        self,
        gateway: PaymentGateway,
    ) -> None:

        if gateway is None:
            raise ValueError(
                "gateway is required."
            )

        self._gateway = gateway

    # ========================================================
    # CREATE
    # ========================================================

    def create_payment(
        self,
        request: PaymentRequest,
    ) -> PaymentResult:

        if request.amount <= 0:
            raise ValueError(
                "Payment amount must be positive."
            )

        if not request.user_id:
            raise ValueError(
                "user_id is required."
            )

        result = (
            self._gateway.create_payment(
                request
            )
        )

        intent = PaymentIntent(
            payment_id=result.payment_id,
            user_id=request.user_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            status=result.status,
            gateway=(
                result.gateway
                or getattr(
                    self._gateway,
                    "name",
                    None,
                )
            ),
            authority=result.authority,
            payment_url=result.payment_url,
            reference_id=result.reference_id,
            order_id=request.order_id,
            metadata={
                **dict(
                    request.metadata
                ),
                **dict(
                    result.metadata
                ),
            },
        )

        with self._lock:
            self._payments[
                intent.payment_id
            ] = intent

        return result

    # ========================================================
    # GET
    # ========================================================

    def get_payment(
        self,
        payment_id: str,
    ) -> PaymentIntent:

        with self._lock:

            payment = self._payments.get(
                payment_id
            )

            if payment is None:
                raise PaymentNotFoundError(
                    f"Payment not found: "
                    f"{payment_id}"
                )

            return payment

    # ========================================================
    # VERIFY
    # ========================================================

    def verify_payment(
        self,
        payment_id: str,
    ) -> PaymentResult:

        payment = self.get_payment(
            payment_id
        )

        result = (
            self._gateway.verify_payment(
                payment
            )
        )

        with self._lock:

            payment.status = result.status

            payment.authority = (
                result.authority
                or payment.authority
            )

            payment.reference_id = (
                result.reference_id
                or payment.reference_id
            )

            payment.updated_at = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            if result.is_successful():

                payment.verified_at = (
                    result.verified_at
                    or datetime.now(
                        timezone.utc
                    ).isoformat()
                )

        return result

    # ========================================================
    # REFUND
    # ========================================================

    def refund_payment(
        self,
        payment_id: str,
    ) -> PaymentResult:

        payment = self.get_payment(
            payment_id
        )

        result = (
            self._gateway.refund_payment(
                payment
            )
        )

        with self._lock:

            payment.status = result.status

            payment.updated_at = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

        return result

    # ========================================================
    # LIST
    # ========================================================

    def list_user_payments(
        self,
        user_id: str,
    ) -> list[PaymentIntent]:

        normalized = str(
            user_id
        ).strip()

        with self._lock:

            return [
                payment
                for payment in self._payments.values()
                if payment.user_id
                == normalized
            ]

    def list_payments(
        self,
    ) -> list[PaymentIntent]:

        with self._lock:

            return list(
                self._payments.values()
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    def summary(
        self,
        user_id: str,
    ) -> dict:

        payments = (
            self.list_user_payments(
                user_id
            )
        )

        successful = [
            item
            for item in payments
            if item.status
            == PaymentStatus.SUCCESS
        ]

        pending = [
            item
            for item in payments
            if item.status
            in {
                PaymentStatus.CREATED,
                PaymentStatus.PENDING,
                PaymentStatus.REDIRECT_REQUIRED,
            }
        ]

        refunded = [
            item
            for item in payments
            if item.status
            == PaymentStatus.REFUNDED
        ]

        return {
            "user_id": str(
                user_id
            ),
            "total_payments": len(
                payments
            ),
            "successful_payments": len(
                successful
            ),
            "pending_payments": len(
                pending
            ),
            "refunded_payments": len(
                refunded
            ),
            "successful_amount": sum(
                item.amount
                for item in successful
            ),
            "refunded_amount": sum(
                item.amount
                for item in refunded
            ),
            "currency": (
                successful[0].currency
                if successful
                else "IRR"
            ),
        }

    # ========================================================
    # RESET
    # ========================================================

    def clear(self) -> None:

        with self._lock:
            self._payments.clear()


# ============================================================
# GLOBAL MANAGER
# ============================================================


_default_payment_manager: Optional[
    PaymentManager
] = None


def get_payment_manager() -> PaymentManager:

    global _default_payment_manager

    if _default_payment_manager is None:

        _default_payment_manager = (
            PaymentManager()
        )

    return _default_payment_manager


def set_payment_manager(
    manager: PaymentManager,
) -> None:

    global _default_payment_manager

    _default_payment_manager = manager


# ============================================================
# CONVENIENCE HELPERS
# ============================================================


def create_payment(
    request: PaymentRequest,
) -> PaymentResult:

    return get_payment_manager().create_payment(
        request
    )


def verify_payment(
    payment_id: str,
) -> PaymentResult:

    return get_payment_manager().verify_payment(
        payment_id
    )


def refund_payment(
    payment_id: str,
) -> PaymentResult:

    return get_payment_manager().refund_payment(
        payment_id
    )


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "PaymentStatus",
    "PaymentError",
    "PaymentConfigurationError",
    "PaymentProviderError",
    "PaymentVerificationError",
    "PaymentNotFoundError",
    "PaymentRequest",
    "PaymentResult",
    "PaymentIntent",
    "PaymentGateway",
    "BasePaymentGateway",
    "PlaceholderPaymentGateway",
    "PaymentManager",
    "get_payment_manager",
    "set_payment_manager",
    "create_payment",
    "verify_payment",
    "refund_payment",
]
