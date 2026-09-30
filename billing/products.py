"""
StructuralBot - Products

Commercial product catalog.

Responsibilities:
- Define sellable products
- Subscription products
- Credit packs
- Paid reports
- AI credit packages
- API products
- Product lookup
- Product pricing metadata

This module does not process payments.

Payment processing belongs to:
    billing.gateway

Order creation belongs to:
    billing.orders

Checkout orchestration belongs to:
    billing.checkout
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================
# PRODUCT TYPE
# ============================================================


class ProductType(str, Enum):
    """
    Types of products that StructuralBot can sell.
    """

    SUBSCRIPTION = "subscription"

    CREDIT_PACK = "credit_pack"

    AI_CREDIT_PACK = "ai_credit_pack"

    PDF_REPORT = "pdf_report"

    EXCEL_REPORT = "excel_report"

    API_ACCESS = "api_access"

    CUSTOM_SERVICE = "custom_service"


# ============================================================
# PRODUCT STATUS
# ============================================================


class ProductStatus(str, Enum):

    ACTIVE = "active"

    INACTIVE = "inactive"

    COMING_SOON = "coming_soon"


# ============================================================
# PRODUCT
# ============================================================


@dataclass
class Product:
    """
    Sellable commercial product.
    """

    code: str

    name: str

    product_type: ProductType

    description: str = ""

    price: int = 0

    currency: str = "IRR"

    active: bool = True

    status: ProductStatus = (
        ProductStatus.ACTIVE
    )

    duration_days: Optional[int] = None

    credits: Optional[int] = None

    plan_code: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def is_available(self) -> bool:

        return (
            self.active
            and self.status
            == ProductStatus.ACTIVE
            and self.price >= 0
        )

    def to_dict(self) -> dict:

        return {
            "code": self.code,
            "name": self.name,
            "product_type": (
                self.product_type.value
            ),
            "description": self.description,
            "price": self.price,
            "currency": self.currency,
            "active": self.active,
            "status": self.status.value,
            "duration_days": (
                self.duration_days
            ),
            "credits": self.credits,
            "plan_code": self.plan_code,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# PRODUCT CATALOG
# ============================================================


class ProductCatalog:
    """
    In-memory commercial product catalog.

    Pricing is intentionally configurable.
    """

    def __init__(
        self,
        products: Optional[
            List[Product]
        ] = None,
    ) -> None:

        self._products: Dict[
            str,
            Product,
        ] = {}

        if products:

            for product in products:

                self.add(product)

    # ========================================================
    # CRUD
    # ========================================================

    def add(
        self,
        product: Product,
    ) -> Product:

        if not product.code:
            raise ValueError(
                "Product code is required."
            )

        code = product.code.strip().lower()

        product.code = code

        self._products[
            code
        ] = product

        return product

    def remove(
        self,
        code: str,
    ) -> bool:

        code = str(
            code
        ).strip().lower()

        return (
            self._products.pop(
                code,
                None,
            )
            is not None
        )

    def get(
        self,
        code: str,
    ) -> Optional[Product]:

        code = str(
            code
        ).strip().lower()

        return self._products.get(
            code
        )

    def require(
        self,
        code: str,
    ) -> Product:

        product = self.get(
            code
        )

        if product is None:
            raise KeyError(
                f"Product not found: {code}"
            )

        return product

    # ========================================================
    # QUERIES
    # ========================================================

    def all(
        self,
    ) -> List[Product]:

        return list(
            self._products.values()
        )

    def available(
        self,
    ) -> List[Product]:

        return [
            product
            for product in self._products.values()
            if product.is_available()
        ]

    def by_type(
        self,
        product_type: ProductType | str,
    ) -> List[Product]:

        if not isinstance(
            product_type,
            ProductType,
        ):

            product_type = ProductType(
                str(
                    product_type
                ).strip().lower()
            )

        return [
            product
            for product in self._products.values()
            if product.product_type
            == product_type
        ]

    def subscriptions(
        self,
    ) -> List[Product]:

        return self.by_type(
            ProductType.SUBSCRIPTION
        )

    def credit_packs(
        self,
    ) -> List[Product]:

        return self.by_type(
            ProductType.CREDIT_PACK
        )

    def ai_credit_packs(
        self,
    ) -> List[Product]:

        return self.by_type(
            ProductType.AI_CREDIT_PACK
        )

    def reports(
        self,
    ) -> List[Product]:

        return [
            product
            for product in self._products.values()
            if product.product_type
            in {
                ProductType.PDF_REPORT,
                ProductType.EXCEL_REPORT,
            }
        ]

    def __contains__(
        self,
        code: str,
    ) -> bool:

        return self.get(
            code
        ) is not None

    def __len__(self) -> int:

        return len(
            self._products
        )


# ============================================================
# DEFAULT PRODUCTS
# ============================================================


def build_default_catalog() -> ProductCatalog:
    """
    Build the initial StructuralBot product catalog.

    Prices are intentionally configurable placeholders.
    """

    catalog = ProductCatalog()

    # --------------------------------------------------------
    # SUBSCRIPTIONS
    # --------------------------------------------------------

    catalog.add(
        Product(
            code="subscription_basic",
            name="StructuralBot Basic",
            product_type=(
                ProductType.SUBSCRIPTION
            ),
            description=(
                "Basic StructuralBot subscription."
            ),
            price=0,
            currency="IRR",
            duration_days=30,
            plan_code="basic",
            metadata={
                "billing_period": "monthly",
            },
        )
    )

    catalog.add(
        Product(
            code="subscription_professional",
            name="StructuralBot Professional",
            product_type=(
                ProductType.SUBSCRIPTION
            ),
            description=(
                "Professional StructuralBot subscription."
            ),
            price=0,
            currency="IRR",
            duration_days=30,
            plan_code="professional",
            metadata={
                "billing_period": "monthly",
            },
        )
    )

    catalog.add(
        Product(
            code="subscription_business",
            name="StructuralBot Business",
            product_type=(
                ProductType.SUBSCRIPTION
            ),
            description=(
                "Business StructuralBot subscription."
            ),
            price=0,
            currency="IRR",
            duration_days=30,
            plan_code="business",
            metadata={
                "billing_period": "monthly",
            },
        )
    )

    # --------------------------------------------------------
    # CREDIT PACKS
    # --------------------------------------------------------

    catalog.add(
        Product(
            code="credits_100",
            name="100 Credits",
            product_type=(
                ProductType.CREDIT_PACK
            ),
            description=(
                "StructuralBot 100-credit package."
            ),
            price=0,
            currency="IRR",
            credits=100,
        )
    )

    catalog.add(
        Product(
            code="credits_500",
            name="500 Credits",
            product_type=(
                ProductType.CREDIT_PACK
            ),
            description=(
                "StructuralBot 500-credit package."
            ),
            price=0,
            currency="IRR",
            credits=500,
        )
    )

    catalog.add(
        Product(
            code="credits_1000",
            name="1000 Credits",
            product_type=(
                ProductType.CREDIT_PACK
            ),
            description=(
                "StructuralBot 1000-credit package."
            ),
            price=0,
            currency="IRR",
            credits=1000,
        )
    )

    # --------------------------------------------------------
    # AI CREDIT PACKS
    # --------------------------------------------------------

    catalog.add(
        Product(
            code="ai_credits_100",
            name="100 AI Credits",
            product_type=(
                ProductType.AI_CREDIT_PACK
            ),
            description=(
                "100 AI usage credits."
            ),
            price=0,
            currency="IRR",
            credits=100,
            metadata={
                "usage": "ai",
            },
        )
    )

    catalog.add(
        Product(
            code="ai_credits_500",
            name="500 AI Credits",
            product_type=(
                ProductType.AI_CREDIT_PACK
            ),
            description=(
                "500 AI usage credits."
            ),
            price=0,
            currency="IRR",
            credits=500,
            metadata={
                "usage": "ai",
            },
        )
    )

    # --------------------------------------------------------
    # REPORTS
    # --------------------------------------------------------

    catalog.add(
        Product(
            code="report_pdf",
            name="PDF Engineering Report",
            product_type=(
                ProductType.PDF_REPORT
            ),
            description=(
                "Professional PDF engineering report."
            ),
            price=0,
            currency="IRR",
        )
    )

    catalog.add(
        Product(
            code="report_excel",
            name="Excel Engineering Report",
            product_type=(
                ProductType.EXCEL_REPORT
            ),
            description=(
                "Engineering calculation data "
                "in Excel format."
            ),
            price=0,
            currency="IRR",
        )
    )

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    catalog.add(
        Product(
            code="api_access",
            name="StructuralBot API Access",
            product_type=(
                ProductType.API_ACCESS
            ),
            description=(
                "API access for external integrations."
            ),
            price=0,
            currency="IRR",
        )
    )

    return catalog


# ============================================================
# GLOBAL CATALOG
# ============================================================


_default_catalog: Optional[
    ProductCatalog
] = None


def get_product_catalog() -> ProductCatalog:

    global _default_catalog

    if _default_catalog is None:

        _default_catalog = (
            build_default_catalog()
        )

    return _default_catalog


def set_product_catalog(
    catalog: ProductCatalog,
) -> None:

    global _default_catalog

    _default_catalog = catalog


# ============================================================
# CONVENIENCE HELPERS
# ============================================================


def get_product(
    code: str,
) -> Optional[Product]:

    return get_product_catalog().get(
        code
    )


def require_product(
    code: str,
) -> Product:

    return get_product_catalog().require(
        code
    )


def get_available_products() -> List[Product]:

    return get_product_catalog().available()


def get_subscription_products() -> List[Product]:

    return get_product_catalog().subscriptions()


def get_credit_products() -> List[Product]:

    return get_product_catalog().credit_packs()


def get_ai_credit_products() -> List[Product]:

    return get_product_catalog().ai_credit_packs()


def get_report_products() -> List[Product]:

    return get_product_catalog().reports()


# ============================================================
# PRODUCT PRICE
# ============================================================


def get_product_price(
    code: str,
) -> int:

    return require_product(
        code
    ).price


def set_product_price(
    code: str,
    price: int,
) -> Product:

    if price < 0:
        raise ValueError(
            "Product price cannot be negative."
        )

    product = require_product(
        code
    )

    product.price = price

    return product


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "ProductType",
    "ProductStatus",
    "Product",
    "ProductCatalog",
    "build_default_catalog",
    "get_product_catalog",
    "set_product_catalog",
    "get_product",
    "require_product",
    "get_available_products",
    "get_subscription_products",
    "get_credit_products",
    "get_ai_credit_products",
    "get_report_products",
    "get_product_price",
    "set_product_price",
]
