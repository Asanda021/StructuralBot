from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class CodeFamily(str, Enum):
    IRAN = "iran"
    ACI = "aci"
    EUROCODE = "eurocode"
    GENERIC = "generic"


class MemberCategory(str, Enum):
    FOUNDATION = "foundation"
    COLUMN = "column"
    BEAM = "beam"
    SLAB = "slab"
    WALL = "wall"
    STAIR = "stair"


class MaterialCategory(str, Enum):
    CONCRETE = "concrete"
    REBAR = "rebar"
    STRUCTURAL_STEEL = "structural_steel"


class LimitState(str, Enum):
    ULS = "ULS"
    SLS = "SLS"
    DETAILING = "DETAILING"


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_CHECKED = "NOT_CHECKED"


@dataclass(frozen=True)
class CodeEdition:
    code_id: str
    title: str
    edition: str
    family: CodeFamily
    country: Optional[str] = None
    language: Optional[str] = None


@dataclass
class CodeCheck:
    name: str
    status: CheckStatus
    value: Optional[float] = None
    limit: Optional[float] = None
    relation: str = ""
    unit: str = ""
    message: str = ""
    clause: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeRequirement:
    name: str
    member_type: str
    limit_state: LimitState
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    unit: str = ""
    clause: Optional[str] = None
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DetailingRule:
    name: str
    member_type: str
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    unit: str = ""
    clause: Optional[str] = None
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MaterialRequirement:
    name: str
    material_type: str
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    unit: str = ""
    clause: Optional[str] = None
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeContext:
    code_id: str
    edition: str
    member_type: str
    material_type: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DesignCode(ABC):
    code_id: str
    family: CodeFamily
    edition: str

    @abstractmethod
    def supported_members(self) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def get_requirement(
        self,
        member_type: str,
        requirement: str,
    ) -> Optional[CodeRequirement]:
        raise NotImplementedError

    @abstractmethod
    def get_material_requirement(
        self,
        material_type: str,
        requirement: str,
    ) -> Optional[MaterialRequirement]:
        raise NotImplementedError

    @abstractmethod
    def get_detailing_rule(
        self,
        member_type: str,
        rule: str,
    ) -> Optional[DetailingRule]:
        raise NotImplementedError

    def run_check(
        self,
        *,
        name: str,
        value: float,
        limit: float,
        relation: str = "<=",
        unit: str = "",
        clause: Optional[str] = None,
        message: str = "",
    ) -> CodeCheck:
        passed = compare(value, relation, limit)

        return CodeCheck(
            name=name,
            status=CheckStatus.PASS if passed else CheckStatus.FAIL,
            value=value,
            limit=limit,
            relation=relation,
            unit=unit,
            message=message,
            clause=clause,
        )


class DesignCodeRegistry:
    def __init__(self):
        self._codes: dict[str, DesignCode] = {}

    def register(self, code: DesignCode) -> None:
        key = code.code_id.lower()
        if key in self._codes:
            raise ValueError(f"Code already registered: {key}")
        self._codes[key] = code

    def replace(self, code: DesignCode) -> None:
        self._codes[code.code_id.lower()] = code

    def get(self, code_id: str) -> DesignCode:
        key = code_id.lower()
        if key not in self._codes:
            raise KeyError(f"Unknown design code: {code_id}")
        return self._codes[key]

    def exists(self, code_id: str) -> bool:
        return code_id.lower() in self._codes

    def all(self) -> tuple[DesignCode, ...]:
        return tuple(self._codes.values())


def compare(value: float, relation: str, limit: float) -> bool:
    value = float(value)
    limit = float(limit)

    if relation == "<=":
        return value <= limit
    if relation == "<":
        return value < limit
    if relation == ">=":
        return value >= limit
    if relation == ">":
        return value > limit
    if relation == "==":
        return abs(value - limit) <= 1e-12

    raise ValueError(f"Unsupported comparison relation: {relation}")


def check_minimum(
    name: str,
    value: float,
    minimum: float,
    *,
    unit: str = "",
    clause: Optional[str] = None,
) -> CodeCheck:
    return CodeCheck(
        name=name,
        status=(
            CheckStatus.PASS
            if float(value) >= float(minimum)
            else CheckStatus.FAIL
        ),
        value=float(value),
        limit=float(minimum),
        relation=">=",
        unit=unit,
        clause=clause,
    )


def check_maximum(
    name: str,
    value: float,
    maximum: float,
    *,
    unit: str = "",
    clause: Optional[str] = None,
) -> CodeCheck:
    return CodeCheck(
        name=name,
        status=(
            CheckStatus.PASS
            if float(value) <= float(maximum)
            else CheckStatus.FAIL
        ),
        value=float(value),
        limit=float(maximum),
        relation="<=",
        unit=unit,
        clause=clause,
    )


def check_range(
    name: str,
    value: float,
    minimum: float,
    maximum: float,
    *,
    unit: str = "",
    clause: Optional[str] = None,
) -> list[CodeCheck]:
    return [
        check_minimum(
            f"{name}_min",
            value,
            minimum,
            unit=unit,
            clause=clause,
        ),
        check_maximum(
            f"{name}_max",
            value,
            maximum,
            unit=unit,
            clause=clause,
        ),
    ]


default_registry = DesignCodeRegistry()


def register_code(code: DesignCode) -> None:
    default_registry.replace(code)


def get_code(code_id: str) -> DesignCode:
    return default_registry.get(code_id)


def list_codes() -> tuple[DesignCode, ...]:
    return default_registry.all()


def code_exists(code_id: str) -> bool:
    return default_registry.exists(code_id)


__all__ = [
    "CodeFamily",
    "MemberCategory",
    "MaterialCategory",
    "LimitState",
    "CheckStatus",
    "CodeEdition",
    "CodeCheck",
    "CodeRequirement",
    "DetailingRule",
    "MaterialRequirement",
    "CodeContext",
    "DesignCode",
    "DesignCodeRegistry",
    "compare",
    "check_minimum",
    "check_maximum",
    "check_range",
    "default_registry",
    "register_code",
    "get_code",
    "list_codes",
    "code_exists",
]
