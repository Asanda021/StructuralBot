"""
StructuralBot input validation.

This module validates engineering inputs before they reach
the calculation engine.

Responsibilities:
- Numeric validation
- Positive-value validation
- Range validation
- Integer validation
- Diameter validation
- Geometry validation
- Required-field validation
- Generic dictionary validation

This module must remain independent from:
- Telegram
- Database
- UI
- PDF / Excel
- Specific design-code implementations
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence


# ============================================================
# VALIDATION RESULT
# ============================================================


@dataclass
class ValidationResult:
    """
    Standard result returned by validation functions.
    """

    valid: bool

    errors: List[str]

    warnings: List[str]

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


# ============================================================
# BASIC HELPERS
# ============================================================


def is_number(value: Any) -> bool:
    """
    Return True when value is a finite real number.

    Boolean values are intentionally rejected because
    bool is a subclass of int in Python.
    """

    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    return math.isfinite(float(value))


def is_integer(value: Any) -> bool:
    """
    Check whether a value represents an integer.
    """

    if isinstance(value, bool):
        return False

    if isinstance(value, int):
        return True

    if isinstance(value, float):
        return math.isfinite(value) and value.is_integer()

    return False


def validate_number(
    value: Any,
    field_name: str,
    *,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    allow_zero: bool = True,
) -> ValidationResult:
    """
    Validate a numeric value and optional range.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    if not is_number(value):
        result.add_error(
            f"{field_name} must be a valid numeric value."
        )
        return result

    numeric_value = float(value)

    if not allow_zero and numeric_value == 0:
        result.add_error(
            f"{field_name} must not be zero."
        )
        return result

    if minimum is not None and numeric_value < minimum:
        result.add_error(
            f"{field_name} must be greater than or equal to "
            f"{minimum}."
        )

    if maximum is not None and numeric_value > maximum:
        result.add_error(
            f"{field_name} must be less than or equal to "
            f"{maximum}."
        )

    return result


def validate_positive(
    value: Any,
    field_name: str,
) -> ValidationResult:
    """
    Validate a strictly positive number.
    """

    return validate_number(
        value,
        field_name,
        minimum=0.0,
        allow_zero=False,
    )


def validate_non_negative(
    value: Any,
    field_name: str,
) -> ValidationResult:
    """
    Validate a number greater than or equal to zero.
    """

    return validate_number(
        value,
        field_name,
        minimum=0.0,
        allow_zero=True,
    )


