from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Optional

from codes.base import (
    CodeCheck,
    CheckStatus,
    CodeRequirement,
    DesignCode,
    DetailingRule,
    LimitState,
    MaterialRequirement,
)
from .materials import IranMaterials


STANDARD_DIAMETERS_MM = (
    8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32, 36, 40,
)

REBAR_DENSITY_KG_M3 = 7850.0


@dataclass(frozen=True)
class RebarProperties:
    diameter_mm: float
    grade: str
    area_mm2: float
    unit_weight_kg_m: float
    fy_mpa: float
    fu_mpa: float


@dataclass(frozen=True)
class DevelopmentInput:
    diameter_mm: float
    fy_mpa: float
    concrete_fc_mpa: float
    factor: float = 1.0


@dataclass(frozen=True)
class LapInput:
    development_length_mm: float
    factor: float = 1.0


class IranReinforcement(DesignCode):
    code_id = "iran_rebar"
    family = __import__("codes.base", fromlist=["CodeFamily"]).CodeFamily.IRAN
    edition = "Iran-Rebar-Generic"

    def __init__(self):
        self._requirements = {}
        for member in (
            "foundation",
            "column",
            "beam",
            "slab",
            "wall",
            "stair",
        ):
            self._requirements[(member, "min_ratio")] = CodeRequirement(
                "minimum reinforcement ratio",
                member,
                LimitState.ULS,
                minimum=0.001,
                unit="ratio",
            )
            self._requirements[(member, "max_ratio")] = CodeRequirement(
                "maximum reinforcement ratio",
                member,
                LimitState.ULS,
                maximum=0.08,
                unit="ratio",
            )

        self._detailing = {}
        for member in self.supported_members():
            self._detailing[(member, "min_spacing")] = DetailingRule(
                "minimum bar spacing",
                member,
                minimum=25.0,
                unit="mm",
            )
            self._detailing[(member, "max_spacing")] = DetailingRule(
                "maximum bar spacing",
                member,
                maximum=300.0,
                unit="mm",
            )

    def supported_members(self) -> tuple[str, ...]:
        return (
            "foundation",
            "column",
            "beam",
            "slab",
            "wall",
            "stair",
        )

    def get_requirement(
        self,
        member_type: str,
        requirement: str,
    ) -> Optional[CodeRequirement]:
        return self._requirements.get(
            (str(member_type).lower(), str(requirement).lower())
        )

    def get_material_requirement(
        self,
        material_type: str,
        requirement: str,
    ) -> Optional[MaterialRequirement]:
        material = str(material_type).lower()
        req = str(requirement).lower()

        if material in {"rebar", "reinforcement", "میلگرد"}:
            if req in {"fy", "minimum_fy", "fy_min"}:
                return MaterialRequirement(
                    "reinforcement yield strength",
                    "rebar",
                    minimum=300.0,
                    unit="MPa",
                )

        return None

    def get_detailing_rule(
        self,
        member_type: str,
        rule: str,
    ) -> Optional[DetailingRule]:
        return self._detailing.get(
            (str(member_type).lower(), str(rule).lower())
        )


def bar_area(diameter_mm: float) -> float:
    d = float(diameter_mm)
    if d <= 0:
        raise ValueError("Diameter must be positive.")
    return pi * d * d / 4.0


def bar_unit_weight(diameter_mm: float) -> float:
    d = float(diameter_mm)
    if d <= 0:
        raise ValueError("Diameter must be positive.")
    return d * d / 162.0


def get_rebar_properties(
    diameter_mm: float,
    grade: str,
) -> RebarProperties:
    material = IranMaterials.get_reinforcement(grade)
    d = float(diameter_mm)

    if d not in STANDARD_DIAMETERS_MM:
        raise ValueError(
            f"Unsupported standard diameter: {diameter_mm}"
        )

    return RebarProperties(
        diameter_mm=d,
        grade=material.grade,
        area_mm2=bar_area(d),
        unit_weight_kg_m=bar_unit_weight(d),
        fy_mpa=material.fy_mpa,
        fu_mpa=material.fu_mpa,
    )


def required_bar_count(
    required_area_mm2: float,
    diameter_mm: float,
) -> int:
    required = float(required_area_mm2)
    area = bar_area(diameter_mm)

    if required <= 0:
        return 0

    return max(1, int((required + area - 1e-12) // area) +
               (1 if required % area > 1e-12 else 0))


def equivalent_area(
    count: int,
    diameter_mm: float,
) -> float:
    if int(count) < 1:
        raise ValueError("Count must be at least 1.")
    return int(count) * bar_area(diameter_mm)


def spacing_from_count(
    width_mm: float,
    cover_mm: float,
    diameter_mm: float,
    count: int,
) -> float:
    width = float(width_mm)
    cover = float(cover_mm)
    d = float(diameter_mm)
    n = int(count)

    if width <= 0 or cover < 0 or d <= 0 or n < 2:
        raise ValueError("Invalid spacing inputs.")

    available = width - 2.0 * cover - d
    if available <= 0:
        raise ValueError("No usable width for reinforcement.")

    return available / (n - 1)


def development_length(
    data: DevelopmentInput,
) -> float:
    d = float(data.diameter_mm)
    fy = float(data.fy_mpa)
    fc = float(data.concrete_fc_mpa)

    if d <= 0 or fy <= 0 or fc <= 0:
        raise ValueError("Invalid development-length inputs.")

    return float(data.factor) * d * fy / max(1.0, 10.0 * fc ** 0.5)


def lap_length(data: LapInput) -> float:
    ld = float(data.development_length_mm)
    factor = float(data.factor)

    if ld <= 0 or factor <= 0:
        raise ValueError("Invalid lap-length inputs.")

    return ld * factor


def minimum_reinforcement_area(
    gross_area_mm2: float,
    ratio: float = 0.001,
) -> float:
    area = float(gross_area_mm2)
    r = float(ratio)

    if area <= 0 or r < 0:
        raise ValueError("Invalid reinforcement inputs.")

    return area * r


def maximum_reinforcement_area(
    gross_area_mm2: float,
    ratio: float = 0.08,
) -> float:
    area = float(gross_area_mm2)
    r = float(ratio)

    if area <= 0 or r <= 0:
        raise ValueError("Invalid reinforcement inputs.")

    return area * r


def check_rebar_ratio(
    ratio: float,
    *,
    minimum: float = 0.001,
    maximum: float = 0.08,
) -> CodeCheck:
    value = float(ratio)

    if value < minimum:
        return CodeCheck(
            "reinforcement_ratio",
            CheckStatus.FAIL,
            value=value,
            limit=minimum,
            relation=">=",
        )

    if value > maximum:
        return CodeCheck(
            "reinforcement_ratio",
            CheckStatus.FAIL,
            value=value,
            limit=maximum,
            relation="<=",
        )

    return CodeCheck(
        "reinforcement_ratio",
        CheckStatus.PASS,
        value=value,
        limit=maximum,
        relation="range",
    )


__all__ = [
    "STANDARD_DIAMETERS_MM",
    "REBAR_DENSITY_KG_M3",
    "RebarProperties",
    "DevelopmentInput",
    "LapInput",
    "IranReinforcement",
    "bar_area",
    "bar_unit_weight",
    "get_rebar_properties",
    "required_bar_count",
    "equivalent_area",
    "spacing_from_count",
    "development_length",
    "lap_length",
    "minimum_reinforcement_area",
    "maximum_reinforcement_area",
    "check_rebar_ratio",
]
