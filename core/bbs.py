from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional


MAX_STOCK_LENGTH_MM = 12000.0


@dataclass
class BBSDimension:
    name: str
    value_mm: float
    note: str = ""

    def __post_init__(self):
        self.value_mm = float(self.value_mm)
        if self.value_mm < 0:
            raise ValueError("BBS dimension cannot be negative.")


@dataclass
class BBSShape:
    code: str = "STRAIGHT"
    dimensions: list[BBSDimension] = field(default_factory=list)
    hooks: Optional[str] = None
    bends: int = 0

    def __post_init__(self):
        self.code = str(self.code).upper()
        self.bends = int(self.bends)
        if self.bends < 0:
            raise ValueError("Bends cannot be negative.")

    def total_dimension_mm(self) -> float:
        return sum(x.value_mm for x in self.dimensions)


@dataclass
class BBSItem:
    mark: str
    member_id: str
    member_type: str
    floor_id: Optional[str]
    bar_mark: str
    role: str
    diameter_mm: float
    grade: str
    quantity: int
    spacing_mm: Optional[float]
    length_mm: float
    shape: BBSShape = field(default_factory=BBSShape)
    length_basis: str = "DESIGN"
    development_length_mm: float = 0.0
    lap_length_mm: float = 0.0
    region: Optional[str] = None
    source_ref: Optional[str] = None
    notes: str = ""

    def __post_init__(self):
        self.diameter_mm = float(self.diameter_mm)
        self.length_mm = float(self.length_mm)
        self.quantity = int(self.quantity)
        self.development_length_mm = float(self.development_length_mm or 0)
        self.lap_length_mm = float(self.lap_length_mm or 0)

        if self.quantity < 1:
            raise ValueError("BBS quantity must be at least 1.")
        if self.diameter_mm <= 0:
            raise ValueError("BBS diameter must be positive.")
        if self.length_mm <= 0:
            raise ValueError("BBS length must be positive.")

        if self.spacing_mm is not None:
            self.spacing_mm = float(self.spacing_mm)
            if self.spacing_mm <= 0:
                raise ValueError("BBS spacing must be positive.")

    @property
    def total_length_mm(self) -> float:
        return self.quantity * self.length_mm

    @property
    def total_length_m(self) -> float:
        return self.total_length_mm / 1000.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mark": self.mark,
            "member_id": self.member_id,
            "member_type": self.member_type,
            "floor_id": self.floor_id,
            "bar_mark": self.bar_mark,
            "role": self.role,
            "diameter_mm": self.diameter_mm,
            "grade": self.grade,
            "quantity": self.quantity,
            "spacing_mm": self.spacing_mm,
            "length_mm": self.length_mm,
            "length_basis": self.length_basis,
            "development_length_mm": self.development_length_mm,
            "lap_length_mm": self.lap_length_mm,
            "region": self.region,
            "source_ref": self.source_ref,
            "shape": {
                "code": self.shape.code,
                "hooks": self.shape.hooks,
                "bends": self.shape.bends,
                "dimensions": [
                    {
                        "name": d.name,
                        "value_mm": d.value_mm,
                        "note": d.note,
                    }
                    for d in self.shape.dimensions
                ],
            },
            "notes": self.notes,
        }


