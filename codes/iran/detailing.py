from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from codes.base import CheckStatus, CodeCheck


@dataclass(frozen=True)
class DetailingLimits:
    min_cover_mm: float = 20.0
    min_clear_spacing_mm: float = 25.0
    min_bar_spacing_mm: float = 25.0
    max_bar_spacing_mm: float = 300.0
    max_bend_diameter_factor: float = 6.0
    min_hook_extension_factor: float = 4.0


@dataclass(frozen=True)
class HookRule:
    angle_deg: float
    extension_factor: float
    min_extension_mm: float = 75.0


@dataclass(frozen=True)
class SpliceRule:
    member_type: str
    region: str
    max_ratio: float = 0.5
    lap_factor: float = 1.3


def check_cover(
    cover_mm: float,
    limits: Optional[DetailingLimits] = None,
) -> CodeCheck:
    limits = limits or DetailingLimits()
    value = float(cover_mm)

    return CodeCheck(
        name="concrete_cover",
        status=(
            CheckStatus.PASS
            if value >= limits.min_cover_mm
            else CheckStatus.FAIL
        ),
        value=value,
        limit=limits.min_cover_mm,
        relation=">=",
        unit="mm",
    )


def check_bar_spacing(
    spacing_mm: float,
    limits: Optional[DetailingLimits] = None,
) -> CodeCheck:
    limits = limits or DetailingLimits()
    value = float(spacing_mm)

    if value < limits.min_bar_spacing_mm:
        status = CheckStatus.FAIL
    elif value > limits.max_bar_spacing_mm:
        status = CheckStatus.FAIL
    else:
        status = CheckStatus.PASS

    return CodeCheck(
        name="bar_spacing",
        status=status,
        value=value,
        limit=limits.max_bar_spacing_mm,
        relation="range",
        unit="mm",
    )


def check_clear_spacing(
    spacing_mm: float,
    limits: Optional[DetailingLimits] = None,
) -> CodeCheck:
    limits = limits or DetailingLimits()
    value = float(spacing_mm)

    return CodeCheck(
        name="clear_spacing",
        status=(
            CheckStatus.PASS
            if value >= limits.min_clear_spacing_mm
            else CheckStatus.FAIL
        ),
        value=value,
        limit=limits.min_clear_spacing_mm,
        relation=">=",
        unit="mm",
    )


def minimum_bend_diameter(
    bar_diameter_mm: float,
    factor: float = 6.0,
) -> float:
    d = float(bar_diameter_mm)
    f = float(factor)

    if d <= 0 or f <= 0:
        raise ValueError("Invalid bend inputs.")

    return d * f


def minimum_hook_extension(
    bar_diameter_mm: float,
    angle_deg: float = 90.0,
    *,
    limits: Optional[DetailingLimits] = None,
) -> float:
    limits = limits or DetailingLimits()
    d = float(bar_diameter_mm)

    if d <= 0:
        raise ValueError("Bar diameter must be positive.")

    factor = limits.min_hook_extension_factor

    if angle_deg >= 135:
        factor *= 1.0
    elif angle_deg >= 90:
        factor *= 1.0
    else:
        factor *= 1.25

    return max(
        d * factor,
        75.0,
    )


def check_bend_diameter(
    bend_diameter_mm: float,
    bar_diameter_mm: float,
    *,
    factor: float = 6.0,
) -> CodeCheck:
    minimum = minimum_bend_diameter(bar_diameter_mm, factor)

    return CodeCheck(
        name="bend_diameter",
        status=(
            CheckStatus.PASS
            if float(bend_diameter_mm) >= minimum
            else CheckStatus.FAIL
        ),
        value=float(bend_diameter_mm),
        limit=minimum,
        relation=">=",
        unit="mm",
    )


def check_hook_extension(
    extension_mm: float,
    bar_diameter_mm: float,
    angle_deg: float = 90.0,
) -> CodeCheck:
    minimum = minimum_hook_extension(
        bar_diameter_mm,
        angle_deg,
    )

    return CodeCheck(
        name="hook_extension",
        status=(
            CheckStatus.PASS
            if float(extension_mm) >= minimum
            else CheckStatus.FAIL
        ),
        value=float(extension_mm),
        limit=minimum,
        relation=">=",
        unit="mm",
    )


def calculate_lap_length(
    development_length_mm: float,
    *,
    factor: float = 1.3,
) -> float:
    ld = float(development_length_mm)
    f = float(factor)

    if ld <= 0 or f <= 0:
        raise ValueError("Invalid lap inputs.")

    return ld * f


def check_development_length(
    provided_mm: float,
    required_mm: float,
) -> CodeCheck:
    return CodeCheck(
        name="development_length",
        status=(
            CheckStatus.PASS
            if float(provided_mm) >= float(required_mm)
            else CheckStatus.FAIL
        ),
        value=float(provided_mm),
        limit=float(required_mm),
        relation=">=",
        unit="mm",
    )


def check_lap_length(
    provided_mm: float,
    required_mm: float,
) -> CodeCheck:
    return CodeCheck(
        name="lap_length",
        status=(
            CheckStatus.PASS
            if float(provided_mm) >= float(required_mm)
            else CheckStatus.FAIL
        ),
        value=float(provided_mm),
        limit=float(required_mm),
        relation=">=",
        unit="mm",
    )


def check_bar_placement(
    cover_mm: float,
    clear_spacing_mm: float,
    *,
    limits: Optional[DetailingLimits] = None,
) -> list[CodeCheck]:
    return [
        check_cover(cover_mm, limits),
        check_clear_spacing(clear_spacing_mm, limits),
    ]


def validate_detailing(
    *,
    cover_mm: float,
    spacing_mm: float,
    clear_spacing_mm: float,
    limits: Optional[DetailingLimits] = None,
) -> list[CodeCheck]:
    return [
        check_cover(cover_mm, limits),
        check_bar_spacing(spacing_mm, limits),
        check_clear_spacing(clear_spacing_mm, limits),
    ]


__all__ = [
    "DetailingLimits",
    "HookRule",
    "SpliceRule",
    "check_cover",
    "check_bar_spacing",
    "check_clear_spacing",
    "minimum_bend_diameter",
    "minimum_hook_extension",
    "check_bend_diameter",
    "check_hook_extension",
    "calculate_lap_length",
    "check_development_length",
    "check_lap_length",
    "check_bar_placement",
    "validate_detailing",
]