def validate_integer(
    value: Any,
    field_name: str,
    *,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> ValidationResult:
    """
    Validate an integer value and optional range.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    if not is_integer(value):
        result.add_error(
            f"{field_name} must be an integer."
        )
        return result

    integer_value = int(value)

    if minimum is not None and integer_value < minimum:
        result.add_error(
            f"{field_name} must be greater than or equal to "
            f"{minimum}."
        )

    if maximum is not None and integer_value > maximum:
        result.add_error(
            f"{field_name} must be less than or equal to "
            f"{maximum}."
        )

    return result


# ============================================================
# STRING VALIDATION
# ============================================================


def validate_required_string(
    value: Any,
    field_name: str,
) -> ValidationResult:
    """
    Validate a required non-empty string.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    if value is None:
        result.add_error(
            f"{field_name} is required."
        )
        return result

    if not isinstance(value, str):
        result.add_error(
            f"{field_name} must be text."
        )
        return result

    if not value.strip():
        result.add_error(
            f"{field_name} cannot be empty."
        )

    return result


# ============================================================
# REQUIRED FIELDS
# ============================================================


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: Iterable[str],
) -> ValidationResult:
    """
    Validate that all required fields exist and are not empty.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    for field_name in required_fields:
        if field_name not in data:
            result.add_error(
                f"Missing required field: {field_name}"
            )
            continue

        value = data[field_name]

        if value is None:
            result.add_error(
                f"Required field is empty: {field_name}"
            )
            continue

        if isinstance(value, str) and not value.strip():
            result.add_error(
                f"Required field is empty: {field_name}"
            )

    return result


# ============================================================
# REBAR VALIDATION
# ============================================================


STANDARD_REBAR_DIAMETERS_MM: Sequence[float] = (
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
    45,
    50,
)


def validate_rebar_diameter(
    diameter: Any,
    *,
    allow_non_standard: bool = False,
) -> ValidationResult:
    """
    Validate reinforcing bar diameter.

    Diameter is expected in millimetres.

    Non-standard diameters may be allowed when the selected
    standard/code permits them.
    """

    result = validate_positive(
        diameter,
        "Rebar diameter",
    )

    if not result.valid:
        return result

    diameter_value = float(diameter)

    if diameter_value > 100:
        result.add_error(
            "Rebar diameter is outside the supported range."
        )
        return result

    if not allow_non_standard:
        if diameter_value not in STANDARD_REBAR_DIAMETERS_MM:
            result.add_warning(
                "The selected diameter is not in the standard "
                "rebar diameter list."
            )

    return result


def validate_rebar_quantity(
    quantity: Any,
) -> ValidationResult:
    """
    Validate reinforcement bar count.
    """

    return validate_integer(
        quantity,
        "Rebar quantity",
        minimum=1,
    )


def validate_rebar_length(
    length: Any,
    *,
    maximum: Optional[float] = None,
) -> ValidationResult:
    """
    Validate actual cut-piece length.

    The default upper limit is intentionally conservative.
    A specific Cut List / stock-bar module may impose a
    stricter limit such as the actual stock length.
    """

    if maximum is None:
        maximum = 12.0

    return validate_number(
        length,
        "Rebar length",
        minimum=0.001,
        maximum=maximum,
        allow_zero=False,
    )


# ============================================================
# CONCRETE VALIDATION
# ============================================================


def validate_concrete_strength(
    fck: Any,
) -> ValidationResult:
    """
    Validate characteristic concrete compressive strength.

    Unit:
        MPa
    """

    return validate_number(
        fck,
        "Concrete compressive strength",
        minimum=1.0,
        maximum=150.0,
        allow_zero=False,
    )


def validate_steel_strength(
    fy: Any,
) -> ValidationResult:
    """
    Validate reinforcing steel yield strength.

    Unit:
        MPa
    """

    return validate_number(
        fy,
        "Steel yield strength",
        minimum=1.0,
        maximum=2000.0,
        allow_zero=False,
    )


# ============================================================
# GEOMETRY VALIDATION
# ============================================================


def validate_rectangular_geometry(
    width: Any,
    height: Any,
    *,
    field_prefix: str = "Section",
) -> ValidationResult:
    """
    Validate rectangular member dimensions.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    width_result = validate_positive(
        width,
        f"{field_prefix} width",
    )

    height_result = validate_positive(
        height,
        f"{field_prefix} height",
    )

    result.errors.extend(width_result.errors)
    result.errors.extend(height_result.errors)

    result.warnings.extend(width_result.warnings)
    result.warnings.extend(height_result.warnings)

    if result.errors:
        result.valid = False

    return result


def validate_circular_geometry(
    diameter: Any,
    *,
    field_name: str = "Section diameter",
) -> ValidationResult:
    """
    Validate circular member diameter.
    """

    return validate_positive(
        diameter,
        field_name,
    )


