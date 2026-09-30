"""
StructuralBot - Fulfillment

Post-payment fulfillment layer.

Responsibilities:
- Fulfill paid orders
- Activate subscriptions
- Grant credits
- Grant AI credits
- Grant paid reports
- Grant API access
- Keep fulfillment idempotent

Payment processing remains in:
    billing.gateway

Order lifecycle remains in:
    billing.orders

Checkout orchestration remains in:
    billing.checkout
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Dict, List, Optional

from billing.credits import (
    CreditManager,
    get_credit_manager,
)

from billing.orders import (
    Order,
    OrderItem,
    OrderStatus,
)

from billing.products import (
    ProductType,
    get_product,
)

from billing.subscription import (
    SubscriptionManager,
    get_subscription_manager,
)


# ============================================================
# HELPERS
# ============================================================


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# EXCEPTIONS
# ============================================================


class FulfillmentError(Exception):
    """Base fulfillment exception."""


class FulfillmentValidationError(
    FulfillmentError
):
    """Invalid fulfillment request."""


class FulfillmentAlreadyCompleted(
    FulfillmentError
):
    """Order has already been fulfilled."""


class FulfillmentNotAllowed(
    FulfillmentError
):
    """Order cannot currently be fulfilled."""


class FulfillmentProductError(
    FulfillmentError
):
    """Product configuration problem."""


# ============================================================
# FULFILLMENT STATUS
# ============================================================


class FulfillmentStatus(str, Enum):

    PENDING = "pending"

    PROCESSING = "processing"

    COMPLETED = "completed"

    FAILED = "failed"

    SKIPPED = "skipped"


# ============================================================
# FULFILLMENT RECORD
# ============================================================


@dataclass
class FulfillmentRecord:
    """
    Persistent-style record describing fulfillment.

    The current implementation uses an in-memory store.
    It is intentionally designed so it can later be moved
    to the database without changing the public API.
    """

    fulfillment_id: str

    order_id: str

    user_id: str

    status: FulfillmentStatus = (
        FulfillmentStatus.PENDING
    )

    completed_at: Optional[
        datetime
    ] = None

    failed_at: Optional[
        datetime
    ] = None

    error: Optional[str] = None

    delivered_items: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=_utcnow
    )

    updated_at: datetime = field(
        default_factory=_utcnow
    )

    def mark_processing(self) -> None:

        self.status = (
            FulfillmentStatus.PROCESSING
        )

        self.error = None
        self.updated_at = _utcnow()

    def mark_completed(
        self,
        delivered_items: Optional[
            List[str]
        ] = None,
    ) -> None:

        self.status = (
            FulfillmentStatus.COMPLETED
        )

        self.completed_at = _utcnow()

        if delivered_items:
            self.delivered_items = list(
                delivered_items
            )

        self.updated_at = _utcnow()

    def mark_failed(
        self,
        error: str,
    ) -> None:

        self.status = (
            FulfillmentStatus.FAILED
        )

        self.failed_at = _utcnow()
        self.error = str(error)
        self.updated_at = _utcnow()

    def to_dict(self) -> dict:

        return {
            "fulfillment_id": (
                self.fulfillment_id
            ),
            "order_id": self.order_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at
                else None
            ),
            "failed_at": (
                self.failed_at.isoformat()
                if self.failed_at
                else None
            ),
            "error": self.error,
            "delivered_items": list(
                self.delivered_items
            ),
            "metadata": deepcopy(
                self.metadata
            ),
            "created_at": (
                self.created_at.isoformat()
            ),
            "updated_at": (
                self.updated_at.isoformat()
            ),
        }


# ============================================================
# FULFILLMENT MANAGER
# ============================================================


class FulfillmentManager:
    """
    Coordinates post-payment fulfillment.

    Important:
    Fulfillment is idempotent.

    If Telegram/payment callbacks are delivered twice,
    the same order must not grant credits or subscriptions
    twice.
    """

    def __init__(
        self,
        subscription_manager: Optional[
            SubscriptionManager
        ] = None,
        credit_manager: Optional[
            CreditManager
        ] = None,
    ) -> None:

        self.subscription_manager = (
            subscription_manager
            or get_subscription_manager()
        )

        self.credit_manager = (
            credit_manager
            or get_credit_manager()
        )

        self._records: Dict[
            str,
            FulfillmentRecord,
        ] = {}

        self._lock = RLock()

    # ========================================================
    # RECORD MANAGEMENT
    # ========================================================

    def _get_record(
        self,
        order_id: str,
    ) -> Optional[FulfillmentRecord]:

        return self._records.get(
            order_id
        )

    def get_record(
        self,
        order_id: str,
    ) -> Optional[FulfillmentRecord]:

        with self._lock:

            record = self._get_record(
                order_id
            )

            if record is None:
                return None

            return deepcopy(record)

    def _create_record(
        self,
        order: Order,
    ) -> FulfillmentRecord:

        fulfillment_id = (
            f"ful_{order.order_id}"
        )

        record = FulfillmentRecord(
            fulfillment_id=fulfillment_id,
            order_id=order.order_id,
            user_id=order.user_id,
        )

        self._records[
            order.order_id
        ] = record

        return record

    # ========================================================
    # VALIDATION
    # ========================================================

    def _validate_order(
        self,
        order: Order,
    ) -> None:

        if not order.order_id:
            raise FulfillmentValidationError(
                "Order ID is required."
            )

        if not order.user_id:
            raise FulfillmentValidationError(
                "User ID is required."
            )

        if not order.items:
            raise FulfillmentValidationError(
                "Order contains no items."
            )

        if order.status not in {
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
        }:

            raise FulfillmentNotAllowed(
                "Only paid or processing orders "
                "can be fulfilled."
            )

    # ========================================================
    # MAIN ENTRY
    # ========================================================

    def fulfill(
        self,
        order: Order,
    ) -> FulfillmentRecord:

        with self._lock:

            self._validate_order(
                order
            )

            existing = self._get_record(
                order.order_id
            )

            if existing is not None:

                if (
                    existing.status
                    == FulfillmentStatus.COMPLETED
                ):
                    return deepcopy(
                        existing
                    )

                if (
                    existing.status
                    == FulfillmentStatus.PROCESSING
                ):
                    raise FulfillmentNotAllowed(
                        "Fulfillment is already processing."
                    )

            if existing is None:

                record = self._create_record(
                    order
                )

            else:

                record = existing

            record.mark_processing()

            delivered: List[str] = []

            try:

                for item in order.items:

                    result = self._fulfill_item(
                        order,
                        item,
                    )

                    if result:

                        delivered.extend(
                            result
                        )

                record.mark_completed(
                    delivered_items=delivered
                )

                return deepcopy(
                    record
                )

            except Exception as exc:

                record.mark_failed(
                    str(exc)
                )

                raise

    # ========================================================
    # ITEM DISPATCH
    # ========================================================

    def _fulfill_item(
        self,
        order: Order,
        item: OrderItem,
    ) -> List[str]:

        product = get_product(
            item.product_code
        )

        product_type = None

        if product is not None:

            product_type = (
                product.product_type
            )

        elif item.metadata.get(
            "product_type"
        ):

            product_type = ProductType(
                item.metadata[
                    "product_type"
                ]
            )

        if product_type is None:

            raise FulfillmentProductError(
                f"Unknown product: "
                f"{item.product_code}"
            )

        if (
            product_type
            == ProductType.SUBSCRIPTION
        ):

            return self._fulfill_subscription(
                order,
                item,
            )

        if (
            product_type
            == ProductType.CREDIT_PACK
        ):

            return self._fulfill_credits(
                order,
                item,
                ai=False,
            )

        if (
            product_type
            == ProductType.AI_CREDIT_PACK
        ):

            return self._fulfill_credits(
                order,
                item,
                ai=True,
            )

        if (
            product_type
            == ProductType.PDF_REPORT
        ):

            return self._fulfill_report(
                order,
                item,
                "pdf",
            )

        if (
            product_type
            == ProductType.EXCEL_REPORT
        ):

            return self._fulfill_report(
                order,
                item,
                "excel",
            )

        if (
            product_type
            == ProductType.API_ACCESS
        ):

            return self._fulfill_api(
                order,
                item,
            )

        if (
            product_type
            == ProductType.CUSTOM_SERVICE
        ):

            return self._fulfill_custom(
                order,
                item,
            )

        raise FulfillmentProductError(
            f"Unsupported product type: "
            f"{product_type}"
        )

    # ========================================================
    # SUBSCRIPTION
    # ========================================================

    def _fulfill_subscription(
        self,
        order: Order,
        item: OrderItem,
    ) -> List[str]:

        metadata = dict(
            item.metadata
        )

        plan_code = (
            metadata.get(
                "plan_code"
            )
        )

        if not plan_code:

            product = get_product(
                item.product_code
            )

            if product:

                plan_code = (
                    product.plan_code
                )

        if not plan_code:

            raise FulfillmentProductError(
                "Subscription product has no "
                "plan_code."
            )

        duration_days = (
            metadata.get(
                "duration_days"
            )
        )

        if duration_days is None:

            product = get_product(
                item.product_code
            )

            if product:

                duration_days = (
                    product.duration_days
                )

        if duration_days is None:

            duration_days = 30

        existing_subscription = (
            self.subscription_manager
            .get_subscription(
                order.user_id
            )
        )

        payment_reference = (
            order.payment_reference
            or order.payment_id
        )

        # ----------------------------------------------------
        # Idempotency
        # ----------------------------------------------------

        if existing_subscription:

            metadata_ref = (
                existing_subscription.metadata.get(
                    "last_fulfilled_order_id"
                )
            )

            if (
                metadata_ref
                == order.order_id
            ):

                return [
                    f"subscription:{plan_code}"
                ]

        subscription = (
            self.subscription_manager.activate(
                user_id=order.user_id,
                plan_code=plan_code,
                duration_days=int(
                    duration_days
                ),
                payment_reference=(
                    payment_reference
                ),
            )
        )

        subscription.metadata[
            "last_fulfilled_order_id"
        ] = order.order_id

        subscription.metadata[
            "fulfillment_time"
        ] = _utcnow().isoformat()

        return [
            f"subscription:{plan_code}"
        ]

    # ========================================================
    # CREDITS
    # ========================================================

    def _fulfill_credits(
        self,
        order: Order,
        item: OrderItem,
        ai: bool = False,
    ) -> List[str]:

        credits = item.metadata.get(
            "credits"
        )

        if credits is None:

            product = get_product(
                item.product_code
            )

            if product:

                credits = product.credits

        if credits is None:

            raise FulfillmentProductError(
                "Credit product has no "
                "credit amount."
            )

        credits = int(
            credits
        )

        if credits <= 0:

            raise FulfillmentProductError(
                "Credit amount must be positive."
            )

        # ----------------------------------------------------
        # Idempotency
        # ----------------------------------------------------

        marker = (
            f"last_fulfilled_order:"
            f"{order.order_id}"
        )

        existing = (
            self.credit_manager
            .get_balance(
                order.user_id
            )
        )

        if marker in existing.metadata:

            return [
                (
                    "ai_credits:"
                    if ai
                    else "credits:"
                )
                + str(credits)
            ]

        if ai:

            # AI credits use the same balance
            # infrastructure for now.
            transaction = (
                self.credit_manager
                .purchase(
                    user_id=order.user_id,
                    amount=credits,
                    reference=order.order_id,
                    metadata={
                        "credit_type": "ai",
                    },
                )
            )

        else:

            transaction = (
                self.credit_manager
                .purchase(
                    user_id=order.user_id,
                    amount=credits,
                    reference=order.order_id,
                    metadata={
                        "credit_type": "general",
                    },
                )
            )

        balance = (
            self.credit_manager
            .get_balance(
                order.user_id
            )
        )

        balance.metadata[
            marker
        ] = True

        balance.metadata[
            "last_credit_transaction"
        ] = transaction.transaction_id

        return [
            (
                "ai_credits:"
                if ai
                else "credits:"
            )
            + str(credits)
        ]

    # ========================================================
    # REPORT
    # ========================================================

    def _fulfill_report(
        self,
        order: Order,
        item: OrderItem,
        report_format: str,
    ) -> List[str]:

        """
        Report fulfillment currently grants the
        entitlement/record only.

        Actual report generation belongs to reports/
        and will consume this entitlement later.
        """

        key = (
            f"paid_report:{report_format}:"
            f"{order.order_id}"
        )

        order.metadata.setdefault(
            "fulfilled_products",
            [],
        )

        if key not in order.metadata[
            "fulfilled_products"
        ]:

            order.metadata[
                "fulfilled_products"
            ].append(key)

        return [
            f"report:{report_format}"
        ]

    # ========================================================
    # API
    # ========================================================

    def _fulfill_api(
        self,
        order: Order,
        item: OrderItem,
    ) -> List[str]:

        order.metadata.setdefault(
            "api_access",
            {},
        )

        access = order.metadata[
            "api_access"
        ]

        access[
            "granted"
        ] = True

        access[
            "granted_order_id"
        ] = order.order_id

        access[
            "granted_at"
        ] = _utcnow().isoformat()

        return [
            "api_access"
        ]

    # ========================================================
    # CUSTOM
    # ========================================================

    def _fulfill_custom(
        self,
        order: Order,
        item: OrderItem,
    ) -> List[str]:

        order.metadata.setdefault(
            "custom_products",
            [],
        )

        order.metadata[
            "custom_products"
        ].append(
            {
                "product_code": (
                    item.product_code
                ),
                "order_id": (
                    order.order_id
                ),
                "fulfilled_at": (
                    _utcnow().isoformat()
                ),
            }
        )

        return [
            f"custom:{item.product_code}"
        ]

    # ========================================================
    # LIST / SUMMARY
    # ========================================================

    def list_records(
        self,
        user_id: Optional[str] = None,
    ) -> List[FulfillmentRecord]:

        with self._lock:

            records = list(
                self._records.values()
            )

            if user_id is not None:

                records = [
                    record
                    for record in records
                    if record.user_id
                    == str(user_id)
                ]

            return deepcopy(
                records
            )

    def summary(
        self,
        user_id: Optional[str] = None,
    ) -> dict:

        records = self.list_records(
            user_id=user_id
        )

        return {
            "total": len(records),
            "pending": sum(
                record.status
                == FulfillmentStatus.PENDING
                for record in records
            ),
            "processing": sum(
                record.status
                == FulfillmentStatus.PROCESSING
                for record in records
            ),
            "completed": sum(
                record.status
                == FulfillmentStatus.COMPLETED
                for record in records
            ),
            "failed": sum(
                record.status
                == FulfillmentStatus.FAILED
                for record in records
            ),
        }

    def clear(self) -> None:

        with self._lock:

            self._records.clear()


# ============================================================
# GLOBAL MANAGER
# ============================================================


_default_fulfillment_manager: Optional[
    FulfillmentManager
] = None


def get_fulfillment_manager(
) -> FulfillmentManager:

    global _default_fulfillment_manager

    if (
        _default_fulfillment_manager
        is None
    ):

        _default_fulfillment_manager = (
            FulfillmentManager()
        )

    return (
        _default_fulfillment_manager
    )


def set_fulfillment_manager(
    manager: FulfillmentManager,
) -> None:

    global _default_fulfillment_manager

    _default_fulfillment_manager = (
        manager
    )


# ============================================================
# CONVENIENCE
# ============================================================


def fulfill_order(
    order: Order,
) -> FulfillmentRecord:

    return (
        get_fulfillment_manager()
        .fulfill(order)
    )


def get_fulfillment_record(
    order_id: str,
) -> Optional[FulfillmentRecord]:

    return (
        get_fulfillment_manager()
        .get_record(order_id)
    )


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "FulfillmentError",
    "FulfillmentValidationError",
    "FulfillmentAlreadyCompleted",
    "FulfillmentNotAllowed",
    "FulfillmentProductError",
    "FulfillmentStatus",
    "FulfillmentRecord",
    "FulfillmentManager",
    "get_fulfillment_manager",
    "set_fulfillment_manager",
    "fulfill_order",
    "get_fulfillment_record",
]
