"""
StructuralBot - Subscription Management

User subscription lifecycle management.

Responsibilities:
- Subscription status
- Start/end dates
- Plan assignment
- Activation
- Renewal
- Cancellation
- Expiration
- Trial subscriptions
- Subscription history

Payment gateway logic is intentionally excluded.

A payment system should create/confirm a payment first,
then call this module to activate or renew a subscription.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import Lock
from typing import Dict, List, Optional

from billing.plans import (
    Plan,
    get_plan,
)


# ============================================================
# SUBSCRIPTION STATUS
# ============================================================

class SubscriptionStatus(str, Enum):
    """
    Subscription lifecycle states.
    """

    ACTIVE = "active"

    TRIAL = "trial"

    EXPIRED = "expired"

    CANCELLED = "cancelled"

    PENDING = "pending"

    SUSPENDED = "suspended"


# ============================================================
# SUBSCRIPTION
# ============================================================

@dataclass
class Subscription:
    """
    Represents one user's current subscription.
    """

    subscription_id: str

    user_id: str

    plan_code: str

    status: SubscriptionStatus = (
        SubscriptionStatus.ACTIVE
    )

    started_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    expires_at: Optional[str] = None

    cancelled_at: Optional[str] = None

    auto_renew: bool = False

    payment_reference: Optional[str] = None

    metadata: dict = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    updated_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    def get_plan(self) -> Plan:
        """Return associated plan."""

        return get_plan(
            self.plan_code
        )

    def is_active(
        self,
        now: Optional[datetime] = None,
    ) -> bool:
        """
        Check whether the subscription is currently active.
        """

        if self.status not in {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIAL,
        }:
            return False

        if self.expires_at is None:
            return True

        current = (
            now
            or datetime.now(
                timezone.utc
            )
        )

        try:
            expiry = datetime.fromisoformat(
                self.expires_at
            )
        except (
            TypeError,
            ValueError,
        ):
            return False

        if expiry.tzinfo is None:
            expiry = expiry.replace(
                tzinfo=timezone.utc
            )

        return current < expiry

    def is_expired(
        self,
        now: Optional[datetime] = None,
    ) -> bool:

        if self.expires_at is None:
            return False

        current = (
            now
            or datetime.now(
                timezone.utc
            )
        )

        try:
            expiry = datetime.fromisoformat(
                self.expires_at
            )
        except (
            TypeError,
            ValueError,
        ):
            return True

        if expiry.tzinfo is None:
            expiry = expiry.replace(
                tzinfo=timezone.utc
            )

        return current >= expiry

    def days_remaining(
        self,
        now: Optional[datetime] = None,
    ) -> Optional[int]:
        """
        Return remaining whole days.

        None means unlimited/no expiration.
        """

        if self.expires_at is None:
            return None

        current = (
            now
            or datetime.now(
                timezone.utc
            )
        )

        try:
            expiry = datetime.fromisoformat(
                self.expires_at
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

        if expiry.tzinfo is None:
            expiry = expiry.replace(
                tzinfo=timezone.utc
            )

        seconds = (
            expiry - current
        ).total_seconds()

        if seconds <= 0:
            return 0

        return int(
            seconds // 86400
        )

    def cancel(self) -> None:
        """
        Mark subscription as cancelled.

        Cancellation does not automatically erase remaining
        subscription time.
        """

        self.status = (
            SubscriptionStatus.CANCELLED
        )

        self.cancelled_at = datetime.now(
            timezone.utc
        ).isoformat()

        self.auto_renew = False

        self.updated_at = datetime.now(
            timezone.utc
        ).isoformat()

    def expire(self) -> None:
        """Mark subscription as expired."""

        self.status = (
            SubscriptionStatus.EXPIRED
        )

        self.auto_renew = False

        self.updated_at = datetime.now(
            timezone.utc
        ).isoformat()

    def to_dict(self) -> dict:
        """Serialize subscription."""

        return {
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "plan_code": self.plan_code,
            "status": (
                self.status.value
                if isinstance(
                    self.status,
                    SubscriptionStatus,
                )
                else str(self.status)
            ),
            "started_at": self.started_at,
            "expires_at": self.expires_at,
            "cancelled_at": self.cancelled_at,
            "auto_renew": self.auto_renew,
            "payment_reference": (
                self.payment_reference
            ),
            "days_remaining": self.days_remaining(),
            "active": self.is_active(),
            "metadata": dict(
                self.metadata
            ),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ============================================================
# SUBSCRIPTION MANAGER
# ============================================================

class SubscriptionManager:
    """
    Thread-safe subscription manager.

    Current implementation uses in-memory storage.

    Later it can be replaced by a database-backed repository
    without changing the public manager API.
    """

    def __init__(self) -> None:

        self._subscriptions: Dict[
            str,
            Subscription,
        ] = {}

        self._history: Dict[
            str,
            List[Subscription],
        ] = {}

        self._lock = Lock()

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    @staticmethod
    def _normalize_user_id(
        user_id: str,
    ) -> str:

        if user_id is None:
            raise ValueError(
                "user_id is required."
            )

        value = str(
            user_id
        ).strip()

        if not value:
            raise ValueError(
                "user_id cannot be empty."
            )

        return value

    @staticmethod
    def _subscription_id(
        user_id: str,
    ) -> str:

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%d%H%M%S%f"
        )

        return (
            f"sub_{user_id}_{timestamp}"
        )

    @staticmethod
    def _parse_datetime(
        value: Optional[str],
    ) -> Optional[datetime]:

        if not value:
            return None

        try:
            result = datetime.fromisoformat(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        if result.tzinfo is None:
            result = result.replace(
                tzinfo=timezone.utc
            )

        return result

    @staticmethod
    def _calculate_expiry(
        *,
        start: datetime,
        duration_days: Optional[int],
    ) -> Optional[str]:

        if duration_days is None:
            return None

        if duration_days <= 0:
            return None

        return (
            start
            + timedelta(
                days=duration_days
            )
        ).isoformat()

    def _save_history(
        self,
        subscription: Subscription,
    ) -> None:

        user_id = subscription.user_id

        self._history.setdefault(
            user_id,
            [],
        ).append(
            subscription
        )

    # ========================================================
    # GET CURRENT
    # ========================================================

    def get_subscription(
        self,
        user_id: str,
    ) -> Optional[Subscription]:

        user_id = self._normalize_user_id(
            user_id
        )

        with self._lock:

            subscription = self._subscriptions.get(
                user_id
            )

            if subscription is None:
                return None

            self._refresh_expiration(
                subscription
            )

            return subscription

    def get_plan(
        self,
        user_id: str,
    ) -> Plan:

        subscription = self.get_subscription(
            user_id
        )

        if subscription is None:
            return get_plan(
                "free"
            )

        if not subscription.is_active():

            return get_plan(
                "free"
            )

        return subscription.get_plan()

    # ========================================================
    # EXPIRATION
    # ========================================================

    def _refresh_expiration(
        self,
        subscription: Subscription,
    ) -> None:

        if (
            subscription.status
            not in {
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIAL,
            }
        ):
            return

        if subscription.is_expired():

            subscription.expire()

    def refresh(
        self,
        user_id: str,
    ) -> Optional[Subscription]:

        subscription = self.get_subscription(
            user_id
        )

        if subscription is not None:

            with self._lock:
                self._refresh_expiration(
                    subscription
                )

        return subscription

    # ========================================================
    # ACTIVATE
    # ========================================================

    def activate(
        self,
        *,
        user_id: str,
        plan_code: str,
        duration_days: Optional[int] = None,
        payment_reference: Optional[str] = None,
        auto_renew: bool = False,
        metadata: Optional[dict] = None,
    ) -> Subscription:

        user_id = self._normalize_user_id(
            user_id
        )

        plan = get_plan(
            plan_code
        )

        now = datetime.now(
            timezone.utc
        )

        duration = (
            duration_days
            if duration_days is not None
            else plan.duration_days
        )

        subscription = Subscription(
            subscription_id=self._subscription_id(
                user_id
            ),
            user_id=user_id,
            plan_code=plan.code,
            status=(
                SubscriptionStatus.TRIAL
                if plan.trial
                else SubscriptionStatus.ACTIVE
            ),
            started_at=now.isoformat(),
            expires_at=self._calculate_expiry(
                start=now,
                duration_days=duration,
            ),
            auto_renew=auto_renew,
            payment_reference=(
                payment_reference
            ),
            metadata=dict(
                metadata or {}
            ),
        )

        with self._lock:

            previous = self._subscriptions.get(
                user_id
            )

            if previous is not None:
                self._save_history(
                    previous
                )

            self._subscriptions[
                user_id
            ] = subscription

        return subscription

    # ========================================================
    # TRIAL
    # ========================================================

    def start_trial(
        self,
        *,
        user_id: str,
        plan_code: str = "basic",
        duration_days: int = 7,
        metadata: Optional[dict] = None,
    ) -> Subscription:

        user_id = self._normalize_user_id(
            user_id
        )

        plan = get_plan(
            plan_code
        )

        now = datetime.now(
            timezone.utc
        )

        subscription = Subscription(
            subscription_id=self._subscription_id(
                user_id
            ),
            user_id=user_id,
            plan_code=plan.code,
            status=(
                SubscriptionStatus.TRIAL
            ),
            started_at=now.isoformat(),
            expires_at=self._calculate_expiry(
                start=now,
                duration_days=duration_days,
            ),
            auto_renew=False,
            metadata={
                "trial": True,
                **dict(
                    metadata or {}
                ),
            },
        )

        with self._lock:

            previous = self._subscriptions.get(
                user_id
            )

            if previous is not None:
                self._save_history(
                    previous
                )

            self._subscriptions[
                user_id
            ] = subscription

        return subscription

    # ========================================================
    # RENEW
    # ========================================================

    def renew(
        self,
        *,
        user_id: str,
        plan_code: Optional[str] = None,
        duration_days: Optional[int] = None,
        payment_reference: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Subscription:

        user_id = self._normalize_user_id(
            user_id
        )

        with self._lock:

            current = self._subscriptions.get(
                user_id
            )

            if current is None:
                raise ValueError(
                    "No existing subscription to renew."
                )

            self._refresh_expiration(
                current
            )

            selected_plan = get_plan(
                plan_code
                or current.plan_code
            )

            now = datetime.now(
                timezone.utc
            )

            duration = (
                duration_days
                if duration_days is not None
                else selected_plan.duration_days
            )

            current_expiry = (
                self._parse_datetime(
                    current.expires_at
                )
            )

            if (
                current_expiry is not None
                and current_expiry > now
            ):
                start = current_expiry
            else:
                start = now

            renewed = Subscription(
                subscription_id=self._subscription_id(
                    user_id
                ),
                user_id=user_id,
                plan_code=selected_plan.code,
                status=(
                    SubscriptionStatus.TRIAL
                    if selected_plan.trial
                    else SubscriptionStatus.ACTIVE
                ),
                started_at=now.isoformat(),
                expires_at=self._calculate_expiry(
                    start=start,
                    duration_days=duration,
                ),
                auto_renew=current.auto_renew,
                payment_reference=(
                    payment_reference
                    or current.payment_reference
                ),
                metadata={
                    **dict(
                        current.metadata
                    ),
                    **dict(
                        metadata or {}
                    ),
                },
            )

            self._save_history(
                current
            )

            self._subscriptions[
                user_id
            ] = renewed

            return renewed

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel(
        self,
        user_id: str,
    ) -> Optional[Subscription]:

        user_id = self._normalize_user_id(
            user_id
        )

        with self._lock:

            subscription = self._subscriptions.get(
                user_id
            )

            if subscription is None:
                return None

            subscription.cancel()

            return subscription

    # ========================================================
    # SUSPEND
    # ========================================================

    def suspend(
        self,
        user_id: str,
    ) -> Optional[Subscription]:

        user_id = self._normalize_user_id(
            user_id
        )

        with self._lock:

            subscription = self._subscriptions.get(
                user_id
            )

            if subscription is None:
                return None

            subscription.status = (
                SubscriptionStatus.SUSPENDED
            )

            subscription.updated_at = datetime.now(
                timezone.utc
            ).isoformat()

            return subscription

    # ========================================================
    # RESTORE
    # ========================================================

    def restore(
        self,
        user_id: str,
    ) -> Optional[Subscription]:

        user_id = self._normalize_user_id(
            user_id
        )

        with self._lock:

            subscription = self._subscriptions.get(
                user_id
            )

            if subscription is None:
                return None

            if subscription.is_expired():

                subscription.expire()

                return subscription

            if subscription.status == (
                SubscriptionStatus.SUSPENDED
            ):

                subscription.status = (
                    SubscriptionStatus.ACTIVE
                )

                subscription.updated_at = datetime.now(
                    timezone.utc
                ).isoformat()

            return subscription

    # ========================================================
    # HISTORY
    # ========================================================

    def get_history(
        self,
        user_id: str,
    ) -> List[Subscription]:

        user_id = self._normalize_user_id(
            user_id
        )

        with self._lock:

            history = list(
                self._history.get(
                    user_id,
                    [],
                )
            )

            current = self._subscriptions.get(
                user_id
            )

            if current is not None:
                history.append(
                    current
                )

            return list(
                reversed(history)
            )

    def get_history_dicts(
        self,
        user_id: str,
    ) -> List[dict]:

        return [
            item.to_dict()
            for item in self.get_history(
                user_id
            )
        ]

    # ========================================================
    # ACCESS
    # ========================================================

    def is_active(
        self,
        user_id: str,
    ) -> bool:

        subscription = self.get_subscription(
            user_id
        )

        if subscription is None:
            return False

        return subscription.is_active()

    def get_status(
        self,
        user_id: str,
    ) -> SubscriptionStatus:

        subscription = self.get_subscription(
            user_id
        )

        if subscription is None:
            return SubscriptionStatus.EXPIRED

        self._refresh_expiration(
            subscription
        )

        return subscription.status

    # ========================================================
    # SUMMARY
    # ========================================================

    def get_summary(
        self,
        user_id: str,
    ) -> dict:

        subscription = self.get_subscription(
            user_id
        )

        if subscription is None:

            plan = get_plan(
                "free"
            )

            return {
                "user_id": str(
                    user_id
                ),
                "plan_code": plan.code,
                "plan_name": plan.name,
                "status": "free",
                "active": True,
                "expires_at": None,
                "days_remaining": None,
            }

        plan = (
            subscription.get_plan()
            if subscription.is_active()
            else get_plan("free")
        )

        return {
            "user_id": subscription.user_id,
            "subscription_id": (
                subscription.subscription_id
            ),
            "plan_code": plan.code,
            "plan_name": plan.name,
            "status": (
                subscription.status.value
            ),
            "active": subscription.is_active(),
            "started_at": (
                subscription.started_at
            ),
            "expires_at": (
                subscription.expires_at
            ),
            "days_remaining": (
                subscription.days_remaining()
            ),
            "auto_renew": (
                subscription.auto_renew
            ),
            "payment_reference": (
                subscription.payment_reference
            ),
        }

    # ========================================================
    # RESET
    # ========================================================

    def reset_user(
        self,
        user_id: str,
    ) -> None:

        user_id = self._normalize_user_id(
            user_id
        )

        with self._lock:

            self._subscriptions.pop(
                user_id,
                None,
            )

            self._history.pop(
                user_id,
                None,
            )

    def clear(self) -> None:

        with self._lock:

            self._subscriptions.clear()

            self._history.clear()


# ============================================================
# GLOBAL MANAGER
# ============================================================

_default_subscription_manager: Optional[
    SubscriptionManager
] = None


def get_subscription_manager() -> SubscriptionManager:
    """Return global subscription manager."""

    global _default_subscription_manager

    if _default_subscription_manager is None:

        _default_subscription_manager = (
            SubscriptionManager()
        )

    return _default_subscription_manager


def set_subscription_manager(
    manager: SubscriptionManager,
) -> None:

    global _default_subscription_manager

    _default_subscription_manager = manager


# ============================================================
# CONVENIENCE HELPERS
# ============================================================

def get_user_subscription(
    user_id: str,
) -> Optional[Subscription]:

    return get_subscription_manager().get_subscription(
        user_id
    )


def get_user_plan(
    user_id: str,
) -> Plan:

    return get_subscription_manager().get_plan(
        user_id
    )


def activate_user_subscription(
    *,
    user_id: str,
    plan_code: str,
    duration_days: Optional[int] = None,
    payment_reference: Optional[str] = None,
) -> Subscription:

    return get_subscription_manager().activate(
        user_id=user_id,
        plan_code=plan_code,
        duration_days=duration_days,
        payment_reference=payment_reference,
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "SubscriptionStatus",
    "Subscription",
    "SubscriptionManager",
    "get_subscription_manager",
    "set_subscription_manager",
    "get_user_subscription",
    "get_user_plan",
    "activate_user_subscription",
]
