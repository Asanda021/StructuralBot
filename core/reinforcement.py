from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil, pi
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from core.models import (
    MemberType,
    ReinforcementBar,
    ReinforcementType,
    StructuralMember,
)


STANDARD_DIAMETERS_MM: Tuple[float, ...] = (
    6.0, 8.0, 10.0, 12.0, 14.0, 16.0,
    18.0, 20.0, 22.0, 25.0, 28.0,
    32.0, 36.0, 40.0,
)

STEEL_DENSITY_KG_M3 = 7850.0


class ReinforcementError(Exception):
    """Base reinforcement error."""


class InvalidReinforcementError(ReinforcementError):
    """Invalid reinforcement input."""


class UnsupportedDiameterError(ReinforcementError):
    """Unsupported rebar diameter."""


def normalize_diameter(diameter_mm: float) -> float:
    value = float(diameter_mm)

    if value <= 0:
        raise InvalidReinforcementError(
            "Rebar diameter must be positive."
        )

    return value


def is_standard_diameter(
    diameter_mm: float,
) -> bool:
    return normalize_diameter(diameter_mm) in STANDARD_DIAMETERS_MM


def validate_standard_diameter(
    diameter_mm: float,
) -> float:
    diameter = normalize_diameter(diameter_mm)

    if diameter not in STANDARD_DIAMETERS_MM:
        raise UnsupportedDiameterError(
            f"Unsupported standard diameter: {diameter:g} mm"
        )

    return diameter


def bar_area_mm2(
    diameter_mm: float,
) -> float:
    diameter = normalize_diameter(diameter_mm)
    return pi * diameter ** 2 / 4.0


def total_bar_area_mm2(
    diameter_mm: float,
    quantity: int,
) -> float:
    if quantity <= 0:
        raise InvalidReinforcementError(
            "Bar quantity must be positive."
        )

    return bar_area_mm2(diameter_mm) * quantity


def bar_weight_kg_per_m(
    diameter_mm: float,
) -> float:
    diameter_m = normalize_diameter(diameter_mm) / 1000.0

    return (
        pi
        * diameter_m ** 2
        / 4.0
        * STEEL_DENSITY_KG_M3
    )


def bar_weight_kg(
    diameter_mm: float,
    length_m: float,
    quantity: int = 1,
) -> float:
    if length_m < 0:
        raise InvalidReinforcementError(
            "Bar length cannot be negative."
        )

    if quantity <= 0:
        raise InvalidReinforcementError(
            "Bar quantity must be positive."
        )

    return (
        bar_weight_kg_per_m(diameter_mm)
        * float(length_m)
        * quantity
    )


def required_bar_count(
    required_area_mm2: float,
    diameter_mm: float,
) -> int:
    if required_area_mm2 <= 0:
        return 0

    area = bar_area_mm2(diameter_mm)

    return max(
        1,
        ceil(required_area_mm2 / area),
    )


def required_area_from_bars(
    diameter_mm: float,
    quantity: int,
) -> float:
    return total_bar_area_mm2(
        diameter_mm,
        quantity,
    )


def reinforcement_ratio(
    steel_area_mm2: float,
    gross_area_mm2: float,
) -> float:
    if gross_area_mm2 <= 0:
        raise InvalidReinforcementError(
            "Gross area must be positive."
        )

    if steel_area_mm2 < 0:
        raise InvalidReinforcementError(
            "Steel area cannot be negative."
        )

    return steel_area_mm2 / gross_area_mm2


def reinforcement_ratio_percent(
    steel_area_mm2: float,
    gross_area_mm2: float,
) -> float:
    return reinforcement_ratio(
        steel_area_mm2,
        gross_area_mm2,
    ) * 100.0


def equivalent_bar_count(
    source_diameter_mm: float,
    source_quantity: int,
    target_diameter_mm: float,
) -> int:
    """
    Mathematical area equivalency only.

    This does NOT perform code compliance, spacing,
    anchorage, development, lap, constructability,
    or detailing checks.
    """
    if source_quantity <= 0:
        raise InvalidReinforcementError(
            "Source quantity must be positive."
        )

    source_area = total_bar_area_mm2(
        source_diameter_mm,
        source_quantity,
    )

    return required_bar_count(
        source_area,
        target_diameter_mm,
    )


def spacing_bar_count(
    length_m: float,
    spacing_mm: float,
    *,
    include_end_bars: bool = True,
) -> int:
    if length_m <= 0:
        raise InvalidReinforcementError(
            "Length must be positive."
        )

    if spacing_mm <= 0:
        raise InvalidReinforcementError(
            "Spacing must be positive."
        )

    length_mm = length_m * 1000.0

    if include_end_bars:
        return max(
            2,
            ceil(length_mm / spacing_mm) + 1,
        )

    return max(
        1,
        ceil(length_mm / spacing_mm),
    )


