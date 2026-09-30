"""
AI usage, limits, credits, and request tracking.

This module is responsible for controlling AI consumption independently
from the AI provider itself.

Design goals:
- Plan-based daily limits
- Optional credit-based limits
- Per-user usage tracking
- Thread-safe in-memory storage for the first version
- Easy replacement with database-backed storage later
- No provider-specific logic
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from threading import Lock
from typing import Dict, Optional


# ============================================================
# EXCEPTIONS
# ============================================================

class AIUsageError(Exception):
    """Base exception for AI usage management."""


class AIUsageLimitError(AIUsageError):
    """Raised when a user reaches an AI usage limit."""


class AIInsufficientCreditsError(AIUsageError):
    """Raised when a user does not have enough credits."""


# ============================================================
# USAGE DATA
# ============================================================

@dataclass
class UsageRecord:
    """Usage information for one user."""

    user_id: str

    date: str = field(
        default_factory=lambda: datetime.now(timezone.utc).date().isoformat()
    )

    requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    credits_used: float = 0.0

    last_request_at: Optional[str] = None

    def reset_if_new_day(self) -> None:
        """Reset daily counters when the calendar day changes."""

        today = datetime.now(timezone.utc).date().isoformat()

        if self.date != today:
            self.date = today
            self.requests = 0
            self.successful_requests = 0
            self.failed_requests = 0
            self.input_tokens = 0
            self.output_tokens = 0
            self.total_tokens = 0
            self.credits_used = 0.0
            self.last_request_at = None

    def register_request(
        self,
        *,
        success: bool,
        input_tokens: int = 0,
        output_tokens: int = 0,
        credits: float = 0.0,
    ) -> None:
        """Register one AI request."""

        self.reset_if_new_day()

        self.requests += 1

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.input_tokens += max(0, int(input_tokens))
        self.output_tokens += max(0, int(output_tokens))

        self.total_tokens = (
            self.input_tokens + self.output_tokens
        )

        self.credits_used += max(0.0, float(credits))

        self.last_request_at = datetime.now(
            timezone.utc
        ).isoformat()

    def to_dict(self) -> dict:
        """Serialize usage data."""

        self.reset_if_new_day()

        return {
            "user_id": self.user_id,
            "date": self.date,
            "requests": self.requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "credits_used": round(self.credits_used, 4),
            "last_request_at": self.last_request_at,
        }


# ============================================================
# LIMITS
# ============================================================

@dataclass(frozen=True)
class UsageLimit:
    """AI usage limits for a plan."""

    plan: str

    daily_requests: Optional[int] = None

    daily_credits: Optional[float] = None

    max_tokens_per_request: Optional[int] = None

    enabled: bool = True

    def allows_request(self, usage: UsageRecord) -> bool:
        """Return True when the request is allowed."""

        if not self.enabled:
            return False

        usage.reset_if_new_day()

        if (
            self.daily_requests is not None
            and usage.requests >= self.daily_requests
        ):
            return False

        if (
            self.daily_credits is not None
            and usage.credits_used >= self.daily_credits
        ):
            return False

        return True


# ============================================================
# DEFAULT PLAN LIMITS
# ============================================================

DEFAULT_USAGE_LIMITS: Dict[str, UsageLimit] = {
    "free": UsageLimit(
        plan="free",
        daily_requests=10,
        daily_credits=None,
        max_tokens_per_request=1200,
    ),

    "basic": UsageLimit(
        plan="basic",
        daily_requests=50,
        daily_credits=None,
        max_tokens_per_request=2000,
    ),

    "professional": UsageLimit(
        plan="professional",
        daily_requests=200,
        daily_credits=None,
        max_tokens_per_request=4000,
    ),

    "business": UsageLimit(
        plan="business",
        daily_requests=1000,
        daily_credits=None,
        max_tokens_per_request=8000,
    ),
}


# ============================================================
# USAGE STORE
# ============================================================

class UsageStore:
    """
    Simple thread-safe usage store.

    This is intentionally storage-agnostic.

    Later this class can be replaced by:
        SQLiteUsageStore
        PostgreSQLUsageStore
        RedisUsageStore

    without changing the AI manager API.
    """

    def __init__(self) -> None:
        self._records: Dict[str, UsageRecord] = {}
        self._lock = Lock()

    def get(self, user_id: str) -> UsageRecord:
        """Get or create a user's usage record."""

        user_id = str(user_id)

        with self._lock:
            record = self._records.get(user_id)

            if record is None:
                record = UsageRecord(user_id=user_id)
                self._records[user_id] = record

            record.reset_if_new_day()

            return record

    def reset(self, user_id: str) -> None:
        """Reset one user's usage."""

        user_id = str(user_id)

        with self._lock:
            self._records[user_id] = UsageRecord(
                user_id=user_id
            )

    def clear(self) -> None:
        """Clear all in-memory usage records."""

        with self._lock:
            self._records.clear()

    def all_records(self) -> Dict[str, UsageRecord]:
        """Return a snapshot of all usage records."""

        with self._lock:
            return dict(self._records)


# ============================================================
# USAGE MANAGER
# ============================================================

