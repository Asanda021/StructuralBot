"""
StructuralBot - Iran Code Validation

Centralized validation helpers for the Iranian design-code layer.

Important:
    This module validates input consistency and applicability.
    It does not replace engineering judgment or the official requirements
    of the selected code edition.

    Code-specific numerical limits should be provided by the active
    design-code implementation rather than hard-coded in the core layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence


# ---------------------------------------------------------------------------
# EXCEPTIONS
# ---------------------------------------------------------------------------

class IranValidationError(ValueError):
    """Base validation error for Iranian-code inputs."""


class MaterialValidationError(IranValidationError):
    """Raised when material data is invalid."""


class GeometryValidationError(IranValidationError):
    """Raised when geometry data is invalid."""


class ReinforcementValidationError(IranValidationError):
    """Raised when reinforcement data is invalid."""


class DetailingValidationError(IranValidationError):
    """Raised when detailing data is invalid."""


# ---------------------------------------------------------------------------
# GENERIC HELPERS
# ---------------------------------------------------------------------------

def require_positive(
    value: float,
    name: str,
) -> float:
    """Require a strictly positive numeric value."""

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise IranValidationError(
            f"{name} must be numeric."
        ) from exc

    if numeric <= 0:
        raise IranValidationError(
            f"{name} must be greater than zero."
        )

    return numeric


def require_non_negative(
    value: float,
    name: str,
) -> float:
    """Require a non-negative numeric value."""

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise IranValidationError(
            f"{name} must be numeric."
        ) from exc

    if numeric < 0:
        raise IranValidationError(
            f"{name} cannot be negative."
        )

    return numeric


def require_range(
    value: float,
    minimum: float,
    maximum: float,
    name: str,
) -> float:
    """Require a value inside an inclusive range."""

    numeric = float(value)

    if minimum > maximum:
        raise IranValidationError(
            "Minimum value cannot be greater than maximum value."
        )

    if numeric < minimum or numeric > maximum:
        raise IranValidationError(
            f"{name} must be between {minimum} and {maximum}."
        )

    return numeric


def require_one_of(
    value: Any,
    allowed: Iterable[Any],
    name: str,
) -> Any:
    """Require a value to belong to an allowed collection."""

    allowed_values = list(allowed)

    if value not in allowed_values:
        raise IranValidationError(
            f"{name} must be one of: {allowed_values!r}."
        )

    return value


# ---------------------------------------------------------------------------
# MATERIAL VALIDATION
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MaterialValidationResult:
    """Result of material validation."""

    valid: bool
    material_type: str
    warnings: tuple[str, ...] = ()


def validate_concrete_strength(
    fc_mpa: float,
    *,
    minimum_fc: Optional[float] = None,
    maximum_fc: Optional[float] = None,
) -> MaterialValidationResult:
    """
    Validate concrete compressive strength.

    The limits are optional because they must ultimately come from the
    selected code edition/material standard.
    """

    fc = require_positive(
        fc_mpa,
        "Concrete compressive strength",
    )

    warnings: list[str] = []

    if minimum_fc is not None:
        if fc < float(minimum_fc):
            raise MaterialValidationError(
                f"Concrete strength {fc:g} MPa is below "
                f"the configured minimum {float(minimum_fc):g} MPa."
            )

    if maximum_fc is not None:
        if fc > float(maximum_fc):
            raise MaterialValidationError(
                f"Concrete strength {fc:g} MPa exceeds "
                f"the configured maximum {float(maximum_fc):g} MPa."
            )

    return MaterialValidationResult(
        valid=True,
        material_type="concrete",
        warnings=tuple(warnings),
    )


def validate_reinforcement_strength(
    fy_mpa: float,
    *,
    fu_mpa: Optional[float] = None,
) -> MaterialValidationResult:
    """Validate reinforcement yield and optional ultimate strength."""

    fy = require_positive(
        fy_mpa,
        "Reinforcement yield strength",
    )

    warnings: list[str] = []

    if fu_mpa is not None:
        fu = require_positive(
            fu_mpa,
            "Reinforcement ultimate strength",
        )

        if fu < fy:
            raise MaterialValidationError(
                "Reinforcement ultimate strength cannot be "
                "less than yield strength."
            )

    return MaterialValidationResult(
        valid=True,
        material_type="reinforcement",
        warnings=tuple(warnings),
    )


def validate_steel_strength(
    fy_mpa: float,
    *,
    fu_mpa: Optional[float] = None,
) -> MaterialValidationResult:
    """Validate structural-steel yield and optional ultimate strength."""

    fy = require_positive(
        fy_mpa,
        "Structural steel yield strength",
    )

    warnings: list[str] = []

    if fu_mpa is not None:
        fu = require_positive(
            fu_mpa,
            "Structural steel ultimate strength",
        )

        if fu < fy:
            raise MaterialValidationError(
                "Structural steel ultimate strength cannot be "
                "less than yield strength."
            )

    return MaterialValidationResult(
        valid=True,
        material_type="structural_steel",
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# GEOMETRY VALIDATION
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RectangularGeometryInput:
    """Validated rectangular section geometry."""

    width_mm: float
    height_mm: float


@dataclass(frozen=True)
class CircularGeometryInput:
    """Validated circular section geometry."""

    diameter_mm: float


def validate_rectangular_geometry(
    width_mm: float,
    height_mm: float,
) -> RectangularGeometryInput:
    """Validate rectangular section dimensions."""

    width = require_positive(
        width_mm,
        "Width",
    )

    height = require_positive(
        height_mm,
        "Height",
    )

    return RectangularGeometryInput(
        width_mm=width,
        height_mm=height,
    )


def validate_circular_geometry(
    diameter_mm: float,
) -> CircularGeometryInput:
    """Validate circular section diameter."""

    diameter = require_positive(
        diameter_mm,
        "Diameter",
    )

    return CircularGeometryInput(
        diameter_mm=diameter,
    )


def validate_length_m(
    length_m: float,
    name: str = "Length",
) -> float:
    """Validate a length expressed in metres."""

    return require_positive(
        length_m,
        name,
    )


# ---------------------------------------------------------------------------
# COVER VALIDATION
# ---------------------------------------------------------------------------

def validate_cover(
    cover_mm: float,
    *,
    section_dimension_mm: Optional[float] = None,
) -> float:
    """
    Validate concrete cover.

    If section dimension is provided, the cover must leave positive
    internal space.
    """

    cover = require_non_negative(
        cover_mm,
        "Concrete cover",
    )

    if section_dimension_mm is not None:
        dimension = require_positive(
            section_dimension_mm,
            "Section dimension",
        )

        if cover * 2 >= dimension:
            raise DetailingValidationError(
                "Concrete cover leaves no positive internal section "
                "dimension."
            )

    return cover


# ---------------------------------------------------------------------------
# REINFORCEMENT VALIDATION
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


def validate_rebar_diameter(
    diameter_mm: float,
    *,
    allowed_diameters: Optional[Sequence[float]] = None,
) -> float:
    """
    Validate reinforcement diameter.

    The allowed diameter list can be supplied by the active code/material
    system. If omitted, the standard internal diameter set is used.
    """

    diameter = require_positive(
        diameter_mm,
        "Rebar diameter",
    )

    allowed = (
        tuple(float(x) for x in allowed_diameters)
        if allowed_diameters is not None
        else tuple(float(x) for x in STANDARD_DIAMETERS_MM)
    )

    if diameter not in allowed:
        raise ReinforcementValidationError(
            f"Unsupported rebar diameter: {diameter:g} mm. "
            f"Allowed diameters: {list(allowed)}."
        )

    return diameter


def validate_rebar_quantity(
    quantity: int,
) -> int:
    """Validate number of reinforcement bars."""

    if isinstance(quantity, bool):
        raise ReinforcementValidationError(
            "Rebar quantity must be an integer."
        )

    try:
        count = int(quantity)
    except (TypeError, ValueError) as exc:
        raise ReinforcementValidationError(
            "Rebar quantity must be an integer."
        ) from exc

    if count <= 0:
        raise ReinforcementValidationError(
            "Rebar quantity must be greater than zero."
        )

    return count


def validate_rebar_spacing(
    spacing_mm: float,
    *,
    minimum_spacing_mm: Optional[float] = None,
    maximum_spacing_mm: Optional[float] = None,
) -> float:
    """Validate reinforcement spacing."""

    spacing = require_positive(
        spacing_mm,
        "Rebar spacing",
    )

    if minimum_spacing_mm is not None:
        minimum = require_positive(
            minimum_spacing_mm,
            "Minimum spacing",
        )

        if spacing < minimum:
            raise ReinforcementValidationError(
                f"Rebar spacing {spacing:g} mm is below "
                f"the configured minimum {minimum:g} mm."
            )

    if maximum_spacing_mm is not None:
        maximum = require_positive(
            maximum_spacing_mm,
            "Maximum spacing",
        )

        if spacing > maximum:
            raise ReinforcementValidationError(
                f"Rebar spacing {spacing:g} mm exceeds "
                f"the configured maximum {maximum:g} mm."
            )

    return spacing


def validate_rebar_area(
    area_mm2: float,
) -> float:
    """Validate reinforcement area."""

    return require_positive(
        area_mm2,
        "Reinforcement area",
    )


def validate_reinforcement_ratio(
    ratio_percent: float,
    *,
    minimum_percent: Optional[float] = None,
    maximum_percent: Optional[float] = None,
) -> float:
    """
    Validate reinforcement ratio in percent.

    Exact minimum/maximum limits must come from the selected code
    implementation.
    """

    ratio = require_non_negative(
        ratio_percent,
        "Reinforcement ratio",
    )

    if minimum_percent is not None:
        minimum = require_non_negative(
            minimum_percent,
            "Minimum reinforcement ratio",
        )

        if ratio < minimum:
            raise ReinforcementValidationError(
                f"Reinforcement ratio {ratio:g}% is below "
                f"the configured minimum {minimum:g}%."
            )

    if maximum_percent is not None:
        maximum = require_non_negative(
            maximum_percent,
            "Maximum reinforcement ratio",
        )

        if ratio > maximum:
            raise ReinforcementValidationError(
                f"Reinforcement ratio {ratio:g}% exceeds "
                f"the configured maximum {maximum:g}%."
            )

    return ratio


# ---------------------------------------------------------------------------
# DEVELOPMENT / SPLICE VALIDATION
# ---------------------------------------------------------------------------

def validate_development_length(
    length_mm: float,
    *,
    bar_diameter_mm: Optional[float] = None,
) -> float:
    """
    Validate development length.

    No universal multiplier such as 40d is assumed here.
    """

    length = require_positive(
        length_mm,
        "Development length",
    )

    if bar_diameter_mm is not None:
        diameter = require_positive(
            bar_diameter_mm,
            "Bar diameter",
        )

        if length <= diameter:
            raise ReinforcementValidationError(
                "Development length must be greater than bar diameter."
            )

    return length


def validate_lap_length(
    length_mm: float,
    *,
    bar_diameter_mm: Optional[float] = None,
) -> float:
    """
    Validate lap length.

    The actual lap-length calculation must be performed by the active
    design-code/detailing implementation.
    """

    length = require_positive(
        length_mm,
        "Lap length",
    )

    if bar_diameter_mm is not None:
        diameter = require_positive(
            bar_diameter_mm,
            "Bar diameter",
        )

        if length <= diameter:
            raise ReinforcementValidationError(
                "Lap length must be greater than bar diameter."
            )

    return length


# ---------------------------------------------------------------------------
# MEMBER VALIDATION
# ---------------------------------------------------------------------------

def validate_rectangular_member(
    *,
    width_mm: float,
    height_mm: float,
    length_m: float,
    cover_mm: Optional[float] = None,
) -> dict[str, float]:
    """
    Validate a rectangular structural member.
    """

    geometry = validate_rectangular_geometry(
        width_mm,
        height_mm,
    )

    length = validate_length_m(
        length_m,
        "Member length",
    )

    result = {
        "width_mm": geometry.width_mm,
        "height_mm": geometry.height_mm,
        "length_m": length,
    }

    if cover_mm is not None:
        result["cover_mm"] = validate_cover(
            cover_mm,
            section_dimension_mm=min(
                geometry.width_mm,
                geometry.height_mm,
            ),
        )

    return result


def validate_circular_member(
    *,
    diameter_mm: float,
    length_m: float,
    cover_mm: Optional[float] = None,
) -> dict[str, float]:
    """
    Validate a circular structural member.
    """

    geometry = validate_circular_geometry(
        diameter_mm,
    )

    length = validate_length_m(
        length_m,
        "Member length",
    )

    result = {
        "diameter_mm": geometry.diameter_mm,
        "length_m": length,
    }

    if cover_mm is not None:
        result["cover_mm"] = validate_cover(
            cover_mm,
            section_dimension_mm=geometry.diameter_mm,
        )

    return result


# ---------------------------------------------------------------------------
# DESIGN INPUT VALIDATION
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConcreteDesignInput:
    """Validated basic concrete-design inputs."""

    fc_mpa: float
    cover_mm: float


def validate_concrete_design_input(
    *,
    fc_mpa: float,
    cover_mm: float,
    minimum_fc: Optional[float] = None,
    maximum_fc: Optional[float] = None,
) -> ConcreteDesignInput:
    """Validate basic concrete member design inputs."""

    validate_concrete_strength(
        fc_mpa,
        minimum_fc=minimum_fc,
        maximum_fc=maximum_fc,
    )

    cover = validate_cover(
        cover_mm,
    )

    return ConcreteDesignInput(
        fc_mpa=float(fc_mpa),
        cover_mm=cover,
    )


@dataclass(frozen=True)
class ReinforcementDesignInput:
    """Validated basic reinforcement-design inputs."""

    fy_mpa: float
    diameter_mm: float
    quantity: int
    spacing_mm: Optional[float] = None


def validate_reinforcement_design_input(
    *,
    fy_mpa: float,
    diameter_mm: float,
    quantity: int,
    spacing_mm: Optional[float] = None,
    fu_mpa: Optional[float] = None,
    allowed_diameters: Optional[Sequence[float]] = None,
) -> ReinforcementDesignInput:
    """Validate basic reinforcement-design inputs."""

    validate_reinforcement_strength(
        fy_mpa,
        fu_mpa=fu_mpa,
    )

    diameter = validate_rebar_diameter(
        diameter_mm,
        allowed_diameters=allowed_diameters,
    )

    count = validate_rebar_quantity(
        quantity,
    )

    validated_spacing = None

    if spacing_mm is not None:
        validated_spacing = validate_rebar_spacing(
            spacing_mm,
        )

    return ReinforcementDesignInput(
        fy_mpa=float(fy_mpa),
        diameter_mm=diameter,
        quantity=count,
        spacing_mm=validated_spacing,
    )


# ---------------------------------------------------------------------------
# BULK VALIDATION
# ---------------------------------------------------------------------------

def validate_rebar_list(
    rebars: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Validate a collection of reinforcement definitions.

    Expected minimum fields:
        diameter_mm
        quantity

    Optional:
        spacing_mm
        length_mm
    """

    validated: list[dict[str, Any]] = []

    for index, rebar in enumerate(rebars):
        if not isinstance(rebar, dict):
            raise ReinforcementValidationError(
                f"Rebar item #{index + 1} must be a dictionary."
            )

        if "diameter_mm" not in rebar:
            raise ReinforcementValidationError(
                f"Rebar item #{index + 1} is missing diameter_mm."
            )

        if "quantity" not in rebar:
            raise ReinforcementValidationError(
                f"Rebar item #{index + 1} is missing quantity."
            )

        item = dict(rebar)

        item["diameter_mm"] = validate_rebar_diameter(
            item["diameter_mm"]
        )

        item["quantity"] = validate_rebar_quantity(
            item["quantity"]
        )

        if "spacing_mm" in item and item["spacing_mm"] is not None:
            item["spacing_mm"] = validate_rebar_spacing(
                item["spacing_mm"]
            )

        if "length_mm" in item and item["length_mm"] is not None:
            item["length_mm"] = require_positive(
                item["length_mm"],
                "Rebar length",
            )

        validated.append(item)

    return validated


# ---------------------------------------------------------------------------
# PUBLIC EXPORTS
# ---------------------------------------------------------------------------

__all__ = [
    "IranValidationError",
    "MaterialValidationError",
    "GeometryValidationError",
    "ReinforcementValidationError",
    "DetailingValidationError",
    "MaterialValidationResult",
    "RectangularGeometryInput",
    "CircularGeometryInput",
    "require_positive",
    "require_non_negative",
    "require_range",
    "require_one_of",
    "validate_concrete_strength",
    "validate_reinforcement_strength",
    "validate_steel_strength",
    "validate_rectangular_geometry",
    "validate_circular_geometry",
    "validate_length_m",
    "validate_cover",
    "STANDARD_DIAMETERS_MM",
    "validate_rebar_diameter",
    "validate_rebar_quantity",
    "validate_rebar_spacing",
    "validate_rebar_area",
    "validate_reinforcement_ratio",
    "validate_development_length",
    "validate_lap_length",
    "validate_rectangular_member",
    "validate_circular_member",
    "ConcreteDesignInput",
    "validate_concrete_design_input",
    "ReinforcementDesignInput",
    "validate_reinforcement_design_input",
    "validate_rebar_list",
]
