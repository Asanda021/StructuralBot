"""
StructuralBot - Invoice

Invoice and billing-document infrastructure.

Responsibilities:
- Invoice creation
- Invoice numbering
- Invoice status lifecycle
- Order-to-invoice mapping
- Line items
- Tax/discount calculation
- Totals
- Invoice metadata
- Serialization

This module does NOT process payments.
Payment processing belongs to:
    billing.gateway

Order lifecycle belongs to:
    billing.orders
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from threading import RLock
from typing import Any, Dict, List, Optional

from billing.orders import (
    Order,
    OrderItem,
)


# ============================================================
# HELPERS
# ============================================================


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _money(value: Any) -> Decimal:
    """
    Normalize monetary values.

    Decimal is used instead of float to avoid
    financial rounding errors.
    """

    if isinstance(value, Decimal):
        amount = value
    else:
        amount = Decimal(str(value))

    return amount.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# EXCEPTIONS
# ============================================================


class InvoiceError(Exception):
    """Base invoice exception."""


class InvoiceValidationError(
    InvoiceError
):
    """Invalid invoice data."""


class InvoiceNotFoundError(
    InvoiceError
):
    """Invoice does not exist."""


class InvoiceStateError(
    InvoiceError
):
    """Invalid invoice state transition."""


# ============================================================
# INVOICE STATUS
# ============================================================


class InvoiceStatus(str, Enum):

    DRAFT = "draft"

    ISSUED = "issued"

    PAID = "paid"

    VOID = "void"

    REFUNDED = "refunded"


# ============================================================
# INVOICE TYPE
# ============================================================


class InvoiceType(str, Enum):

    SUBSCRIPTION = "subscription"

    CREDIT = "credit"

    AI_CREDIT = "ai_credit"

    REPORT = "report"

    API = "api"

    CUSTOM = "custom"

    MIXED = "mixed"


# ============================================================
# INVOICE ITEM
# ============================================================


@dataclass
class InvoiceItem:
    """
    Single invoice line.
    """

    item_id: str

    product_code: str

    description: str

    quantity: int = 1

    unit_price: Decimal = Decimal("0.00")

    discount: Decimal = Decimal("0.00")

    tax_rate: Decimal = Decimal("0.00")

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:

        self.quantity = int(
            self.quantity
        )

        if self.quantity <= 0:

            raise InvoiceValidationError(
                "Invoice item quantity must "
                "be greater than zero."
            )

        self.unit_price = _money(
            self.unit_price
        )

        self.discount = _money(
            self.discount
        )

        self.tax_rate = Decimal(
            str(self.tax_rate)
        )

        if self.tax_rate < 0:

            raise InvoiceValidationError(
                "Tax rate cannot be negative."
            )

        if self.discount < 0:

            raise InvoiceValidationError(
                "Discount cannot be negative."
            )

    @property
    def gross_amount(self) -> Decimal:

        return _money(
            self.unit_price
            * self.quantity
        )

    @property
    def net_before_tax(self) -> Decimal:

        value = (
            self.gross_amount
            - self.discount
        )

        if value < 0:

            value = Decimal("0.00")

        return _money(value)

    @property
    def tax_amount(self) -> Decimal:

        return _money(
            self.net_before_tax
            * self.tax_rate
            / Decimal("100")
        )

    @property
    def total(self) -> Decimal:

        return _money(
            self.net_before_tax
            + self.tax_amount
        )

    def to_dict(self) -> dict:

        return {
            "item_id": self.item_id,
            "product_code": self.product_code,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": str(
                self.unit_price
            ),
            "gross_amount": str(
                self.gross_amount
            ),
            "discount": str(
                self.discount
            ),
            "net_before_tax": str(
                self.net_before_tax
            ),
            "tax_rate": str(
                self.tax_rate
            ),
            "tax_amount": str(
                self.tax_amount
            ),
            "total": str(
                self.total
            ),
            "metadata": deepcopy(
                self.metadata
            ),
        }


# ============================================================
# INVOICE
# ============================================================


@dataclass
class Invoice:
    """
    Commercial invoice.

    The invoice is intentionally independent from
    the payment gateway.
    """

    invoice_id: str

    invoice_number: str

    user_id: str

    invoice_type: InvoiceType

    currency: str = "IRR"

    status: InvoiceStatus = (
        InvoiceStatus.DRAFT
    )

    items: List[InvoiceItem] = field(
        default_factory=list
    )

    tax: Decimal = Decimal("0.00")

    discount: Decimal = Decimal("0.00")

    subtotal: Decimal = Decimal("0.00")

    total: Decimal = Decimal("0.00")

    order_id: Optional[str] = None

    payment_id: Optional[str] = None

    payment_reference: Optional[str] = None

    customer_name: Optional[str] = None

    customer_phone: Optional[str] = None

    customer_email: Optional[str] = None

    description: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    issued_at: Optional[
        datetime
    ] = None

    paid_at: Optional[
        datetime
    ] = None

    voided_at: Optional[
        datetime
    ] = None

    refunded_at: Optional[
        datetime
    ] = None

    created_at: datetime = field(
        default_factory=_utcnow
    )

    updated_at: datetime = field(
        default_factory=_utcnow
    )

    def recalculate(self) -> None:

        self.subtotal = _money(
            sum(
                (
                    item.net_before_tax
                    for item in self.items
                ),
                Decimal("0.00"),
            )
        )

        self.tax = _money(
            sum(
                (
                    item.tax_amount
                    for item in self.items
                ),
                Decimal("0.00"),
            )
        )

        self.discount = _money(
            sum(
                (
                    item.discount
                    for item in self.items
                ),
                Decimal("0.00"),
            )
        )

        self.total = _money(
            self.subtotal
            + self.tax
        )

        self.updated_at = _utcnow()

    def add_item(
        self,
        item: InvoiceItem,
    ) -> None:

        if self.status not in {
            InvoiceStatus.DRAFT
        }:

            raise InvoiceStateError(
                "Items can only be added "
                "to draft invoices."
            )

        self.items.append(item)

        self.recalculate()

    def issue(self) -> None:

        if not self.items:

            raise InvoiceValidationError(
                "Cannot issue an empty invoice."
            )

        if self.status != (
            InvoiceStatus.DRAFT
        ):

            raise InvoiceStateError(
                "Only draft invoices can "
                "be issued."
            )

        self.recalculate()

        self.status = (
            InvoiceStatus.ISSUED
        )

        self.issued_at = _utcnow()
        self.updated_at = _utcnow()

    def mark_paid(
        self,
        payment_id: Optional[str] = None,
        payment_reference: Optional[str] = None,
    ) -> None:

        if self.status not in {
            InvoiceStatus.ISSUED,
            InvoiceStatus.PAID,
        }:

            raise InvoiceStateError(
                "Only issued invoices can "
                "be marked as paid."
            )

        if self.status == InvoiceStatus.PAID:

            return

        self.status = (
            InvoiceStatus.PAID
        )

        self.payment_id = payment_id
        self.payment_reference = (
            payment_reference
        )

        self.paid_at = _utcnow()
        self.updated_at = _utcnow()

    def void(self) -> None:

        if self.status in {
            InvoiceStatus.PAID,
            InvoiceStatus.REFUNDED,
        }:

            raise InvoiceStateError(
                "Paid or refunded invoices "
                "cannot be voided."
            )

        if self.status == InvoiceStatus.VOID:

            return

        self.status = (
            InvoiceStatus.VOID
        )

        self.voided_at = _utcnow()
        self.updated_at = _utcnow()

    def refund(self) -> None:

        if self.status != (
            InvoiceStatus.PAID
        ):

            raise InvoiceStateError(
                "Only paid invoices can "
                "be refunded."
            )

        self.status = (
            InvoiceStatus.REFUNDED
        )

        self.refunded_at = _utcnow()
        self.updated_at = _utcnow()

    def to_dict(self) -> dict:

        return {
            "invoice_id": self.invoice_id,
            "invoice_number": (
                self.invoice_number
            ),
            "user_id": self.user_id,
            "invoice_type": (
                self.invoice_type.value
            ),
            "currency": self.currency,
            "status": self.status.value,
            "items": [
                item.to_dict()
                for item in self.items
            ],
            "subtotal": str(
                self.subtotal
            ),
            "discount": str(
                self.discount
            ),
            "tax": str(
                self.tax
            ),
            "total": str(
                self.total
            ),
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "payment_reference": (
                self.payment_reference
            ),
            "customer_name": (
                self.customer_name
            ),
            "customer_phone": (
                self.customer_phone
            ),
            "customer_email": (
                self.customer_email
            ),
            "description": (
                self.description
            ),
            "metadata": deepcopy(
                self.metadata
            ),
            "issued_at": (
                self.issued_at.isoformat()
                if self.issued_at
                else None
            ),
            "paid_at": (
                self.paid_at.isoformat()
                if self.paid_at
                else None
            ),
            "voided_at": (
                self.voided_at.isoformat()
                if self.voided_at
                else None
            ),
            "refunded_at": (
                self.refunded_at.isoformat()
                if self.refunded_at
                else None
            ),
            "created_at": (
                self.created_at.isoformat()
            ),
            "updated_at": (
                self.updated_at.isoformat()
            ),
        }


# ============================================================
# INVOICE MANAGER
# ============================================================


class InvoiceManager:
    """
    In-memory invoice repository/service.

    Later this class can be backed by SQLite/PostgreSQL
    without changing the handler/API layer.
    """

    def __init__(self) -> None:

        self._invoices: Dict[
            str,
            Invoice,
        ] = {}

        self._order_index: Dict[
            str,
            str,
        ] = {}

        self._number_counter = 0

        self._lock = RLock()

    # ========================================================
    # IDENTIFIERS
    # ========================================================

    def _next_invoice_number(
        self,
    ) -> str:

        self._number_counter += 1

        year = _utcnow().year

        return (
            f"SB-{year}-"
            f"{self._number_counter:08d}"
        )

    # ========================================================
    # CREATE
    # ========================================================

    def create(
        self,
        user_id: str,
        invoice_type: InvoiceType,
        currency: str = "IRR",
        order_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_email: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Invoice:

        with self._lock:

            user_id = str(user_id)

            if not user_id:

                raise InvoiceValidationError(
                    "User ID is required."
                )

            if order_id:

                existing_id = (
                    self._order_index.get(
                        str(order_id)
                    )
                )

                if existing_id:

                    existing = (
                        self._invoices[
                            existing_id
                        ]
                    )

                    return deepcopy(
                        existing
                    )

            invoice_id = (
                f"inv_{year_safe_id()}"
            )

            while invoice_id in self._invoices:

                invoice_id = (
                    f"inv_{year_safe_id()}"
                )

            invoice = Invoice(
                invoice_id=invoice_id,
                invoice_number=(
                    self._next_invoice_number()
                ),
                user_id=user_id,
                invoice_type=(
                    invoice_type
                ),
                currency=currency,
                order_id=(
                    str(order_id)
                    if order_id
                    else None
                ),
                customer_name=(
                    customer_name
                ),
                customer_phone=(
                    customer_phone
                ),
                customer_email=(
                    customer_email
                ),
                description=(
                    description
                ),
                metadata=(
                    deepcopy(metadata)
                    if metadata
                    else {}
                ),
            )

            self._invoices[
                invoice_id
            ] = invoice

            if order_id:

                self._order_index[
                    str(order_id)
                ] = invoice_id

            return deepcopy(
                invoice
            )

    # ========================================================
    # CREATE FROM ORDER
    # ========================================================

    def create_from_order(
        self,
        order: Order,
        invoice_type: InvoiceType = (
            InvoiceType.MIXED
        ),
        currency: str = "IRR",
        tax_rate: Decimal = Decimal("0.00"),
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_email: Optional[str] = None,
    ) -> Invoice:

        invoice = self.create(
            user_id=order.user_id,
            invoice_type=invoice_type,
            currency=(
                getattr(
                    order,
                    "currency",
                    None,
                )
                or currency
            ),
            order_id=order.order_id,
            customer_name=(
                customer_name
            ),
            customer_phone=(
                customer_phone
            ),
            customer_email=(
                customer_email
            ),
            metadata={
                "source": "order",
                "order_id": order.order_id,
            },
        )

        for index, item in enumerate(
            order.items,
            start=1,
        ):

            invoice_item = (
                self._order_item_to_invoice_item(
                    item=item,
                    index=index,
                    tax_rate=tax_rate,
                )
            )

            self._invoices[
                invoice.invoice_id
            ].add_item(
                invoice_item
            )

        return self.get(
            invoice.invoice_id
        )

    def _order_item_to_invoice_item(
        self,
        item: OrderItem,
        index: int,
        tax_rate: Decimal,
    ) -> InvoiceItem:

        quantity = int(
            getattr(
                item,
                "quantity",
                1,
            )
        )

        unit_price = getattr(
            item,
            "unit_price",
            Decimal("0.00"),
        )

        description = getattr(
            item,
            "description",
            None,
        )

        if not description:

            description = (
                item.product_code
            )

        discount = getattr(
            item,
            "discount",
            Decimal("0.00"),
        )

        return InvoiceItem(
            item_id=(
                f"invitem_{index}"
            ),
            product_code=(
                item.product_code
            ),
            description=description,
            quantity=quantity,
            unit_price=(
                _money(unit_price)
            ),
            discount=(
                _money(discount)
            ),
            tax_rate=(
                Decimal(str(tax_rate))
            ),
            metadata=deepcopy(
                getattr(
                    item,
                    "metadata",
                    {},
                )
            ),
        )

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        invoice_id: str,
    ) -> Invoice:

        with self._lock:

            invoice = self._invoices.get(
                str(invoice_id)
            )

            if invoice is None:

                raise InvoiceNotFoundError(
                    f"Invoice not found: "
                    f"{invoice_id}"
                )

            return deepcopy(
                invoice
            )

    def get_by_order(
        self,
        order_id: str,
    ) -> Optional[Invoice]:

        with self._lock:

            invoice_id = (
                self._order_index.get(
                    str(order_id)
                )
            )

            if not invoice_id:

                return None

            return deepcopy(
                self._invoices[
                    invoice_id
                ]
            )

    # ========================================================
    # ITEM OPERATIONS
    # ========================================================

    def add_item(
        self,
        invoice_id: str,
        item: InvoiceItem,
    ) -> Invoice:

        with self._lock:

            invoice = self._require(
                invoice_id
            )

            invoice.add_item(item)

            return deepcopy(
                invoice
            )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def issue(
        self,
        invoice_id: str,
    ) -> Invoice:

        with self._lock:

            invoice = self._require(
                invoice_id
            )

            invoice.issue()

            return deepcopy(
                invoice
            )

    def mark_paid(
        self,
        invoice_id: str,
        payment_id: Optional[str] = None,
        payment_reference: Optional[str] = None,
    ) -> Invoice:

        with self._lock:

            invoice = self._require(
                invoice_id
            )

            invoice.mark_paid(
                payment_id=payment_id,
                payment_reference=(
                    payment_reference
                ),
            )

            return deepcopy(
                invoice
            )

    def void(
        self,
        invoice_id: str,
    ) -> Invoice:

        with self._lock:

            invoice = self._require(
                invoice_id
            )

            invoice.void()

            return deepcopy(
                invoice
            )

    def refund(
        self,
        invoice_id: str,
    ) -> Invoice:

        with self._lock:

            invoice = self._require(
                invoice_id
            )

            invoice.refund()

            return deepcopy(
                invoice
            )

    # ========================================================
    # LISTING
    # ========================================================

    def list_user(
        self,
        user_id: str,
        status: Optional[
            InvoiceStatus
        ] = None,
    ) -> List[Invoice]:

        with self._lock:

            invoices = [
                invoice
                for invoice
                in self._invoices.values()
                if invoice.user_id
                == str(user_id)
            ]

            if status is not None:

                invoices = [
                    invoice
                    for invoice in invoices
                    if invoice.status
                    == status
                ]

            invoices.sort(
                key=lambda item: (
                    item.created_at
                ),
                reverse=True,
            )

            return deepcopy(
                invoices
            )

    def list_all(
        self,
        status: Optional[
            InvoiceStatus
        ] = None,
    ) -> List[Invoice]:

        with self._lock:

            invoices = list(
                self._invoices.values()
            )

            if status is not None:

                invoices = [
                    invoice
                    for invoice in invoices
                    if invoice.status
                    == status
                ]

            invoices.sort(
                key=lambda item: (
                    item.created_at
                ),
                reverse=True,
            )

            return deepcopy(
                invoices
            )

    # ========================================================
    # SEARCH
    # ========================================================

    def find_by_number(
        self,
        invoice_number: str,
    ) -> Optional[Invoice]:

        with self._lock:

            for invoice in (
                self._invoices.values()
            ):

                if (
                    invoice.invoice_number
                    == str(invoice_number)
                ):

                    return deepcopy(
                        invoice
                    )

            return None

    # ========================================================
    # SUMMARY
    # ========================================================

    def summary(
        self,
        user_id: Optional[str] = None,
    ) -> dict:

        if user_id is None:

            invoices = self.list_all()

        else:

            invoices = self.list_user(
                user_id
            )

        total_amount = _money(
            sum(
                (
                    invoice.total
                    for invoice in invoices
                ),
                Decimal("0.00"),
            )
        )

        paid_amount = _money(
            sum(
                (
                    invoice.total
                    for invoice in invoices
                    if invoice.status
                    == InvoiceStatus.PAID
                ),
                Decimal("0.00"),
            )
        )

        return {
            "total": len(invoices),
            "draft": sum(
                invoice.status
                == InvoiceStatus.DRAFT
                for invoice in invoices
            ),
            "issued": sum(
                invoice.status
                == InvoiceStatus.ISSUED
                for invoice in invoices
            ),
            "paid": sum(
                invoice.status
                == InvoiceStatus.PAID
                for invoice in invoices
            ),
            "void": sum(
                invoice.status
                == InvoiceStatus.VOID
                for invoice in invoices
            ),
            "refunded": sum(
                invoice.status
                == InvoiceStatus.REFUNDED
                for invoice in invoices
            ),
            "total_amount": str(
                total_amount
            ),
            "paid_amount": str(
                paid_amount
            ),
        }

    # ========================================================
    # INTERNAL
    # ========================================================

    def _require(
        self,
        invoice_id: str,
    ) -> Invoice:

        invoice = self._invoices.get(
            str(invoice_id)
        )

        if invoice is None:

            raise InvoiceNotFoundError(
                f"Invoice not found: "
                f"{invoice_id}"
            )

        return invoice

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def export_dicts(
        self,
        user_id: Optional[str] = None,
    ) -> List[dict]:

        if user_id is None:

            invoices = self.list_all()

        else:

            invoices = self.list_user(
                user_id
            )

        return [
            invoice.to_dict()
            for invoice in invoices
        ]

    # ========================================================
    # RESET
    # ========================================================

    def clear(self) -> None:

        with self._lock:

            self._invoices.clear()
            self._order_index.clear()
            self._number_counter = 0


# ============================================================
# ID GENERATOR
# ============================================================


def year_safe_id() -> str:

    now = _utcnow()

    return (
        now.strftime(
            "%Y%m%d%H%M%S"
        )
        + "_"
        + str(
            int(
                now.timestamp()
                * 1000000
            ) % 1000000
        )
    )


# ============================================================
# GLOBAL MANAGER
# ============================================================


_default_invoice_manager: Optional[
    InvoiceManager
] = None


def get_invoice_manager() -> InvoiceManager:

    global _default_invoice_manager

    if (
        _default_invoice_manager
        is None
    ):

        _default_invoice_manager = (
            InvoiceManager()
        )

    return (
        _default_invoice_manager
    )


def set_invoice_manager(
    manager: InvoiceManager,
) -> None:

    global _default_invoice_manager

    _default_invoice_manager = manager


# ============================================================
# CONVENIENCE HELPERS
# ============================================================


def create_invoice_from_order(
    order: Order,
    invoice_type: InvoiceType = (
        InvoiceType.MIXED
    ),
    currency: str = "IRR",
    tax_rate: Decimal = Decimal("0.00"),
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    customer_email: Optional[str] = None,
) -> Invoice:

    return (
        get_invoice_manager()
        .create_from_order(
            order=order,
            invoice_type=invoice_type,
            currency=currency,
            tax_rate=tax_rate,
            customer_name=(
                customer_name
            ),
            customer_phone=(
                customer_phone
            ),
            customer_email=(
                customer_email
            ),
        )
    )


def get_invoice(
    invoice_id: str,
) -> Invoice:

    return (
        get_invoice_manager()
        .get(invoice_id)
    )


def get_invoice_by_order(
    order_id: str,
) -> Optional[Invoice]:

    return (
        get_invoice_manager()
        .get_by_order(order_id)
    )


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "InvoiceError",
    "InvoiceValidationError",
    "InvoiceNotFoundError",
    "InvoiceStateError",
    "InvoiceStatus",
    "InvoiceType",
    "InvoiceItem",
    "Invoice",
    "InvoiceManager",
    "get_invoice_manager",
    "set_invoice_manager",
    "create_invoice_from_order",
    "get_invoice",
    "get_invoice_by_order",
]
