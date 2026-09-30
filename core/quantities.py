from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from .models import MaterialQuantity


@dataclass
class QuantitySummary:
    items: list[MaterialQuantity] = field(default_factory=list)

    def add(self, item: MaterialQuantity) -> None:
        self.items.append(item)

    @property
    def concrete_m3(self) -> float:
        return sum(
            float(x.quantity)
            for x in self.items
            if str(x.material).lower() in {"concrete", "بتن"}
        )

    @property
    def steel_kg(self) -> float:
        return sum(
            float(x.quantity)
            for x in self.items
            if str(x.material).lower() in {
                "steel", "rebar", "reinforcement", "فولاد", "میلگرد"
            }
        )

    def by_material(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for item in self.items:
            key = str(item.material)
            result[key] = result.get(key, 0.0) + float(item.quantity)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [
                {
                    "material": x.material,
                    "quantity": x.quantity,
                    "unit": x.unit,
                    "source_ref": getattr(x, "source_ref", None),
                }
                for x in self.items
            ],
            "by_material": self.by_material(),
            "concrete_m3": self.concrete_m3,
            "steel_kg": self.steel_kg,
        }


def add_quantity(
    result: QuantitySummary,
    material: str,
    quantity: float,
    unit: str,
    source_ref: Optional[str] = None,
) -> MaterialQuantity:
    item = MaterialQuantity(
        material=material,
        quantity=float(quantity),
        unit=unit,
        source_ref=source_ref,
    )
    result.add(item)
    return item


def calculate_concrete_volume(
    length_m: float,
    width_m: float,
    thickness_m: float,
) -> float:
    values = (float(length_m), float(width_m), float(thickness_m))
    if any(x <= 0 for x in values):
        raise ValueError("Concrete dimensions must be positive.")
    return values[0] * values[1] * values[2]


def calculate_rebar_weight(
    diameter_mm: float,
    length_m: float,
    quantity: int = 1,
) -> float:
    d = float(diameter_mm)
    l = float(length_m)
    q = int(quantity)

    if d <= 0 or l <= 0 or q < 1:
        raise ValueError("Invalid rebar dimensions or quantity.")

    unit_weight = d * d / 162.0
    return unit_weight * l * q


def summarize_material_quantities(
    items: Iterable[MaterialQuantity],
) -> QuantitySummary:
    result = QuantitySummary()
    for item in items:
        result.add(item)
    return result


def calculate_project_quantities(
    concrete_volumes: Iterable[float] = (),
    rebar_items: Iterable[tuple[float, float, int]] = (),
) -> QuantitySummary:
    result = QuantitySummary()

    concrete_total = sum(float(x) for x in concrete_volumes)
    if concrete_total > 0:
        add_quantity(result, "concrete", concrete_total, "m3")

    steel_total = 0.0
    for diameter, length_m, quantity in rebar_items:
        steel_total += calculate_rebar_weight(
            diameter,
            length_m,
            quantity,
        )

    if steel_total > 0:
        add_quantity(result, "rebar", steel_total, "kg")

    return result


__all__ = [
    "QuantitySummary",
    "add_quantity",
    "calculate_concrete_volume",
    "calculate_rebar_weight",
    "summarize_material_quantities",
    "calculate_project_quantities",
]
