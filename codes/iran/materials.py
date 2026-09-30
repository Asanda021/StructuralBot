from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from codes.base import MaterialCategory, MaterialRequirement


class ConcreteClass(str, Enum):
    C20 = "C20"
    C25 = "C25"
    C30 = "C30"
    C35 = "C35"
    C40 = "C40"
    C45 = "C45"
    C50 = "C50"


class ReinforcementGrade(str, Enum):
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    S400 = "S400"
    S500 = "S500"


class StructuralSteelGrade(str, Enum):
    ST37 = "ST37"
    ST52 = "ST52"


@dataclass(frozen=True)
class ConcreteMaterial:
    grade: str
    fc_mpa: float
    density_kg_m3: float = 2400.0


@dataclass(frozen=True)
class ReinforcementMaterial:
    grade: str
    fy_mpa: float
    fu_mpa: float
    density_kg_m3: float = 7850.0


@dataclass(frozen=True)
class StructuralSteelMaterial:
    grade: str
    fy_mpa: float
    fu_mpa: float
    density_kg_m3: float = 7850.0


class IranMaterials:
    concrete: dict[str, ConcreteMaterial] = {
        x.value: ConcreteMaterial(x.value, float(x.value[1:]))
        for x in ConcreteClass
    }

    reinforcement: dict[str, ReinforcementMaterial] = {
        "A2": ReinforcementMaterial("A2", 300.0, 450.0),
        "A3": ReinforcementMaterial("A3", 400.0, 600.0),
        "A4": ReinforcementMaterial("A4", 500.0, 650.0),
        "S400": ReinforcementMaterial("S400", 400.0, 600.0),
        "S500": ReinforcementMaterial("S500", 500.0, 650.0),
    }

    structural_steel: dict[str, StructuralSteelMaterial] = {
        "ST37": StructuralSteelMaterial("ST37", 240.0, 370.0),
        "ST52": StructuralSteelMaterial("ST52", 360.0, 520.0),
    }

    @classmethod
    def get_concrete(cls, grade: str) -> ConcreteMaterial:
        key = str(grade).upper()
        if key not in cls.concrete:
            raise KeyError(f"Unknown concrete grade: {grade}")
        return cls.concrete[key]

    @classmethod
    def get_reinforcement(cls, grade: str) -> ReinforcementMaterial:
        key = str(grade).upper()
        if key not in cls.reinforcement:
            raise KeyError(f"Unknown reinforcement grade: {grade}")
        return cls.reinforcement[key]

    @classmethod
    def get_structural_steel(cls, grade: str) -> StructuralSteelMaterial:
        key = str(grade).upper()
        if key not in cls.structural_steel:
            raise KeyError(f"Unknown structural steel grade: {grade}")
        return cls.structural_steel[key]

    @classmethod
    def material_requirement(
        cls,
        material_type: str,
        requirement: str,
    ) -> Optional[MaterialRequirement]:
        key = str(material_type).lower()
        req = str(requirement).lower()

        if key in {"concrete", "بتن"}:
            if req in {"min_fc", "minimum_fc", "fc_min"}:
                return MaterialRequirement(
                    "minimum concrete strength",
                    MaterialCategory.CONCRETE.value,
                    minimum=20.0,
                    unit="MPa",
                )
            if req in {"max_fc", "maximum_fc", "fc_max"}:
                return MaterialRequirement(
                    "maximum concrete strength",
                    MaterialCategory.CONCRETE.value,
                    maximum=50.0,
                    unit="MPa",
                )

        if key in {"rebar", "reinforcement", "میلگرد"}:
            if req in {"fy_min", "minimum_fy"}:
                return MaterialRequirement(
                    "minimum reinforcement yield strength",
                    MaterialCategory.REBAR.value,
                    minimum=300.0,
                    unit="MPa",
                )

        return None


def get_concrete(grade: str) -> ConcreteMaterial:
    return IranMaterials.get_concrete(grade)


def get_reinforcement(grade: str) -> ReinforcementMaterial:
    return IranMaterials.get_reinforcement(grade)


def get_structural_steel(grade: str) -> StructuralSteelMaterial:
    return IranMaterials.get_structural_steel(grade)


__all__ = [
    "ConcreteClass",
    "ReinforcementGrade",
    "StructuralSteelGrade",
    "ConcreteMaterial",
    "ReinforcementMaterial",
    "StructuralSteelMaterial",
    "IranMaterials",
    "get_concrete",
    "get_reinforcement",
    "get_structural_steel",
]
