"""
StructuralBot - Billing Notification Transport Layer

Provider-agnostic transport infrastructure for billing notifications.

Responsibilities:
- Define a stable notification transport interface
- Keep billing business logic independent from Telegram/email/SMS providers
- Provide a safe in-memory transport for development and testing
- Normalize transport results
- Support future Telegram, Email, SMS, Push and Webhook adapters

IMPORTANT:
This module does NOT send real messages.
Real provider integrations should be implemented in separate adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Dict, Iterable, List, Mapping, Optional, Protocol
from uuid import uuid4


# ============================================================
# HELPERS
# ============================================================


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _normalize_id(value: Any) -> str:
    return _safe_str(value)


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


# ============================================================
# ENUMS
# ============================================================


class TransportErrorCode(str, Enum):
    """Normalized transport error categories."""

    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    INVALID_RECIPIENT = "invalid_recipient"
    INVALID_MESSAGE = "invalid_message"
    PROVIDER = "provider"
    TIMEOUT = "timeout"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class TransportStatus(str, Enum):
    """Normalized result status."""

    ACCEPTED = "accepted"
    SENT = "sent"
    QUEUED = "queued"
    FAILED = "failed"
    SKIPPED = "skipped"


# ============================================================
# ERRORS
# ============================================================


class NotificationTransportError(Exception):
    """Base notification transport error."""


class TransportConfigurationError(NotificationTransportError):
    """Transport configuration is invalid or incomplete."""


class TransportProviderError(NotificationTransportError):
    """Underlying provider returned an error."""


class TransportValidationError(NotificationTransportError):
    """Notification payload is invalid."""


class TransportUnsupportedError(NotificationTransportError):
    """Requested operation/channel is not supported."""


# ============================================================
# DATA MODELS
# ============================================================


@dataclass(frozen=True)
class TransportMessage:
    """
    Provider-independent notification message.

    The billing layer can create this object without knowing
    whether the final destination is Telegram, email, SMS, etc.
    """

    notification_id: str
    user_id: str
    channel: str
    recipient: str
    subject: str = ""
    body: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _normalize_id(self.notification_id):
            raise TransportValidationError(
                "notification_id cannot be empty."
            )

        if not _normalize_id(self.user_id):
            raise TransportValidationError(
                "user_id cannot be empty."
            )

        if not _normalize_id(self.channel):
            raise TransportValidationError(
                "channel cannot be empty."
            )

        if not _normalize_id(self.recipient):
            raise TransportValidationError(
                "recipient cannot be empty."
            )

        if not self.body and not self.subject:
            raise TransportValidationError(
                "Notification must contain body or subject."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "channel": self.channel,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "metadata": dict(self.metadata),
        }


@dataclass
class TransportResult:
    """
    Normalized result returned by every transport adapter.
    """

    transport_id: str
    notification_id: str
    status: TransportStatus

    provider: str = ""
    channel: str = ""

    provider_message_id: Optional[str] = None

    error_code: Optional[TransportErrorCode] = None
    error_message: Optional[str] = None

    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status in {
            TransportStatus.ACCEPTED,
            TransportStatus.SENT,
            TransportStatus.QUEUED,
        }

    @property
    def failed(self) -> bool:
        return self.status == TransportStatus.FAILED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transport_id": self.transport_id,
            "notification_id": self.notification_id,
            "status": self.status.value,
            "provider": self.provider,
            "channel": self.channel,
            "provider_message_id": self.provider_message_id,
            "error_code": (
                self.error_code.value
                if self.error_code
                else None
            ),
            "error_message": self.error_message,
            "accepted_at": (
                self.accepted_at.isoformat()
                if self.accepted_at
                else None
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at
                else None
            ),
            "metadata": dict(self.metadata),
        }


# ============================================================
# TRANSPORT PROTOCOL
# ============================================================


class NotificationTransport(Protocol):
    """
    Provider-independent notification transport contract.

    Concrete adapters should implement this protocol.
    """

    name: str

    def supports_channel(self, channel: str) -> bool:
        ...

    def send(self, message: TransportMessage) -> TransportResult:
        ...

    def health_check(self) -> bool:
        ...


# ============================================================
# BASE TRANSPORT
# ============================================================


class BaseNotificationTransport:
    """
    Common base class for concrete notification transports.
    """

    name = "base"

    supported_channels: frozenset[str] = frozenset()

    def supports_channel(self, channel: str) -> bool:
        return _safe_str(channel).lower() in {
            value.lower()
            for value in self.supported_channels
        }

    def health_check(self) -> bool:
        return True

    def validate_message(
        self,
        message: TransportMessage,
    ) -> None:
        if not self.supports_channel(message.channel):
            raise TransportUnsupportedError(
                f"Transport '{self.name}' does not support "
                f"channel '{message.channel}'."
            )

    def send(
        self,
        message: TransportMessage,
    ) -> TransportResult:
        raise NotImplementedError


# ============================================================
# IN-MEMORY TRANSPORT
# ============================================================


class InMemoryNotificationTransport(BaseNotificationTransport):
    """
    Development/test transport.

    It records messages in memory instead of sending them.

    This is useful for:
    - Unit tests
    - Integration tests
    - Local development
    - Billing flow testing
    - Bot callback testing

    No external network call is performed.
    """

    name = "memory"

    supported_channels = frozenset(
        {
            "telegram",
            "email",
            "sms",
            "push",
            "webhook",
            "internal",
        }
    )

    def __init__(self) -> None:
        self._messages: List[TransportMessage] = []
        self._results: List[TransportResult] = []
        self._lock = RLock()

    def send(
        self,
        message: TransportMessage,
    ) -> TransportResult:

        self.validate_message(message)

        now = _utcnow()

        result = TransportResult(
            transport_id=_generate_id("transport"),
            notification_id=message.notification_id,
            status=TransportStatus.SENT,
            provider=self.name,
            channel=message.channel,
            provider_message_id=_generate_id("memory_msg"),
            accepted_at=now,
            completed_at=now,
        )

        with self._lock:
            self._messages.append(message)
            self._results.append(result)

        return result

    def messages(self) -> List[TransportMessage]:
        with self._lock:
            return list(self._messages)

    def results(self) -> List[TransportResult]:
        with self._lock:
            return list(self._results)

    def get_message(
        self,
        notification_id: str,
    ) -> Optional[TransportMessage]:

        notification_id = _normalize_id(notification_id)

        with self._lock:
            for message in reversed(self._messages):
                if message.notification_id == notification_id:
                    return message

        return None

    def clear(self) -> None:
        with self._lock:
            self._messages.clear()
            self._results.clear()


# ============================================================
# TELEGRAM PLACEHOLDER TRANSPORT
# ============================================================


class TelegramNotificationTransport(BaseNotificationTransport):
    """
    Placeholder Telegram transport.

    Real Telegram delivery should be implemented later using
    the bot application's existing Telegram client.

    Keeping it as a separate adapter prevents billing logic
    from becoming coupled to python-telegram-bot.
    """

    name = "telegram"

    supported_channels = frozenset({"telegram"})

    def __init__(
        self,
        bot_token: Optional[str] = None,
    ) -> None:
        self.bot_token = _safe_str(bot_token)

    def health_check(self) -> bool:
        return bool(self.bot_token)

    def send(
        self,
        message: TransportMessage,
    ) -> TransportResult:

        self.validate_message(message)

        if not self.bot_token:
            return TransportResult(
                transport_id=_generate_id("transport"),
                notification_id=message.notification_id,
                status=TransportStatus.FAILED,
                provider=self.name,
                channel=message.channel,
                error_code=TransportErrorCode.CONFIGURATION,
                error_message=(
                    "Telegram bot token is not configured."
                ),
            )

        # Intentionally not performing network I/O here.
        return TransportResult(
            transport_id=_generate_id("transport"),
            notification_id=message.notification_id,
            status=TransportStatus.SKIPPED,
            provider=self.name,
            channel=message.channel,
            metadata={
                "reason": "telegram_adapter_not_connected",
            },
        )


# ============================================================
# TRANSPORT REGISTRY
# ============================================================


class NotificationTransportRegistry:
    """
    Registry for notification transport adapters.

    The registry lets the application select a transport by
    channel without embedding provider-specific logic in
    billing services.
    """

    def __init__(self) -> None:
        self._transports: Dict[str, NotificationTransport] = {}
        self._lock = RLock()

    def register(
        self,
        transport: NotificationTransport,
        *,
        replace: bool = True,
    ) -> None:

        name = _safe_str(
            getattr(transport, "name", "")
        ).lower()

        if not name:
            raise TransportValidationError(
                "Transport must define a non-empty name."
            )

        with self._lock:
            if name in self._transports and not replace:
                raise TransportValidationError(
                    f"Transport '{name}' is already registered."
                )

            self._transports[name] = transport

    def unregister(self, name: str) -> bool:
        name = _safe_str(name).lower()

        with self._lock:
            return self._transports.pop(name, None) is not None

    def get(
        self,
        name: str,
    ) -> Optional[NotificationTransport]:

        name = _safe_str(name).lower()

        with self._lock:
            return self._transports.get(name)

    def require(
        self,
        name: str,
    ) -> NotificationTransport:

        transport = self.get(name)

        if transport is None:
            raise TransportConfigurationError(
                f"Transport '{name}' is not registered."
            )

        return transport

    def all(self) -> List[NotificationTransport]:
        with self._lock:
            return list(self._transports.values())

    def names(self) -> List[str]:
        with self._lock:
            return sorted(self._transports.keys())

    def find_for_channel(
        self,
        channel: str,
    ) -> Optional[NotificationTransport]:

        channel = _safe_str(channel).lower()

        with self._lock:
            transports = list(self._transports.values())

        for transport in transports:
            try:
                if transport.supports_channel(channel):
                    return transport
            except Exception:
                continue

        return None

    def require_for_channel(
        self,
        channel: str,
    ) -> NotificationTransport:

        transport = self.find_for_channel(channel)

        if transport is None:
            raise TransportUnsupportedError(
                f"No notification transport supports "
                f"channel '{channel}'."
            )

        return transport

    def clear(self) -> None:
        with self._lock:
            self._transports.clear()


# ============================================================
# TRANSPORT MANAGER
# ============================================================


class NotificationTransportManager:
    """
    High-level transport facade.

    Billing code should normally call this manager instead of
    directly selecting Telegram/email/SMS adapters.
    """

    def __init__(
        self,
        registry: Optional[NotificationTransportRegistry] = None,
    ) -> None:

        self.registry = (
            registry
            or NotificationTransportRegistry()
        )

    def register(
        self,
        transport: NotificationTransport,
        *,
        replace: bool = True,
    ) -> None:

        self.registry.register(
            transport,
            replace=replace,
        )

    def send(
        self,
        message: TransportMessage,
        *,
        transport_name: Optional[str] = None,
    ) -> TransportResult:

        if transport_name:
            transport = self.registry.require(
                transport_name
            )
        else:
            transport = self.registry.require_for_channel(
                message.channel
            )

        try:
            return transport.send(message)

        except TransportValidationError:
            raise

        except NotificationTransportError as exc:
            return TransportResult(
                transport_id=_generate_id("transport"),
                notification_id=message.notification_id,
                status=TransportStatus.FAILED,
                provider=getattr(
                    transport,
                    "name",
                    "",
                ),
                channel=message.channel,
                error_code=TransportErrorCode.PROVIDER,
                error_message=str(exc),
            )

        except TimeoutError as exc:
            return TransportResult(
                transport_id=_generate_id("transport"),
                notification_id=message.notification_id,
                status=TransportStatus.FAILED,
                provider=getattr(
                    transport,
                    "name",
                    "",
                ),
                channel=message.channel,
                error_code=TransportErrorCode.TIMEOUT,
                error_message=str(exc),
            )

        except Exception as exc:
            return TransportResult(
                transport_id=_generate_id("transport"),
                notification_id=message.notification_id,
                status=TransportStatus.FAILED,
                provider=getattr(
                    transport,
                    "name",
                    "",
                ),
                channel=message.channel,
                error_code=TransportErrorCode.UNKNOWN,
                error_message=str(exc),
            )

    def send_many(
        self,
        messages: Iterable[TransportMessage],
    ) -> List[TransportResult]:

        results: List[TransportResult] = []

        for message in messages:
            results.append(self.send(message))

        return results

    def health_check(self) -> Dict[str, bool]:
        result: Dict[str, bool] = {}

        for transport in self.registry.all():
            try:
                result[
                    getattr(transport, "name", "unknown")
                ] = bool(
                    transport.health_check()
                )
            except Exception:
                result[
                    getattr(transport, "name", "unknown")
                ] = False

        return result


# ============================================================
# DEFAULT REGISTRY / MANAGER
# ============================================================


_default_transport_registry = (
    NotificationTransportRegistry()
)

_default_memory_transport = (
    InMemoryNotificationTransport()
)

_default_telegram_transport = (
    TelegramNotificationTransport()
)

_default_transport_registry.register(
    _default_memory_transport
)

_default_transport_registry.register(
    _default_telegram_transport
)

_default_transport_manager = (
    NotificationTransportManager(
        registry=_default_transport_registry
    )
)


# ============================================================
# PUBLIC HELPERS
# ============================================================


def get_transport_registry() -> NotificationTransportRegistry:
    return _default_transport_registry


def get_transport_manager() -> NotificationTransportManager:
    return _default_transport_manager


def register_notification_transport(
    transport: NotificationTransport,
    *,
    replace: bool = True,
) -> None:

    _default_transport_registry.register(
        transport,
        replace=replace,
    )


def send_notification(
    message: TransportMessage,
    *,
    transport_name: Optional[str] = None,
) -> TransportResult:

    return _default_transport_manager.send(
        message,
        transport_name=transport_name,
    )


def send_notifications(
    messages: Iterable[TransportMessage],
) -> List[TransportResult]:

    return _default_transport_manager.send_many(
        messages
    )


def transport_health() -> Dict[str, bool]:
    return _default_transport_manager.health_check()


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    # Errors
    "NotificationTransportError",
    "TransportConfigurationError",
    "TransportProviderError",
    "TransportValidationError",
    "TransportUnsupportedError",

    # Enums
    "TransportErrorCode",
    "TransportStatus",

    # Models
    "TransportMessage",
    "TransportResult",

    # Protocol/base
    "NotificationTransport",
    "BaseNotificationTransport",

    # Transports
    "InMemoryNotificationTransport",
    "TelegramNotificationTransport",

    # Registry/manager
    "NotificationTransportRegistry",
    "NotificationTransportManager",

    # Globals/helpers
    "get_transport_registry",
    "get_transport_manager",
    "register_notification_transport",
    "send_notification",
    "send_notifications",
    "transport_health",
]
