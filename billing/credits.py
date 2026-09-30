"""
StructuralBot - Credits

Credit accounting for paid and metered features.

Credits can later be consumed by:
- AI requests
- PDF generation
- Excel generation
- Advanced calculations
- Premium reports
- API usage
- Other metered services

This module contains business logic only.
Payment gateway integration belongs elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Dict, List, Optional


# ============================================================
# EXCEPTIONS
# ============================================================

class CreditError(Exception):
    """Base credit exception."""


class InsufficientCreditsError(CreditError):
    """Raised when a user does not have enough credits."""


class InvalidCreditAmountError(CreditError):
    """Raised for invalid credit amounts."""


class CreditTransactionError(CreditError):
    """Raised when a credit transaction cannot be completed."""


# ============================================================
# TRANSACTION TYPES
# ============================================================

class CreditTransactionType(str, Enum):
    """
    Types of credit movements.
    """

    PURCHASE = "purchase"

    BONUS = "bonus"

    REFUND = "refund"

    ADMIN_GRANT = "admin_grant"

    CONSUMPTION = "consumption"

    EXPIRATION = "expiration"

    ADJUSTMENT = "adjustment"


# ============================================================
# CREDIT BALANCE
# ============================================================

@dataclass
class CreditBalance:
    """
    Current credit balance for one user.
    """

    user_id: str

    balance: float = 0.0

    total_purchased: float = 0.0

    total_bonus: float = 0.0

    total_consumed: float = 0.0

    total_refunded: float = 0.0

    total_expired: float = 0.0

    updated_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    def available(self) -> float:
        """Return available balance."""

        return max(
            0.0,
            float(self.balance),
        )

    def has(
        self,
        amount: float,
    ) -> bool:
        """Check whether enough credits exist."""

        amount = float(amount)

        if amount < 0:
            return False

        return self.balance >= amount

    def add(
        self,
        amount: float,
        transaction_type: CreditTransactionType,
    ) -> None:
        """Add credits."""

        amount = float(amount)

        if amount <= 0:
            raise InvalidCreditAmountError(
                "Credit amount must be greater than zero."
            )

        self.balance += amount

        if transaction_type == CreditTransactionType.PURCHASE:
            self.total_purchased += amount

        elif transaction_type == CreditTransactionType.BONUS:
            self.total_bonus += amount

        elif transaction_type == CreditTransactionType.REFUND:
            self.total_refunded += amount

        elif transaction_type == CreditTransactionType.ADMIN_GRANT:
            self.total_bonus += amount

        self.updated_at = datetime.now(
            timezone.utc
        ).isoformat()

    def consume(
        self,
        amount: float,
    ) -> None:
        """Consume credits."""

        amount = float(amount)

        if amount <= 0:
            raise InvalidCreditAmountError(
                "Credit amount must be greater than zero."
            )

        if self.balance < amount:
            raise InsufficientCreditsError(
                "Insufficient credits."
            )

        self.balance -= amount

        self.total_consumed += amount

        self.updated_at = datetime.now(
            timezone.utc
        ).isoformat()

    def expire(
        self,
        amount: float,
    ) -> None:
        """Expire credits."""

        amount = float(amount)

        if amount <= 0:
            raise InvalidCreditAmountError(
                "Credit amount must be greater than zero."
            )

        if self.balance < amount:
            amount = self.balance

        self.balance -= amount

        self.total_expired += amount

        self.updated_at = datetime.now(
            timezone.utc
        ).isoformat()

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "balance": round(
                self.balance,
                4,
            ),
            "available": round(
                self.available(),
                4,
            ),
            "total_purchased": round(
                self.total_purchased,
                4,
            ),
            "total_bonus": round(
                self.total_bonus,
                4,
            ),
            "total_consumed": round(
                self.total_consumed,
                4,
            ),
            "total_refunded": round(
                self.total_refunded,
                4,
            ),
            "total_expired": round(
                self.total_expired,
                4,
            ),
            "updated_at": self.updated_at,
        }


# ============================================================
# CREDIT TRANSACTION
# ============================================================

@dataclass(frozen=True)
class CreditTransaction:
    """
    Immutable credit transaction record.
    """

    transaction_id: str

    user_id: str

    amount: float

    transaction_type: CreditTransactionType

    description: str = ""

    reference_id: Optional[str] = None

    metadata: dict = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "amount": round(
                self.amount,
                4,
            ),
            "transaction_type": (
                self.transaction_type.value
                if isinstance(
                    self.transaction_type,
                    CreditTransactionType,
                )
                else str(
                    self.transaction_type
                )
            ),
            "description": self.description,
            "reference_id": self.reference_id,
            "metadata": dict(
                self.metadata
            ),
            "created_at": self.created_at,
        }


# ============================================================
# CREDIT MANAGER
# ============================================================

class CreditManager:
    """
    Thread-safe in-memory credit manager.

    This is the business-logic layer.

    It can later be backed by:
        SQLite
        PostgreSQL
        Redis
        another persistent store

    without changing handler-level APIs.
    """

    def __init__(self) -> None:

        self._balances: Dict[
            str,
            CreditBalance,
        ] = {}

        self._transactions: Dict[
            str,
            List[CreditTransaction],
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
    def _validate_amount(
        amount: float,
    ) -> float:

        try:
            value = float(
                amount
            )
        except (
            TypeError,
            ValueError,
        ) as exc:

            raise InvalidCreditAmountError(
                "Credit amount must be numeric."
            ) from exc

        if value <= 0:
            raise InvalidCreditAmountError(
                "Credit amount must be greater than zero."
            )

        return value

    @staticmethod
    def _transaction_id(
        user_id: str,
        index: int,
    ) -> str:

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%d%H%M%S%f"
        )

        return (
            f"cr_{user_id}_"
            f"{timestamp}_"
            f"{index}"
        )

    def _get_or_create_balance(
        self,
        user_id: str,
    ) -> CreditBalance:

        balance = self._balances.get(
            user_id
        )

        if balance is None:

            balance = CreditBalance(
                user_id=user_id
            )

            self._balances[
                user_id
            ] = balance

        return balance

    def _add_transaction(
        self,
        transaction: CreditTransaction,
    ) -> CreditTransaction:

        self._transactions.setdefault(
            transaction.user_id,
            [],
        ).append(
            transaction
        )

        return transaction

    # ========================================================
    # BALANCE
    # ========================================================

    def get_balance(
        self,
        user_id: str,
    ) -> CreditBalance:

        user_id = self._normalize_user_id(
            user_id
        )

        with self._lock:

            return self._get_or_create_balance(
                user_id
            )

    def get_balance_dict(
        self,
        user_id: str,
    ) -> dict:

        return self.get_balance(
            user_id
        ).to_dict()

    # ========================================================
    # ADD CREDITS
    # ========================================================

    def add_credits(
        self,
        *,
        user_id: str,
        amount: float,
        transaction_type: CreditTransactionType = (
            CreditTransactionType.BONUS
        ),
        description: str = "",
        reference_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> CreditTransaction:

        user_id = self._normalize_user_id(
            user_id
        )

        amount = self._validate_amount(
            amount
        )

        if transaction_type in {
            CreditTransactionType.CONSUMPTION,
            CreditTransactionType.EXPIRATION,
        }:

            raise CreditTransactionError(
                "This transaction type cannot add credits."
            )

        with self._lock:

            balance = self._get_or_create_balance(
                user_id
            )

            balance.add(
                amount,
                transaction_type,
            )

            transaction = CreditTransaction(
                transaction_id=self._transaction_id(
                    user_id,
                    len(
                        self._transactions.get(
                            user_id,
                            [],
                        )
                    ),
                ),
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                reference_id=reference_id,
                metadata=dict(
                    metadata or {}
                ),
            )

            return self._add_transaction(
                transaction
            )

    # ========================================================
    # PURCHASE
    # ========================================================

    def purchase_credits(
        self,
        *,
        user_id: str,
        amount: float,
        reference_id: Optional[str] = None,
        description: str = "Credit purchase",
        metadata: Optional[dict] = None,
    ) -> CreditTransaction:

        return self.add_credits(
            user_id=user_id,
            amount=amount,
            transaction_type=(
                CreditTransactionType.PURCHASE
            ),
            description=description,
            reference_id=reference_id,
            metadata=metadata,
        )

    # ========================================================
    # BONUS
    # ========================================================

    def grant_bonus(
        self,
        *,
        user_id: str,
        amount: float,
        reference_id: Optional[str] = None,
        description: str = "Bonus credits",
        metadata: Optional[dict] = None,
    ) -> CreditTransaction:

        return self.add_credits(
            user_id=user_id,
            amount=amount,
            transaction_type=(
                CreditTransactionType.BONUS
            ),
            description=description,
            reference_id=reference_id,
            metadata=metadata,
        )

    # ========================================================
    # REFUND
    # ========================================================

    def refund_credits(
        self,
        *,
        user_id: str,
        amount: float,
        reference_id: Optional[str] = None,
        description: str = "Credit refund",
        metadata: Optional[dict] = None,
    ) -> CreditTransaction:

        return self.add_credits(
            user_id=user_id,
            amount=amount,
            transaction_type=(
                CreditTransactionType.REFUND
            ),
            description=description,
            reference_id=reference_id,
            metadata=metadata,
        )

    # ========================================================
    # ADMIN GRANT
    # ========================================================

    def admin_grant(
        self,
        *,
        user_id: str,
        amount: float,
        reference_id: Optional[str] = None,
        description: str = "Administrative credit grant",
        metadata: Optional[dict] = None,
    ) -> CreditTransaction:

        return self.add_credits(
            user_id=user_id,
            amount=amount,
            transaction_type=(
                CreditTransactionType.ADMIN_GRANT
            ),
            description=description,
            reference_id=reference_id,
            metadata=metadata,
        )

    # ========================================================
    # CONSUME
    # ========================================================

    def consume_credits(
        self,
        *,
        user_id: str,
        amount: float,
        description: str = "Credit consumption",
        reference_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> CreditTransaction:

        user_id = self._normalize_user_id(
            user_id
        )

        amount = self._validate_amount(
            amount
        )

        with self._lock:

            balance = self._get_or_create_balance(
                user_id
            )

            if not balance.has(
                amount
            ):
                raise InsufficientCreditsError(
                    "Insufficient credits."
                )

            balance.consume(
                amount
            )

            transaction = CreditTransaction(
                transaction_id=self._transaction_id(
                    user_id,
                    len(
                        self._transactions.get(
                            user_id,
                            [],
                        )
                    ),
                ),
                user_id=user_id,
                amount=-amount,
                transaction_type=(
                    CreditTransactionType.CONSUMPTION
                ),
                description=description,
                reference_id=reference_id,
                metadata=dict(
                    metadata or {}
                ),
            )

            return self._add_transaction(
                transaction
            )

    # ========================================================
    # EXPIRATION
    # ========================================================

    def expire_credits(
        self,
        *,
        user_id: str,
        amount: float,
        description: str = "Credit expiration",
        reference_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> CreditTransaction:

        user_id = self._normalize_user_id(
            user_id
        )

        amount = self._validate_amount(
            amount
        )

        with self._lock:

            balance = self._get_or_create_balance(
                user_id
            )

            actual_amount = min(
                amount,
                balance.balance,
            )

            if actual_amount <= 0:
                raise CreditTransactionError(
                    "No credits available to expire."
                )

            balance.expire(
                actual_amount
            )

            transaction = CreditTransaction(
                transaction_id=self._transaction_id(
                    user_id,
                    len(
                        self._transactions.get(
                            user_id,
                            [],
                        )
                    ),
                ),
                user_id=user_id,
                amount=-actual_amount,
                transaction_type=(
                    CreditTransactionType.EXPIRATION
                ),
                description=description,
                reference_id=reference_id,
                metadata=dict(
                    metadata or {}
                ),
            )

            return self._add_transaction(
                transaction
            )

    # ========================================================
    # CHECK
    # ========================================================

    def has_credits(
        self,
        *,
        user_id: str,
        amount: float,
    ) -> bool:

        amount = self._validate_amount(
            amount
        )

        balance = self.get_balance(
            user_id
        )

        return balance.has(
            amount
        )

    def require_credits(
        self,
        *,
        user_id: str,
        amount: float,
    ) -> None:

        if not self.has_credits(
            user_id=user_id,
            amount=amount,
        ):
            raise InsufficientCreditsError(
                "Insufficient credits."
            )

    # ========================================================
    # TRANSACTIONS
    # ========================================================

    def get_transactions(
        self,
        user_id: str,
        limit: Optional[int] = None,
    ) -> List[CreditTransaction]:

        user_id = self._normalize_user_id(
            user_id
        )

        with self._lock:

            transactions = list(
                self._transactions.get(
                    user_id,
                    [],
                )
            )

        transactions.reverse()

        if limit is not None:

            try:
                limit = int(
                    limit
                )
            except (
                TypeError,
                ValueError,
            ):
                limit = 0

            if limit > 0:
                transactions = transactions[
                    :limit
                ]

        return transactions

    def get_transaction_dicts(
        self,
        user_id: str,
        limit: Optional[int] = None,
    ) -> List[dict]:

        return [
            transaction.to_dict()
            for transaction in self.get_transactions(
                user_id,
                limit=limit,
            )
        ]

    # ========================================================
    # SUMMARY
    # ========================================================

    def get_summary(
        self,
        user_id: str,
    ) -> dict:

        balance = self.get_balance(
            user_id
        )

        transactions = self.get_transactions(
            user_id,
            limit=20,
        )

        return {
            **balance.to_dict(),
            "recent_transactions": [
                transaction.to_dict()
                for transaction in transactions
            ],
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

            self._balances.pop(
                user_id,
                None,
            )

            self._transactions.pop(
                user_id,
                None,
            )

    def clear(self) -> None:

        with self._lock:

            self._balances.clear()

            self._transactions.clear()


# ============================================================
# GLOBAL MANAGER
# ============================================================

_default_credit_manager: Optional[
    CreditManager
] = None


def get_credit_manager() -> CreditManager:
    """Return global credit manager."""

    global _default_credit_manager

    if _default_credit_manager is None:
        _default_credit_manager = CreditManager()

    return _default_credit_manager


def set_credit_manager(
    manager: CreditManager,
) -> None:

    global _default_credit_manager

    _default_credit_manager = manager


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def get_user_credit_balance(
    user_id: str,
) -> float:

    return get_credit_manager().get_balance(
        user_id
    ).available()


def add_user_credits(
    *,
    user_id: str,
    amount: float,
    transaction_type: CreditTransactionType = (
        CreditTransactionType.BONUS
    ),
    description: str = "",
    reference_id: Optional[str] = None,
) -> CreditTransaction:

    return get_credit_manager().add_credits(
        user_id=user_id,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        reference_id=reference_id,
    )


def consume_user_credits(
    *,
    user_id: str,
    amount: float,
    description: str = "",
    reference_id: Optional[str] = None,
) -> CreditTransaction:

    return get_credit_manager().consume_credits(
        user_id=user_id,
        amount=amount,
        description=description,
        reference_id=reference_id,
    )


def refund_user_credits(
    *,
    user_id: str,
    amount: float,
    reference_id: Optional[str] = None,
    description: str = "Credit refund",
) -> CreditTransaction:

    return get_credit_manager().refund_credits(
        user_id=user_id,
        amount=amount,
        reference_id=reference_id,
        description=description,
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "CreditError",
    "InsufficientCreditsError",
    "InvalidCreditAmountError",
    "CreditTransactionError",
    "CreditTransactionType",
    "CreditBalance",
    "CreditTransaction",
    "CreditManager",
    "get_credit_manager",
    "set_credit_manager",
    "get_user_credit_balance",
    "add_user_credits",
    "consume_user_credits",
    "refund_user_credits",
]
