"""
StructuralBot - Core Validation

Central validation layer for StructuralBot.

Responsibilities:
- Validate domain inputs before engineering calculations.
- Keep validation independent from Telegram, AI and billing.
- Provide reusable validation helpers.
- Prevent silent defaults for engineering-critical values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from core.models import (
    BeamType,
    CalculationResult,
    CircularGeometry,
    ColumnType,
    ConcreteMaterial,
    EngineeringContext,
    Floor,
    FoundationType,
    MaterialQuantity,
    MemberType,
    Project,
    RectangularGeometry,
    RebarShape,
    ReinforcementBar,
    SlabGeometry,
    SlabType,
    Splice,
    SpliceType,
    SteelMaterial,
    StructuralMember,
    StructureType,
    UnitSystem,
)


# =====================================================================
# EXCEPTIONS
# =====================================================================

class ValidationError(ValueError):
    """Base validation exception."""


class RequiredFieldError(ValidationError):
    """Raised when a required field is missing."""


class NumericValidationError(ValidationError):
    """Raised when a numeric value is invalid."""


class GeometryValidationError(ValidationError):
    """Raised when geometry is invalid."""


class MaterialValidationError(ValidationError):
    """Raised when material data is invalid."""


class ReinforcementValidationError(ValidationError):
    """Raised when reinforcement data is invalid."""


# =====================================================================
# CONSTANTS
# =====================================================================

STANDARD_REBAR_DIAMETERS_MM: Tuple[float, ...] = (
    6.0,
    8.0,
    10.0,
    12.0,
    14.0,
    16.0,
    18.0,
    20.0,
    22.0,
    25.0,
    28.0,
    32.0,
    36.0,
    40.0,
    45.0,
    50.0,
)

DEFAULT_MAX_BAR_LENGTH_M = 12.0
DEFAULT_MIN_COVER_MM = 15.0
DEFAULT_MAX_COVER_MM = 150.0

DEFAULT_MIN_CONCRETE_FC_MPA = 15.0
DEFAULT_MAX_CONCRETE_FC_MPA = 100.0

DEFAULT_MIN_STEEL_FY_MPA = 200.0
DEFAULT_MAX_STEEL_FY_MPA = 1000.0


# =====================================================================
# RESULT OBJECTS
# =====================================================================

@dataclass(slots=True)
class ValidationIssue:
    field: str
    message: str
    code: str = "invalid"
    severity: str = "error"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "code": self.code,
            "severity": self.severity,
        }


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == "error"
        ]

    def add_error(
        self,
        field: str,
        message: str,
        code: str = "invalid",
    ) -> None:
        self.issues.append(
            ValidationIssue(
                field=field,
                message=message,
                code=code,
                severity="error",
            )
        )
        self.valid = False

    def add_warning(self, message: str) -> None:
        if message and message not in self.warnings:
            self.warnings.append(message)

    def raise_if_invalid(self) -> None:
        if not self.valid:
            messages = "; ".join(
                f"{issue.field}: {issue.message}"
                for issue in self.errors
            )
            raise ValidationError(messages or "Validation failed.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
            "warnings": list(self.warnings),
        }


# =====================================================================
# BASIC HELPERS
# =====================================================================

def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not _is_bool(value)
    )


def require_number(
    value: Any,
    field: str,
    *,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    allow_zero: bool = False,
) -> float:
    if value is None:
        raise RequiredFieldError(
            f"{field} is required."
        )

    if not is_number(value):
        raise NumericValidationError(
            f"{field} must be numeric."
        )

    numeric = float(value)

    if not allow_zero and numeric <= 0:
        raise NumericValidationError(
            f"{field} must be greater than zero."
        )

    if allow_zero and numeric < 0:
        raise NumericValidationError(
            f"{field} cannot be negative."
        )

    if minimum is not None and numeric < minimum:
        raise NumericValidationError(
            f"{field} must be >= {minimum}."
        )

    if maximum is not None and numeric > maximum:
        raise NumericValidationError(
            f"{field} must be <= {maximum}."
        )

    return numeric


def require_positive_number(
    value: Any,
    field: str,
    *,
    maximum: Optional[float] = None,
) -> float:
    return require_number(
        value,
        field,
        minimum=None,
        maximum=maximum,
        allow_zero=False,
    )


def require_non_negative_number(
    value: Any,
    field: str,
    *,
    maximum: Optional[float] = None,
) -> float:
    return require_number(
        value,
        field,
        minimum=None,
        maximum=maximum,
        allow_zero=True,
    )


def require_integer(
    value: Any,
    field: str,
    *,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
    allow_zero: bool = False,
) -> int:
    if value is None:
        raise RequiredFieldError(
            f"{field} is required."
        )

    if _is_bool(value) or not isinstance(value, int):
        raise NumericValidationError(
            f"{field} must be an integer."
        )

    if not allow_zero and value <= 0:
        raise NumericValidationError(
            f"{field} must be greater than zero."
        )

    if allow_zero and value < 0:
        raise NumericValidationError(
            f"{field} cannot be negative."
        )

    if minimum is not None and value < minimum:
        raise NumericValidationError(
            f"{field} must be >= {minimum}."
        )

    if maximum is not None and value > maximum:
        raise NumericValidationError(
            f"{field} must be <= {maximum}."
        )

    return value


def require_string(
    value: Any,
    field: str,
    *,
    min_length: int = 1,
    max_length: Optional[int] = None,
) -> str:
    if value is None:
        raise RequiredFieldError(
            f"{field} is required."
        )

    if not isinstance(value, str):
        raise ValidationError(
            f"{field} must be a string."
        )

    result = value.strip()

    if len(result) < min_length:
        raise ValidationError(
            f"{field} is too short."
        )

    if max_length is not None and len(result) > max_length:
        raise ValidationError(
            f"{field} exceeds maximum length."
        )

    return result


def optional_string(
    value: Any,
    field: str,
    *,
    max_length: Optional[int] = None,
) -> Optional[str]:
    if value is None:
        return None

    return require_string(
        value,
        field,
        min_length=1,
        max_length=max_length,
    )


def ensure_enum(
    value: Any,
    enum_type: Any,
    field: str,
) -> Any:
    if isinstance(value, enum_type):
        return value

    if isinstance(value, str):
        try:
            return enum_type(value)
        except ValueError:
            pass

    allowed = ", ".join(
        str(item.value)
        for item in enum_type
    )

    raise ValidationError(
        f"{field} must be one of: {allowed}."
    )


# =====================================================================
# REBAR HELPERS
# =====================================================================

def validate_rebar_diameter(
    diameter_mm: Any,
    *,
    require_standard: bool = True,
) -> float:
    diameter = require_positive_number(
        diameter_mm,
        "diameter_mm",
        maximum=100.0,
    )

    if require_standard:
        if diameter not in STANDARD_REBAR_DIAMETERS_MM:
            raise ReinforcementValidationError(
                f"Unsupported standard rebar diameter: {diameter_mm} mm."
            )

    return diameter


def validate_rebar_quantity(
    quantity: Any,
) -> int:
    return require_integer(
        quantity,
        "quantity",
        minimum=1,
        maximum=1_000_000,
    )


def validate_rebar_length(
    length_m: Any,
    *,
    max_length_m: float = DEFAULT_MAX_BAR_LENGTH_M,
    allow_overlength: bool = False,
) -> float:
    length = require_positive_number(
        length_m,
        "length_m",
    )

    if not allow_overlength and length > max_length_m:
        raise ReinforcementValidationError(
            f"Physical rebar piece length cannot exceed "
            f"{max_length_m:g} m."
        )

    return length


def validate_spacing(
    spacing_mm: Any,
    *,
    minimum_mm: float = 1.0,
    maximum_mm: float = 2000.0,
) -> float:
    return require_positive_number(
        spacing_mm,
        "spacing_mm",
        maximum=maximum_mm,
    ) if float(spacing_mm) >= minimum_mm else _raise(
        ReinforcementValidationError(
            f"spacing_mm must be >= {minimum_mm}."
        )
    )


def _raise(error: Exception) -> Any:
    raise error


# =====================================================================
# MATERIAL VALIDATION
# =====================================================================

def validate_concrete_material(
    material: ConcreteMaterial,
    *,
    min_fc_mpa: float = DEFAULT_MIN_CONCRETE_FC_MPA,
    max_fc_mpa: float = DEFAULT_MAX_CONCRETE_FC_MPA,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    try:
        require_string(material.grade, "grade")
    except ValidationError as exc:
        result.add_error("grade", str(exc))

    try:
        require_number(
            material.fc_mpa,
            "fc_mpa",
            minimum=min_fc_mpa,
            maximum=max_fc_mpa,
        )
    except ValidationError as exc:
        result.add_error("fc_mpa", str(exc))

    try:
        require_number(
            material.density_kg_m3,
            "density_kg_m3",
            minimum=1000.0,
            maximum=5000.0,
        )
    except ValidationError as exc:
        result.add_error(
            "density_kg_m3",
            str(exc),
        )

    return result


def validate_steel_material(
    material: SteelMaterial,
    *,
    min_fy_mpa: float = DEFAULT_MIN_STEEL_FY_MPA,
    max_fy_mpa: float = DEFAULT_MAX_STEEL_FY_MPA,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    try:
        require_string(material.grade, "grade")
    except ValidationError as exc:
        result.add_error("grade", str(exc))

    try:
        require_number(
            material.fy_mpa,
            "fy_mpa",
            minimum=min_fy_mpa,
            maximum=max_fy_mpa,
        )
    except ValidationError as exc:
        result.add_error("fy_mpa", str(exc))

    if material.fu_mpa is not None:
        try:
            require_number(
                material.fu_mpa,
                "fu_mpa",
                minimum=material.fy_mpa,
                maximum=2000.0,
            )
        except ValidationError as exc:
            result.add_error("fu_mpa", str(exc))

    try:
        require_number(
            material.density_kg_m3,
            "density_kg_m3",
            minimum=5000.0,
            maximum=10000.0,
        )
    except ValidationError as exc:
        result.add_error(
            "density_kg_m3",
            str(exc),
        )

    return result


# =====================================================================
# GEOMETRY VALIDATION
# =====================================================================

def validate_rectangular_geometry(
    geometry: RectangularGeometry,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    for field_name in ("width_m", "depth_m"):
        try:
            require_positive_number(
                getattr(geometry, field_name),
                field_name,
                maximum=1000.0,
            )
        except ValidationError as exc:
            result.add_error(field_name, str(exc))

    if geometry.height_m is not None:
        try:
            require_positive_number(
                geometry.height_m,
                "height_m",
                maximum=1000.0,
            )
        except ValidationError as exc:
            result.add_error("height_m", str(exc))

    return result


def validate_circular_geometry(
    geometry: CircularGeometry,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    try:
        require_positive_number(
            geometry.diameter_m,
            "diameter_m",
            maximum=1000.0,
        )
    except ValidationError as exc:
        result.add_error("diameter_m", str(exc))

    if geometry.height_m is not None:
        try:
            require_positive_number(
                geometry.height_m,
                "height_m",
                maximum=1000.0,
            )
        except ValidationError as exc:
            result.add_error("height_m", str(exc))

    return result


def validate_slab_geometry(
    geometry: SlabGeometry,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    for field_name in (
        "length_m",
        "width_m",
        "thickness_m",
    ):
        try:
            require_positive_number(
                getattr(geometry, field_name),
                field_name,
                maximum=1000.0,
            )
        except ValidationError as exc:
            result.add_error(field_name, str(exc))

    return result


def validate_geometry(
    geometry: Any,
) -> ValidationResult:
    if isinstance(geometry, RectangularGeometry):
        return validate_rectangular_geometry(geometry)

    if isinstance(geometry, CircularGeometry):
        return validate_circular_geometry(geometry)

    if isinstance(geometry, SlabGeometry):
        return validate_slab_geometry(geometry)

    result = ValidationResult(valid=False)
    result.add_error(
        "geometry",
        "Unsupported geometry type.",
        code="unsupported_geometry",
    )
    return result


# =====================================================================
# COVER VALIDATION
# =====================================================================

def validate_cover(
    cover_mm: Any,
    *,
    minimum_mm: float = DEFAULT_MIN_COVER_MM,
    maximum_mm: float = DEFAULT_MAX_COVER_MM,
) -> float:
    cover = require_positive_number(
        cover_mm,
        "cover_mm",
        maximum=maximum_mm,
    )

    if cover < minimum_mm:
        raise ValidationError(
            f"cover_mm must be >= {minimum_mm:g} mm."
        )

    return cover


# =====================================================================
# PROJECT VALIDATION
# =====================================================================

def validate_project(
    project: Project,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    try:
        require_string(project.project_id, "project_id")
    except ValidationError as exc:
        result.add_error("project_id", str(exc))

    try:
        require_string(project.name, "name")
    except ValidationError as exc:
        result.add_error("name", str(exc))

    try:
        ensure_enum(
            project.structure_type,
            StructureType,
            "structure_type",
        )
    except ValidationError as exc:
        result.add_error("structure_type", str(exc))

    try:
        ensure_enum(
            project.unit_system,
            UnitSystem,
            "unit_system",
        )
    except ValidationError as exc:
        result.add_error("unit_system", str(exc))

    if project.revision < 1:
        result.add_error(
            "revision",
            "revision must be >= 1.",
        )

    if project.design_code is not None:
        try:
            require_string(
                project.design_code,
                "design_code",
            )
        except ValidationError as exc:
            result.add_error(
                "design_code",
                str(exc),
            )

    if project.code_edition is not None:
        try:
            require_string(
                project.code_edition,
                "code_edition",
            )
        except ValidationError as exc:
            result.add_error(
                "code_edition",
                str(exc),
            )

    return result


# =====================================================================
# FLOOR VALIDATION
# =====================================================================

def validate_floor(
    floor: Floor,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    for field_name in (
        "floor_id",
        "project_id",
        "name",
    ):
        try:
            require_string(
                getattr(floor, field_name),
                field_name,
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    if floor.revision < 1:
        result.add_error(
            "revision",
            "revision must be >= 1.",
        )

    return result


# =====================================================================
# STRUCTURAL MEMBER VALIDATION
# =====================================================================

def validate_structural_member(
    member: StructuralMember,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    for field_name in (
        "member_id",
        "project_id",
    ):
        try:
            require_string(
                getattr(member, field_name),
                field_name,
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    try:
        ensure_enum(
            member.member_type,
            MemberType,
            "member_type",
        )
    except ValidationError as exc:
        result.add_error(
            "member_type",
            str(exc),
        )

    try:
        ensure_enum(
            member.structure_type,
            StructureType,
            "structure_type",
        )
    except ValidationError as exc:
        result.add_error(
            "structure_type",
            str(exc),
        )

    if member.revision < 1:
        result.add_error(
            "revision",
            "revision must be >= 1.",
        )

    if member.cover_mm is not None:
        try:
            validate_cover(member.cover_mm)
        except ValidationError as exc:
            result.add_error(
                "cover_mm",
                str(exc),
            )

    if member.geometry is not None:
        geometry_result = validate_geometry(
            member.geometry
        )

        for issue in geometry_result.issues:
            result.issues.append(issue)

        result.warnings.extend(
            geometry_result.warnings
        )

        if not geometry_result.valid:
            result.valid = False

    if member.materials is not None:
        if member.materials.concrete is not None:
            material_result = validate_concrete_material(
                member.materials.concrete
            )

            for issue in material_result.issues:
                result.issues.append(
                    ValidationIssue(
                        field=f"materials.concrete.{issue.field}",
                        message=issue.message,
                        code=issue.code,
                        severity=issue.severity,
                    )
                )

            if not material_result.valid:
                result.valid = False

        if member.materials.reinforcement is not None:
            steel_result = validate_steel_material(
                member.materials.reinforcement
            )

            for issue in steel_result.issues:
                result.issues.append(
                    ValidationIssue(
                        field=f"materials.reinforcement.{issue.field}",
                        message=issue.message,
                        code=issue.code,
                        severity=issue.severity,
                    )
                )

            if not steel_result.valid:
                result.valid = False

        if member.materials.structural_steel is not None:
            steel_result = validate_steel_material(
                member.materials.structural_steel
            )

            for issue in steel_result.issues:
                result.issues.append(
                    ValidationIssue(
                        field=f"materials.structural_steel.{issue.field}",
                        message=issue.message,
                        code=issue.code,
                        severity=issue.severity,
                    )
                )

            if not steel_result.valid:
                result.valid = False

    return result


# =====================================================================
# REBAR SHAPE VALIDATION
# =====================================================================

def validate_rebar_shape(
    shape: RebarShape,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    try:
        require_string(
            shape.shape_code,
            "shape_code",
        )
    except ValidationError as exc:
        result.add_error(
            "shape_code",
            str(exc),
        )

    for key, value in shape.dimensions_mm.items():
        try:
            require_positive_number(
                value,
                f"dimensions_mm.{key}",
                maximum=100_000.0,
            )
        except ValidationError as exc:
            result.add_error(
                f"dimensions_mm.{key}",
                str(exc),
            )

    for angle in shape.bend_angles_deg:
        try:
            require_number(
                angle,
                "bend_angle",
                minimum=0.0,
                maximum=360.0,
                allow_zero=True,
            )
        except ValidationError as exc:
            result.add_error(
                "bend_angles_deg",
                str(exc),
            )

    return result


# =====================================================================
# REINFORCEMENT VALIDATION
# =====================================================================

def validate_reinforcement_bar(
    bar: ReinforcementBar,
    *,
    max_piece_length_m: float = DEFAULT_MAX_BAR_LENGTH_M,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    for field_name in (
        "bar_id",
        "member_id",
        "project_id",
    ):
        try:
            require_string(
                getattr(bar, field_name),
                field_name,
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    try:
        validate_rebar_diameter(
            bar.diameter_mm
        )
    except ValidationError as exc:
        result.add_error(
            "diameter_mm",
            str(exc),
        )

    try:
        validate_rebar_quantity(
            bar.quantity
        )
    except ValidationError as exc:
        result.add_error(
            "quantity",
            str(exc),
        )

    try:
        validate_rebar_length(
            bar.length_m,
            max_length_m=max_piece_length_m,
        )
    except ValidationError as exc:
        result.add_error(
            "length_m",
            str(exc),
        )

    if bar.spacing_mm is not None:
        try:
            validate_spacing(
                bar.spacing_mm
            )
        except ValidationError as exc:
            result.add_error(
                "spacing_mm",
                str(exc),
            )

    if bar.development_length_m < 0:
        result.add_error(
            "development_length_m",
            "development length cannot be negative.",
        )

    if bar.lap_length_m < 0:
        result.add_error(
            "lap_length_m",
            "lap length cannot be negative.",
        )

    if bar.shape is not None:
        shape_result = validate_rebar_shape(
            bar.shape
        )

        for issue in shape_result.issues:
            result.issues.append(issue)

        if not shape_result.valid:
            result.valid = False

    if bar.source_revision is not None:
        if bar.source_revision < 1:
            result.add_error(
                "source_revision",
                "source_revision must be >= 1.",
            )

    return result


# =====================================================================
# SPLICE VALIDATION
# =====================================================================

def validate_splice(
    splice: Splice,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    for field_name in (
        "splice_id",
        "member_id",
        "bar_id",
    ):
        try:
            require_string(
                getattr(splice, field_name),
                field_name,
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    try:
        ensure_enum(
            splice.splice_type,
            SpliceType,
            "splice_type",
        )
    except ValidationError as exc:
        result.add_error(
            "splice_type",
            str(exc),
        )

    if splice.position_m is not None:
        try:
            require_non_negative_number(
                splice.position_m,
                "position_m",
            )
        except ValidationError as exc:
            result.add_error(
                "position_m",
                str(exc),
            )

    if splice.length_m is not None:
        try:
            require_positive_number(
                splice.length_m,
                "length_m",
            )
        except ValidationError as exc:
            result.add_error(
                "length_m",
                str(exc),
            )

    return result


# =====================================================================
# CALCULATION RESULT VALIDATION
# =====================================================================

def validate_calculation_result(
    result_obj: CalculationResult,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    for field_name in (
        "calculation_id",
        "project_id",
        "member_id",
    ):
        try:
            require_string(
                getattr(result_obj, field_name),
                field_name,
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    try:
        ensure_enum(
            result_obj.member_type,
            MemberType,
            "member_type",
        )
    except ValidationError as exc:
        result.add_error(
            "member_type",
            str(exc),
        )

    if result_obj.revision < 1:
        result.add_error(
            "revision",
            "revision must be >= 1.",
        )

    for index, check in enumerate(result_obj.checks):
        if not check.check_id:
            result.add_error(
                f"checks[{index}].check_id",
                "check_id is required.",
            )

    for index, bar in enumerate(
        result_obj.reinforcement
    ):
        bar_result = validate_reinforcement_bar(bar)

        for issue in bar_result.issues:
            result.issues.append(
                ValidationIssue(
                    field=f"reinforcement[{index}].{issue.field}",
                    message=issue.message,
                    code=issue.code,
                    severity=issue.severity,
                )
            )

        if not bar_result.valid:
            result.valid = False

    return result


# =====================================================================
# MATERIAL QUANTITY VALIDATION
# =====================================================================

def validate_material_quantity(
    item: MaterialQuantity,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    for field_name in (
        "item_id",
        "project_id",
        "material_type",
        "unit",
    ):
        try:
            require_string(
                getattr(item, field_name),
                field_name,
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    try:
        require_non_negative_number(
            item.quantity,
            "quantity",
        )
    except ValidationError as exc:
        result.add_error(
            "quantity",
            str(exc),
        )

    if item.revision < 1:
        result.add_error(
            "revision",
            "revision must be >= 1.",
        )

    return result


# =====================================================================
# ENGINEERING CONTEXT VALIDATION
# =====================================================================

def validate_engineering_context(
    context: EngineeringContext,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    structure_type = context.resolve_structure_type()

    if structure_type is None:
        result.add_error(
            "structure_type",
            "Structure type must be explicitly resolvable.",
            code="missing_structure_type",
        )
    else:
        try:
            ensure_enum(
                structure_type,
                StructureType,
                "structure_type",
            )
        except ValidationError as exc:
            result.add_error(
                "structure_type",
                str(exc),
            )

    if context.project is not None:
        project_result = validate_project(
            context.project
        )

        for issue in project_result.issues:
            result.issues.append(issue)

        if not project_result.valid:
            result.valid = False

    if context.floor is not None:
        floor_result = validate_floor(
            context.floor
        )

        for issue in floor_result.issues:
            result.issues.append(issue)

        if not floor_result.valid:
            result.valid = False

    if context.member is not None:
        member_result = validate_structural_member(
            context.member
        )

        for issue in member_result.issues:
            result.issues.append(issue)

        if not member_result.valid:
            result.valid = False

    if context.revision < 1:
        result.add_error(
            "revision",
            "revision must be >= 1.",
        )

    if context.design_code is None:
        if context.project is None or context.project.design_code is None:
            result.add_warning(
                "No design code is configured in the engineering context."
            )

    return result


# =====================================================================
# SPECIALIZED INPUT VALIDATORS
# =====================================================================

@dataclass(slots=True)
class FoundationInput:
    foundation_type: FoundationType
    length_m: float
    width_m: float
    thickness_m: float
    depth_m: Optional[float] = None
    soil_bearing_capacity_kpa: Optional[float] = None
    axial_load_kn: Optional[float] = None
    moment_x_knm: Optional[float] = None
    moment_y_knm: Optional[float] = None
    cover_mm: Optional[float] = None


def validate_foundation_input(
    data: FoundationInput,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    try:
        ensure_enum(
            data.foundation_type,
            FoundationType,
            "foundation_type",
        )
    except ValidationError as exc:
        result.add_error(
            "foundation_type",
            str(exc),
        )

    for field_name in (
        "length_m",
        "width_m",
        "thickness_m",
    ):
        try:
            require_positive_number(
                getattr(data, field_name),
                field_name,
                maximum=1000.0,
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    optional_positive = (
        "depth_m",
        "soil_bearing_capacity_kpa",
    )

    for field_name in optional_positive:
        value = getattr(data, field_name)
        if value is not None:
            try:
                require_positive_number(
                    value,
                    field_name,
                )
            except ValidationError as exc:
                result.add_error(
                    field_name,
                    str(exc),
                )

    for field_name in (
        "axial_load_kn",
        "moment_x_knm",
        "moment_y_knm",
    ):
        value = getattr(data, field_name)
        if value is not None:
            try:
                require_number(
                    value,
                    field_name,
                    allow_zero=True,
                )
            except ValidationError as exc:
                result.add_error(
                    field_name,
                    str(exc),
                )

    if data.cover_mm is not None:
        try:
            validate_cover(data.cover_mm)
        except ValidationError as exc:
            result.add_error(
                "cover_mm",
                str(exc),
            )

    return result


@dataclass(slots=True)
class ColumnInput:
    column_type: ColumnType
    width_m: Optional[float] = None
    depth_m: Optional[float] = None
    diameter_m: Optional[float] = None
    height_m: float = 3.0
    axial_load_kn: Optional[float] = None
    moment_x_knm: Optional[float] = None
    moment_y_knm: Optional[float] = None
    cover_mm: Optional[float] = None


def validate_column_input(
    data: ColumnInput,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    try:
        ensure_enum(
            data.column_type,
            ColumnType,
            "column_type",
        )
    except ValidationError as exc:
        result.add_error(
            "column_type",
            str(exc),
        )

    if data.column_type == ColumnType.RECTANGULAR:
        for field_name in (
            "width_m",
            "depth_m",
        ):
            if getattr(data, field_name) is None:
                result.add_error(
                    field_name,
                    "Required for rectangular columns.",
                    code="required",
                )
            else:
                try:
                    require_positive_number(
                        getattr(data, field_name),
                        field_name,
                    )
                except ValidationError as exc:
                    result.add_error(
                        field_name,
                        str(exc),
                    )

    if data.column_type == ColumnType.CIRCULAR:
        if data.diameter_m is None:
            result.add_error(
                "diameter_m",
                "Required for circular columns.",
                code="required",
            )
        else:
            try:
                require_positive_number(
                    data.diameter_m,
                    "diameter_m",
                )
            except ValidationError as exc:
                result.add_error(
                    "diameter_m",
                    str(exc),
                )

    try:
        require_positive_number(
            data.height_m,
            "height_m",
        )
    except ValidationError as exc:
        result.add_error(
            "height_m",
            str(exc),
        )

    for field_name in (
        "axial_load_kn",
        "moment_x_knm",
        "moment_y_knm",
    ):
        value = getattr(data, field_name)
        if value is not None:
            try:
                require_number(
                    value,
                    field_name,
                    allow_zero=True,
                )
            except ValidationError as exc:
                result.add_error(
                    field_name,
                    str(exc),
                )

    if data.cover_mm is not None:
        try:
            validate_cover(data.cover_mm)
        except ValidationError as exc:
            result.add_error(
                "cover_mm",
                str(exc),
            )

    return result


@dataclass(slots=True)
class BeamInput:
    beam_type: BeamType
    width_m: float
    depth_m: float
    span_m: float
    uniform_load_kn_m: Optional[float] = None
    point_load_kn: Optional[float] = None
    point_load_position_m: Optional[float] = None
    cover_mm: Optional[float] = None


def validate_beam_input(
    data: BeamInput,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    try:
        ensure_enum(
            data.beam_type,
            BeamType,
            "beam_type",
        )
    except ValidationError as exc:
        result.add_error(
            "beam_type",
            str(exc),
        )

    for field_name in (
        "width_m",
        "depth_m",
        "span_m",
    ):
        try:
            require_positive_number(
                getattr(data, field_name),
                field_name,
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    if data.uniform_load_kn_m is not None:
        try:
            require_non_negative_number(
                data.uniform_load_kn_m,
                "uniform_load_kn_m",
            )
        except ValidationError as exc:
            result.add_error(
                "uniform_load_kn_m",
                str(exc),
            )

    if data.point_load_kn is not None:
        try:
            require_non_negative_number(
                data.point_load_kn,
                "point_load_kn",
            )
        except ValidationError as exc:
            result.add_error(
                "point_load_kn",
                str(exc),
            )

    if data.point_load_position_m is not None:
        try:
            require_non_negative_number(
                data.point_load_position_m,
                "point_load_position_m",
            )

        except ValidationError as exc:
            result.add_error(
                "point_load_position_m",
                str(exc),
            )

        if (
            data.point_load_position_m is not None
            and data.span_m > 0
            and data.point_load_position_m > data.span_m
        ):
            result.add_error(
                "point_load_position_m",
                "Point load position cannot exceed beam span.",
            )

    if data.cover_mm is not None:
        try:
            validate_cover(data.cover_mm)
        except ValidationError as exc:
            result.add_error(
                "cover_mm",
                str(exc),
            )

    return result


@dataclass(slots=True)
class SlabInput:
    slab_type: SlabType
    length_m: float
    width_m: float
    thickness_m: float
    cover_mm: Optional[float] = None
    uniform_load_kn_m2: Optional[float] = None


def validate_slab_input(
    data: SlabInput,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    try:
        ensure_enum(
            data.slab_type,
            SlabType,
            "slab_type",
        )
    except ValidationError as exc:
        result.add_error(
            "slab_type",
            str(exc),
        )

    for field_name in (
        "length_m",
        "width_m",
        "thickness_m",
    ):
        try:
            require_positive_number(
                getattr(data, field_name),
                field_name,
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    if data.uniform_load_kn_m2 is not None:
        try:
            require_non_negative_number(
                data.uniform_load_kn_m2,
                "uniform_load_kn_m2",
            )
        except ValidationError as exc:
            result.add_error(
                "uniform_load_kn_m2",
                str(exc),
            )

    if data.cover_mm is not None:
        try:
            validate_cover(data.cover_mm)
        except ValidationError as exc:
            result.add_error(
                "cover_mm",
                str(exc),
            )

    return result


@dataclass(slots=True)
class EquivalencyInput:
    source_diameter_mm: float
    source_quantity: int
    target_diameter_mm: float
    target_quantity: Optional[int] = None


def validate_equivalency_input(
    data: EquivalencyInput,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    for field_name in (
        "source_diameter_mm",
        "target_diameter_mm",
    ):
        try:
            validate_rebar_diameter(
                getattr(data, field_name)
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    try:
        validate_rebar_quantity(
            data.source_quantity
        )
    except ValidationError as exc:
        result.add_error(
            "source_quantity",
            str(exc),
        )

    if data.target_quantity is not None:
        try:
            validate_rebar_quantity(
                data.target_quantity
            )
        except ValidationError as exc:
            result.add_error(
                "target_quantity",
                str(exc),
            )

    return result


# =====================================================================
# CUT PIECE VALIDATION
# =====================================================================

def validate_cut_piece(
    piece: Any,
    *,
    max_length_m: float = DEFAULT_MAX_BAR_LENGTH_M,
) -> ValidationResult:
    result = ValidationResult(valid=True)

    required_fields = (
        "piece_id",
        "bar_mark",
    )

    for field_name in required_fields:
        value = getattr(piece, field_name, None)

        try:
            require_string(
                value,
                field_name,
            )
        except ValidationError as exc:
            result.add_error(
                field_name,
                str(exc),
            )

    try:
        validate_rebar_diameter(
            piece.diameter_mm
        )
    except ValidationError as exc:
        result.add_error(
            "diameter_mm",
            str(exc),
        )

    try:
        validate_rebar_length(
            piece.length_m,
            max_length_m=max_length_m,
        )
    except ValidationError as exc:
        result.add_error(
            "length_m",
            str(exc),
        )

    try:
        validate_rebar_quantity(
            piece.quantity
        )
    except ValidationError as exc:
        result.add_error(
            "quantity",
            str(exc),
        )

    return result


# =====================================================================
# BATCH VALIDATION
# =====================================================================

def validate_all(
    objects: Iterable[Any],
) -> ValidationResult:
    combined = ValidationResult(valid=True)

    for index, obj in enumerate(objects):
        validator = validator_for(obj)

        if validator is None:
            combined.add_warning(
                f"Object at index {index} has no registered validator."
            )
            continue

        result = validator(obj)

        for issue in result.issues:
            combined.issues.append(
                ValidationIssue(
                    field=f"[{index}].{issue.field}",
                    message=issue.message,
                    code=issue.code,
                    severity=issue.severity,
                )
            )

        combined.warnings.extend(
            result.warnings
        )

        if not result.valid:
            combined.valid = False

    return combined


def validator_for(
    obj: Any,
):
    if isinstance(obj, Project):
        return validate_project

    if isinstance(obj, Floor):
        return validate_floor

    if isinstance(obj, StructuralMember):
        return validate_structural_member

    if isinstance(obj, ReinforcementBar):
        return validate_reinforcement_bar

    if isinstance(obj, Splice):
        return validate_splice

    if isinstance(obj, CalculationResult):
        return validate_calculation_result

    if isinstance(obj, MaterialQuantity):
        return validate_material_quantity

    if isinstance(obj, EngineeringContext):
        return validate_engineering_context

    return None


# =====================================================================
# ASSERTION HELPERS
# =====================================================================

def assert_valid(
    obj: Any,
) -> None:
    validator = validator_for(obj)

    if validator is None:
        raise ValidationError(
            f"No validator registered for {type(obj).__name__}."
        )

    result = validator(obj)
    result.raise_if_invalid()


def validate_and_raise(
    obj: Any,
) -> ValidationResult:
    validator = validator_for(obj)

    if validator is None:
        raise ValidationError(
            f"No validator registered for {type(obj).__name__}."
        )

    result = validator(obj)
    result.raise_if_invalid()
    return result


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    # Exceptions
    "ValidationError",
    "RequiredFieldError",
    "NumericValidationError",
    "GeometryValidationError",
    "MaterialValidationError",
    "ReinforcementValidationError",

    # Constants
    "STANDARD_REBAR_DIAMETERS_MM",
    "DEFAULT_MAX_BAR_LENGTH_M",
    "DEFAULT_MIN_COVER_MM",
    "DEFAULT_MAX_COVER_MM",

    # Result objects
    "ValidationIssue",
    "ValidationResult",

    # Basic helpers
    "is_number",
    "require_number",
    "require_positive_number",
    "require_non_negative_number",
    "require_integer",
    "require_string",
    "optional_string",
    "ensure_enum",

    # Rebar
    "validate_rebar_diameter",
    "validate_rebar_quantity",
    "validate_rebar_length",
    "validate_spacing",

    # Materials
    "validate_concrete_material",
    "validate_steel_material",

    # Geometry
    "validate_rectangular_geometry",
    "validate_circular_geometry",
    "validate_slab_geometry",
    "validate_geometry",
    "validate_cover",

    # Domain
    "validate_project",
    "validate_floor",
    "validate_structural_member",
    "validate_rebar_shape",
    "validate_reinforcement_bar",
    "validate_splice",
    "validate_calculation_result",
    "validate_material_quantity",
    "validate_engineering_context",
    "validate_cut_piece",

    # Specialized inputs
    "FoundationInput",
    "ColumnInput",
    "BeamInput",
    "SlabInput",
    "EquivalencyInput",

    "validate_foundation_input",
    "validate_column_input",
    "validate_beam_input",
    "validate_slab_input",
    "validate_equivalency_input",

    # Batch / assertions
    "validate_all",
    "validator_for",
    "assert_valid",
    "validate_and_raise",
]
