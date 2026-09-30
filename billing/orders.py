"""
StructuralBot - Orders

Commercial order management.

Responsibilities:
- Create orders for plans, credits, reports, and other products
- Track order lifecycle
- Connect orders to payments
- Connect successful orders to subscriptions/credits
- Keep commercial transaction state independent from Telegram UI

This module does not perform payment processing itself.
Payment gateways are handled by billing.gateway.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional


# ============================================================
# ORDER STATUS
# ============================================================


class OrderStatus(str, Enum):
    """
    Commercial order lifecycle.
    """

    CREATED = "created"

    PENDING_PAYMENT = "pending_payment"

    PAID = "paid"

    PROCESSING = "processing"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"

    REFUNDED = "refunded"

    EXPIRED = "expired"


# ============================================================
# ORDER TYPE
# ============================================================


class OrderType(str, Enum):
    """
    Types of products/services that can be purchased.
    """

    SUBSCRIPTION = "subscription"

    CREDIT = "credit"

    PDF_REPORT = "pdf_report"

    EXCEL_REPORT = "excel_report"

    AI_CREDITS = "ai_credits"

    API = "api"

    CUSTOM = "custom"


# ============================================================
# ORDER ERROR
# ============================================================


class OrderError(Exception):
    """Base order exception."""


class OrderNotFoundError(OrderError):
    """Order does not exist."""


class InvalidOrderError(OrderError):
    """Order data is invalid."""


class OrderStateError(OrderError):
    """Invalid order state transition."""


# ============================================================
# ORDER ITEM
# ============================================================


@dataclass
class OrderItem:
    """
    A single commercial item inside an order.
    """

    item_id: str

    product_code: str

    name: str

    quantity: int

    unit_price: int

    currency: str = "IRR"

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def total_price(self) -> int:
        return (
            self.quantity
            * self.unit_price
        )

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "product_code": self.product_code,
            "name": self.name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "currency": self.currency,
            "total_price": self.total_price,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# ORDER
# ============================================================


@dataclass
class Order:
    """
    Commercial order.

    An order is the business record connecting:
        user -> product -> amount -> payment -> fulfillment
    """

    order_id: str

    user_id: str

    order_type: OrderType

    items: List[OrderItem]

    currency: str = "IRR"

    status: OrderStatus = (
        OrderStatus.CREATED
    )

    payment_id: Optional[str] = None

    payment_reference: Optional[str] = None

    description: str = ""

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

    paid_at: Optional[str] = None

    completed_at: Optional[str] = None

    cancelled_at: Optional[str] = None

    refunded_at: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def total_amount(self) -> int:
        return sum(
            item.total_price
            for item in self.items
        )

    @property
    def is_paid(self) -> bool:
        return self.status in {
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
            OrderStatus.COMPLETED,
        }

    @property
    def is_completed(self) -> bool:
        return (
            self.status
            == OrderStatus.COMPLETED
        )

    def mark_pending_payment(
        self,
        payment_id: Optional[str] = None,
    ) -> None:

        self.status = (
            OrderStatus.PENDING_PAYMENT
        )

        if payment_id:
            self.payment_id = payment_id

        self._touch()

    def mark_paid(
        self,
        payment_id: Optional[str] = None,
        payment_reference: Optional[str] = None,
    ) -> None:

        self.status = OrderStatus.PAID

        if payment_id:
            self.payment_id = payment_id

        if payment_reference:
            self.payment_reference = (
                payment_reference
            )

        self.paid_at = datetime.now(
            timezone.utc
        ).isoformat()

        self._touch()

    def mark_processing(self) -> None:

        if not self.is_paid:
            raise OrderStateError(
                "Only paid orders can enter "
                "processing state."
            )

        self.status = (
            OrderStatus.PROCESSING
        )

        self._touch()

    def mark_completed(self) -> None:

        if self.status not in {
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
        }:
            raise OrderStateError(
                "Only paid or processing orders "
                "can be completed."
            )

        self.status = (
            OrderStatus.COMPLETED
        )

        self.completed_at = datetime.now(
            timezone.utc
        ).isoformat()

        self._touch()

    def mark_failed(self) -> None:

        self.status = (
            OrderStatus.FAILED
        )

        self._touch()

    def cancel(self) -> None:

        if self.status in {
            OrderStatus.COMPLETED,
            OrderStatus.REFUNDED,
        }:
            raise OrderStateError(
                "Completed/refunded orders "
                "cannot be cancelled."
            )

        self.status = (
            OrderStatus.CANCELLED
        )

        self.cancelled_at = datetime.now(
            timezone.utc
        ).isoformat()

        self._touch()

    def refund(self) -> None:

        if not self.is_paid:
            raise OrderStateError(
                "Only paid orders can be refunded."
            )

        self.status = (
            OrderStatus.REFUNDED
        )

        self.refunded_at = datetime.now(
            timezone.utc
        ).isoformat()

        self._touch()

    def expire(self) -> None:

        if self.status in {
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
            OrderStatus.COMPLETED,
        }:
            raise OrderStateError(
                "Paid orders cannot be expired."
            )

        self.status = (
            OrderStatus.EXPIRED
        )

        self._touch()

    def _touch(self) -> None:

        self.updated_at = datetime.now(
            timezone.utc
        ).isoformat()

    def to_dict(self) -> dict:

        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "order_type": (
                self.order_type.value
                if isinstance(
                    self.order_type,
                    OrderType,
                )
                else str(
                    self.order_type
                )
            ),
            "items": [
                item.to_dict()
                for item in self.items
            ],
            "currency": self.currency,
            "status": (
                self.status.value
                if isinstance(
                    self.status,
                    OrderStatus,
                )
                else str(
                    self.status
                )
            ),
            "total_amount": self.total_amount,
            "payment_id": self.payment_id,
            "payment_reference": (
                self.payment_reference
            ),
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "paid_at": self.paid_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
            "refunded_at": self.refunded_at,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# ORDER MANAGER
# ============================================================


class OrderManager:
    """
    Thread-safe order manager.

    Current implementation is in-memory.
    It is intentionally structured so it can later be backed
    by database repositories.
    """

    def __init__(self) -> None:

        self._orders: Dict[
            str,
            Order,
        ] = {}

        self._lock = Lock()

    # ========================================================
    # INTERNAL
    # ========================================================

    @staticmethod
    def _normalize_user_id(
        user_id: str,
    ) -> str:

        if user_id is None:
            raise InvalidOrderError(
                "user_id is required."
            )

        value = str(
            user_id
        ).strip()

        if not value:
            raise InvalidOrderError(
                "user_id cannot be empty."
            )

        return value

    @staticmethod
    def _make_id(
        prefix: str,
        user_id: str,
    ) -> str:

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%d%H%M%S%f"
        )

        return (
            f"{prefix}_"
            f"{user_id}_"
            f"{timestamp}"
        )

    # ========================================================
    # CREATE
    # ========================================================

    def create_order(
        self,
        *,
        user_id: str,
        order_type: OrderType | str,
        items: List[OrderItem],
        currency: str = "IRR",
        description: str = "",
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Order:

        user_id = self._normalize_user_id(
            user_id
        )

        if not items:
            raise InvalidOrderError(
                "Order must contain at least "
                "one item."
            )

        normalized_items = []

        for item in items:

            if item.quantity <= 0:
                raise InvalidOrderError(
                    "Item quantity must be positive."
                )

            if item.unit_price < 0:
                raise InvalidOrderError(
                    "Item price cannot be negative."
                )

            normalized_items.append(
                item
            )

        if isinstance(
            order_type,
            OrderType,
        ):
            normalized_type = order_type
        else:
            try:
                normalized_type = OrderType(
                    str(
                        order_type
                    ).strip().lower()
                )
            except ValueError as exc:
                raise InvalidOrderError(
                    f"Unknown order type: "
                    f"{order_type}"
                ) from exc

        order = Order(
            order_id=self._make_id(
                "ord",
                user_id,
            ),
            user_id=user_id,
            order_type=normalized_type,
            items=normalized_items,
            currency=currency,
            description=description,
            metadata=dict(
                metadata or {}
            ),
        )

        with self._lock:

            self._orders[
                order.order_id
            ] = order

        return order

    # ========================================================
    # GET
    # ========================================================

    def get_order(
        self,
        order_id: str,
    ) -> Order:

        with self._lock:

            order = self._orders.get(
                order_id
            )

            if order is None:
                raise OrderNotFoundError(
                    f"Order not found: "
                    f"{order_id}"
                )

            return order

    def get_optional(
        self,
        order_id: str,
    ) -> Optional[Order]:

        with self._lock:

            return self._orders.get(
                order_id
            )

    # ========================================================
    # PAYMENT
    # ========================================================

    def attach_payment(
        self,
        order_id: str,
        payment_id: str,
    ) -> Order:

        order = self.get_order(
            order_id
        )

        order.mark_pending_payment(
            payment_id
        )

        return order

    def mark_paid(
        self,
        order_id: str,
        payment_id: Optional[str] = None,
        payment_reference: Optional[
            str
        ] = None,
    ) -> Order:

        order = self.get_order(
            order_id
        )

        order.mark_paid(
            payment_id=payment_id,
            payment_reference=(
                payment_reference
            ),
        )

        return order

    # ========================================================
    # STATUS
    # ========================================================

    def mark_processing(
        self,
        order_id: str,
    ) -> Order:

        order = self.get_order(
            order_id
        )

        order.mark_processing()

        return order

    def mark_completed(
        self,
        order_id: str,
    ) -> Order:

        order = self.get_order(
            order_id
        )

        order.mark_completed()

        return order

    def mark_failed(
        self,
        order_id: str,
    ) -> Order:

        order = self.get_order(
            order_id
        )

        order.mark_failed()

        return order

    def cancel(
        self,
        order_id: str,
    ) -> Order:

        order = self.get_order(
            order_id
        )

        order.cancel()

        return order

    def refund(
        self,
        order_id: str,
    ) -> Order:

        order = self.get_order(
            order_id
        )

        order.refund()

        return order

    def expire(
        self,
        order_id: str,
    ) -> Order:

        order = self.get_order(
            order_id
        )

        order.expire()

        return order

    # ========================================================
    # USER ORDERS
    # ========================================================

    def list_user_orders(
        self,
        user_id: str,
    ) -> List[Order]:

        user_id = self._normalize_user_id(
            user_id
        )

        with self._lock:

            result = [
                order
                for order in self._orders.values()
                if order.user_id == user_id
            ]

        return sorted(
            result,
            key=lambda item:
                item.created_at,
            reverse=True,
        )

    def list_orders(
        self,
        *,
        status: Optional[
            OrderStatus | str
        ] = None,
        order_type: Optional[
            OrderType | str
        ] = None,
    ) -> List[Order]:

        with self._lock:

            orders = list(
                self._orders.values()
            )

        if status is not None:

            normalized_status = (
                status
                if isinstance(
                    status,
                    OrderStatus,
                )
                else OrderStatus(
                    str(
                        status
                    ).lower()
                )
            )

            orders = [
                order
                for order in orders
                if order.status
                == normalized_status
            ]

        if order_type is not None:

            normalized_type = (
                order_type
                if isinstance(
                    order_type,
                    OrderType,
                )
                else OrderType(
                    str(
                        order_type
                    ).lower()
                )
            )

            orders = [
                order
                for order in orders
                if order.order_type
                == normalized_type
            ]

        return sorted(
            orders,
            key=lambda item:
                item.created_at,
            reverse=True,
        )

    # ========================================================
    # QUERIES
    # ========================================================

    def has_pending_payment(
        self,
        user_id: str,
    ) -> bool:

        orders = self.list_user_orders(
            user_id
        )

        return any(
            order.status
            in {
                OrderStatus.CREATED,
                OrderStatus.PENDING_PAYMENT,
            }
            for order in orders
        )

    def get_latest_order(
        self,
        user_id: str,
    ) -> Optional[Order]:

        orders = self.list_user_orders(
            user_id
        )

        return (
            orders[0]
            if orders
            else None
        )

    # ========================================================
    # FINANCIAL SUMMARY
    # ========================================================

    def get_user_summary(
        self,
        user_id: str,
    ) -> dict:

        orders = self.list_user_orders(
            user_id
        )

        paid = [
            order
            for order in orders
            if order.status
            in {
                OrderStatus.PAID,
                OrderStatus.PROCESSING,
                OrderStatus.COMPLETED,
            }
        ]

        refunded = [
            order
            for order in orders
            if order.status
            == OrderStatus.REFUNDED
        ]

        pending = [
            order
            for order in orders
            if order.status
            in {
                OrderStatus.CREATED,
                OrderStatus.PENDING_PAYMENT,
            }
        ]

        return {
            "user_id": str(
                user_id
            ),
            "total_orders": len(
                orders
            ),
            "paid_orders": len(
                paid
            ),
            "pending_orders": len(
                pending
            ),
            "refunded_orders": len(
                refunded
            ),
            "paid_amount": sum(
                order.total_amount
                for order in paid
            ),
            "refunded_amount": sum(
                order.total_amount
                for order in refunded
            ),
            "currency": (
                paid[0].currency
                if paid
                else "IRR"
            ),
        }

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(
        self,
        order_id: str,
    ) -> dict:

        return self.get_order(
            order_id
        ).to_dict()

    def user_orders_dict(
        self,
        user_id: str,
    ) -> List[dict]:

        return [
            order.to_dict()
            for order in self.list_user_orders(
                user_id
            )
        ]

    # ========================================================
    # RESET
    # ========================================================

    def clear(self) -> None:

        with self._lock:
            self._orders.clear()


# ============================================================
# GLOBAL MANAGER
# ============================================================


_default_order_manager: Optional[
    OrderManager
] = None


def get_order_manager() -> OrderManager:

    global _default_order_manager

    if _default_order_manager is None:

        _default_order_manager = (
            OrderManager()
        )

    return _default_order_manager


def set_order_manager(
    manager: OrderManager,
) -> None:

    global _default_order_manager

    _default_order_manager = manager


# ============================================================
# CONVENIENCE HELPERS
# ============================================================


def create_order(
    *,
    user_id: str,
    order_type: OrderType | str,
    items: List[OrderItem],
    currency: str = "IRR",
    description: str = "",
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> Order:

    return get_order_manager().create_order(
        user_id=user_id,
        order_type=order_type,
        items=items,
        currency=currency,
        description=description,
        metadata=metadata,
    )


def get_order(
    order_id: str,
) -> Order:

    return get_order_manager().get_order(
        order_id
    )


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "OrderStatus",
    "OrderType",
    "OrderError",
    "OrderNotFoundError",
    "InvalidOrderError",
    "OrderStateError",
    "OrderItem",
    "Order",
    "OrderManager",
    "get_order_manager",
    "set_order_manager",
    "create_order",
    "get_order",
]
