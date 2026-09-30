from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from codes.base import (
    CodeFamily,
    CodeRequirement,
    DesignCode,
    DetailingRule,
    LimitState,
    MaterialRequirement,
)
from .materials import IranMaterials


@dataclass(frozen=True)
class ConcreteLimits:
    min_fc_mpa: float = 20.0
    max_fc_mpa: float = 50.0
    min_cover_mm: float = 20.0
    density_kg_m3: float = 2400.0


@dataclass(frozen=True)
class ConcreteSectionProperties:
    width_mm: float
    depth_mm: float
    cover_mm: float

    @property
    def gross_area_mm2(self) -> float:
        return self.width_mm * self.depth_mm

    @property
    def core_width_mm(self) -> float:
        return max(0.0, self.width_mm - 2.0 * self.cover_mm)

    @property
    def core_depth_mm(self) -> float:
        return max(0.0, self.depth_mm - 2.0 * self.cover_mm)


class IranConcrete(DesignCode):
    code_id = "iran"
    family = CodeFamily.IRAN
    edition = "Iran-Concrete-Generic"

    def __init__(self, limits: Optional[ConcreteLimits] = None):
        self.limits = limits or ConcreteLimits()

        self._requirements = {
            ("foundation", "fc"): CodeRequirement(
                "concrete strength",
                "foundation",
                LimitState.ULS,
                minimum=self.limits.min_fc_mpa,
                maximum=self.limits.max_fc_mpa,
                unit="MPa",
            ),
            ("column", "fc"): CodeRequirement(
                "concrete strength",
                "column",
                LimitState.ULS,
                minimum=self.limits.min_fc_mpa,
                maximum=self.limits.max_fc_mpa,
                unit="MPa",
            ),
            ("beam", "fc"): CodeRequirement(
                "concrete strength",
                "beam",
                LimitState.ULS,
                minimum=self.limits.min_fc_mpa,
                maximum=self.limits.max_fc_mpa,
                unit="MPa",
            ),
            ("slab", "fc"): CodeRequirement(
                "concrete strength",
                "slab",
                LimitState.ULS,
                minimum=self.limits.min_fc_mpa,
                maximum=self.limits.max_fc_mpa,
                unit="MPa",
            ),
            ("wall", "fc"): CodeRequirement(
                "concrete strength",
                "wall",
                LimitState.ULS,
                minimum=self.limits.min_fc_mpa,
                maximum=self.limits.max_fc_mpa,
                unit="MPa",
            ),
            ("stair", "fc"): CodeRequirement(
                "concrete strength",
                "stair",
                LimitState.ULS,
                minimum=self.limits.min_fc_mpa,
                maximum=self.limits.max_fc_mpa,
                unit="MPa",
            ),
        }

        self._detail_rules = {
            (member, "cover"): DetailingRule(
                "minimum concrete cover",
                member,
                minimum=self.limits.min_cover_mm,
                unit="mm",
            )
            for member in self.supported_members()
        }

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
        return IranMaterials.material_requirement(
            material_type,
            requirement,
        )

    def get_detailing_rule(
        self,
        member_type: str,
        rule: str,
    ) -> Optional[DetailingRule]:
        return self._detail_rules.get(
            (str(member_type).lower(), str(rule).lower())
        )


def create_iran_concrete_code(
    limits: Optional[ConcreteLimits] = None,
) -> IranConcrete:
    return IranConcrete(limits)


__all__ = [
    "ConcreteLimits",
    "ConcreteSectionProperties",
    "IranConcrete",
    "create_iran_concrete_code",
]
