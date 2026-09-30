"""
StructuralBot - Billing Service

High-level billing facade.

Responsibilities:
- Unified billing API
- Products
- Orders
- Payments
- Checkout
- Fulfillment
- Invoices
- Subscriptions
- Credits
- Entitlements

Handlers should prefer this service instead of directly
coordinating multiple billing modules.

Architecture:

Telegram Handler
        |
        v
BillingService
        |
        +--> Products
        +--> Orders
        +--> Checkout
        +--> Gateway
        +--> Fulfillment
        +--> Invoice
        +--> Subscription
        +--> Credits
        +--> Entitlements
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from decimal import Decimal
from threading import RLock
from typing import Any, Dict, List, Optional

from billing.checkout import (
    CheckoutManager,
    CheckoutRequest,
    CheckoutResult,
    get_checkout_manager,
)

from billing.credits import (
    CreditBalance,
    CreditManager,
    get_credit_manager,
)

from billing.entitlements import (
    EntitlementManager,
    get_entitlement_manager,
)

from billing.fulfillment import (
    FulfillmentManager,
    FulfillmentRecord,
    get_fulfillment_manager,
)

from billing.gateway import (
    PaymentManager,
    PaymentResult,
    get_payment_manager,
)

from billing.invoice import (
    Invoice,
    InvoiceManager,
    InvoiceType,
    create_invoice_from_order,
    get_invoice_manager,
)

from billing.orders import (
    Order,
    OrderItem,
    OrderManager,
    OrderStatus,
    OrderType,
    get_order_manager,
)

from billing.plans import (
    Plan,
    get_all_plans,
    get_plan,
)

from billing.products import (
    Product,
    ProductCatalog,
    ProductType,
    get_all_products,
    get_product,
    get_product_catalog,
)

from billing.subscription import (
    Subscription,
    SubscriptionManager,
    get_subscription_manager,
)


# ============================================================
# EXCEPTIONS
# ============================================================


class BillingServiceError(Exception):
    """Base billing service exception."""


class BillingValidationError(
    BillingServiceError
):
    """Invalid billing request."""


class BillingProductError(
    BillingServiceError
):
    """Invalid or unavailable product."""


class BillingOrderError(
    BillingServiceError
):
    """Order-related billing error."""


class BillingPaymentError(
    BillingServiceError
):
    """Payment-related billing error."""


class BillingFulfillmentError(
    BillingServiceError
):
    """Fulfillment-related billing error."""


# ============================================================
# REQUEST MODELS
# ============================================================


@dataclass
class BillingCheckoutItem:
    """
    High-level checkout item.

    Handlers do not need to know the internal OrderItem
    representation.
    """

    product_code: str

    quantity: int = 1

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:

        self.product_code = str(
            self.product_code
        )

        self.quantity = int(
            self.quantity
        )

        if not self.product_code:

            raise BillingValidationError(
                "Product code is required."
            )

        if self.quantity <= 0:

            raise BillingValidationError(
                "Quantity must be greater than zero."
            )


@dataclass
class BillingCheckout:
    """
    High-level checkout request.
    """

    user_id: str

    items: List[
        BillingCheckoutItem
    ]

    currency: str = "IRR"

    customer_name: Optional[str] = None

    customer_phone: Optional[str] = None

    customer_email: Optional[str] = None

    description: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class BillingCheckoutResponse:
    """
    Unified checkout response.
    """

    success: bool

    order: Optional[Order] = None

    checkout: Optional[
        CheckoutResult
    ] = None

    invoice: Optional[
        Invoice
    ] = None

    payment: Optional[
        PaymentResult
    ] = None

    fulfillment: Optional[
        FulfillmentRecord
    ] = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# BILLING SERVICE
# ============================================================


class BillingService:
    """
    Main billing facade.

    This class is intentionally thin.

    Business rules remain inside the dedicated billing
    modules. The service only coordinates them.
    """

    def __init__(
        self,
        catalog: Optional[
            ProductCatalog
        ] = None,
        order_manager: Optional[
            OrderManager
        ] = None,
        payment_manager: Optional[
            PaymentManager
        ] = None,
        checkout_manager: Optional[
            CheckoutManager
        ] = None,
        fulfillment_manager: Optional[
            FulfillmentManager
        ] = None,
        invoice_manager: Optional[
            InvoiceManager
        ] = None,
        subscription_manager: Optional[
            SubscriptionManager
        ] = None,
        credit_manager: Optional[
            CreditManager
        ] = None,
        entitlement_manager: Optional[
            EntitlementManager
        ] = None,
    ) -> None:

        self.catalog = (
            catalog
            or get_product_catalog()
        )

        self.orders = (
            order_manager
            or get_order_manager()
        )

        self.payments = (
            payment_manager
            or get_payment_manager()
        )

        self.checkout = (
            checkout_manager
            or get_checkout_manager()
        )

        self.fulfillment = (
            fulfillment_manager
            or get_fulfillment_manager()
        )

        self.invoices = (
            invoice_manager
            or get_invoice_manager()
        )

        self.subscriptions = (
            subscription_manager
            or get_subscription_manager()
        )

        self.credits = (
            credit_manager
            or get_credit_manager()
        )

        self.entitlements = (
            entitlement_manager
            or get_entitlement_manager()
        )

        self._lock = RLock()

    # ========================================================
    # PRODUCTS
    # ========================================================

    def get_product(
        self,
        product_code: str,
    ) -> Optional[Product]:

        return get_product(
            product_code
        )

    def require_product(
        self,
        product_code: str,
    ) -> Product:

        product = self.get_product(
            product_code
        )

        if product is None:

            raise BillingProductError(
                f"Product not found: "
                f"{product_code}"
            )

        if not product.is_available():

            raise BillingProductError(
                f"Product is not available: "
                f"{product_code}"
            )

        return product

    def list_products(
        self,
        product_type: Optional[
            ProductType
        ] = None,
    ) -> List[Product]:

        if product_type is None:

            return get_all_products()

        return self.catalog.by_type(
            product_type
        )

    def list_available_products(
        self,
        product_type: Optional[
            ProductType
        ] = None,
    ) -> List[Product]:

        products = (
            self.catalog.available()
        )

        if product_type is not None:

            products = [
                product
                for product in products
                if product.product_type
                == product_type
            ]

        return products

    # ========================================================
    # PLANS
    # ========================================================

    def get_plan(
        self,
        plan_code: str,
    ) -> Plan:

        try:

            return get_plan(
                plan_code
            )

        except Exception as exc:

            raise BillingValidationError(
                str(exc)
            ) from exc

    def list_plans(self) -> List[Plan]:

        return get_all_plans()

    # ========================================================
    # CHECKOUT
    # ========================================================

    def prepare_checkout(
        self,
        request: BillingCheckout,
    ) -> List[OrderItem]:

        if not request.user_id:

            raise BillingValidationError(
                "User ID is required."
            )

        if not request.items:

            raise BillingValidationError(
                "Checkout must contain "
                "at least one item."
            )

        order_items: List[
            OrderItem
        ] = []

        for item in request.items:

            product = self.require_product(
                item.product_code
            )

            unit_price = Decimal(
                str(product.price)
            )

            order_item = OrderItem(
                product_code=(
                    product.code
                ),
                quantity=item.quantity,
                unit_price=unit_price,
                description=(
                    product.description
                    or product.name
                ),
                metadata={
                    **deepcopy(
                        product.metadata
                    ),
                    **deepcopy(
                        item.metadata
                    ),
                    "product_type": (
                        product.product_type.value
                    ),
                },
            )

            order_items.append(
                order_item
            )

        return order_items

    def create_checkout(
        self,
        request: BillingCheckout,
    ) -> BillingCheckoutResponse:

        with self._lock:

            try:

                order_items = (
                    self.prepare_checkout(
                        request
                    )
                )

                checkout_request = (
                    self._build_checkout_request(
                        request,
                        order_items,
                    )
                )

                result = (
                    self.checkout
                    .create_checkout(
                        checkout_request
                    )
                )

                order = self._get_order_from_result(
                    result
                )

                invoice = None

                if order is not None:

                    invoice = (
                        self._ensure_invoice(
                            order
                        )
                    )

                return (
                    BillingCheckoutResponse(
                        success=True,
                        order=order,
                        checkout=result,
                        invoice=invoice,
                        metadata={
                            "stage": (
                                "checkout_created"
                            ),
                        },
                    )
                )

            except Exception as exc:

                return (
                    BillingCheckoutResponse(
                        success=False,
                        error=str(exc),
                    )
                )

    def _build_checkout_request(
        self,
        request: BillingCheckout,
        order_items: List[OrderItem],
    ) -> CheckoutRequest:

        """
        Build the internal checkout request.

        The exact constructor is intentionally isolated here
        so future CheckoutManager changes affect only this
        adapter.
        """

        return CheckoutRequest(
            user_id=request.user_id,
            items=order_items,
            currency=request.currency,
            customer_name=(
                request.customer_name
            ),
            customer_phone=(
                request.customer_phone
            ),
            customer_email=(
                request.customer_email
            ),
            description=(
                request.description
            ),
            metadata=deepcopy(
                request.metadata
            ),
        )

    def _get_order_from_result(
        self,
        result: CheckoutResult,
    ) -> Optional[Order]:

        order_id = getattr(
            result,
            "order_id",
            None,
        )

        if not order_id:

            return None

        try:

            return self.orders.get(
                order_id
            )

        except Exception:

            return None

    # ========================================================
    # PAYMENT VERIFICATION
    # ========================================================

    def verify_checkout(
        self,
        checkout_id: str,
    ) -> BillingCheckoutResponse:

        with self._lock:

            try:

                result = (
                    self.checkout
                    .verify_checkout(
                        checkout_id
                    )
                )

                order = self._get_order_from_result(
                    result
                )

                invoice = None

                if order is not None:

                    invoice = (
                        self._ensure_invoice(
                            order
                        )
                    )

                    if (
                        getattr(
                            order,
                            "status",
                            None,
                        )
                        == OrderStatus.PAID
                    ):

                        payment_id = getattr(
                            result,
                            "payment_id",
                            None,
                        )

                        payment_reference = getattr(
                            result,
                            "payment_reference",
                            None,
                        )

                        if (
                            invoice.status.value
                            == "issued"
                        ):

                            invoice = (
                                self.invoices
                                .mark_paid(
                                    invoice.invoice_id,
                                    payment_id=(
                                        payment_id
                                    ),
                                    payment_reference=(
                                        payment_reference
                                    ),
                                )
                            )

                return (
                    BillingCheckoutResponse(
                        success=True,
                        order=order,
                        checkout=result,
                        invoice=invoice,
                        metadata={
                            "stage": (
                                "checkout_verified"
                            ),
                        },
                    )
                )

            except Exception as exc:

                return (
                    BillingCheckoutResponse(
                        success=False,
                        error=str(exc),
                    )
                )

    # ========================================================
    # FULFILLMENT
    # ========================================================

    def fulfill_order(
        self,
        order_id: str,
    ) -> BillingCheckoutResponse:

        with self._lock:

            try:

                order = self.orders.get(
                    order_id
                )

                record = (
                    self.fulfillment
                    .fulfill(order)
                )

                invoice = (
                    self._ensure_invoice(
                        order
                    )
                )

                if (
                    invoice.status.value
                    == "draft"
                ):

                    invoice = (
                        self.invoices
                        .issue(
                            invoice.invoice_id
                        )
                    )

                if (
                    order.status
                    == OrderStatus.PAID
                    and invoice.status.value
                    == "issued"
                ):

                    payment_id = getattr(
                        order,
                        "payment_id",
                        None,
                    )

                    payment_reference = (
                        getattr(
                            order,
                            "payment_reference",
                            None,
                        )
                    )

                    invoice = (
                        self.invoices
                        .mark_paid(
                            invoice.invoice_id,
                            payment_id=(
                                payment_id
                            ),
                            payment_reference=(
                                payment_reference
                            ),
                        )
                    )

                return (
                    BillingCheckoutResponse(
                        success=True,
                        order=order,
                        invoice=invoice,
                        fulfillment=record,
                        metadata={
                            "stage": (
                                "fulfilled"
                            ),
                        },
                    )
                )

            except Exception as exc:

                return (
                    BillingCheckoutResponse(
                        success=False,
                        error=str(exc),
                    )
                )

    # ========================================================
    # INVOICES
    # ========================================================

    def _ensure_invoice(
        self,
        order: Order,
    ) -> Invoice:

        existing = (
            self.invoices
            .get_by_order(
                order.order_id
            )
        )

        if existing is not None:

            return existing

        invoice_type = (
            self._detect_invoice_type(
                order
            )
        )

        invoice = (
            create_invoice_from_order(
                order=order,
                invoice_type=invoice_type,
                currency=(
                    getattr(
                        order,
                        "currency",
                        None,
                    )
                    or "IRR"
                ),
            )
        )

        return invoice

    def _detect_invoice_type(
        self,
        order: Order,
    ) -> InvoiceType:

        types = set()

        for item in order.items:

            product = self.get_product(
                item.product_code
            )

            if product is None:

                continue

            mapping = {
                ProductType.SUBSCRIPTION:
                    InvoiceType.SUBSCRIPTION,

                ProductType.CREDIT_PACK:
                    InvoiceType.CREDIT,

                ProductType.AI_CREDIT_PACK:
                    InvoiceType.AI_CREDIT,

                ProductType.PDF_REPORT:
                    InvoiceType.REPORT,

                ProductType.EXCEL_REPORT:
                    InvoiceType.REPORT,

                ProductType.API_ACCESS:
                    InvoiceType.API,

                ProductType.CUSTOM_SERVICE:
                    InvoiceType.CUSTOM,
            }

            invoice_type = mapping.get(
                product.product_type
            )

            if invoice_type:

                types.add(
                    invoice_type
                )

        if len(types) == 1:

            return next(
                iter(types)
            )

        return InvoiceType.MIXED

    def get_invoice(
        self,
        invoice_id: str,
    ) -> Invoice:

        return self.invoices.get(
            invoice_id
        )

    def get_order_invoice(
        self,
        order_id: str,
    ) -> Optional[Invoice]:

        return (
            self.invoices
            .get_by_order(
                order_id
            )
        )

    def list_user_invoices(
        self,
        user_id: str,
    ) -> List[Invoice]:

        return self.invoices.list_user(
            user_id
        )

    # ========================================================
    # ORDERS
    # ========================================================

    def get_order(
        self,
        order_id: str,
    ) -> Order:

        return self.orders.get(
            order_id
        )

    def list_user_orders(
        self,
        user_id: str,
    ) -> List[Order]:

        return self.orders.list_user(
            user_id
        )

    # ========================================================
    # SUBSCRIPTION
    # ========================================================

    def get_subscription(
        self,
        user_id: str,
    ) -> Optional[Subscription]:

        return (
            self.subscriptions
            .get_subscription(
                user_id
            )
        )

    def get_user_plan(
        self,
        user_id: str,
    ) -> Plan:

        subscription = (
            self.get_subscription(
                user_id
            )
        )

        if subscription is None:

            return self.get_plan(
                "free"
            )

        return subscription.get_plan()

    # ========================================================
    # CREDITS
    # ========================================================

    def get_credit_balance(
        self,
        user_id: str,
    ) -> CreditBalance:

        return self.credits.get_balance(
            user_id
        )

    # ========================================================
    # ENTITLEMENTS
    # ========================================================

    def get_entitlements(
        self,
        user_id: str,
    ) -> dict:

        return (
            self.entitlements
            .summary(
                user_id
            )
        )

    # ========================================================
    # USER SUMMARY
    # ========================================================

    def user_summary(
        self,
        user_id: str,
    ) -> dict:

        subscription = (
            self.get_subscription(
                user_id
            )
        )

        balance = (
            self.get_credit_balance(
                user_id
            )
        )

        orders = (
            self.list_user_orders(
                user_id
            )
        )

        invoices = (
            self.list_user_invoices(
                user_id
            )
        )

        fulfillment = (
            self.fulfillment
            .summary(
                user_id
            )
        )

        return {
            "user_id": str(
                user_id
            ),
            "plan": (
                subscription.plan_code
                if subscription
                else "free"
            ),
            "subscription": (
                subscription.to_dict()
                if subscription
                else None
            ),
            "credits": (
                balance.to_dict()
            ),
            "orders": {
                "total": len(orders),
                "paid": sum(
                    order.status
                    == OrderStatus.PAID
                    for order in orders
                ),
            },
            "invoices": {
                "total": len(invoices),
                "paid": sum(
                    invoice.status.value
                    == "paid"
                    for invoice
                    in invoices
                ),
            },
            "fulfillment": fulfillment,
        }

    # ========================================================
    # SYSTEM SUMMARY
    # ========================================================

    def system_summary(self) -> dict:

        return {
            "products": len(
                self.list_products()
            ),
            "plans": len(
                self.list_plans()
            ),
            "orders": len(
                self.orders.list_all()
            ),
            "payments": len(
                self.payments.list_payments()
            ),
            "invoices": len(
                self.invoices.list_all()
            ),
            "fulfillments": len(
                self.fulfillment.list_records()
            ),
        }


# ============================================================
# GLOBAL SERVICE
# ============================================================


_default_billing_service: Optional[
    BillingService
] = None


def get_billing_service() -> BillingService:

    global _default_billing_service

    if (
        _default_billing_service
        is None
    ):

        _default_billing_service = (
            BillingService()
        )

    return (
        _default_billing_service
    )


def set_billing_service(
    service: BillingService,
) -> None:

    global _default_billing_service

    _default_billing_service = service


# ============================================================
# CONVENIENCE HELPERS
# ============================================================


def create_billing_checkout(
    request: BillingCheckout,
) -> BillingCheckoutResponse:

    return (
        get_billing_service()
        .create_checkout(
            request
        )
    )


def verify_billing_checkout(
    checkout_id: str,
) -> BillingCheckoutResponse:

    return (
        get_billing_service()
        .verify_checkout(
            checkout_id
        )
    )


def fulfill_billing_order(
    order_id: str,
) -> BillingCheckoutResponse:

    return (
        get_billing_service()
        .fulfill_order(
            order_id
        )
    )


def get_user_billing_summary(
    user_id: str,
) -> dict:

    return (
        get_billing_service()
        .user_summary(
            user_id
        )
    )


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "BillingServiceError",
    "BillingValidationError",
    "BillingProductError",
    "BillingOrderError",
    "BillingPaymentError",
    "BillingFulfillmentError",
    "BillingCheckoutItem",
    "BillingCheckout",
    "BillingCheckoutResponse",
    "BillingService",
    "get_billing_service",
    "set_billing_service",
    "create_billing_checkout",
    "verify_billing_checkout",
    "fulfill_billing_order",
    "get_user_billing_summary",
]