def validate_slab_geometry(
    length: Any,
    width: Any,
    thickness: Any,
) -> ValidationResult:
    """
    Validate basic slab geometry.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    values = (
        ("Slab length", length),
        ("Slab width", width),
        ("Slab thickness", thickness),
    )

    for field_name, value in values:
        field_result = validate_positive(
            value,
            field_name,
        )

        result.errors.extend(
            field_result.errors
        )

        result.warnings.extend(
            field_result.warnings
        )

    if result.errors:
        result.valid = False

    return result


# ============================================================
# COVER VALIDATION
# ============================================================


def validate_cover(
    cover: Any,
    *,
    minimum: float = 0.0,
    maximum: float = 500.0,
) -> ValidationResult:
    """
    Validate nominal concrete cover.

    The actual minimum required cover must come from
    the selected design code and exposure conditions.
    """

    return validate_number(
        cover,
        "Concrete cover",
        minimum=minimum,
        maximum=maximum,
        allow_zero=True,
    )


# ============================================================
# SPACING VALIDATION
# ============================================================


def validate_spacing(
    spacing: Any,
    *,
    minimum: float = 0.001,
    maximum: float = 5000.0,
) -> ValidationResult:
    """
    Validate reinforcement spacing.
    """

    return validate_number(
        spacing,
        "Reinforcement spacing",
        minimum=minimum,
        maximum=maximum,
        allow_zero=False,
    )


# ============================================================
# PROJECT VALIDATION
# ============================================================


def validate_project_data(
    project_data: Dict[str, Any],
) -> ValidationResult:
    """
    Validate basic project-level data.

    Engineering-specific rules are intentionally not handled
    here. Those belong to the selected design-code module.
    """

    result = validate_required_fields(
        project_data,
        (
            "name",
            "structure_type",
            "design_code",
            "unit_system",
        ),
    )

    if "name" in project_data:
        name_result = validate_required_string(
            project_data["name"],
            "Project name",
        )

        result.errors.extend(
            name_result.errors
        )

    if result.errors:
        result.valid = False

    return result


# ============================================================
# MEMBER INPUT VALIDATION
# ============================================================


def validate_member_data(
    member_data: Dict[str, Any],
) -> ValidationResult:
    """
    Generic validation for a structural member.

    Specific member modules should perform additional
    engineering validation.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    required_fields = (
        "member_type",
        "name",
    )

    required_result = validate_required_fields(
        member_data,
        required_fields,
    )

    result.errors.extend(
        required_result.errors
    )

    result.warnings.extend(
        required_result.warnings
    )

    if "name" in member_data:
        name_result = validate_required_string(
            member_data["name"],
            "Member name",
        )

        result.errors.extend(
            name_result.errors
        )

    if result.errors:
        result.valid = False

    return result


# ============================================================
# COLUMN VALIDATION
# ============================================================


def validate_column_inputs(
    inputs: Dict[str, Any],
) -> ValidationResult:
    """
    Validate common reinforced-concrete column inputs.

    This function validates input integrity only.

    Code-specific requirements such as:
    - minimum reinforcement ratio
    - maximum reinforcement ratio
    - slenderness
    - interaction diagrams
    - confinement
    - critical-zone detailing

    belong to the selected design-code module.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    if "width" in inputs:
        result.errors.extend(
            validate_positive(
                inputs["width"],
                "Column width",
            ).errors
        )

    if "depth" in inputs:
        result.errors.extend(
            validate_positive(
                inputs["depth"],
                "Column depth",
            ).errors
        )

    if "diameter" in inputs:
        result.errors.extend(
            validate_positive(
                inputs["diameter"],
                "Column diameter",
            ).errors
        )

    if "height" in inputs:
        result.errors.extend(
            validate_positive(
                inputs["height"],
                "Column height",
            ).errors
        )

    if "cover" in inputs:
        result.errors.extend(
            validate_cover(
                inputs["cover"],
            ).errors
        )

    if "rebar_diameter" in inputs:
        result.errors.extend(
            validate_rebar_diameter(
                inputs["rebar_diameter"],
                allow_non_standard=True,
            ).errors
        )

    if "rebar_count" in inputs:
        result.errors.extend(
            validate_rebar_quantity(
                inputs["rebar_count"],
            ).errors
        )

    if result.errors:
        result.valid = False

    return result


# ============================================================
# BEAM VALIDATION
# ============================================================


def validate_beam_inputs(
    inputs: Dict[str, Any],
) -> ValidationResult:
    """
    Validate common reinforced-concrete beam inputs.

    Code-specific design checks are handled elsewhere.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    fields = (
        ("width", "Beam width"),
        ("depth", "Beam depth"),
        ("span", "Beam span"),
    )

    for key, label in fields:
        if key in inputs:
            field_result = validate_positive(
                inputs[key],
                label,
            )

            result.errors.extend(
                field_result.errors
            )

    if "cover" in inputs:
        result.errors.extend(
            validate_cover(
                inputs["cover"],
            ).errors
        )

    if "rebar_diameter" in inputs:
        result.errors.extend(
            validate_rebar_diameter(
                inputs["rebar_diameter"],
                allow_non_standard=True,
            ).errors
        )

    if result.errors:
        result.valid = False

    return result


# ============================================================
# FOUNDATION VALIDATION
# ============================================================


