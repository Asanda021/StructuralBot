"""
StructuralBot - Payment Gateway Registry

Provider-independent registry for payment gateways.

Responsibilities:
- Register multiple payment gateway adapters
- Select gateways by name/provider
- Select gateways by currency or capability
- Keep checkout logic independent from concrete providers
- Support fallback/default gateway selection
- Provide health/status information

This module does NOT implement any payment provider.
Concrete gateways belong in separate adapter modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, Iterable, List, Mapping, Optional, Protocol, Set


# ============================================================
# HELPERS
# ============================================================


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


# ============================================================
# ERRORS
# ============================================================


class GatewayRegistryError(Exception):
    """Base gateway registry error."""


class GatewayRegistrationError(GatewayRegistryError):
    """Gateway registration failed."""


class GatewayNotFoundError(GatewayRegistryError):
    """Requested gateway does not exist."""


class GatewaySelectionError(GatewayRegistryError):
    """No suitable gateway could be selected."""


class GatewayCapabilityError(GatewayRegistryError):
    """Gateway does not support requested capability."""


# ============================================================
# CAPABILITIES
# ============================================================


@dataclass(frozen=True)
class GatewayCapabilities:
    """
    Describes what a payment gateway supports.

    Values are intentionally provider-independent.
    """

    currencies: frozenset[str] = frozenset({"IRR"})

    supports_subscription: bool = True
    supports_credit_purchase: bool = True
    supports_report_purchase: bool = True
    supports_refund: bool = False
    supports_verification: bool = True
    supports_webhook: bool = False

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def supports_currency(
        self,
        currency: str,
    ) -> bool:

        currency = _safe_str(currency).upper()

        return currency in {
            item.upper()
            for item in self.currencies
        }

    def supports_order_type(
        self,
        order_type: str,
    ) -> bool:

        value = _safe_str(order_type).lower()

        mapping = {
            "subscription": self.supports_subscription,
            "credit": self.supports_credit_purchase,
            "ai_credits": self.supports_credit_purchase,
            "pdf_report": self.supports_report_purchase,
            "excel_report": self.supports_report_purchase,
            "report": self.supports_report_purchase,
        }

        if value not in mapping:
            return True

        return mapping[value]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "currencies": sorted(
                item.upper()
                for item in self.currencies
            ),
            "supports_subscription": (
                self.supports_subscription
            ),
            "supports_credit_purchase": (
                self.supports_credit_purchase
            ),
            "supports_report_purchase": (
                self.supports_report_purchase
            ),
            "supports_refund": (
                self.supports_refund
            ),
            "supports_verification": (
                self.supports_verification
            ),
            "supports_webhook": (
                self.supports_webhook
            ),
            "metadata": dict(self.metadata),
        }


# ============================================================
# GATEWAY PROTOCOL
# ============================================================


class PaymentGatewayProtocol(Protocol):
    """
    Minimal contract expected from a payment gateway adapter.

    The existing billing/gateway.py contains the actual
    payment request/result models and manager abstractions.
    This registry deliberately keeps the contract lightweight.
    """

    name: str

    def health_check(self) -> bool:
        ...

    def create_payment(self, request: Any) -> Any:
        ...

    def verify_payment(self, payment: Any) -> Any:
        ...


# ============================================================
# REGISTERED GATEWAY
# ============================================================


@dataclass
class RegisteredGateway:
    """
    Metadata wrapper around a concrete gateway adapter.
    """

    name: str
    gateway: PaymentGatewayProtocol

    capabilities: GatewayCapabilities = field(
        default_factory=GatewayCapabilities
    )

    priority: int = 100

    enabled: bool = True

    environment: str = "production"

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def normalized_name(self) -> str:
        return self.name.strip().lower()

    def is_usable(self) -> bool:
        if not self.enabled:
            return False

        try:
            return bool(self.gateway.health_check())
        except Exception:
            return False

    def supports(
        self,
        *,
        currency: Optional[str] = None,
        order_type: Optional[str] = None,
        require_refund: bool = False,
        require_webhook: bool = False,
        require_verification: bool = False,
    ) -> bool:

        if not self.enabled:
            return False

        if currency:
            if not self.capabilities.supports_currency(
                currency
            ):
                return False

        if order_type:
            if not self.capabilities.supports_order_type(
                order_type
            ):
                return False

        if require_refund:
            if not self.capabilities.supports_refund:
                return False

        if require_webhook:
            if not self.capabilities.supports_webhook:
                return False

        if require_verification:
            if not self.capabilities.supports_verification:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "priority": self.priority,
            "enabled": self.enabled,
            "environment": self.environment,
            "usable": self.is_usable(),
            "capabilities": self.capabilities.to_dict(),
            "metadata": dict(self.metadata),
        }


# ============================================================
# REGISTRY
# ============================================================


class PaymentGatewayRegistry:
    """
    Thread-safe payment gateway registry.

    Example:

        registry.register(
            gateway,
            capabilities=GatewayCapabilities(
                currencies=frozenset({"IRR"})
            ),
            priority=10,
        )

        selected = registry.select(
            currency="IRR",
            order_type="subscription",
        )
    """

    def __init__(
        self,
        *,
        default_gateway: Optional[str] = None,
    ) -> None:

        self._gateways: Dict[str, RegisteredGateway] = {}
        self._default_gateway = (
            _safe_str(default_gateway).lower()
            or None
        )
        self._lock = RLock()

    # --------------------------------------------------------
    # Registration
    # --------------------------------------------------------

    def register(
        self,
        gateway: PaymentGatewayProtocol,
        *,
        name: Optional[str] = None,
        capabilities: Optional[GatewayCapabilities] = None,
        priority: int = 100,
        enabled: bool = True,
        environment: str = "production",
        metadata: Optional[Mapping[str, Any]] = None,
        replace: bool = True,
    ) -> RegisteredGateway:

        gateway_name = _safe_str(
            name
            or getattr(gateway, "name", "")
        ).lower()

        if not gateway_name:
            raise GatewayRegistrationError(
                "Payment gateway must have a name."
            )

        if priority < 0:
            raise GatewayRegistrationError(
                "Gateway priority cannot be negative."
            )

        registered = RegisteredGateway(
            name=gateway_name,
            gateway=gateway,
            capabilities=(
                capabilities
                or GatewayCapabilities()
            ),
            priority=int(priority),
            enabled=bool(enabled),
            environment=(
                _safe_str(environment)
                or "production"
            ),
            metadata=dict(metadata or {}),
        )

        with self._lock:

            if (
                gateway_name in self._gateways
                and not replace
            ):
                raise GatewayRegistrationError(
                    f"Gateway '{gateway_name}' "
                    "is already registered."
                )

            self._gateways[gateway_name] = registered

            if self._default_gateway is None:
                self._default_gateway = gateway_name

        return registered

    def unregister(
        self,
        name: str,
    ) -> bool:

        normalized = _safe_str(name).lower()

        with self._lock:

            removed = (
                self._gateways.pop(
                    normalized,
                    None,
                )
                is not None
            )

            if (
                removed
                and self._default_gateway
                == normalized
            ):
                self._default_gateway = None

            return removed

    # --------------------------------------------------------
    # Lookup
    # --------------------------------------------------------

    def get(
        self,
        name: str,
    ) -> Optional[RegisteredGateway]:

        normalized = _safe_str(name).lower()

        with self._lock:
            return self._gateways.get(normalized)

    def require(
        self,
        name: str,
    ) -> RegisteredGateway:

        gateway = self.get(name)

        if gateway is None:
            raise GatewayNotFoundError(
                f"Payment gateway '{name}' "
                "is not registered."
            )

        return gateway

    def names(self) -> List[str]:

        with self._lock:
            return sorted(self._gateways.keys())

    def all(self) -> List[RegisteredGateway]:

        with self._lock:
            return list(self._gateways.values())

    def enabled(self) -> List[RegisteredGateway]:

        with self._lock:
            return [
                gateway
                for gateway in self._gateways.values()
                if gateway.enabled
            ]

    # --------------------------------------------------------
    # Default gateway
    # --------------------------------------------------------

    def set_default(
        self,
        name: str,
    ) -> None:

        normalized = _safe_str(name).lower()

        with self._lock:

            if normalized not in self._gateways:
                raise GatewayNotFoundError(
                    f"Cannot set unknown gateway "
                    f"'{normalized}' as default."
                )

            self._default_gateway = normalized

    def clear_default(self) -> None:

        with self._lock:
            self._default_gateway = None

    def get_default(
        self,
    ) -> Optional[RegisteredGateway]:

        with self._lock:

            if not self._default_gateway:
                return None

            return self._gateways.get(
                self._default_gateway
            )

    def require_default(
        self,
    ) -> RegisteredGateway:

        gateway = self.get_default()

        if gateway is None:
            raise GatewaySelectionError(
                "No default payment gateway "
                "has been configured."
            )

        return gateway

    # --------------------------------------------------------
    # Selection
    # --------------------------------------------------------

    def candidates(
        self,
        *,
        currency: Optional[str] = None,
        order_type: Optional[str] = None,
        require_refund: bool = False,
        require_webhook: bool = False,
        require_verification: bool = False,
        environment: Optional[str] = None,
        usable_only: bool = True,
    ) -> List[RegisteredGateway]:

        environment_value = (
            _safe_str(environment).lower()
            if environment
            else None
        )

        with self._lock:
            gateways = list(
                self._gateways.values()
            )

        selected: List[RegisteredGateway] = []

        for gateway in gateways:

            if not gateway.supports(
                currency=currency,
                order_type=order_type,
                require_refund=require_refund,
                require_webhook=require_webhook,
                require_verification=require_verification,
            ):
                continue

            if (
                environment_value
                and gateway.environment.lower()
                != environment_value
            ):
                continue

            if usable_only and not gateway.is_usable():
                continue

            selected.append(gateway)

        selected.sort(
            key=lambda item: (
                item.priority,
                item.name,
            )
        )

        return selected

    def select(
        self,
        *,
        name: Optional[str] = None,
        currency: Optional[str] = None,
        order_type: Optional[str] = None,
        require_refund: bool = False,
        require_webhook: bool = False,
        require_verification: bool = False,
        environment: Optional[str] = None,
        usable_only: bool = True,
        allow_default: bool = True,
    ) -> RegisteredGateway:

        # Explicit gateway selection has highest priority.
        if name:

            gateway = self.require(name)

            if not gateway.supports(
                currency=currency,
                order_type=order_type,
                require_refund=require_refund,
                require_webhook=require_webhook,
                require_verification=require_verification,
            ):
                raise GatewayCapabilityError(
                    f"Gateway '{gateway.name}' "
                    "does not support the requested "
                    "payment operation."
                )

            if (
                environment
                and gateway.environment.lower()
                != _safe_str(environment).lower()
            ):
                raise GatewaySelectionError(
                    f"Gateway '{gateway.name}' is not "
                    f"configured for environment "
                    f"'{environment}'."
                )

            if usable_only and not gateway.is_usable():
                raise GatewaySelectionError(
                    f"Gateway '{gateway.name}' "
                    "is currently unavailable."
                )

            return gateway

        # Default gateway is preferred when compatible.
        if allow_default:

            default = self.get_default()

            if default is not None:

                if default.supports(
                    currency=currency,
                    order_type=order_type,
                    require_refund=require_refund,
                    require_webhook=require_webhook,
                    require_verification=require_verification,
                ):

                    if (
                        not environment
                        or default.environment.lower()
                        == _safe_str(
                            environment
                        ).lower()
                    ):

                        if (
                            not usable_only
                            or default.is_usable()
                        ):
                            return default

        # Fall back to best compatible gateway.
        candidates = self.candidates(
            currency=currency,
            order_type=order_type,
            require_refund=require_refund,
            require_webhook=require_webhook,
            require_verification=require_verification,
            environment=environment,
            usable_only=usable_only,
        )

        if not candidates:
            raise GatewaySelectionError(
                "No suitable payment gateway "
                "is available for the requested "
                "operation."
            )

        return candidates[0]

    # --------------------------------------------------------
    # Health/status
    # --------------------------------------------------------

    def health_check(self) -> Dict[str, bool]:

        result: Dict[str, bool] = {}

        for gateway in self.all():

            try:
                result[gateway.name] = bool(
                    gateway.gateway.health_check()
                )
            except Exception:
                result[gateway.name] = False

        return result

    def status(
        self,
    ) -> List[Dict[str, Any]]:

        return [
            gateway.to_dict()
            for gateway in self.all()
        ]

    # --------------------------------------------------------
    # Maintenance
    # --------------------------------------------------------

    def enable(
        self,
        name: str,
    ) -> RegisteredGateway:

        gateway = self.require(name)
        gateway.enabled = True
        return gateway

    def disable(
        self,
        name: str,
    ) -> RegisteredGateway:

        gateway = self.require(name)
        gateway.enabled = False
        return gateway

    def clear(self) -> None:

        with self._lock:
            self._gateways.clear()
            self._default_gateway = None

    def __len__(self) -> int:

        with self._lock:
            return len(self._gateways)


# ============================================================
# DEFAULT REGISTRY
# ============================================================


_default_gateway_registry = (
    PaymentGatewayRegistry()
)


# ============================================================
# PUBLIC HELPERS
# ============================================================


def get_gateway_registry() -> PaymentGatewayRegistry:
    return _default_gateway_registry


def register_payment_gateway(
    gateway: PaymentGatewayProtocol,
    *,
    name: Optional[str] = None,
    capabilities: Optional[GatewayCapabilities] = None,
    priority: int = 100,
    enabled: bool = True,
    environment: str = "production",
    metadata: Optional[Mapping[str, Any]] = None,
    replace: bool = True,
) -> RegisteredGateway:

    return _default_gateway_registry.register(
        gateway,
        name=name,
        capabilities=capabilities,
        priority=priority,
        enabled=enabled,
        environment=environment,
        metadata=metadata,
        replace=replace,
    )


def get_payment_gateway(
    name: str,
) -> Optional[RegisteredGateway]:

    return _default_gateway_registry.get(name)


def require_payment_gateway(
    name: str,
) -> RegisteredGateway:

    return _default_gateway_registry.require(name)


def select_payment_gateway(
    *,
    name: Optional[str] = None,
    currency: Optional[str] = None,
    order_type: Optional[str] = None,
    require_refund: bool = False,
    require_webhook: bool = False,
    require_verification: bool = False,
    environment: Optional[str] = None,
    usable_only: bool = True,
) -> RegisteredGateway:

    return _default_gateway_registry.select(
        name=name,
        currency=currency,
        order_type=order_type,
        require_refund=require_refund,
        require_webhook=require_webhook,
        require_verification=require_verification,
        environment=environment,
        usable_only=usable_only,
    )


def gateway_health() -> Dict[str, bool]:
    return _default_gateway_registry.health_check()


def gateway_status() -> List[Dict[str, Any]]:
    return _default_gateway_registry.status()


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    # Errors
    "GatewayRegistryError",
    "GatewayRegistrationError",
    "GatewayNotFoundError",
    "GatewaySelectionError",
    "GatewayCapabilityError",

    # Models
    "GatewayCapabilities",
    "RegisteredGateway",

    # Protocol
    "PaymentGatewayProtocol",

    # Registry
    "PaymentGatewayRegistry",

    # Helpers
    "get_gateway_registry",
    "register_payment_gateway",
    "get_payment_gateway",
    "require_payment_gateway",
    "select_payment_gateway",
    "gateway_health",
    "gateway_status",
]
