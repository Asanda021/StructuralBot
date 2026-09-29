"""
StructuralBot - Iran Reinforcement Rules

Iranian reinforcement rules and reinforcement-related code interface.

Important:
    This module intentionally avoids pretending that generic values such as
    "40d" are universal Iranian code requirements.

    Exact reinforcement limits, development lengths, lap lengths, spacing
    limits, anchorage rules, seismic requirements, and detailing provisions
    must be selected according to the active Iranian code edition and the
    applicable member/detailing condition.

    The calculation engine remains code-independent. This module provides
    the Iran-specific rules/interface consumed by the calculation engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import pi
from typing import Any, Dict, Iterable, List, Optional

from codes.base import (
    CodeCheck,
    CodeEdition,
    CodeFamily,
    CodeContext,
    CodeRequirement,
    DetailingRule,
    DesignCode,
    MaterialCategory,
    MemberCategory,
    CheckStatus,
    LimitState,
    check_maximum,
    check_minimum,
    check_range,
)

from codes.iran.materials import (
    IranMaterials,
    ReinforcementGrade,
    ReinforcementMaterial,
)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

STANDARD_DIAMETERS_MM: tuple[int, ...] = (
    6,
    8,
    10,
    12,
    14,
    16,
    18,
    20,
    22,
    25,
    28,
    32,
    36,
    40,
)

STEEL_DENSITY_KG_M3 = 7850.0


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------

class ReinforcementRole(str, Enum):
    """
    Functional role of reinforcement.
    """

    LONGITUDINAL = "longitudinal"
    TRANSVERSE = "transverse"
    DISTRIBUTION = "distribution"
    TEMPERATURE = "temperature"
    CONFINEMENT = "confinement"
    SHEAR = "shear"
    TORSION = "torsion"
    STARTER = "starter"
    DOWEL = "dowel"


class ReinforcementRegion(str, Enum):
    """
    Structural/detailing region.

    Critical regions are intentionally represented explicitly because
    detailing requirements can differ from ordinary regions.
    """

    GENERAL = "general"
    SUPPORT = "support"
    SPAN = "span"
    JOINT = "joint"
    CRITICAL = "critical"
    END = "end"
    LAP = "lap"
    ANCHORAGE = "anchorage"


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReinforcementLimits:
    """
    Configurable reinforcement limits.

    Values are optional because exact limits depend on:
        - member type
        - load case
        - reinforcement role
        - seismic/detailing condition
        - code edition
        - governing design provision

    Do not treat None as a numeric design limit.
    """

    minimum_ratio: Optional[float] = None
    maximum_ratio: Optional[float] = None

    minimum_area_mm2: Optional[float] = None
    maximum_area_mm2: Optional[float] = None

    minimum_spacing_mm: Optional[float] = None
    maximum_spacing_mm: Optional[float] = None


@dataclass(frozen=True)
class BarProperties:
    """
    Basic geometric/mechanical properties of one reinforcement bar.
    """

    diameter_mm: float
    area_mm2: float
    perimeter_mm: float
    weight_kg_per_m: float
    grade: ReinforcementGrade
    fy_mpa: float
    fu_mpa: float
    Es_mpa: float


@dataclass(frozen=True)
class DevelopmentLengthInput:
    """
    Inputs for code-aware development-length calculation.

    The module does not assume a universal multiplier such as 40d.

    `coefficient` must come from the active code rule/condition.
    """

    diameter_mm: float
    coefficient: float

    member_category: MemberCategory
    reinforcement_role: ReinforcementRole = ReinforcementRole.LONGITUDINAL
    region: ReinforcementRegion = ReinforcementRegion.GENERAL

    concrete_factor: float = 1.0
    steel_factor: float = 1.0
    confinement_factor: float = 1.0

    minimum_length_mm: Optional[float] = None


@dataclass(frozen=True)
class LapLengthInput:
    """
    Inputs for code-aware lap-splice calculation.

    The lap coefficient is intentionally supplied by the active code rule.
    """

    development_length_mm: float
    coefficient: float

    member_category: MemberCategory
    reinforcement_role: ReinforcementRole = ReinforcementRole.LONGITUDINAL
    region: ReinforcementRegion = ReinforcementRegion.LAP

    minimum_length_mm: Optional[float] = None


# ---------------------------------------------------------------------------
# BASIC REBAR GEOMETRY
# ---------------------------------------------------------------------------

def validate_diameter(diameter_mm: float) -> float:
    """
    Validate reinforcement diameter.

    Returns:
        float: validated diameter in mm.
    """

    diameter = float(diameter_mm)

    if diameter <= 0:
        raise ValueError("Reinforcement diameter must be greater than zero.")

    return diameter


def bar_area_mm2(diameter_mm: float) -> float:
    """
    Calculate cross-sectional area of a circular reinforcement bar.

    Args:
        diameter_mm: bar diameter in millimeters.

    Returns:
        Area in mm².
    """

    d = validate_diameter(diameter_mm)
    return pi * d * d / 4.0


def bar_perimeter_mm(diameter_mm: float) -> float:
    """
    Calculate bar perimeter in mm.
    """

    d = validate_diameter(diameter_mm)
    return pi * d


def bar_weight_kg_per_m(
    diameter_mm: float,
    density_kg_m3: float = STEEL_DENSITY_KG_M3,
) -> float:
    """
    Calculate theoretical reinforcement weight per meter.

    Uses:
        mass = area × density

    Returns:
        kg/m
    """

    d = validate_diameter(diameter_mm)

    if density_kg_m3 <= 0:
        raise ValueError("Steel density must be greater than zero.")

    area_m2 = bar_area_mm2(d) / 1_000_000.0
    return area_m2 * float(density_kg_m3)


def total_bar_weight_kg(
    diameter_mm: float,
    length_m: float,
    quantity: int = 1,
    density_kg_m3: float = STEEL_DENSITY_KG_M3,
) -> float:
    """
    Calculate total theoretical weight of reinforcement.
    """

    if length_m < 0:
        raise ValueError("Bar length cannot be negative.")

    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    return (
        bar_weight_kg_per_m(diameter_mm, density_kg_m3)
        * float(length_m)
        * int(quantity)
    )


# ---------------------------------------------------------------------------
# MATERIAL INTERFACE
# ---------------------------------------------------------------------------

class IranReinforcement(DesignCode):
    """
    Iran-specific reinforcement code interface.

    This class is intentionally focused on reinforcement rules and metadata.
    It does not perform complete member design.

    Complete beam/column/slab/foundation calculations remain in the core
    calculation layer and consume this code interface.
    """

    DEFAULT_CODE_ID = "m9"

    def __init__(
        self,
        code_edition: str = "1399",
        *,
        reinforcement_limits: Optional[
            Dict[MemberCategory, ReinforcementLimits]
        ] = None,
    ) -> None:

        self.code_edition = str(code_edition)

        self.edition = CodeEdition(
            family=CodeFamily.IRAN,
            code_id=self.DEFAULT_CODE_ID,
            edition=self.code_edition,
            title="Iranian Reinforcement Design Rules",
            authority="Iranian structural design code framework",
            language="fa",
        )

        self.context = CodeContext(
            edition=self.edition,
            description=(
                "Iran-specific reinforcement properties, validation, "
                "detailing interfaces, and code-aware reinforcement checks."
            ),
        )

        self._limits = reinforcement_limits or {}

    # ------------------------------------------------------------------
    # DESIGN CODE INTERFACE
    # ------------------------------------------------------------------

    @property
    def code_id(self) -> str:
        return self.DEFAULT_CODE_ID

    @property
    def family(self) -> CodeFamily:
        return CodeFamily.IRAN

    def supported_members(self) -> List[MemberCategory]:
        return [
            MemberCategory.FOUNDATION,
            MemberCategory.COLUMN,
            MemberCategory.BEAM,
            MemberCategory.SLAB,
            MemberCategory.WALL,
            MemberCategory.STAIR,
        ]

    def get_material_requirement(
        self,
        member_category: MemberCategory,
    ) -> Optional[CodeRequirement]:

        return CodeRequirement(
            key=f"{member_category.value}.reinforcement.material",
            title="Reinforcement Material",
            description=(
                "Reinforcement material shall be selected from the "
                "approved material database for the active code context."
            ),
            value_type="reinforcement_grade",
            unit=None,
            clause=self._clause("material"),
        )

    def get_requirement(
        self,
        member_category: MemberCategory,
        key: str,
    ) -> Optional[CodeRequirement]:

        normalized = str(key).strip().lower()

        known_keys = {
            "minimum_ratio",
            "maximum_ratio",
            "minimum_area",
            "maximum_area",
            "minimum_spacing",
            "maximum_spacing",
            "development_length",
            "lap_length",
        }

        if normalized not in known_keys:
            return None

        return CodeRequirement(
            key=f"{member_category.value}.reinforcement.{normalized}",
            title=normalized.replace("_", " ").title(),
            description=(
                "Value is edition- and condition-dependent and must be "
                "resolved from the active Iranian code configuration."
            ),
            value_type="numeric",
            unit=(
                "mm"
                if "spacing" in normalized
                or "length" in normalized
                else (
                    "mm2"
                    if "area" in normalized
                    else "%"
                )
            ),
            clause=self._clause(normalized),
        )

    def get_detailing_rule(
        self,
        member_category: MemberCategory,
        key: str,
    ) -> Optional[DetailingRule]:

        normalized = str(key).strip().lower()

        if normalized == "bar_spacing":
            return DetailingRule(
                key=f"{member_category.value}.bar_spacing",
                title="Bar Spacing",
                description=(
                    "Bar spacing shall be checked against all applicable "
                    "code and constructability limits."
                ),
                clause=self._clause("bar_spacing"),
            )

        if normalized == "development_length":
            return DetailingRule(
                key=f"{member_category.value}.development_length",
                title="Development Length",
                description=(
                    "Development length must be calculated from the active "
                    "code provision and reinforcement/concrete conditions."
                ),
                clause=self._clause("development_length"),
            )

        if normalized == "lap_length":
            return DetailingRule(
                key=f"{member_category.value}.lap_length",
                title="Lap Splice Length",
                description=(
                    "Lap splice length must be calculated from the active "
                    "code provision and splice condition."
                ),
                clause=self._clause("lap_length"),
            )

        return None

    # ------------------------------------------------------------------
    # MATERIALS
    # ------------------------------------------------------------------

    def get_reinforcement_material(
        self,
        grade: ReinforcementGrade | str,
    ) -> ReinforcementMaterial:

        return IranMaterials.reinforcement(grade)

    def available_grades(self) -> List[str]:
        return [
            grade.value
            for grade in ReinforcementGrade
        ]

    def available_diameters(self) -> List[int]:
        return list(STANDARD_DIAMETERS_MM)

    # ------------------------------------------------------------------
    # BAR PROPERTIES
    # ------------------------------------------------------------------

    def bar_properties(
        self,
        diameter_mm: float,
        grade: ReinforcementGrade | str,
    ) -> BarProperties:

        material = self.get_reinforcement_material(grade)

        diameter = validate_diameter(diameter_mm)

        return BarProperties(
            diameter_mm=diameter,
            area_mm2=bar_area_mm2(diameter),
            perimeter_mm=bar_perimeter_mm(diameter),
            weight_kg_per_m=bar_weight_kg_per_m(diameter),
            grade=material.grade,
            fy_mpa=material.fy,
            fu_mpa=material.fu,
            Es_mpa=material.Es,
        )

    # ------------------------------------------------------------------
    # AREA / RATIO
    # ------------------------------------------------------------------

    @staticmethod
    def reinforcement_area(
        diameter_mm: float,
        quantity: int,
    ) -> float:
        """
        Total steel area in mm².
        """

        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")

        return bar_area_mm2(diameter_mm) * int(quantity)

    @staticmethod
    def reinforcement_ratio(
        steel_area_mm2: float,
        gross_area_mm2: float,
    ) -> float:
        """
        Return reinforcement ratio as a decimal.

        Example:
            0.01 = 1%
        """

        if steel_area_mm2 < 0:
            raise ValueError("Steel area cannot be negative.")

        if gross_area_mm2 <= 0:
            raise ValueError("Gross area must be greater than zero.")

        return steel_area_mm2 / gross_area_mm2

    @staticmethod
    def reinforcement_percentage(
        steel_area_mm2: float,
        gross_area_mm2: float,
    ) -> float:
        """
        Return reinforcement ratio as percentage.
        """

        return (
            IranReinforcement.reinforcement_ratio(
                steel_area_mm2,
                gross_area_mm2,
            )
            * 100.0
        )

    # ------------------------------------------------------------------
    # MINIMUM / MAXIMUM AREA
    # ------------------------------------------------------------------

    def minimum_reinforcement_area(
        self,
        member_category: MemberCategory,
        gross_area_mm2: float,
        *,
        minimum_ratio: Optional[float] = None,
    ) -> Optional[float]:
        """
        Calculate minimum reinforcement area.

        If minimum_ratio is not supplied, the configured code limit is used.

        Returns:
            Minimum steel area in mm², or None if no rule is configured.
        """

        if gross_area_mm2 <= 0:
            raise ValueError("Gross area must be greater than zero.")

        ratio = minimum_ratio

        if ratio is None:
            limits = self._limits.get(member_category)
            ratio = (
                limits.minimum_ratio
                if limits is not None
                else None
            )

        if ratio is None:
            return None

        if ratio < 0:
            raise ValueError("Minimum reinforcement ratio cannot be negative.")

        return gross_area_mm2 * ratio

    def maximum_reinforcement_area(
        self,
        member_category: MemberCategory,
        gross_area_mm2: float,
        *,
        maximum_ratio: Optional[float] = None,
    ) -> Optional[float]:
        """
        Calculate maximum reinforcement area from configured/code ratio.
        """

        if gross_area_mm2 <= 0:
            raise ValueError("Gross area must be greater than zero.")

        ratio = maximum_ratio

        if ratio is None:
            limits = self._limits.get(member_category)
            ratio = (
                limits.maximum_ratio
                if limits is not None
                else None
            )

        if ratio is None:
            return None

        if ratio <= 0:
            raise ValueError("Maximum reinforcement ratio must be positive.")

        return gross_area_mm2 * ratio

    # ------------------------------------------------------------------
    # SPACING
    # ------------------------------------------------------------------

    def check_spacing(
        self,
        spacing_mm: float,
        member_category: MemberCategory,
        *,
        minimum_spacing_mm: Optional[float] = None,
        maximum_spacing_mm: Optional[float] = None,
    ) -> CodeCheck:

        if spacing_mm <= 0:
            raise ValueError("Spacing must be greater than zero.")

        limits = self._limits.get(member_category)

        min_spacing = minimum_spacing_mm
        max_spacing = maximum_spacing_mm

        if min_spacing is None and limits is not None:
            min_spacing = limits.minimum_spacing_mm

        if max_spacing is None and limits is not None:
            max_spacing = limits.maximum_spacing_mm

        if min_spacing is not None and spacing_mm < min_spacing:
            return check_minimum(
                value=spacing_mm,
                minimum=min_spacing,
                name="reinforcement spacing",
                unit="mm",
                clause=self._clause("minimum_spacing"),
            )

        if max_spacing is not None and spacing_mm > max_spacing:
            return check_maximum(
                value=spacing_mm,
                maximum=max_spacing,
                name="reinforcement spacing",
                unit="mm",
                clause=self._clause("maximum_spacing"),
            )

        return CodeCheck(
            name="reinforcement spacing",
            status=CheckStatus.PASS,
            value=spacing_mm,
            limit_min=min_spacing,
            limit_max=max_spacing,
            unit="mm",
            clause=self._clause("spacing"),
            message="Reinforcement spacing satisfies configured limits.",
        )

    # ------------------------------------------------------------------
    # DEVELOPMENT LENGTH
    # ------------------------------------------------------------------

    @staticmethod
    def development_length(
        data: DevelopmentLengthInput,
    ) -> float:
        """
        Calculate code-aware development length.

        Formula:

            Ld = d × coefficient
                 × concrete_factor
                 × steel_factor
                 × confinement_factor

        The coefficient must be supplied by the active code rule.

        No universal coefficient is assumed.
        """

        if data.diameter_mm <= 0:
            raise ValueError("Bar diameter must be greater than zero.")

        if data.coefficient <= 0:
            raise ValueError("Development-length coefficient must be positive.")

        if data.concrete_factor <= 0:
            raise ValueError("Concrete factor must be positive.")

        if data.steel_factor <= 0:
            raise ValueError("Steel factor must be positive.")

        if data.confinement_factor <= 0:
            raise ValueError("Confinement factor must be positive.")

        length = (
            data.diameter_mm
            * data.coefficient
            * data.concrete_factor
            * data.steel_factor
            * data.confinement_factor
        )

        if data.minimum_length_mm is not None:
            if data.minimum_length_mm < 0:
                raise ValueError(
                    "Minimum development length cannot be negative."
                )

            length = max(length, data.minimum_length_mm)

        return length

    # ------------------------------------------------------------------
    # LAP LENGTH
    # ------------------------------------------------------------------

    @staticmethod
    def lap_length(
        data: LapLengthInput,
    ) -> float:
        """
        Calculate code-aware lap splice length.

        The splice coefficient must be supplied by the active code rule.
        """

        if data.development_length_mm <= 0:
            raise ValueError(
                "Development length must be greater than zero."
            )

        if data.coefficient <= 0:
            raise ValueError(
                "Lap-length coefficient must be positive."
            )

        length = (
            data.development_length_mm
            * data.coefficient
        )

        if data.minimum_length_mm is not None:
            if data.minimum_length_mm < 0:
                raise ValueError(
                    "Minimum lap length cannot be negative."
                )

            length = max(length, data.minimum_length_mm)

        return length

    # ------------------------------------------------------------------
    # BASIC REINFORCEMENT VALIDATION
    # ------------------------------------------------------------------

    def validate_bar(
        self,
        diameter_mm: float,
        grade: ReinforcementGrade | str,
        quantity: int = 1,
    ) -> BarProperties:

        diameter = validate_diameter(diameter_mm)

        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")

        if diameter not in STANDARD_DIAMETERS_MM:
            raise ValueError(
                f"Unsupported standard reinforcement diameter: {diameter:g} mm"
            )

        return self.bar_properties(
            diameter_mm=diameter,
            grade=grade,
        )

    # ------------------------------------------------------------------
    # CODE CHECK
    # ------------------------------------------------------------------

    def run_check(
        self,
        *,
        member_category: MemberCategory,
        steel_area_mm2: float,
        gross_area_mm2: float,
        minimum_ratio: Optional[float] = None,
        maximum_ratio: Optional[float] = None,
    ) -> CodeCheck:
        """
        Check reinforcement ratio against configured or explicitly supplied
        limits.

        This is a generic code-interface check.

        It does NOT replace complete member design.
        """

        if steel_area_mm2 < 0:
            raise ValueError("Steel area cannot be negative.")

        if gross_area_mm2 <= 0:
            raise ValueError("Gross area must be greater than zero.")

        ratio = self.reinforcement_ratio(
            steel_area_mm2,
            gross_area_mm2,
        )

        limits = self._limits.get(member_category)

        min_ratio = minimum_ratio
        max_ratio = maximum_ratio

        if min_ratio is None and limits is not None:
            min_ratio = limits.minimum_ratio

        if max_ratio is None and limits is not None:
            max_ratio = limits.maximum_ratio

        if min_ratio is not None and ratio < min_ratio:
            return check_minimum(
                value=ratio,
                minimum=min_ratio,
                name="reinforcement ratio",
                unit="ratio",
                clause=self._clause("minimum_ratio"),
            )

        if max_ratio is not None and ratio > max_ratio:
            return check_maximum(
                value=ratio,
                maximum=max_ratio,
                name="reinforcement ratio",
                unit="ratio",
                clause=self._clause("maximum_ratio"),
            )

        return CodeCheck(
            name="reinforcement ratio",
            status=CheckStatus.PASS,
            value=ratio,
            limit_min=min_ratio,
            limit_max=max_ratio,
            unit="ratio",
            clause=self._clause("reinforcement_ratio"),
            message="Reinforcement ratio satisfies configured limits.",
        )

    # ------------------------------------------------------------------
    # REQUIREMENT CONFIGURATION
    # ------------------------------------------------------------------

    def set_limits(
        self,
        member_category: MemberCategory,
        limits: ReinforcementLimits,
    ) -> None:
        """
        Set edition/condition-specific reinforcement limits.

        This allows later integration of verified code provisions without
        modifying the core reinforcement engine.
        """

        self._limits[member_category] = limits

    def get_limits(
        self,
        member_category: MemberCategory,
    ) -> Optional[ReinforcementLimits]:

        return self._limits.get(member_category)

    # ------------------------------------------------------------------
    # METADATA
    # ------------------------------------------------------------------

    def metadata(self) -> Dict[str, Any]:
        return {
            "code_family": self.family.value,
            "code_id": self.code_id,
            "edition": self.code_edition,
            "title": self.edition.title,
            "supported_members": [
                member.value
                for member in self.supported_members()
            ],
            "standard_diameters_mm": list(STANDARD_DIAMETERS_MM),
            "available_grades": self.available_grades(),
            "notes": [
                (
                    "Exact reinforcement limits must be resolved from "
                    "the selected code edition and member condition."
                ),
                (
                    "Development and lap lengths require code-specific "
                    "coefficients and conditions."
                ),
                (
                    "Generic assumptions such as universal 40d are "
                    "intentionally not hard-coded."
                ),
            ],
        }

    # ------------------------------------------------------------------
    # INTERNAL
    # ------------------------------------------------------------------

    def _clause(self, key: str) -> str:
        """
        Return a stable internal code-reference identifier.

        These identifiers are intentionally not presented as official
        clause numbers until the exact code edition and official source
        have been verified.
        """

        normalized = str(key).strip().lower()

        return (
            f"{self.code_id}/"
            f"{self.code_edition}/"
            f"reinforcement/{normalized}"
        )


# ---------------------------------------------------------------------------
# FACTORY
# ---------------------------------------------------------------------------

def create_iran_reinforcement_code(
    code_edition: str = "1399",
    *,
    reinforcement_limits: Optional[
        Dict[MemberCategory, ReinforcementLimits]
    ] = None,
) -> IranReinforcement:
    """
    Create an Iran reinforcement code instance.
    """

    return IranReinforcement(
        code_edition=code_edition,
        reinforcement_limits=reinforcement_limits,
    )


# ---------------------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# ---------------------------------------------------------------------------

def get_bar_properties(
    diameter_mm: float,
    grade: ReinforcementGrade | str,
) -> BarProperties:
    """
    Convenience wrapper for bar properties.
    """

    return IranReinforcement().bar_properties(
        diameter_mm=diameter_mm,
        grade=grade,
    )


def calculate_development_length(
    diameter_mm: float,
    coefficient: float,
    *,
    member_category: MemberCategory,
    reinforcement_role: ReinforcementRole = ReinforcementRole.LONGITUDINAL,
    region: ReinforcementRegion = ReinforcementRegion.GENERAL,
    concrete_factor: float = 1.0,
    steel_factor: float = 1.0,
    confinement_factor: float = 1.0,
    minimum_length_mm: Optional[float] = None,
) -> float:
    """
    Convenience wrapper for development length.
    """

    return IranReinforcement.development_length(
        DevelopmentLengthInput(
            diameter_mm=diameter_mm,
            coefficient=coefficient,
            member_category=member_category,
            reinforcement_role=reinforcement_role,
            region=region,
            concrete_factor=concrete_factor,
            steel_factor=steel_factor,
            confinement_factor=confinement_factor,
            minimum_length_mm=minimum_length_mm,
        )
    )


def calculate_lap_length(
    development_length_mm: float,
    coefficient: float,
    *,
    member_category: MemberCategory,
    reinforcement_role: ReinforcementRole = ReinforcementRole.LONGITUDINAL,
    region: ReinforcementRegion = ReinforcementRegion.LAP,
    minimum_length_mm: Optional[float] = None,
) -> float:
    """
    Convenience wrapper for lap length.
    """

    return IranReinforcement.lap_length(
        LapLengthInput(
            development_length_mm=development_length_mm,
            coefficient=coefficient,
            member_category=member_category,
            reinforcement_role=reinforcement_role,
            region=region,
            minimum_length_mm=minimum_length_mm,
        )
    )


def calculate_bar_weight(
    diameter_mm: float,
    length_m: float,
    quantity: int = 1,
) -> float:
    """
    Convenience wrapper for total bar weight.
    """

    return total_bar_weight_kg(
        diameter_mm=diameter_mm,
        length_m=length_m,
        quantity=quantity,
    )


# ---------------------------------------------------------------------------
# EXPORTS
# ---------------------------------------------------------------------------

__all__ = [
    "STANDARD_DIAMETERS_MM",
    "STEEL_DENSITY_KG_M3",
    "ReinforcementRole",
    "ReinforcementRegion",
    "ReinforcementLimits",
    "BarProperties",
    "DevelopmentLengthInput",
    "LapLengthInput",
    "bar_area_mm2",
    "bar_perimeter_mm",
    "bar_weight_kg_per_m",
    "total_bar_weight_kg",
    "IranReinforcement",
    "create_iran_reinforcement_code",
    "get_bar_properties",
    "calculate_development_length",
    "calculate_lap_length",
    "calculate_bar_weight",
]