def validate_foundation_inputs(
    inputs: Dict[str, Any],
) -> ValidationResult:
    """
    Validate common foundation inputs.

    Foundation bearing, punching, one-way shear and
    reinforcement rules belong to the design-code layer.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    fields = (
        ("length", "Foundation length"),
        ("width", "Foundation width"),
        ("thickness", "Foundation thickness"),
    )

    for key, label in fields:
        if key in inputs:
            field_result = validate_positive(
                inputs[key],
                label,
            )

            result.errors.extend(
                field_result.errors
            )

    if "cover" in inputs:
        result.errors.extend(
            validate_cover(
                inputs["cover"],
            ).errors
        )

    if "rebar_diameter" in inputs:
        result.errors.extend(
            validate_rebar_diameter(
                inputs["rebar_diameter"],
                allow_non_standard=True,
            ).errors
        )

    if result.errors:
        result.valid = False

    return result


# ============================================================
# SLAB VALIDATION
# ============================================================


def validate_slab_inputs(
    inputs: Dict[str, Any],
) -> ValidationResult:
    """
    Validate common slab inputs.

    Individual slab-system rules are implemented in the
    relevant slab calculation modules.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    fields = (
        ("length", "Slab length"),
        ("width", "Slab width"),
        ("thickness", "Slab thickness"),
    )

    for key, label in fields:
        if key in inputs:
            field_result = validate_positive(
                inputs[key],
                label,
            )

            result.errors.extend(
                field_result.errors
            )

    if "cover" in inputs:
        result.errors.extend(
            validate_cover(
                inputs["cover"],
            ).errors
        )

    if "rebar_diameter" in inputs:
        result.errors.extend(
            validate_rebar_diameter(
                inputs["rebar_diameter"],
                allow_non_standard=True,
            ).errors
        )

    if result.errors:
        result.valid = False

    return result


# ============================================================
# EQUIVALENCY VALIDATION
# ============================================================


def validate_rebar_equivalency_inputs(
    current_diameter: Any,
    current_quantity: Any,
    replacement_diameter: Any,
) -> ValidationResult:
    """
    Validate inputs for the standalone rebar equivalency tool.

    The actual replacement quantity is NOT calculated here.

    It belongs to the engineering/code calculation layer.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    current_diameter_result = validate_rebar_diameter(
        current_diameter,
        allow_non_standard=True,
    )

    quantity_result = validate_rebar_quantity(
        current_quantity,
    )

    replacement_diameter_result = validate_rebar_diameter(
        replacement_diameter,
        allow_non_standard=True,
    )

    result.errors.extend(
        current_diameter_result.errors
    )

    result.errors.extend(
        quantity_result.errors
    )

    result.errors.extend(
        replacement_diameter_result.errors
    )

    result.warnings.extend(
        current_diameter_result.warnings
    )

    result.warnings.extend(
        replacement_diameter_result.warnings
    )

    if result.errors:
        result.valid = False

    return result


# ============================================================
# CUT LIST VALIDATION
# ============================================================


def validate_cut_piece(
    diameter: Any,
    length: Any,
    quantity: Any,
    *,
    stock_length: float = 12.0,
) -> ValidationResult:
    """
    Validate an actual reinforcement cut piece.

    A single physical piece must never exceed the selected
    stock-bar length.
    """

    result = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    diameter_result = validate_rebar_diameter(
        diameter,
        allow_non_standard=True,
    )

    quantity_result = validate_rebar_quantity(
        quantity,
    )

    length_result = validate_rebar_length(
        length,
        maximum=stock_length,
    )

    result.errors.extend(
        diameter_result.errors
    )

    result.errors.extend(
        quantity_result.errors
    )

    result.errors.extend(
        length_result.errors
    )

    result.warnings.extend(
        diameter_result.warnings
    )

    if result.errors:
        result.valid = False

    return result


# ============================================================
# VALIDATE MULTIPLE RESULTS
# ============================================================


def merge_validation_results(
    results: Iterable[ValidationResult],
) -> ValidationResult:
    """
    Merge multiple validation results into one result.
    """

    merged = ValidationResult(
        valid=True,
        errors=[],
        warnings=[],
    )

    for result in results:
        merged.errors.extend(
            result.errors
        )

        merged.warnings.extend(
            result.warnings
        )

        if not result.valid:
            merged.valid = False

    return merged


# ============================================================
# ENGINEERING SAFETY CHECK
# ============================================================


def ensure_valid(
    result: ValidationResult,
) -> None:
    """
    Raise ValueError when validation fails.

    Calculation modules can use this before starting
    an engineering calculation.
    """

    if not result.valid:
        message = " | ".join(result.errors)

        raise ValueError(
            message or "Invalid engineering input."
        )
