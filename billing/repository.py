"""
StructuralBot - Billing Repository

Repository abstraction for billing persistence.

Responsibilities:
- Store and retrieve billing entities
- Keep persistence concerns outside business logic
- Provide an in-memory implementation for development/tests
- Prepare the billing layer for SQLite/PostgreSQL later

Business logic must NOT depend directly on database queries.

Architecture:

BillingService
      |
      v
Repository Interfaces
      |
      +--> InMemoryRepository
      |
      +--> Future DatabaseRepository
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Protocol,
    TypeVar,
)


# ============================================================
# TYPES
# ============================================================


T = TypeVar("T")


# ============================================================
# EXCEPTIONS
# ============================================================


class RepositoryError(Exception):
    """Base repository exception."""


class RepositoryNotFoundError(
    RepositoryError
):
    """Requested entity was not found."""


class RepositoryDuplicateError(
    RepositoryError
):
    """Entity already exists."""


class RepositoryValidationError(
    RepositoryError
):
    """Invalid repository operation."""


# ============================================================
# REPOSITORY PROTOCOL
# ============================================================


class Repository(
    Protocol,
    Generic[T],
):
    """
    Generic repository contract.

    Concrete implementations may use:
    - memory
    - SQLite
    - PostgreSQL
    - another database
    """

    def get(
        self,
        entity_id: str,
    ) -> Optional[T]:
        ...

    def add(
        self,
        entity_id: str,
        entity: T,
    ) -> T:
        ...

    def update(
        self,
        entity_id: str,
        entity: T,
    ) -> T:
        ...

    def delete(
        self,
        entity_id: str,
    ) -> bool:
        ...

    def list(
        self,
    ) -> List[T]:
        ...

    def exists(
        self,
        entity_id: str,
    ) -> bool:
        ...

    def clear(
        self,
    ) -> None:
        ...


# ============================================================
# IN-MEMORY REPOSITORY
# ============================================================


class InMemoryRepository(
    Generic[T]
):
    """
    Thread-safe in-memory repository.

    Used for:
    - development
    - unit tests
    - local testing
    - temporary environments

    It deliberately returns deep copies so callers cannot
    accidentally mutate repository state.
    """

    def __init__(self) -> None:

        self._data: Dict[
            str,
            T,
        ] = {}

        self._lock = RLock()

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        entity_id: str,
    ) -> Optional[T]:

        with self._lock:

            entity = self._data.get(
                str(entity_id)
            )

            if entity is None:

                return None

            return deepcopy(
                entity
            )

    def require(
        self,
        entity_id: str,
    ) -> T:

        entity = self.get(
            entity_id
        )

        if entity is None:

            raise RepositoryNotFoundError(
                f"Entity not found: "
                f"{entity_id}"
            )

        return entity

    # ========================================================
    # ADD
    # ========================================================

    def add(
        self,
        entity_id: str,
        entity: T,
    ) -> T:

        entity_id = str(
            entity_id
        )

        if not entity_id:

            raise RepositoryValidationError(
                "Entity ID is required."
            )

        with self._lock:

            if entity_id in self._data:

                raise RepositoryDuplicateError(
                    f"Entity already exists: "
                    f"{entity_id}"
                )

            self._data[
                entity_id
            ] = deepcopy(entity)

            return deepcopy(
                entity
            )

    # ========================================================
    # UPSERT
    # ========================================================

    def upsert(
        self,
        entity_id: str,
        entity: T,
    ) -> T:

        entity_id = str(
            entity_id
        )

        if not entity_id:

            raise RepositoryValidationError(
                "Entity ID is required."
            )

        with self._lock:

            self._data[
                entity_id
            ] = deepcopy(entity)

            return deepcopy(
                entity
            )

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        entity_id: str,
        entity: T,
    ) -> T:

        entity_id = str(
            entity_id
        )

        with self._lock:

            if entity_id not in self._data:

                raise RepositoryNotFoundError(
                    f"Entity not found: "
                    f"{entity_id}"
                )

            self._data[
                entity_id
            ] = deepcopy(entity)

            return deepcopy(
                entity
            )

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        entity_id: str,
    ) -> bool:

        entity_id = str(
            entity_id
        )

        with self._lock:

            if entity_id not in self._data:

                return False

            del self._data[
                entity_id
            ]

            return True

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        entity_id: str,
    ) -> bool:

        with self._lock:

            return (
                str(entity_id)
                in self._data
            )

    # ========================================================
    # LIST
    # ========================================================

    def list(
        self,
    ) -> List[T]:

        with self._lock:

            return deepcopy(
                list(
                    self._data.values()
                )
            )

    # ========================================================
    # IDS
    # ========================================================

    def ids(
        self,
    ) -> List[str]:

        with self._lock:

            return list(
                self._data.keys()
            )

    # ========================================================
    # COUNT
    # ========================================================

    def count(
        self,
    ) -> int:

        with self._lock:

            return len(
                self._data
            )

    # ========================================================
    # FILTER
    # ========================================================

    def filter(
        self,
        predicate,
    ) -> List[T]:

        with self._lock:

            result = []

            for entity in (
                self._data.values()
            ):

                entity_copy = deepcopy(
                    entity
                )

                if predicate(
                    entity_copy
                ):

                    result.append(
                        entity_copy
                    )

            return result

    # ========================================================
    # FIND FIRST
    # ========================================================

    def find_first(
        self,
        predicate,
    ) -> Optional[T]:

        with self._lock:

            for entity in (
                self._data.values()
            ):

                entity_copy = deepcopy(
                    entity
                )

                if predicate(
                    entity_copy
                ):

                    return entity_copy

            return None

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:

        with self._lock:

            self._data.clear()


# ============================================================
# BILLING REPOSITORY CONTAINER
# ============================================================


@dataclass
class BillingRepositories:
    """
    Collection of repositories used by Billing.

    This provides one dependency-injection point for the
    complete billing persistence layer.
    """

    products: InMemoryRepository = None
    plans: InMemoryRepository = None
    orders: InMemoryRepository = None
    payments: InMemoryRepository = None
    subscriptions: InMemoryRepository = None
    credits: InMemoryRepository = None
    invoices: InMemoryRepository = None
    fulfillments: InMemoryRepository = None

    def __post_init__(
        self,
    ) -> None:

        if self.products is None:

            self.products = (
                InMemoryRepository()
            )

        if self.plans is None:

            self.plans = (
                InMemoryRepository()
            )

        if self.orders is None:

            self.orders = (
                InMemoryRepository()
            )

        if self.payments is None:

            self.payments = (
                InMemoryRepository()
            )

        if self.subscriptions is None:

            self.subscriptions = (
                InMemoryRepository()
            )

        if self.credits is None:

            self.credits = (
                InMemoryRepository()
            )

        if self.invoices is None:

            self.invoices = (
                InMemoryRepository()
            )

        if self.fulfillments is None:

            self.fulfillments = (
                InMemoryRepository()
            )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:

        self.products.clear()
        self.plans.clear()
        self.orders.clear()
        self.payments.clear()
        self.subscriptions.clear()
        self.credits.clear()
        self.invoices.clear()
        self.fulfillments.clear()

    # ========================================================
    # SUMMARY
    # ========================================================

    def summary(
        self,
    ) -> dict:

        return {
            "products": (
                self.products.count()
            ),
            "plans": (
                self.plans.count()
            ),
            "orders": (
                self.orders.count()
            ),
            "payments": (
                self.payments.count()
            ),
            "subscriptions": (
                self.subscriptions.count()
            ),
            "credits": (
                self.credits.count()
            ),
            "invoices": (
                self.invoices.count()
            ),
            "fulfillments": (
                self.fulfillments.count()
            ),
        }


# ============================================================
# GLOBAL REPOSITORIES
# ============================================================


_default_repositories: Optional[
    BillingRepositories
] = None


def get_billing_repositories(
) -> BillingRepositories:

    global _default_repositories

    if (
        _default_repositories
        is None
    ):

        _default_repositories = (
            BillingRepositories()
        )

    return (
        _default_repositories
    )


def set_billing_repositories(
    repositories: BillingRepositories,
) -> None:

    global _default_repositories

    _default_repositories = (
        repositories
    )


# ============================================================
# GENERIC HELPERS
# ============================================================


def repository_get(
    repository: Repository[T],
    entity_id: str,
) -> Optional[T]:

    return repository.get(
        entity_id
    )


def repository_require(
    repository: InMemoryRepository[T],
    entity_id: str,
) -> T:

    return repository.require(
        entity_id
    )


def repository_add(
    repository: Repository[T],
    entity_id: str,
    entity: T,
) -> T:

    return repository.add(
        entity_id,
        entity,
    )


def repository_update(
    repository: Repository[T],
    entity_id: str,
    entity: T,
) -> T:

    return repository.update(
        entity_id,
        entity,
    )


def repository_delete(
    repository: Repository[T],
    entity_id: str,
) -> bool:

    return repository.delete(
        entity_id
    )


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryDuplicateError",
    "RepositoryValidationError",
    "Repository",
    "InMemoryRepository",
    "BillingRepositories",
    "get_billing_repositories",
    "set_billing_repositories",
    "repository_get",
    "repository_require",
    "repository_add",
    "repository_update",
    "repository_delete",
]
