"""
StructuralBot - Iran Concrete Code Rules

Concrete-specific rules and helper functions for the Iranian
structural design workflow.

IMPORTANT:
- This module does not perform full structural analysis.
- It does not calculate seismic loads or load combinations.
- It provides code-oriented concrete properties, limits,
  checks, and helper functions for the calculation engine.
- Exact values must be tied to the selected code edition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from codes.base import (
    CheckStatus,
    CodeCheck,
    CodeContext,
    CodeEdition,
    CodeFamily,
    CodeRequirement,
    DesignCode,
    DetailingRule,
    MaterialCategory,
    MaterialRequirement,
    MemberCategory,
)

from codes.iran.materials import (
    ConcreteMaterial,
    IranMaterials,
    ReinforcementMaterial,
)


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass(frozen=True)
class ConcreteLimits:
    """
    General concrete limits used by the selected code edition.

    Values are intentionally stored separately from calculation
    logic so that future code editions can be added cleanly.
    """

    minimum_fc: float = 20.0
    maximum_fc: float = 50.0

    minimum_cover: float = 20.0

    density: float = 2400.0

    code_edition: str = ""


@dataclass(frozen=True)
class ConcreteSectionProperties:
    """
    Basic derived properties of a concrete section.
    """

    width: float
    height: float
    area: float
    volume_per_meter: float

    unit_area: str = "mm2"
    unit_volume: str = "m3/m"


# ============================================================
# CONCRETE CODE IMPLEMENTATION
# ============================================================

class IranConcrete(DesignCode):
    """
    Iranian concrete design-code interface.

    This class provides the concrete-related interface used by
    the calculation engine.

    It intentionally does not contain full member design
    algorithms. Beam, column, foundation and slab calculations
    remain separate calculation modules.
    """

    DEFAULT_CODE_ID = "m9"

    def __init__(
        self,
        code_edition: str = "",
    ) -> None:
        self._edition = CodeEdition(
            family=CodeFamily.IRAN,
            code_id=self.DEFAULT_CODE_ID,
            edition=code_edition,
            title="Iranian Concrete Design Rules",
            description=(
                "Concrete design and detailing rules "
                "for the selected Iranian code edition."
            ),
        )

        self.materials = IranMaterials(
            code_edition=code_edition
        )

        self.limits = ConcreteLimits(
            code_edition=code_edition
        )

    # --------------------------------------------------------
    # DESIGN CODE INTERFACE
    # --------------------------------------------------------

    @property
    def family(self) -> CodeFamily:
        return CodeFamily.IRAN

    @property
    def edition(self) -> CodeEdition:
        return self._edition

    def supported_members(self):
        return (
            MemberCategory.FOUNDATION,
            MemberCategory.COLUMN,
            MemberCategory.BEAM,
            MemberCategory.SLAB,
            MemberCategory.WALL,
            MemberCategory.STAIR,
        )

    # --------------------------------------------------------
    # MATERIAL REQUIREMENTS
    # --------------------------------------------------------

    def get_material_requirement(
        self,
        material: MaterialCategory,
        property_name: str,
        context: Optional[CodeContext] = None,
    ) -> Optional[MaterialRequirement]:
        """
        Return concrete-related material requirements.
        """

        if material != MaterialCategory.CONCRETE:
            return None

        normalized = (
            property_name
            .strip()
            .lower()
        )

        if normalized in {
            "fc_min",
            "minimum_fc",
            "min_fc",
        }:
            return MaterialRequirement(
                material=MaterialCategory.CONCRETE,
                property_name="fc",
                value=self.limits.minimum_fc,
                unit="MPa",
                minimum=self.limits.minimum_fc,
                clause=self._clause(
                    "minimum concrete strength"
                ),
                description=(
                    "Minimum concrete compressive strength "
                    "for the selected code configuration."
                ),
            )

        if normalized in {
            "fc_max",
            "maximum_fc",
            "max_fc",
        }:
            return MaterialRequirement(
                material=MaterialCategory.CONCRETE,
                property_name="fc",
                value=self.limits.maximum_fc,
                unit="MPa",
                maximum=self.limits.maximum_fc,
                clause=self._clause(
                    "maximum concrete strength"
                ),
                description=(
                    "Maximum concrete strength supported by "
                    "this module configuration."
                ),
            )

        if normalized in {
            "density",
            "concrete_density",
        }:
            return MaterialRequirement(
                material=MaterialCategory.CONCRETE,
                property_name="density",
                value=self.limits.density,
                unit="kg/m3",
                clause=self._clause(
                    "concrete density"
                ),
                description="Nominal concrete density.",
            )

        return None

    # --------------------------------------------------------
    # GENERAL REQUIREMENTS
    # --------------------------------------------------------

    def get_requirement(
        self,
        name: str,
        context: Optional[CodeContext] = None,
    ) -> Optional[CodeRequirement]:
        """
        Return a general concrete requirement.
        """

        normalized = (
            name
            .strip()
            .lower()
        )

        if normalized in {
            "minimum_fc",
            "fc_min",
            "minimum_concrete_strength",
        }:
            return CodeRequirement(
                name="minimum_concrete_strength",
                value=self.limits.minimum_fc,
                unit="MPa",
                minimum=self.limits.minimum_fc,
                clause=self._clause(
                    "minimum concrete strength"
                ),
                description=(
                    "Minimum concrete compressive strength."
                ),
            )

        if normalized in {
            "maximum_fc",
            "fc_max",
            "maximum_concrete_strength",
        }:
            return CodeRequirement(
                name="maximum_concrete_strength",
                value=self.limits.maximum_fc,
                unit="MPa",
                maximum=self.limits.maximum_fc,
                clause=self._clause(
                    "maximum concrete strength"
                ),
                description=(
                    "Maximum concrete strength supported "
                    "by this module."
                ),
            )

        if normalized in {
            "minimum_cover",
            "min_cover",
        }:
            return CodeRequirement(
                name="minimum_cover",
                value=self.limits.minimum_cover,
                unit="mm",
                minimum=self.limits.minimum_cover,
                clause=self._clause(
                    "minimum concrete cover"
                ),
                description=(
                    "Baseline minimum cover. "
                    "Final cover must consider member type, "
                    "exposure and applicable code provisions."
                ),
            )

        return None

    # --------------------------------------------------------
    # DETAILING
    # --------------------------------------------------------

    def get_detailing_rule(
        self,
        name: str,
        member_category: MemberCategory,
        context: Optional[CodeContext] = None,
    ) -> Optional[DetailingRule]:
        """
        Return basic concrete detailing rules.

        Member-specific detailed rules should be implemented in
        reinforcement.py and detailing.py.
        """

        normalized = (
            name
            .strip()
            .lower()
        )

        if normalized in {
            "minimum_cover",
            "cover",
        }:
            return DetailingRule(
                name="minimum_cover",
                member_category=member_category,
                value=self.limits.minimum_cover,
                unit="mm",
                clause=self._clause(
                    "minimum concrete cover"
                ),
                description=(
                    "Baseline minimum concrete cover."
                ),
            )

        return None

    # --------------------------------------------------------
    # MATERIAL VALIDATION
    # --------------------------------------------------------

    def validate_concrete(
        self,
        concrete: ConcreteMaterial,
    ) -> List[str]:
        """
        Validate concrete against configured limits.
        """

        errors: List[str] = []

        if concrete.fc < self.limits.minimum_fc:
            errors.append(
                f"Concrete strength fc={concrete.fc:g} MPa "
                f"is below the configured minimum "
                f"{self.limits.minimum_fc:g} MPa."
            )

        if concrete.fc > self.limits.maximum_fc:
            errors.append(
                f"Concrete strength fc={concrete.fc:g} MPa "
                f"exceeds the configured maximum "
                f"{self.limits.maximum_fc:g} MPa."
            )

        if concrete.density <= 0:
            errors.append(
                "Concrete density must be positive."
            )

        return errors

    def validate_reinforcement_material(
        self,
        reinforcement: ReinforcementMaterial,
    ) -> List[str]:
        """
        Validate reinforcement material at the generic concrete
        module level.

        Detailed reinforcement-grade rules belong to
        reinforcement.py.
        """

        errors: List[str] = []

        if reinforcement.fy <= 0:
            errors.append(
                "Reinforcement fy must be positive."
            )

        if reinforcement.fu < reinforcement.fy:
            errors.append(
                "Reinforcement fu cannot be lower than fy."
            )

        return errors

    # --------------------------------------------------------
    # SECTION PROPERTIES
    # --------------------------------------------------------

    @staticmethod
    def rectangular_section(
        width: float,
        height: float,
    ) -> ConcreteSectionProperties:
        """
        Calculate basic properties of a rectangular concrete
        section.

        Inputs:
            width  = mm
            height = mm

        Outputs:
            area = mm2
            volume_per_meter = m3/m
        """

        if width <= 0:
            raise ValueError(
                "Section width must be greater than zero."
            )

        if height <= 0:
            raise ValueError(
                "Section height must be greater than zero."
            )

        area = width * height

        volume_per_meter = (
            width
            * height
            / 1_000_000
        )

        return ConcreteSectionProperties(
            width=float(width),
            height=float(height),
            area=float(area),
            volume_per_meter=float(
                volume_per_meter
            ),
        )

    # --------------------------------------------------------
    # CONCRETE VOLUME
    # --------------------------------------------------------

    @staticmethod
    def rectangular_volume(
        width: float,
        height: float,
        length: float,
    ) -> float:
        """
        Calculate rectangular concrete volume.

        Inputs:
            width  = mm
            height = mm
            length = m

        Output:
            m3
        """

        if width <= 0:
            raise ValueError(
                "Width must be greater than zero."
            )

        if height <= 0:
            raise ValueError(
                "Height must be greater than zero."
            )

        if length <= 0:
            raise ValueError(
                "Length must be greater than zero."
            )

        return (
            width
            * height
            * length
            / 1_000_000
        )

    # --------------------------------------------------------
    # CIRCULAR VOLUME
    # --------------------------------------------------------

    @staticmethod
    def circular_volume(
        diameter: float,
        length: float,
    ) -> float:
        """
        Calculate cylindrical concrete volume.

        Inputs:
            diameter = mm
            length   = m

        Output:
            m3
        """

        import math

        if diameter <= 0:
            raise ValueError(
                "Diameter must be greater than zero."
            )

        if length <= 0:
            raise ValueError(
                "Length must be greater than zero."
            )

        area_mm2 = (
            math.pi
            * diameter**2
            / 4.0
        )

        return (
            area_mm2
            * length
            / 1_000_000
        )

    # --------------------------------------------------------
    # CHECKS
    # --------------------------------------------------------

    def run_check(
        self,
        check_name: str,
        inputs: Dict[str, Any],
        context: Optional[CodeContext] = None,
    ) -> CodeCheck:
        """
        Run a generic concrete check.
        """

        normalized = (
            check_name
            .strip()
            .lower()
        )

        if normalized in {
            "concrete_strength",
            "fc",
            "minimum_fc",
        }:
            fc = inputs.get("fc")

            if fc is None:
                return CodeCheck(
                    name=check_name,
                    status=CheckStatus.WARNING,
                    message=(
                        "Concrete strength fc was not supplied."
                    ),
                )

            try:
                fc = float(fc)
            except (
                TypeError,
                ValueError,
            ):
                return CodeCheck(
                    name=check_name,
                    status=CheckStatus.FAIL,
                    message=(
                        "Concrete strength fc must be numeric."
                    ),
                )

            if fc >= self.limits.minimum_fc:
                return CodeCheck(
                    name=check_name,
                    status=CheckStatus.PASS,
                    value=fc,
                    limit=self.limits.minimum_fc,
                    unit="MPa",
                    clause=self._clause(
                        "minimum concrete strength"
                    ),
                    message=(
                        f"fc={fc:g} MPa satisfies the "
                        f"configured minimum."
                    ),
                )

            return CodeCheck(
                name=check_name,
                status=CheckStatus.FAIL,
                value=fc,
                limit=self.limits.minimum_fc,
                unit="MPa",
                clause=self._clause(
                    "minimum concrete strength"
                ),
                message=(
                    f"fc={fc:g} MPa is below the "
                    f"configured minimum."
                ),
            )

        return super().run_check(
            check_name,
            inputs,
            context,
        )

    # --------------------------------------------------------
    # CLAUSE HANDLING
    # --------------------------------------------------------

    def _clause(
        self,
        key: str,
    ) -> str:
        """
        Return a clause reference placeholder.

        Exact clause references should be populated only after
        the selected official code edition has been verified.

        This prevents the software from inventing or silently
        assigning incorrect clause numbers.
        """

        if self.edition.edition:
            return (
                f"{self.edition.code_id}"
                f"/{self.edition.edition}"
                f"/{key}"
            )

        return (
            f"{self.edition.code_id}"
            f"/{key}"
        )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    def metadata(self) -> Dict[str, Any]:
        """
        Return module metadata.
        """

        data = super().metadata()

        data.update(
            {
                "module": "iran.concrete",
                "material_family": "concrete",
                "minimum_fc": self.limits.minimum_fc,
                "maximum_fc": self.limits.maximum_fc,
                "minimum_cover": self.limits.minimum_cover,
            }
        )

        return data


# ============================================================
# FACTORY
# ============================================================

def create_iran_concrete_code(
    code_edition: str = "",
) -> IranConcrete:
    """
    Factory for IranConcrete.
    """

    return IranConcrete(
        code_edition=code_edition
    )


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def concrete_strength_check(
    fc: float,
    *,
    code_edition: str = "",
) -> CodeCheck:
    """
    Check concrete compressive strength against the configured
    minimum.
    """

    code = IranConcrete(
        code_edition=code_edition
    )

    return code.run_check(
        "concrete_strength",
        {
            "fc": fc,
        },
    )


def rectangular_concrete_volume(
    width_mm: float,
    height_mm: float,
    length_m: float,
) -> float:
    """
    Convenience function for rectangular concrete volume.
    """

    return IranConcrete.rectangular_volume(
        width=width_mm,
        height=height_mm,
        length=length_m,
    )


def circular_concrete_volume(
    diameter_mm: float,
    length_m: float,
) -> float:
    """
    Convenience function for circular concrete volume.
    """

    return IranConcrete.circular_volume(
        diameter=diameter_mm,
        length=length_m,
    )


# ============================================================
# MODULE EXPORTS
# ============================================================

__all__ = [
    "ConcreteLimits",
    "ConcreteSectionProperties",
    "IranConcrete",
    "create_iran_concrete_code",
    "concrete_strength_check",
    "rectangular_concrete_volume",
    "circular_concrete_volume",
]