@dataclass
class BBSSchedule:
    project_id: Optional[str] = None
    items: list[BBSItem] = field(default_factory=list)
    revision: int = 1
    notes: list[str] = field(default_factory=list)

    def add(self, item: BBSItem) -> None:
        if not isinstance(item, BBSItem):
            raise TypeError("item must be BBSItem")
        self.items.append(item)

    def extend(self, items: Iterable[BBSItem]) -> None:
        for item in items:
            self.add(item)

    def validate(self, max_stock_length_mm: float = MAX_STOCK_LENGTH_MM) -> list[str]:
        errors: list[str] = []

        for item in self.items:
            if item.length_mm > max_stock_length_mm:
                errors.append(
                    f"{item.mark}: length {item.length_mm:.0f} mm exceeds "
                    f"stock limit {max_stock_length_mm:.0f} mm."
                )

        return errors

    def merge_same_marks(self) -> None:
        merged: dict[tuple[Any, ...], BBSItem] = {}

        for item in self.items:
            key = (
                item.mark,
                item.member_id,
                item.member_type,
                item.floor_id,
                item.bar_mark,
                item.role,
                item.diameter_mm,
                item.grade,
                item.spacing_mm,
                item.length_mm,
                item.region,
                item.source_ref,
            )

            if key in merged:
                merged[key].quantity += item.quantity
            else:
                merged[key] = item

        self.items = list(merged.values())

    def total_length_m(self) -> float:
        return sum(item.total_length_m for item in self.items)

    def summary(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "revision": self.revision,
            "items": len(self.items),
            "total_bars": sum(x.quantity for x in self.items),
            "total_length_m": round(self.total_length_m(), 3),
            "validation_errors": self.validate(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "revision": self.revision,
            "items": [x.to_dict() for x in self.items],
            "notes": list(self.notes),
            "summary": self.summary(),
        }


def create_bbs_item(
    mark: str,
    member_id: str,
    member_type: str,
    bar_mark: str,
    role: str,
    diameter_mm: float,
    grade: str,
    quantity: int,
    length_mm: float,
    *,
    floor_id: Optional[str] = None,
    spacing_mm: Optional[float] = None,
    shape: Optional[BBSShape] = None,
    length_basis: str = "DESIGN",
    development_length_mm: float = 0.0,
    lap_length_mm: float = 0.0,
    region: Optional[str] = None,
    source_ref: Optional[str] = None,
    notes: str = "",
) -> BBSItem:
    return BBSItem(
        mark=mark,
        member_id=member_id,
        member_type=member_type,
        floor_id=floor_id,
        bar_mark=bar_mark,
        role=role,
        diameter_mm=diameter_mm,
        grade=grade,
        quantity=quantity,
        spacing_mm=spacing_mm,
        length_mm=length_mm,
        shape=shape or BBSShape(),
        length_basis=length_basis,
        development_length_mm=development_length_mm,
        lap_length_mm=lap_length_mm,
        region=region,
        source_ref=source_ref,
        notes=notes,
    )


def bbs_to_cut_pieces(
    schedule: BBSSchedule,
    *,
    max_stock_length_mm: float = MAX_STOCK_LENGTH_MM,
):
    from .models import CutPiece

    pieces = []

    for item in schedule.items:
        if item.length_mm > max_stock_length_mm:
            raise ValueError(
                f"{item.mark}: BBS piece exceeds maximum stock length."
            )

        for index in range(item.quantity):
            pieces.append(
                CutPiece(
                    mark=f"{item.mark}-{index + 1}",
                    diameter_mm=item.diameter_mm,
                    grade=item.grade,
                    length_mm=item.length_mm,
                    quantity=1,
                    source_ref=item.source_ref or item.member_id,
                )
            )

    return pieces


def bbs_from_items(
    items: Iterable[BBSItem],
    project_id: Optional[str] = None,
    *,
    merge: bool = True,
) -> BBSSchedule:
    schedule = BBSSchedule(project_id=project_id)
    schedule.extend(items)

    if merge:
        schedule.merge_same_marks()

    return schedule


def validate_bbs(
    schedule: BBSSchedule,
    *,
    max_stock_length_mm: float = MAX_STOCK_LENGTH_MM,
) -> list[str]:
    if not isinstance(schedule, BBSSchedule):
        raise TypeError("schedule must be BBSSchedule")

    return schedule.validate(max_stock_length_mm)


def bbs_summary(schedule: BBSSchedule) -> dict[str, Any]:
    return schedule.summary()


__all__ = [
    "MAX_STOCK_LENGTH_MM",
    "BBSDimension",
    "BBSShape",
    "BBSItem",
    "BBSSchedule",
    "create_bbs_item",
    "bbs_from_items",
    "bbs_to_cut_pieces",
    "validate_bbs",
    "bbs_summary",
]