class AIUsageManager:
    """
    High-level usage manager.

    Responsible for:
    - Plan limits
    - Request authorization
    - Credit authorization
    - Recording successful/failed requests
    - Usage summaries
    """

    def __init__(
        self,
        *,
        store: Optional[UsageStore] = None,
        limits: Optional[Dict[str, UsageLimit]] = None,
    ) -> None:

        self.store = store or UsageStore()

        self.limits = dict(
            limits or DEFAULT_USAGE_LIMITS
        )

    # --------------------------------------------------------
    # PLAN
    # --------------------------------------------------------

    def get_limit(
        self,
        plan: str,
    ) -> UsageLimit:
        """Get the usage limit for a plan."""

        normalized = str(plan or "free").strip().lower()

        return self.limits.get(
            normalized,
            self.limits["free"],
        )

    # --------------------------------------------------------
    # CHECK REQUEST
    # --------------------------------------------------------

    def check_request(
        self,
        *,
        user_id: str,
        plan: str = "free",
        estimated_credits: float = 0.0,
    ) -> UsageRecord:
        """
        Validate whether the user can make an AI request.

        Returns current usage when allowed.
        """

        record = self.store.get(user_id)

        limit = self.get_limit(plan)

        if not limit.enabled:
            raise AIUsageLimitError(
                "AI service is disabled for this plan."
            )

        if (
            limit.daily_requests is not None
            and record.requests >= limit.daily_requests
        ):
            raise AIUsageLimitError(
                f"Daily AI request limit reached for plan '{limit.plan}'."
            )

        if (
            limit.daily_credits is not None
            and (
                record.credits_used
                + max(0.0, float(estimated_credits))
                > limit.daily_credits
            )
        ):
            raise AIInsufficientCreditsError(
                "Daily AI credit limit reached."
            )

        return record

    # --------------------------------------------------------
    # RECORD
    # --------------------------------------------------------

    def record_success(
        self,
        *,
        user_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        credits: float = 0.0,
    ) -> UsageRecord:

        record = self.store.get(user_id)

        record.register_request(
            success=True,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            credits=credits,
        )

        return record

    def record_failure(
        self,
        *,
        user_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        credits: float = 0.0,
    ) -> UsageRecord:

        record = self.store.get(user_id)

        record.register_request(
            success=False,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            credits=credits,
        )

        return record

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    def get_usage(
        self,
        user_id: str,
    ) -> dict:

        return self.store.get(user_id).to_dict()

    def get_remaining_requests(
        self,
        *,
        user_id: str,
        plan: str = "free",
    ) -> Optional[int]:

        record = self.store.get(user_id)
        limit = self.get_limit(plan)

        if limit.daily_requests is None:
            return None

        return max(
            0,
            limit.daily_requests - record.requests,
        )

    def get_remaining_credits(
        self,
        *,
        user_id: str,
        plan: str = "free",
    ) -> Optional[float]:

        record = self.store.get(user_id)
        limit = self.get_limit(plan)

        if limit.daily_credits is None:
            return None

        return max(
            0.0,
            limit.daily_credits - record.credits_used,
        )

    def get_summary(
        self,
        *,
        user_id: str,
        plan: str = "free",
    ) -> dict:

        record = self.store.get(user_id)
        limit = self.get_limit(plan)

        return {
            "user_id": str(user_id),
            "plan": limit.plan,
            "date": record.date,
            "requests_used": record.requests,
            "requests_limit": limit.daily_requests,
            "requests_remaining": self.get_remaining_requests(
                user_id=user_id,
                plan=plan,
            ),
            "credits_used": round(
                record.credits_used,
                4,
            ),
            "credits_limit": limit.daily_credits,
            "credits_remaining": self.get_remaining_credits(
                user_id=user_id,
                plan=plan,
            ),
            "successful_requests": record.successful_requests,
            "failed_requests": record.failed_requests,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "total_tokens": record.total_tokens,
            "last_request_at": record.last_request_at,
        }


# ============================================================
# GLOBAL INSTANCE
# ============================================================

_default_usage_manager: Optional[AIUsageManager] = None


def get_ai_usage_manager() -> AIUsageManager:
    """Return the global AI usage manager."""

    global _default_usage_manager

    if _default_usage_manager is None:
        _default_usage_manager = AIUsageManager()

    return _default_usage_manager


def set_ai_usage_manager(
    manager: AIUsageManager,
) -> None:
    """Replace the global AI usage manager."""

    global _default_usage_manager

    _default_usage_manager = manager


# ============================================================
# CONVENIENCE HELPERS
# ============================================================

def check_ai_usage(
    *,
    user_id: str,
    plan: str = "free",
    estimated_credits: float = 0.0,
) -> UsageRecord:

    return get_ai_usage_manager().check_request(
        user_id=user_id,
        plan=plan,
        estimated_credits=estimated_credits,
    )


def record_ai_success(
    *,
    user_id: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    credits: float = 0.0,
) -> UsageRecord:

    return get_ai_usage_manager().record_success(
        user_id=user_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        credits=credits,
    )


def record_ai_failure(
    *,
    user_id: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    credits: float = 0.0,
) -> UsageRecord:

    return get_ai_usage_manager().record_failure(
        user_id=user_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        credits=credits,
    )


def get_ai_usage_summary(
    *,
    user_id: str,
    plan: str = "free",
) -> dict:

    return get_ai_usage_manager().get_summary(
        user_id=user_id,
        plan=plan,
    )


__all__ = [
    "AIUsageError",
    "AIUsageLimitError",
    "AIInsufficientCreditsError",
    "UsageRecord",
    "UsageLimit",
    "DEFAULT_USAGE_LIMITS",
    "UsageStore",
    "AIUsageManager",
    "get_ai_usage_manager",
    "set_ai_usage_manager",
    "check_ai_usage",
    "record_ai_success",
    "record_ai_failure",
    "get_ai_usage_summary",
]
