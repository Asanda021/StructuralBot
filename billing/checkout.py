"""
StructuralBot - Checkout

Commercial checkout orchestration.

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
    Subscription / Credits / Product delivery

Responsibilities:
- Create checkout orders
- Create payment requests
- Attach payments to orders
- Verify payments
- Fulfill successful purchases
- Activate subscriptions
- Add purchased credits
- Complete orders

Payment gateway implementation remains inside billing.gateway.
Product-specific UI remains inside Telegram handlers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from billing.gateway import (
    PaymentManager,
    PaymentRequest,
    PaymentResult,
    PaymentStatus,
    get_payment_manager,
)

from billing.orders import (
    Order,
    OrderItem,
    OrderManager,
    OrderStatus,
    OrderType,
    get_order_manager,
)

from billing.subscription import (
    Subscription,
    SubscriptionManager,
    get_subscription_manager,
)

from billing.credits import (
    CreditManager,
    get_credit_manager,
)


# ============================================================
# CHECKOUT ERRORS
# ============================================================


class CheckoutError(Exception):
    """Base checkout exception."""


class CheckoutValidationError(
    CheckoutError
):
    """Invalid checkout request."""


class CheckoutPaymentError(
    CheckoutError
):
    """Payment-related checkout failure."""


class CheckoutFulfillmentError(
    CheckoutError
):
    """Product fulfillment failure."""


# ============================================================
# CHECKOUT REQUEST
# ============================================================


@dataclass
class CheckoutRequest:
    """
    Input required to create a commercial checkout.
    """

    user_id: str

    order_type: OrderType | str

    items: List[OrderItem]

    currency: str = "IRR"

    description: str = ""

    callback_url: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# CHECKOUT RESULT
# ============================================================


@dataclass
class CheckoutResult:
    """
    Unified checkout response.
    """

    success: bool

    order: Optional[Order] = None

    payment: Optional[PaymentResult] = None

    subscription: Optional[
        Subscription
    ] = None

    credits_added: int = 0

    message: str = ""

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict:

        return {
            "success": self.success,
            "order": (
                self.order.to_dict()
                if self.order
                else None
            ),
            "payment": (
                self.payment.to_dict()
                if self.payment
                else None
            ),
            "subscription": (
                self.subscription.to_dict()
                if self.subscription
                else None
            ),
            "credits_added": (
                self.credits_added
            ),
            "message": self.message,
            "error": self.error,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# CHECKOUT MANAGER
# ============================================================


class CheckoutManager:
    """
    Coordinates commercial checkout.

    It intentionally depends on abstractions from:
        - orders
        - gateway
        - subscription
        - credits
    """

    def __init__(
        self,
        *,
        order_manager: Optional[
            OrderManager
        ] = None,
        payment_manager: Optional[
            PaymentManager
        ] = None,
        subscription_manager: Optional[
            SubscriptionManager
        ] = None,
        credit_manager: Optional[
            CreditManager
        ] = None,
    ) -> None:

        self.order_manager = (
            order_manager
            or get_order_manager()
        )

        self.payment_manager = (
            payment_manager
            or get_payment_manager()
        )

        self.subscription_manager = (
            subscription_manager
            or get_subscription_manager()
        )

        self.credit_manager = (
            credit_manager
            or get_credit_manager()
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def validate_request(
        request: CheckoutRequest,
    ) -> None:

        if not request.user_id:
            raise CheckoutValidationError(
                "user_id is required."
            )

        if not request.items:
            raise CheckoutValidationError(
                "At least one order item is required."
            )

        for item in request.items:

            if item.quantity <= 0:
                raise CheckoutValidationError(
                    "Item quantity must be positive."
                )

            if item.unit_price < 0:
                raise CheckoutValidationError(
                    "Item price cannot be negative."
                )

        total = sum(
            item.total_price
            for item in request.items
        )

        if total <= 0:
            raise CheckoutValidationError(
                "Checkout amount must be greater than zero."
            )

    # ========================================================
    # CREATE CHECKOUT
    # ========================================================

    def create_checkout(
        self,
        request: CheckoutRequest,
    ) -> CheckoutResult:

        self.validate_request(
            request
        )

        try:

            order = (
                self.order_manager.create_order(
                    user_id=request.user_id,
                    order_type=request.order_type,
                    items=request.items,
                    currency=request.currency,
                    description=request.description,
                    metadata=request.metadata,
                )
            )

            payment_request = PaymentRequest(
                user_id=request.user_id,
                amount=order.total_amount,
                currency=order.currency,
                description=(
                    order.description
                    or f"StructuralBot "
                    f"Order {order.order_id}"
                ),
                callback_url=(
                    request.callback_url
                ),
                order_id=order.order_id,
                metadata={
                    "order_id": order.order_id,
                    "order_type": (
                        order.order_type.value
                    ),
                    **dict(
                        request.metadata
                    ),
                },
            )

            payment = (
                self.payment_manager.create_payment(
                    payment_request
                )
            )

            self.order_manager.attach_payment(
                order.order_id,
                payment.payment_id,
            )

            return CheckoutResult(
                success=True,
                order=order,
                payment=payment,
                message=(
                    "Checkout created successfully."
                ),
            )

        except Exception as exc:

            return CheckoutResult(
                success=False,
                message=(
                    "Unable to create checkout."
                ),
                error=str(exc),
            )

    # ========================================================
    # VERIFY
    # ========================================================

    def verify_checkout(
        self,
        order_id: str,
    ) -> CheckoutResult:

        try:

            order = (
                self.order_manager.get_order(
                    order_id
                )
            )

            if not order.payment_id:
                raise CheckoutPaymentError(
                    "Order has no payment attached."
                )

            payment = (
                self.payment_manager.verify_payment(
                    order.payment_id
                )
            )

            if payment.status != (
                PaymentStatus.SUCCESS
            ):

                return CheckoutResult(
                    success=False,
                    order=order,
                    payment=payment,
                    message=(
                        "Payment has not been "
                        "confirmed."
                    ),
                )

            self.order_manager.mark_paid(
                order.order_id,
                payment_id=payment.payment_id,
                payment_reference=(
                    payment.reference_id
                    or payment.authority
                ),
            )

            fulfillment = (
                self.fulfill_order(
                    order.order_id
                )
            )

            return fulfillment

        except Exception as exc:

            return CheckoutResult(
                success=False,
                message=(
                    "Payment verification failed."
                ),
                error=str(exc),
            )

    # ========================================================
    # FULFILLMENT
    # ========================================================

    def fulfill_order(
        self,
        order_id: str,
    ) -> CheckoutResult:

        try:

            order = (
                self.order_manager.get_order(
                    order_id
                )
            )

            if not order.is_paid:

                raise CheckoutFulfillmentError(
                    "Only paid orders can be fulfilled."
                )

            self.order_manager.mark_processing(
                order_id
            )

            subscription = None

            credits_added = 0

            if order.order_type == (
                OrderType.SUBSCRIPTION
            ):

                subscription = (
                    self._fulfill_subscription(
                        order
                    )
                )

            elif order.order_type in {
                OrderType.CREDIT,
                OrderType.AI_CREDITS,
            }:

                credits_added = (
                    self._fulfill_credits(
                        order
                    )
                )

            elif order.order_type in {
                OrderType.PDF_REPORT,
                OrderType.EXCEL_REPORT,
            }:

                self._mark_report_purchase(
                    order
                )

            elif order.order_type == (
                OrderType.API
            ):

                self._mark_api_purchase(
                    order
                )

            elif order.order_type == (
                OrderType.CUSTOM
            ):

                self._mark_custom_purchase(
                    order
                )

            self.order_manager.mark_completed(
                order_id
            )

            return CheckoutResult(
                success=True,
                order=order,
                subscription=subscription,
                credits_added=credits_added,
                message=(
                    "Order completed successfully."
                ),
            )

        except Exception as exc:

            return CheckoutResult(
                success=False,
                message=(
                    "Order fulfillment failed."
                ),
                error=str(exc),
            )

    # ========================================================
    # SUBSCRIPTION FULFILLMENT
    # ========================================================

    def _fulfill_subscription(
        self,
        order: Order,
    ) -> Subscription:

        plan_code = (
            order.metadata.get(
                "plan_code"
            )
        )

        if not plan_code:

            for item in order.items:

                candidate = (
                    item.metadata.get(
                        "plan_code"
                    )
                )

                if candidate:
                    plan_code = candidate
                    break

        if not plan_code:

            raise CheckoutFulfillmentError(
                "Subscription order does not "
                "contain plan_code."
            )

        duration_days = (
            order.metadata.get(
                "duration_days"
            )
        )

        if duration_days is None:

            for item in order.items:

                duration_days = (
                    item.metadata.get(
                        "duration_days"
                    )
                )

                if duration_days is not None:
                    break

        subscription = (
            self.subscription_manager.activate(
                user_id=order.user_id,
                plan_code=plan_code,
                duration_days=duration_days,
                payment_reference=(
                    order.payment_reference
                ),
                metadata={
                    "order_id": order.order_id,
                    "payment_id": (
                        order.payment_id
                    ),
                    "source": "checkout",
                },
            )
        )

        return subscription

    # ========================================================
    # CREDIT FULFILLMENT
    # ========================================================

    def _fulfill_credits(
        self,
        order: Order,
    ) -> int:

        total_credits = 0

        for item in order.items:

            credits = item.metadata.get(
                "credits"
            )

            if credits is None:

                credits = item.metadata.get(
                    "credit_amount"
                )

            if credits is None:

                continue

            try:
                credits_value = int(
                    credits
                )
            except (
                TypeError,
                ValueError,
            ):

                raise CheckoutFulfillmentError(
                    "Invalid credit amount."
                )

            if credits_value <= 0:
                continue

            amount = (
                credits_value
                * item.quantity
            )

            self.credit_manager.purchase(
                user_id=order.user_id,
                amount=amount,
                reference=(
                    order.order_id
                ),
                metadata={
                    "order_id": (
                        order.order_id
                    ),
                    "payment_id": (
                        order.payment_id
                    ),
                    "product_code": (
                        item.product_code
                    ),
                },
            )

            total_credits += amount

        if total_credits <= 0:

            raise CheckoutFulfillmentError(
                "Credit order contains no "
                "valid credit amount."
            )

        return total_credits

    # ========================================================
    # REPORT PURCHASE
    # ========================================================

    @staticmethod
    def _mark_report_purchase(
        order: Order,
    ) -> None:

        order.metadata[
            "fulfilled"
        ] = True

        order.metadata[
            "fulfillment_type"
        ] = "report"

        order.metadata[
            "requires_generation"
        ] = True

    # ========================================================
    # API PURCHASE
    # ========================================================

    @staticmethod
    def _mark_api_purchase(
        order: Order,
    ) -> None:

        order.metadata[
            "fulfilled"
        ] = True

        order.metadata[
            "fulfillment_type"
        ] = "api_access"

    # ========================================================
    # CUSTOM PURCHASE
    # ========================================================

    @staticmethod
    def _mark_custom_purchase(
        order: Order,
    ) -> None:

        order.metadata[
            "fulfilled"
        ] = True

        order.metadata[
            "fulfillment_type"
        ] = "custom"

    # ========================================================
    # DIRECT SUBSCRIPTION CHECKOUT
    # ========================================================

    def create_subscription_checkout(
        self,
        *,
        user_id: str,
        plan_code: str,
        price: int,
        currency: str = "IRR",
        duration_days: Optional[
            int
        ] = None,
        callback_url: Optional[
            str
        ] = None,
    ) -> CheckoutResult:

        item_metadata = {
            "plan_code": plan_code,
        }

        if duration_days is not None:

            item_metadata[
                "duration_days"
            ] = duration_days

        item = OrderItem(
            item_id=(
                f"plan_{plan_code}"
            ),
            product_code=(
                f"subscription_{plan_code}"
            ),
            name=(
                f"StructuralBot "
                f"{plan_code} Subscription"
            ),
            quantity=1,
            unit_price=price,
            currency=currency,
            metadata=item_metadata,
        )

        request = CheckoutRequest(
            user_id=user_id,
            order_type=(
                OrderType.SUBSCRIPTION
            ),
            items=[item],
            currency=currency,
            description=(
                f"StructuralBot "
                f"{plan_code} subscription"
            ),
            callback_url=callback_url,
            metadata={
                "plan_code": plan_code,
                "duration_days": (
                    duration_days
                ),
            },
        )

        return self.create_checkout(
            request
        )

    # ========================================================
    # DIRECT CREDIT CHECKOUT
    # ========================================================

    def create_credit_checkout(
        self,
        *,
        user_id: str,
        credits: int,
        price: int,
        currency: str = "IRR",
        product_code: str = "credit_pack",
        callback_url: Optional[
            str
        ] = None,
    ) -> CheckoutResult:

        if credits <= 0:
            raise CheckoutValidationError(
                "credits must be positive."
            )

        item = OrderItem(
            item_id=(
                f"credits_{credits}"
            ),
            product_code=product_code,
            name=(
                f"StructuralBot "
                f"{credits} Credits"
            ),
            quantity=1,
            unit_price=price,
            currency=currency,
            metadata={
                "credits": credits,
            },
        )

        request = CheckoutRequest(
            user_id=user_id,
            order_type=OrderType.CREDIT,
            items=[item],
            currency=currency,
            description=(
                f"StructuralBot "
                f"{credits} credits"
            ),
            callback_url=callback_url,
            metadata={
                "credits": credits,
                "product_code": product_code,
            },
        )

        return self.create_checkout(
            request
        )


# ============================================================
# GLOBAL MANAGER
# ============================================================


_default_checkout_manager: Optional[
    CheckoutManager
] = None


def get_checkout_manager() -> CheckoutManager:

    global _default_checkout_manager

    if _default_checkout_manager is None:

        _default_checkout_manager = (
            CheckoutManager()
        )

    return _default_checkout_manager


def set_checkout_manager(
    manager: CheckoutManager,
) -> None:

    global _default_checkout_manager

    _default_checkout_manager = manager


# ============================================================
# CONVENIENCE HELPERS
# ============================================================


def create_checkout(
    request: CheckoutRequest,
) -> CheckoutResult:

    return get_checkout_manager().create_checkout(
        request
    )


def verify_checkout(
    order_id: str,
) -> CheckoutResult:

    return get_checkout_manager().verify_checkout(
        order_id
    )


def fulfill_order(
    order_id: str,
) -> CheckoutResult:

    return get_checkout_manager().fulfill_order(
        order_id
    )


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "CheckoutError",
    "CheckoutValidationError",
    "CheckoutPaymentError",
    "CheckoutFulfillmentError",
    "CheckoutRequest",
    "CheckoutResult",
    "CheckoutManager",
    "get_checkout_manager",
    "set_checkout_manager",
    "create_checkout",
    "verify_checkout",
    "fulfill_order",
]
