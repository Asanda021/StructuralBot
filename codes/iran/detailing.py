"""
StructuralBot - Iran Reinforcement Detailing Rules

Iranian reinforcement detailing interface.

This module is responsible for:
- reinforcement spacing rules
- concrete cover interface
- development / anchorage interfaces
- lap splice interfaces
- hooks and bends
- critical-region metadata
- constructability checks
- detailing requirements consumed by BBS / Cut List

Important:
    Exact numerical requirements are edition- and condition-dependent.
    Therefore, this module does not hard-code universal values such as
    "40d", universal seismic spacing, or a single cover value for every
    member.

    Verified code provisions can later be loaded into DetailingConfig
    without changing the calculation architecture.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import pi
from typing import Any, Dict, List, Optional

from codes.base import (
    CodeCheck,
    CodeEdition,
    CodeFamily,
    CodeContext,
    CodeRequirement,
    DetailingRule,
    DesignCode,
    MemberCategory,
    CheckStatus,
    check_maximum,
    check_minimum,
    check_range,
)

from codes.iran.reinforcement import (
    IranReinforcement,
    ReinforcementRegion,
    ReinforcementRole,
    STANDARD_DIAMETERS_MM,
    bar_area_mm2,
    bar_perimeter_mm,
)


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------

class DetailingCondition(str, Enum):
    """
    General detailing condition.
    """

    GENERAL = "general"
    EXPOSURE = "exposure"
    CASTING = "casting"
    SEISMIC = "seismic"
    CRITICAL_REGION = "critical_region"
    SUPPORT = "support"
    JOINT = "joint"
    ANCHORAGE = "anchorage"
    LAP = "lap"


class HookType(str, Enum):
    """
    Hook / bend type.

    The actual bend diameter and extension requirements are resolved from
    the active code configuration.
    """

    NONE = "none"
    STANDARD = "standard"
    STIRRUP = "stirrup"
    CLOSED = "closed"
    U_HOOK = "u_hook"
    L_HOOK = "l_hook"
    CUSTOM = "custom"


class SpliceType(str, Enum):
    """
    Reinforcement splice type.
    """

    NONE = "none"
    LAP = "lap"
    MECHANICAL = "mechanical"
    WELDED = "welded"


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DetailingLimits:
    """
    Configurable detailing limits.

    Any value may remain None until the exact code provision is configured.
    """

    minimum_cover_mm: Optional[float] = None
    maximum_cover_mm: Optional[float] = None

    minimum_spacing_mm: Optional[float] = None
    maximum_spacing_mm: Optional[float] = None

    minimum_clear_spacing_mm: Optional[float] = None

    minimum_bend_diameter_factor: Optional[float] = None

    minimum_hook_extension_factor: Optional[float] = None

    maximum_lap_ratio: Optional[float] = None


@dataclass(frozen=True)
class CoverInput:
    """
    Concrete cover input.
    """

    cover_mm: float
    member_category: MemberCategory
    condition: DetailingCondition = DetailingCondition.GENERAL


@dataclass(frozen=True)
class SpacingInput:
    """
    Reinforcement spacing input.
    """

    spacing_mm: float
    bar_diameter_mm: float
    member_category: MemberCategory
    role: ReinforcementRole = ReinforcementRole.LONGITUDINAL
    region: ReinforcementRegion = ReinforcementRegion.GENERAL


@dataclass(frozen=True)
class BendInput:
    """
    Bend/hook geometry input.

    `bend_diameter_factor` is code-controlled.
    """

    bar_diameter_mm: float
    bend_diameter_factor: float
    hook_type: HookType = HookType.STANDARD

    extension_factor: Optional[float] = None
    minimum_extension_mm: Optional[float] = None


@dataclass(frozen=True)
class AnchorageInput:
    """
    Anchorage/development input.

    The coefficient is supplied by the active code rule.
    """

    bar_diameter_mm: float
    coefficient: float
    member_category: MemberCategory
    role: ReinforcementRole = ReinforcementRole.LONGITUDINAL
    region: ReinforcementRegion = ReinforcementRegion.ANCHORAGE

    concrete_factor: float = 1.0
    steel_factor: float = 1.0
    confinement_factor: float = 1.0

    minimum_length_mm: Optional[float] = None


@dataclass(frozen=True)
class LapInput:
    """
    Lap splice input.
    """

    development_length_mm: float
    coefficient: float
    member_category: MemberCategory
    region: ReinforcementRegion = ReinforcementRegion.LAP
    minimum_length_mm: Optional[float] = None


@dataclass(frozen=True)
class BarPlacement:
    """
    Basic representation of a reinforcement placement.

    This is useful as an intermediate object between calculation and BBS.
    """

    diameter_mm: float
    quantity: int
    spacing_mm: Optional[float]
    cover_mm: float

    role: ReinforcementRole
    region: ReinforcementRegion

    start_offset_mm: float = 0.0
    end_offset_mm: float = 0.0

    hook_type: HookType = HookType.NONE
    splice_type: SpliceType = SpliceType.NONE


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def validate_positive(value: float, name: str) -> float:
    """
    Validate a positive numeric value.
    """

    result = float(value)

    if result <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return result


def validate_non_negative(value: float, name: str) -> float:
    """
    Validate a non-negative numeric value.
    """

    result = float(value)

    if result < 0:
        raise ValueError(f"{name} cannot be negative.")

    return result


# ---------------------------------------------------------------------------
# IRAN DETAILING CLASS
# ---------------------------------------------------------------------------

class IranDetailing(DesignCode):
    """
    Iran-specific reinforcement detailing interface.

    This module does not perform complete structural member design.

    Its purpose is to translate code-controlled detailing rules into
    machine-readable checks and geometry information used by:

        calculation
            ↓
        reinforcement
            ↓
        detailing
            ↓
        BBS
            ↓
        Cut List
            ↓
        quantities / reports
    """

    DEFAULT_CODE_ID = "m9"

    def __init__(
        self,
        code_edition: str = "1399",
        *,
        limits: Optional[
            Dict[MemberCategory, DetailingLimits]
        ] = None,
        reinforcement: Optional[IranReinforcement] = None,
    ) -> None:

        self.code_edition = str(code_edition)

        self.edition = CodeEdition(
            family=CodeFamily.IRAN,
            code_id=self.DEFAULT_CODE_ID,
            edition=self.code_edition,
            title="Iranian Reinforcement Detailing Rules",
            authority="Iranian structural design code framework",
            language="fa",
        )

        self.context = CodeContext(
            edition=self.edition,
            description=(
                "Iran-specific reinforcement detailing, spacing, cover, "
                "anchorage, lap, hook and critical-region interfaces."
            ),
        )

        self.reinforcement = reinforcement or IranReinforcement(
            code_edition=self.code_edition
        )

        self._limits = limits or {}

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
            key=f"{member_category.value}.detailing.material",
            title="Reinforcement Material",
            description=(
                "Reinforcement material must satisfy the active "
                "material and design-code requirements."
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

        mapping = {
            "cover": "concrete_cover",
            "concrete_cover": "concrete_cover",
            "spacing": "bar_spacing",
            "bar_spacing": "bar_spacing",
            "clear_spacing": "clear_spacing",
            "bend": "bend_diameter",
            "bend_diameter": "bend_diameter",
            "hook": "hook_extension",
            "hook_extension": "hook_extension",
            "development": "development_length",
            "development_length": "development_length",
            "anchorage": "anchorage_length",
            "anchorage_length": "anchorage_length",
            "lap": "lap_length",
            "lap_length": "lap_length",
        }

        requirement_key = mapping.get(normalized)

        if requirement_key is None:
            return None

        return CodeRequirement(
            key=f"{member_category.value}.detailing.{requirement_key}",
            title=requirement_key.replace("_", " ").title(),
            description=(
                "Requirement is resolved from the active Iranian code "
                "edition and structural/detailing condition."
            ),
            value_type="numeric",
            unit="mm",
            clause=self._clause(requirement_key),
        )

    def get_detailing_rule(
        self,
        member_category: MemberCategory,
        key: str,
    ) -> Optional[DetailingRule]:

        normalized = str(key).strip().lower()

        descriptions = {
            "cover": "Concrete cover requirement.",
            "spacing": "Reinforcement spacing requirement.",
            "clear_spacing": "Minimum clear spacing between reinforcement bars.",
            "bend": "Minimum bend diameter requirement.",
            "hook": "Hook/extension requirement.",
            "development": "Development/anchorage length requirement.",
            "lap": "Lap splice length requirement.",
            "critical_region": (
                "Additional detailing requirements for a critical region."
            ),
        }

        description = descriptions.get(normalized)

        if description is None:
            return None

        return DetailingRule(
            key=f"{member_category.value}.detailing.{normalized}",
            title=normalized.replace("_", " ").title(),
            description=description,
            clause=self._clause(normalized),
        )

    # ------------------------------------------------------------------
    # LIMITS
    # ------------------------------------------------------------------

    def set_limits(
        self,
        member_category: MemberCategory,
        limits: DetailingLimits,
    ) -> None:
        """
        Configure edition-specific/member-specific detailing limits.
        """

        self._limits[member_category] = limits

    def get_limits(
        self,
        member_category: MemberCategory,
    ) -> Optional[DetailingLimits]:

        return self._limits.get(member_category)

    # ------------------------------------------------------------------
    # COVER
    # ------------------------------------------------------------------

    def check_cover(
        self,
        data: CoverInput,
        *,
        minimum_cover_mm: Optional[float] = None,
        maximum_cover_mm: Optional[float] = None,
    ) -> CodeCheck:
        """
        Check concrete cover.

        The actual minimum/maximum values are supplied by the selected
        code configuration.
        """

        cover = validate_non_negative(
            data.cover_mm,
            "Concrete cover",
        )

        limits = self._limits.get(data.member_category)

        minimum = minimum_cover_mm

        if minimum is None and limits is not None:
            minimum = limits.minimum_cover_mm

        maximum = maximum_cover_mm

        if maximum is None and limits is not None:
            maximum = limits.maximum_cover_mm

        if minimum is not None and cover < minimum:
            return check_minimum(
                value=cover,
                minimum=minimum,
                name="concrete cover",
                unit="mm",
                clause=self._clause("minimum_cover"),
            )

        if maximum is not None and cover > maximum:
            return check_maximum(
                value=cover,
                maximum=maximum,
                name="concrete cover",
                unit="mm",
                clause=self._clause("maximum_cover"),
            )

        return CodeCheck(
            name="concrete cover",
            status=CheckStatus.PASS,
            value=cover,
            limit_min=minimum,
            limit_max=maximum,
            unit="mm",
            clause=self._clause("cover"),
            message="Concrete cover satisfies configured limits.",
        )

    # ------------------------------------------------------------------
    # SPACING
    # ------------------------------------------------------------------

    def check_spacing(
        self,
        data: SpacingInput,
        *,
        minimum_spacing_mm: Optional[float] = None,
        maximum_spacing_mm: Optional[float] = None,
        minimum_clear_spacing_mm: Optional[float] = None,
    ) -> CodeCheck:
        """
        Check reinforcement spacing.

        Both center-to-center and clear-spacing constraints can be
        represented.
        """

        spacing = validate_positive(
            data.spacing_mm,
            "Reinforcement spacing",
        )

        diameter = validate_positive(
            data.bar_diameter_mm,
            "Bar diameter",
        )

        limits = self._limits.get(data.member_category)

        min_spacing = minimum_spacing_mm

        if min_spacing is None and limits is not None:
            min_spacing = limits.minimum_spacing_mm

        max_spacing = maximum_spacing_mm

        if max_spacing is None and limits is not None:
            max_spacing = limits.maximum_spacing_mm

        clear_spacing = spacing - diameter

        minimum_clear = minimum_clear_spacing_mm

        if minimum_clear is None and limits is not None:
            minimum_clear = limits.minimum_clear_spacing_mm

        if min_spacing is not None and spacing < min_spacing:
            return check_minimum(
                value=spacing,
                minimum=min_spacing,
                name="reinforcement spacing",
                unit="mm",
                clause=self._clause("minimum_spacing"),
            )

        if max_spacing is not None and spacing > max_spacing:
            return check_maximum(
                value=spacing,
                maximum=max_spacing,
                name="reinforcement spacing",
                unit="mm",
                clause=self._clause("maximum_spacing"),
            )

        if minimum_clear is not None and clear_spacing < minimum_clear:
            return check_minimum(
                value=clear_spacing,
                minimum=minimum_clear,
                name="clear reinforcement spacing",
                unit="mm",
                clause=self._clause("minimum_clear_spacing"),
            )

        return CodeCheck(
            name="reinforcement spacing",
            status=CheckStatus.PASS,
            value=spacing,
            limit_min=min_spacing,
            limit_max=max_spacing,
            unit="mm",
            clause=self._clause("spacing"),
            message=(
                "Reinforcement spacing and configured clear-spacing "
                "requirements are satisfied."
            ),
        )

    # ------------------------------------------------------------------
    # BEND / HOOK
    # ------------------------------------------------------------------

    @staticmethod
    def bend_diameter(
        bar_diameter_mm: float,
        bend_diameter_factor: float,
    ) -> float:
        """
        Calculate required bend diameter.

        Formula:
            D_bend = factor × d_bar
        """

        d = validate_positive(
            bar_diameter_mm,
            "Bar diameter",
        )

        factor = validate_positive(
            bend_diameter_factor,
            "Bend diameter factor",
        )

        return d * factor

    @staticmethod
    def hook_extension(
        bar_diameter_mm: float,
        *,
        extension_factor: Optional[float] = None,
        minimum_extension_mm: Optional[float] = None,
    ) -> float:
        """
        Calculate hook extension.

        At least one code-controlled value must be supplied.
        """

        d = validate_positive(
            bar_diameter_mm,
            "Bar diameter",
        )

        extension_from_factor: Optional[float] = None

        if extension_factor is not None:
            factor = validate_positive(
                extension_factor,
                "Hook extension factor",
            )
            extension_from_factor = d * factor

        extension_from_minimum = None

        if minimum_extension_mm is not None:
            extension_from_minimum = validate_non_negative(
                minimum_extension_mm,
                "Minimum hook extension",
            )

        if (
            extension_from_factor is None
            and extension_from_minimum is None
        ):
            raise ValueError(
                "A code-controlled hook extension factor or "
                "minimum extension must be provided."
            )

        values = [
            value
            for value in (
                extension_from_factor,
                extension_from_minimum,
            )
            if value is not None
        ]

        return max(values)

    def check_bend(
        self,
        data: BendInput,
        *,
        minimum_bend_diameter_factor: Optional[float] = None,
    ) -> CodeCheck:
        """
        Check bend diameter against the configured/code requirement.
        """

        diameter = validate_positive(
            data.bar_diameter_mm,
            "Bar diameter",
        )

        actual_bend_factor = validate_positive(
            data.bend_diameter_factor,
            "Bend diameter factor",
        )

        limits = self._limits

        # Bend requirement is normally member/condition dependent.
        # No universal factor is assumed here.
        minimum_factor = minimum_bend_diameter_factor

        if minimum_factor is None:
            # Search only when one unambiguous global limit is configured.
            factors = {
                item.minimum_bend_diameter_factor
                for item in limits.values()
                if item.minimum_bend_diameter_factor is not None
            }

            if len(factors) == 1:
                minimum_factor = factors.pop()

        actual_diameter = diameter * actual_bend_factor

        if minimum_factor is not None:
            required_diameter = diameter * minimum_factor

            if actual_bend_factor < minimum_factor:
                return check_minimum(
                    value=actual_diameter,
                    minimum=required_diameter,
                    name="bend diameter",
                    unit="mm",
                    clause=self._clause("minimum_bend_diameter"),
                )

        return CodeCheck(
            name="bend diameter",
            status=CheckStatus.PASS,
            value=actual_diameter,
            limit_min=(
                diameter * minimum_factor
                if minimum_factor is not None
                else None
            ),
            limit_max=None,
            unit="mm",
            clause=self._clause("bend_diameter"),
            message="Bend diameter satisfies configured limits.",
        )

    # ------------------------------------------------------------------
    # DEVELOPMENT / ANCHORAGE
    # ------------------------------------------------------------------

    def development_length(
        self,
        data: AnchorageInput,
    ) -> float:
        """
        Code-aware development/anchorage length.

        No generic 40d assumption is made.
        """

        return self.reinforcement.development_length(
            data=self._to_development_input(data)
        )

    def _to_development_input(
        self,
        data: AnchorageInput,
    ):
        from codes.iran.reinforcement import DevelopmentLengthInput

        return DevelopmentLengthInput(
            diameter_mm=data.bar_diameter_mm,
            coefficient=data.coefficient,
            member_category=data.member_category,
            reinforcement_role=data.role,
            region=data.region,
            concrete_factor=data.concrete_factor,
            steel_factor=data.steel_factor,
            confinement_factor=data.confinement_factor,
            minimum_length_mm=data.minimum_length_mm,
        )

    # ------------------------------------------------------------------
    # LAP
    # ------------------------------------------------------------------

    def lap_length(
        self,
        data: LapInput,
    ) -> float:
        """
        Code-aware lap splice length.
        """

        from codes.iran.reinforcement import LapLengthInput

        return self.reinforcement.lap_length(
            LapLengthInput(
                development_length_mm=data.development_length_mm,
                coefficient=data.coefficient,
                member_category=data.member_category,
                region=data.region,
                minimum_length_mm=data.minimum_length_mm,
            )
        )

    # ------------------------------------------------------------------
    # CRITICAL REGION
    # ------------------------------------------------------------------

    def critical_region_metadata(
        self,
        member_category: MemberCategory,
    ) -> Dict[str, Any]:
        """
        Return machine-readable metadata describing critical-region logic.

        Exact dimensions/spacing limits must be populated from the active
        code edition.
        """

        return {
            "member_category": member_category.value,
            "critical_region_supported": True,
            "region_types": [
                region.value
                for region in ReinforcementRegion
            ],
            "requirements": [
                "spacing",
                "confinement",
                "lap_location",
                "anchorage",
                "bar_termination",
            ],
            "note": (
                "Exact critical-region dimensions and reinforcement "
                "limits are code-edition and member-condition dependent."
            ),
            "clause": self._clause("critical_region"),
        }

    # ------------------------------------------------------------------
    # BAR PLACEMENT
    # ------------------------------------------------------------------

    def validate_bar_placement(
        self,
        placement: BarPlacement,
        member_category: MemberCategory,
    ) -> Dict[str, Any]:
        """
        Validate the basic geometry of a reinforcement placement.

        This does not perform complete member design.
        """

        diameter = validate_positive(
            placement.diameter_mm,
            "Bar diameter",
        )

        if diameter not in STANDARD_DIAMETERS_MM:
            raise ValueError(
                f"Unsupported standard bar diameter: {diameter:g} mm"
            )

        if placement.quantity < 1:
            raise ValueError(
                "Reinforcement quantity must be at least 1."
            )

        cover = validate_non_negative(
            placement.cover_mm,
            "Concrete cover",
        )

        start = validate_non_negative(
            placement.start_offset_mm,
            "Start offset",
        )

        end = validate_non_negative(
            placement.end_offset_mm,
            "End offset",
        )

        if (
            placement.spacing_mm is not None
            and placement.spacing_mm <= 0
        ):
            raise ValueError(
                "Reinforcement spacing must be greater than zero."
            )

        return {
            "valid": True,
            "member_category": member_category.value,
            "diameter_mm": diameter,
            "area_mm2": bar_area_mm2(diameter),
            "perimeter_mm": bar_perimeter_mm(diameter),
            "quantity": placement.quantity,
            "cover_mm": cover,
            "spacing_mm": placement.spacing_mm,
            "role": placement.role.value,
            "region": placement.region.value,
            "start_offset_mm": start,
            "end_offset_mm": end,
            "hook_type": placement.hook_type.value,
            "splice_type": placement.splice_type.value,
        }

    # ------------------------------------------------------------------
    # DETAILING LENGTH HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def straight_bar_length(
        clear_length_mm: float,
        *,
        start_anchorage_mm: float = 0.0,
        end_anchorage_mm: float = 0.0,
        start_hook_extension_mm: float = 0.0,
        end_hook_extension_mm: float = 0.0,
    ) -> float:
        """
        Calculate geometric bar length before shape-specific bend
        deductions/additions.

        This is intentionally a geometry helper, not a final BBS formula.
        """

        clear_length = validate_non_negative(
            clear_length_mm,
            "Clear bar length",
        )

        start_anchorage = validate_non_negative(
            start_anchorage_mm,
            "Start anchorage",
        )

        end_anchorage = validate_non_negative(
            end_anchorage_mm,
            "End anchorage",
        )

        start_hook = validate_non_negative(
            start_hook_extension_mm,
            "Start hook extension",
        )

        end_hook = validate_non_negative(
            end_hook_extension_mm,
            "End hook extension",
        )

        return (
            clear_length
            + start_anchorage
            + end_anchorage
            + start_hook
            + end_hook
        )

    # ------------------------------------------------------------------
    # GENERIC CHECK
    # ------------------------------------------------------------------

    def run_check(
        self,
        *,
        member_category: MemberCategory,
        cover_mm: Optional[float] = None,
        spacing_mm: Optional[float] = None,
        bar_diameter_mm: Optional[float] = None,
    ) -> CodeCheck:
        """
        Run a basic detailing check.

        If more than one value is supplied, cover is checked first,
        followed by spacing.

        Complete member-specific detailing checks are performed by the
        corresponding calculation module.
        """

        if cover_mm is not None:
            return self.check_cover(
                CoverInput(
                    cover_mm=cover_mm,
                    member_category=member_category,
                )
            )

        if spacing_mm is not None:
            if bar_diameter_mm is None:
                raise ValueError(
                    "bar_diameter_mm is required when checking spacing."
                )

            return self.check_spacing(
                SpacingInput(
                    spacing_mm=spacing_mm,
                    bar_diameter_mm=bar_diameter_mm,
                    member_category=member_category,
                )
            )

        return CodeCheck(
            name="detailing",
            status=CheckStatus.PASS,
            value=0.0,
            limit_min=None,
            limit_max=None,
            unit=None,
            clause=self._clause("general"),
            message=(
                "No numeric detailing input was supplied. "
                "No numeric check was performed."
            ),
        )

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
            "supported_conditions": [
                condition.value
                for condition in DetailingCondition
            ],
            "supported_regions": [
                region.value
                for region in ReinforcementRegion
            ],
            "supported_hook_types": [
                hook.value
                for hook in HookType
            ],
            "supported_splice_types": [
                splice.value
                for splice in SpliceType
            ],
            "notes": [
                (
                    "Exact cover, spacing, bend, hook, anchorage and "
                    "lap requirements must come from the active code edition."
                ),
                (
                    "No universal development-length or lap-length "
                    "coefficient is hard-coded."
                ),
                (
                    "Critical-region detailing is explicitly represented "
                    "so it can affect BBS and Cut List generation."
                ),
            ],
        }

    # ------------------------------------------------------------------
    # INTERNAL
    # ------------------------------------------------------------------

    def _clause(self, key: str) -> str:
        """
        Stable internal code-reference identifier.

        These are not presented as official clause numbers until the exact
        code edition and official source have been verified.
        """

        normalized = str(key).strip().lower()

        return (
            f"{self.code_id}/"
            f"{self.code_edition}/"
            f"detailing/{normalized}"
        )


# ---------------------------------------------------------------------------
# FACTORY
# ---------------------------------------------------------------------------

def create_iran_detailing_code(
    code_edition: str = "1399",
    *,
    limits: Optional[
        Dict[MemberCategory, DetailingLimits]
    ] = None,
) -> IranDetailing:
    """
    Create an Iran detailing code instance.
    """

    return IranDetailing(
        code_edition=code_edition,
        limits=limits,
    )


# ---------------------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# ---------------------------------------------------------------------------

def calculate_bend_diameter(
    bar_diameter_mm: float,
    bend_diameter_factor: float,
) -> float:
    """
    Convenience wrapper for bend diameter.
    """

    return IranDetailing.bend_diameter(
        bar_diameter_mm,
        bend_diameter_factor,
    )


def calculate_hook_extension(
    bar_diameter_mm: float,
    *,
    extension_factor: Optional[float] = None,
    minimum_extension_mm: Optional[float] = None,
) -> float:
    """
    Convenience wrapper for hook extension.
    """

    return IranDetailing.hook_extension(
        bar_diameter_mm,
        extension_factor=extension_factor,
        minimum_extension_mm=minimum_extension_mm,
    )


def calculate_straight_bar_length(
    clear_length_mm: float,
    *,
    start_anchorage_mm: float = 0.0,
    end_anchorage_mm: float = 0.0,
    start_hook_extension_mm: float = 0.0,
    end_hook_extension_mm: float = 0.0,
) -> float:
    """
    Convenience wrapper for geometric straight-bar length.
    """

    return IranDetailing.straight_bar_length(
        clear_length_mm,
        start_anchorage_mm=start_anchorage_mm,
        end_anchorage_mm=end_anchorage_mm,
        start_hook_extension_mm=start_hook_extension_mm,
        end_hook_extension_mm=end_hook_extension_mm,
    )


# ---------------------------------------------------------------------------
# EXPORTS
# ---------------------------------------------------------------------------

__all__ = [
    "DetailingCondition",
    "HookType",
    "SpliceType",
    "DetailingLimits",
    "CoverInput",
    "SpacingInput",
    "BendInput",
    "AnchorageInput",
    "LapInput",
    "BarPlacement",
    "IranDetailing",
    "create_iran_detailing_code",
    "calculate_bend_diameter",
    "calculate_hook_extension",
    "calculate_straight_bar_length",
]
