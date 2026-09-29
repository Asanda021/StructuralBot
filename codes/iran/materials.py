"""
StructuralBot - Iran Code Materials

Material definitions and validation helpers for Iranian
structural design workflows.

IMPORTANT:
This module does not perform structural analysis.
It provides material models and code-aware material data
for the calculation engine.

Exact code edition must always be explicitly selected.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Sequence


# ============================================================
# ENUMS
# ============================================================

class ConcreteClass(str, Enum):
    """
    Common concrete strength classes.

    Values are nominal compressive strengths in MPa.
    """

    C20 = "C20"
    C25 = "C25"
    C30 = "C30"
    C35 = "C35"
    C40 = "C40"
    C45 = "C45"
    C50 = "C50"


class ReinforcementGrade(str, Enum):
    """
    Reinforcement steel grades.

    These identifiers are kept generic so that the exact
    mechanical properties can be controlled by the selected
    code edition and project settings.
    """

    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    S400 = "S400"
    S500 = "S500"


class StructuralSteelGrade(str, Enum):
    """
    Structural steel grades.

    Included for future steel/composite support.
    """

    ST37 = "ST37"
    ST52 = "ST52"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass(frozen=True)
class ConcreteMaterial:
    """
    Concrete material definition.

    fc:
        Characteristic compressive strength in MPa.

    gamma_c:
        Material partial/safety factor where applicable.

    density:
        Density in kg/m3.
    """

    name: str
    fc: float

    gamma_c: float = 1.50

    density: float = 2400.0

    unit: str = "MPa"

    code_id: str = "iran"

    code_edition: str = ""

    metadata: Dict[str, object] = None

    def __post_init__(self) -> None:
        if self.fc <= 0:
            raise ValueError(
                "Concrete compressive strength must be greater than zero."
            )

        if self.gamma_c <= 0:
            raise ValueError(
                "Concrete material factor must be greater than zero."
            )

        if self.density <= 0:
            raise ValueError(
                "Concrete density must be greater than zero."
            )

        if self.metadata is None:
            object.__setattr__(
                self,
                "metadata",
                {},
            )


@dataclass(frozen=True)
class ReinforcementMaterial:
    """
    Reinforcement steel material definition.

    fy:
        Characteristic/yield strength in MPa.

    fu:
        Ultimate tensile strength in MPa.

    Es:
        Elastic modulus in MPa.

    density:
        Steel density in kg/m3.
    """

    name: str
    grade: str

    fy: float
    fu: float

    Es: float = 200000.0

    density: float = 7850.0

    gamma_s: float = 1.15

    code_id: str = "iran"

    code_edition: str = ""

    metadata: Dict[str, object] = None

    def __post_init__(self) -> None:
        if self.fy <= 0:
            raise ValueError(
                "Reinforcement yield strength must be greater than zero."
            )

        if self.fu <= 0:
            raise ValueError(
                "Reinforcement ultimate strength must be greater than zero."
            )

        if self.fu < self.fy:
            raise ValueError(
                "Ultimate strength cannot be lower than yield strength."
            )

        if self.Es <= 0:
            raise ValueError(
                "Elastic modulus must be greater than zero."
            )

        if self.density <= 0:
            raise ValueError(
                "Steel density must be greater than zero."
            )

        if self.gamma_s <= 0:
            raise ValueError(
                "Steel material factor must be greater than zero."
            )

        if self.metadata is None:
            object.__setattr__(
                self,
                "metadata",
                {},
            )


@dataclass(frozen=True)
class StructuralSteelMaterial:
    """
    Structural steel material definition.

    Included now so the architecture can support steel and
    composite structures without redesigning the material layer.
    """

    name: str
    grade: str

    fy: float
    fu: float

    Es: float = 200000.0

    density: float = 7850.0

    gamma_m: float = 1.0

    code_id: str = "iran"

    code_edition: str = ""

    metadata: Dict[str, object] = None

    def __post_init__(self) -> None:
        if self.fy <= 0:
            raise ValueError(
                "Structural steel yield strength must be greater than zero."
            )

        if self.fu <= 0:
            raise ValueError(
                "Structural steel ultimate strength must be greater than zero."
            )

        if self.fu < self.fy:
            raise ValueError(
                "Ultimate strength cannot be lower than yield strength."
            )

        if self.Es <= 0:
            raise ValueError(
                "Elastic modulus must be greater than zero."
            )

        if self.density <= 0:
            raise ValueError(
                "Steel density must be greater than zero."
            )

        if self.gamma_m <= 0:
            raise ValueError(
                "Steel material factor must be greater than zero."
            )

        if self.metadata is None:
            object.__setattr__(
                self,
                "metadata",
                {},
            )


# ============================================================
# MATERIAL FACTORY
# ============================================================

class IranMaterials:
    """
    Material provider for Iranian structural design.

    This class centralizes material definitions so that the
    calculation modules do not hard-code material properties.

    The exact edition is passed when creating the provider.
    """

    DEFAULT_CODE_ID = "iran"

    def __init__(
        self,
        code_edition: str = "",
    ) -> None:
        self.code_edition = code_edition

    # --------------------------------------------------------
    # CONCRETE
    # --------------------------------------------------------

    def concrete(
        self,
        fc: float,
        *,
        name: Optional[str] = None,
        gamma_c: float = 1.50,
        density: float = 2400.0,
    ) -> ConcreteMaterial:
        """
        Create a concrete material.

        Parameters:
            fc:
                Compressive strength in MPa.
        """

        if name is None:
            name = f"C{int(fc)}"

        return ConcreteMaterial(
            name=name,
            fc=float(fc),
            gamma_c=float(gamma_c),
            density=float(density),
            code_id=self.DEFAULT_CODE_ID,
            code_edition=self.code_edition,
        )

    # --------------------------------------------------------
    # REINFORCEMENT
    # --------------------------------------------------------

    def reinforcement(
        self,
        grade: str,
        *,
        fy: Optional[float] = None,
        fu: Optional[float] = None,
        Es: float = 200000.0,
        gamma_s: float = 1.15,
    ) -> ReinforcementMaterial:
        """
        Create a reinforcement material.

        If fy/fu are not supplied, known standard grades are
        looked up from the internal material table.
        """

        normalized_grade = str(
            grade
        ).upper().strip()

        defaults = (
            _REINFORCEMENT_DATABASE.get(
                normalized_grade
            )
        )

        if defaults is not None:
            if fy is None:
                fy = defaults["fy"]

            if fu is None:
                fu = defaults["fu"]

        if fy is None or fu is None:
            raise ValueError(
                "fy and fu must be supplied for unknown "
                f"reinforcement grade '{grade}'."
            )

        return ReinforcementMaterial(
            name=normalized_grade,
            grade=normalized_grade,
            fy=float(fy),
            fu=float(fu),
            Es=float(Es),
            gamma_s=float(gamma_s),
            code_id=self.DEFAULT_CODE_ID,
            code_edition=self.code_edition,
        )

    # --------------------------------------------------------
    # STRUCTURAL STEEL
    # --------------------------------------------------------

    def structural_steel(
        self,
        grade: str,
        *,
        fy: Optional[float] = None,
        fu: Optional[float] = None,
        Es: float = 200000.0,
        gamma_m: float = 1.0,
    ) -> StructuralSteelMaterial:
        """
        Create a structural steel material.

        Included for future steel/composite modules.
        """

        normalized_grade = str(
            grade
        ).upper().strip()

        defaults = (
            _STRUCTURAL_STEEL_DATABASE.get(
                normalized_grade
            )
        )

        if defaults is not None:
            if fy is None:
                fy = defaults["fy"]

            if fu is None:
                fu = defaults["fu"]

        if fy is None or fu is None:
            raise ValueError(
                "fy and fu must be supplied for unknown "
                f"structural steel grade '{grade}'."
            )

        return StructuralSteelMaterial(
            name=normalized_grade,
            grade=normalized_grade,
            fy=float(fy),
            fu=float(fu),
            Es=float(Es),
            gamma_m=float(gamma_m),
            code_id=self.DEFAULT_CODE_ID,
            code_edition=self.code_edition,
        )

    # --------------------------------------------------------
    # LISTS
    # --------------------------------------------------------

    def available_concrete_strengths(
        self,
    ) -> List[float]:
        """
        Return commonly supported concrete strengths.
        """

        return [
            20.0,
            25.0,
            30.0,
            35.0,
            40.0,
            45.0,
            50.0,
        ]

    def available_reinforcement_grades(
        self,
    ) -> List[str]:
        """
        Return known reinforcement grades.
        """

        return list(
            _REINFORCEMENT_DATABASE.keys()
        )

    def available_structural_steel_grades(
        self,
    ) -> List[str]:
        """
        Return known structural steel grades.
        """

        return list(
            _STRUCTURAL_STEEL_DATABASE.keys()
        )


# ============================================================
# INTERNAL MATERIAL DATABASES
# ============================================================

# NOTE:
# These values are kept in one place intentionally.
# Final engineering acceptance of a material must be based on
# the selected project code, material standard, certificate,
# and applicable edition.

_REINFORCEMENT_DATABASE: Dict[
    str,
    Dict[str, float],
] = {
    "A2": {
        "fy": 300.0,
        "fu": 450.0,
    },
    "A3": {
        "fy": 400.0,
        "fu": 600.0,
    },
    "A4": {
        "fy": 500.0,
        "fu": 650.0,
    },
    "S400": {
        "fy": 400.0,
        "fu": 600.0,
    },
    "S500": {
        "fy": 500.0,
        "fu": 650.0,
    },
}


_STRUCTURAL_STEEL_DATABASE: Dict[
    str,
    Dict[str, float],
] = {
    "ST37": {
        "fy": 240.0,
        "fu": 370.0,
    },
    "ST52": {
        "fy": 360.0,
        "fu": 520.0,
    },
}


# ============================================================
# DEFAULT MATERIAL HELPERS
# ============================================================

def get_concrete(
    fc: float,
    *,
    code_edition: str = "",
) -> ConcreteMaterial:
    """
    Convenience function for creating concrete.
    """

    provider = IranMaterials(
        code_edition=code_edition
    )

    return provider.concrete(
        fc
    )


def get_reinforcement(
    grade: str,
    *,
    code_edition: str = "",
) -> ReinforcementMaterial:
    """
    Convenience function for creating reinforcement.
    """

    provider = IranMaterials(
        code_edition=code_edition
    )

    return provider.reinforcement(
        grade
    )


def get_structural_steel(
    grade: str,
    *,
    code_edition: str = "",
) -> StructuralSteelMaterial:
    """
    Convenience function for creating structural steel.
    """

    provider = IranMaterials(
        code_edition=code_edition
    )

    return provider.structural_steel(
        grade
    )


# ============================================================
# VALIDATION HELPERS
# ============================================================

def validate_concrete(
    concrete: ConcreteMaterial,
) -> List[str]:
    """
    Validate concrete material data.
    """

    errors: List[str] = []

    if concrete.fc <= 0:
        errors.append(
            "Concrete compressive strength must be positive."
        )

    if concrete.gamma_c <= 0:
        errors.append(
            "Concrete material factor must be positive."
        )

    if concrete.density <= 0:
        errors.append(
            "Concrete density must be positive."
        )

    return errors


def validate_reinforcement(
    reinforcement: ReinforcementMaterial,
) -> List[str]:
    """
    Validate reinforcement material data.
    """

    errors: List[str] = []

    if reinforcement.fy <= 0:
        errors.append(
            "Reinforcement yield strength must be positive."
        )

    if reinforcement.fu <= 0:
        errors.append(
            "Reinforcement ultimate strength must be positive."
        )

    if reinforcement.fu < reinforcement.fy:
        errors.append(
            "Ultimate strength cannot be lower than yield strength."
        )

    if reinforcement.Es <= 0:
        errors.append(
            "Reinforcement elastic modulus must be positive."
        )

    return errors


def validate_structural_steel(
    steel: StructuralSteelMaterial,
) -> List[str]:
    """
    Validate structural steel material data.
    """

    errors: List[str] = []

    if steel.fy <= 0:
        errors.append(
            "Structural steel yield strength must be positive."
        )

    if steel.fu <= 0:
        errors.append(
            "Structural steel ultimate strength must be positive."
        )

    if steel.fu < steel.fy:
        errors.append(
            "Ultimate strength cannot be lower than yield strength."
        )

    if steel.Es <= 0:
        errors.append(
            "Structural steel elastic modulus must be positive."
        )

    return errors


# ============================================================
# MODULE EXPORTS
# ============================================================

__all__ = [
    # Enums
    "ConcreteClass",
    "ReinforcementGrade",
    "StructuralSteelGrade",

    # Materials
    "ConcreteMaterial",
    "ReinforcementMaterial",
    "StructuralSteelMaterial",

    # Provider
    "IranMaterials",

    # Factory helpers
    "get_concrete",
    "get_reinforcement",
    "get_structural_steel",

    # Validation
    "validate_concrete",
    "validate_reinforcement",
    "validate_structural_steel",
]