def actual_spacing_mm(
    length_m: float,
    quantity: int,
    *,
    include_end_bars: bool = True,
) -> float:
    if length_m <= 0:
        raise InvalidReinforcementError(
            "Length must be positive."
        )

    if quantity < 1:
        raise InvalidReinforcementError(
            "Quantity must be positive."
        )

    if include_end_bars:
        if quantity < 2:
            return 0.0

        return length_m * 1000.0 / (quantity - 1)

    return length_m * 1000.0 / quantity


def round_diameter(
    diameter_mm: float,
    *,
    direction: str = "up",
) -> float:
    value = normalize_diameter(diameter_mm)

    if value in STANDARD_DIAMETERS_MM:
        return value

    if direction == "up":
        for diameter in STANDARD_DIAMETERS_MM:
            if diameter >= value:
                return diameter

        return STANDARD_DIAMETERS_MM[-1]

    if direction == "down":
        candidates = [
            diameter
            for diameter in STANDARD_DIAMETERS_MM
            if diameter <= value
        ]

        if not candidates:
            return STANDARD_DIAMETERS_MM[0]

        return candidates[-1]

    raise ValueError(
        "direction must be 'up' or 'down'."
    )


def minimum_clear_spacing_mm(
    diameter_mm: float,
    *,
    absolute_minimum_mm: float = 25.0,
) -> float:
    diameter = normalize_diameter(diameter_mm)

    return max(
        absolute_minimum_mm,
        diameter,
    )


def effective_depth_mm(
    overall_depth_mm: float,
    cover_mm: float,
    stirrup_diameter_mm: float = 0.0,
    main_bar_diameter_mm: float = 0.0,
) -> float:
    if overall_depth_mm <= 0:
        raise InvalidReinforcementError(
            "Overall depth must be positive."
        )

    for value, name in (
        (cover_mm, "cover_mm"),
        (stirrup_diameter_mm, "stirrup_diameter_mm"),
        (main_bar_diameter_mm, "main_bar_diameter_mm"),
    ):
        if value < 0:
            raise InvalidReinforcementError(
                f"{name} cannot be negative."
            )

    d = (
        overall_depth_mm
        - cover_mm
        - stirrup_diameter_mm
        - main_bar_diameter_mm / 2.0
    )

    if d <= 0:
        raise InvalidReinforcementError(
            "Effective depth must be positive."
        )

    return d


def create_rebar(
    *,
    bar_id: str,
    member_id: str,
    project_id: str,
    diameter_mm: float,
    quantity: int,
    length_m: float,
    reinforcement_type: ReinforcementType,
    mark: Optional[str] = None,
    spacing_mm: Optional[float] = None,
    role: Optional[str] = None,
    region: Optional[str] = None,
    grade: Optional[str] = None,
    development_length_m: float = 0.0,
    lap_length_m: float = 0.0,
    shape=None,
    notes: Optional[str] = None,
) -> ReinforcementBar:
    if not bar_id:
        raise InvalidReinforcementError(
            "bar_id is required."
        )

    if not member_id:
        raise InvalidReinforcementError(
            "member_id is required."
        )

    if not project_id:
        raise InvalidReinforcementError(
            "project_id is required."
        )

    if quantity <= 0:
        raise InvalidReinforcementError(
            "quantity must be positive."
        )

    if length_m <= 0:
        raise InvalidReinforcementError(
            "length_m must be positive."
        )

    if spacing_mm is not None and spacing_mm <= 0:
        raise InvalidReinforcementError(
            "spacing_mm must be positive."
        )

    if development_length_m < 0:
        raise InvalidReinforcementError(
            "development_length_m cannot be negative."
        )

    if lap_length_m < 0:
        raise InvalidReinforcementError(
            "lap_length_m cannot be negative."
        )

    return ReinforcementBar(
        bar_id=bar_id,
        member_id=member_id,
        project_id=project_id,
        mark=mark,
        reinforcement_type=reinforcement_type,
        diameter_mm=normalize_diameter(diameter_mm),
        quantity=quantity,
        spacing_mm=spacing_mm,
        length_m=length_m,
        role=role,
        region=region,
        grade=grade,
        shape=shape,
        development_length_m=development_length_m,
        lap_length_m=lap_length_m,
        notes=notes,
    )


