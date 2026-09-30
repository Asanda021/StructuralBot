from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .materials import IranMaterials
from .reinforcement import STANDARD_DIAMETERS_MM


class IranValidationError(ValueError):
    pass


@dataclass(frozen=True)
class MaterialInput:
    concrete_grade: Optional[str] = None
    reinforcement_grade: Optional[str] = None
    steel_grade: Optional[str] = None


@dataclass(frozen=True)
class GeometryInput:
    width_mm: float
    depth_mm: float
    cover_mm: float = 0.0


@dataclass(frozen=True)
class RebarInput:
    diameter_mm: float
    grade: str
    quantity: int = 1
    spacing_mm: Optional[float] = None


def validate_concrete_grade(grade: str) -> None:
    try:
        IranMaterials.get_concrete(grade)
    except KeyError as exc:
        raise IranValidationError(
            f"Unsupported concrete grade: {grade}"
        ) from exc


def validate_reinforcement_grade(grade: str) -> None:
    try:
        IranMaterials.get_reinforcement(grade)
    except KeyError as exc:
        raise IranValidationError(
            f"Unsupported reinforcement grade: {grade}"
        ) from exc


def validate_steel_grade(grade: str) -> None:
    try:
        IranMaterials.get_structural_steel(grade)
    except KeyError as exc:
        raise IranValidationError(
            f"Unsupported structural steel grade: {grade}"
        ) from exc


def validate_geometry(data: GeometryInput) -> None:
    if data.width_mm <= 0:
        raise IranValidationError("Width must be positive.")

    if data.depth_mm <= 0:
        raise IranValidationError("Depth must be positive.")

    if data.cover_mm < 0:
        raise IranValidationError("Cover cannot be negative.")

    if 2.0 * data.cover_mm >= min(
        data.width_mm,
        data.depth_mm,
    ):
        raise IranValidationError(
            "Cover leaves no usable section core."
        )


def validate_rebar(data: RebarInput) -> None:
    if float(data.diameter_mm) not in STANDARD_DIAMETERS_MM:
        raise IranValidationError(
            f"Unsupported rebar diameter: {data.diameter_mm}"
        )

    validate_reinforcement_grade(data.grade)

    if int(data.quantity) < 1:
        raise IranValidationError(
            "Rebar quantity must be at least 1."
        )

    if data.spacing_mm is not None and data.spacing_mm <= 0:
        raise IranValidationError(
            "Rebar spacing must be positive."
        )


def validate_materials(data: MaterialInput) -> None:
    if data.concrete_grade:
        validate_concrete_grade(data.concrete_grade)

    if data.reinforcement_grade:
        validate_reinforcement_grade(
            data.reinforcement_grade
        )

    if data.steel_grade:
        validate_steel_grade(data.steel_grade)


def validate_all(
    *,
    materials: Optional[MaterialInput] = None,
    geometry: Optional[GeometryInput] = None,
    rebar: Optional[RebarInput] = None,
) -> None:
    if materials:
        validate_materials(materials)

    if geometry:
        validate_geometry(geometry)

    if rebar:
        validate_rebar(rebar)


__all__ = [
    "IranValidationError",
    "MaterialInput",
    "GeometryInput",
    "RebarInput",
    "validate_concrete_grade",
    "validate_reinforcement_grade",
    "validate_steel_grade",
    "validate_geometry",
    "validate_rebar",
    "validate_materials",
    "validate_all",
]