@dataclass(slots=True)
class ReinforcementCollection:
    bars: List[ReinforcementBar] = field(
        default_factory=list
    )

    def add(
        self,
        bar: ReinforcementBar,
    ) -> None:
        self.bars.append(bar)

    def extend(
        self,
        bars: Iterable[ReinforcementBar],
    ) -> None:
        self.bars.extend(bars)

    def total_weight_kg(self) -> float:
        return sum(
            bar_weight_kg(
                bar.diameter_mm,
                bar.length_m,
                bar.quantity,
            )
            for bar in self.bars
        )

    def total_area_mm2_by_member(
        self,
    ) -> Dict[str, float]:
        result: Dict[str, float] = {}

        for bar in self.bars:
            result[bar.member_id] = (
                result.get(bar.member_id, 0.0)
                + total_bar_area_mm2(
                    bar.diameter_mm,
                    bar.quantity,
                )
            )

        return result

    def weight_by_diameter(
        self,
    ) -> Dict[float, float]:
        result: Dict[float, float] = {}

        for bar in self.bars:
            result[bar.diameter_mm] = (
                result.get(bar.diameter_mm, 0.0)
                + bar_weight_kg(
                    bar.diameter_mm,
                    bar.length_m,
                    bar.quantity,
                )
            )

        return result

    def filter_member(
        self,
        member_id: str,
    ) -> List[ReinforcementBar]:
        return [
            bar
            for bar in self.bars
            if bar.member_id == member_id
        ]

    def filter_type(
        self,
        reinforcement_type: ReinforcementType,
    ) -> List[ReinforcementBar]:
        return [
            bar
            for bar in self.bars
            if bar.reinforcement_type
            == reinforcement_type
        ]

    def by_diameter(
        self,
    ) -> Dict[float, List[ReinforcementBar]]:
        result: Dict[
            float,
            List[ReinforcementBar],
        ] = {}

        for bar in self.bars:
            result.setdefault(
                bar.diameter_mm,
                [],
            ).append(bar)

        return result


def theoretical_weight_kg(
    bars: Sequence[ReinforcementBar],
) -> float:
    return sum(
        bar_weight_kg(
            bar.diameter_mm,
            bar.length_m,
            bar.quantity,
        )
        for bar in bars
    )


@dataclass(slots=True)
class ReinforcementDesign:
    member_id: str
    required_area_mm2: float
    provided_area_mm2: float
    bars: List[ReinforcementBar] = field(
        default_factory=list
    )
    notes: List[str] = field(
        default_factory=list
    )

    @property
    def area_ratio(self) -> float:
        if self.required_area_mm2 <= 0:
            return 0.0

        return (
            self.provided_area_mm2
            / self.required_area_mm2
        )

    @property
    def adequate_by_area(self) -> bool:
        return (
            self.provided_area_mm2
            >= self.required_area_mm2
        )


def design_by_required_area(
    *,
    member: StructuralMember,
    required_area_mm2: float,
    diameter_mm: float,
    length_m: float,
    reinforcement_type: ReinforcementType,
    mark: Optional[str] = None,
    spacing_mm: Optional[float] = None,
    role: Optional[str] = None,
    region: Optional[str] = None,
    grade: Optional[str] = None,
    shape=None,
) -> ReinforcementDesign:
    if required_area_mm2 < 0:
        raise InvalidReinforcementError(
            "Required reinforcement area cannot be negative."
        )

    quantity = required_bar_count(
        required_area_mm2,
        diameter_mm,
    )

    bar = create_rebar(
        bar_id=(
            f"{member.member_id}:"
            f"{mark or reinforcement_type.value}:"
            f"{diameter_mm:g}"
        ),
        member_id=member.member_id,
        project_id=member.project_id,
        diameter_mm=diameter_mm,
        quantity=quantity,
        length_m=length_m,
        reinforcement_type=reinforcement_type,
        mark=mark,
        spacing_mm=spacing_mm,
        role=role,
        region=region,
        grade=grade,
        shape=shape,
    )

    provided_area = total_bar_area_mm2(
        diameter_mm,
        quantity,
    )

    return ReinforcementDesign(
        member_id=member.member_id,
        required_area_mm2=required_area_mm2,
        provided_area_mm2=provided_area,
        bars=[bar],
    )


__all__ = [
    "STANDARD_DIAMETERS_MM",
    "STEEL_DENSITY_KG_M3",
    "ReinforcementError",
    "InvalidReinforcementError",
    "UnsupportedDiameterError",
    "normalize_diameter",
    "is_standard_diameter",
    "validate_standard_diameter",
    "bar_area_mm2",
    "total_bar_area_mm2",
    "bar_weight_kg_per_m",
    "bar_weight_kg",
    "required_bar_count",
    "required_area_from_bars",
    "reinforcement_ratio",
    "reinforcement_ratio_percent",
    "equivalent_bar_count",
    "spacing_bar_count",
    "actual_spacing_mm",
    "round_diameter",
    "minimum_clear_spacing_mm",
    "effective_depth_mm",
    "create_rebar",
    "ReinforcementCollection",
    "theoretical_weight_kg",
    "ReinforcementDesign",
    "design_by_required_area",
]
