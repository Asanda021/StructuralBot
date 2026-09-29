"""
StructuralBot - Quantity Takeoff Engine

This module handles:
- Material quantity aggregation
- Project-level quantity summaries
- Member-level quantity summaries
- Floor-level quantity summaries
- Rebar quantity aggregation
- BBS to quantity conversion
- Cut List to quantity conversion
- Telegram-friendly summaries

IMPORTANT:
This module does NOT perform structural design.

Geometry-based material calculations belong to the relevant
structural calculation modules.

This module only stores, normalizes, aggregates, and summarizes
already-calculated quantities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

from core.validation import (
    ValidationError,
    validate_positive_number,
    validate_non_negative_number,
)


# ============================================================
# MATERIAL TYPES
# ============================================================

MATERIAL_CONCRETE = "concrete"
MATERIAL_REBAR = "rebar"
MATERIAL_POLYSTYRENE = "polystyrene"
MATERIAL_BLOCK = "block"
MATERIAL_JOIST = "joist"
MATERIAL_FORMWORK = "formwork"
MATERIAL_COUPLER = "coupler"
MATERIAL_OTHER = "other"


SUPPORTED_MATERIALS = {
    MATERIAL_CONCRETE,
    MATERIAL_REBAR,
    MATERIAL_POLYSTYRENE,
    MATERIAL_BLOCK,
    MATERIAL_JOIST,
    MATERIAL_FORMWORK,
    MATERIAL_COUPLER,
    MATERIAL_OTHER,
}


# ============================================================
# QUANTITY ITEM
# ============================================================

@dataclass
class QuantityItem:
    """
    Represents one material quantity.

    Examples:

        Concrete:
            quantity=12.5
            unit="m3"

        Rebar:
            quantity=850
            unit="kg"

        Polystyrene:
            quantity=120
            unit="piece"
    """

    material_type: str

    quantity: float

    unit: str

    member_id: Optional[int] = None
    floor_id: Optional[int] = None

    member_name: Optional[str] = None
    floor_name: Optional[str] = None

    description: str = ""

    diameter: Optional[float] = None
    grade: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.material_type not in SUPPORTED_MATERIALS:
            raise ValidationError(
                f"Unsupported material type: {self.material_type}"
            )

        validate_positive_number(
            self.quantity,
            field_name="quantity",
        )

        if not self.unit or not self.unit.strip():
            raise ValidationError(
                "Quantity unit cannot be empty."
            )

        self.unit = self.unit.strip()

    def key(self) -> tuple:
        """
        Aggregation key.

        Quantities are only merged when:
        - material type is identical
        - unit is identical
        - diameter is identical
        - grade is identical
        """

        return (
            self.material_type,
            self.unit,
            self.diameter,
            self.grade,
        )


# ============================================================
# QUANTITY GROUP
# ============================================================

@dataclass
class QuantityGroup:
    """
    Aggregated quantities belonging to the same material category.
    """

    material_type: str

    unit: str

    total_quantity: float = 0.0

    items: List[QuantityItem] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def add(
        self,
        item: QuantityItem,
    ) -> None:
        """
        Add one quantity item to the group.
        """

        if (
            item.material_type != self.material_type
            or item.unit != self.unit
        ):
            raise ValidationError(
                "Quantity item does not match group."
            )

        self.items.append(item)
        self.total_quantity += item.quantity

    def rounded_total(
        self,
        digits: int = 3,
    ) -> float:
        """
        Return rounded total quantity.
        """

        return round(
            self.total_quantity,
            digits,
        )


# ============================================================
# QUANTITY TAKEOFF
# ============================================================

@dataclass
class QuantityTakeoff:
    """
    Main quantity aggregation container.

    It can hold quantities for:
    - one member
    - one floor
    - an entire project
    """

    project_id: Optional[int] = None

    items: List[QuantityItem] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    # --------------------------------------------------------
    # ADD
    # --------------------------------------------------------

    def add(
        self,
        item: QuantityItem,
    ) -> None:
        """
        Add a quantity item.
        """

        self.items.append(item)

    def add_many(
        self,
        items: Iterable[QuantityItem],
    ) -> None:
        """
        Add multiple quantity items.
        """

        for item in items:
            self.add(item)

    # --------------------------------------------------------
    # FILTERING
    # --------------------------------------------------------

    def filter_by_material(
        self,
        material_type: str,
    ) -> List[QuantityItem]:
        """
        Return all items for a material type.
        """

        return [
            item
            for item in self.items
            if item.material_type == material_type
        ]

    def filter_by_member(
        self,
        member_id: int,
    ) -> List[QuantityItem]:
        """
        Return all quantities belonging to a member.
        """

        return [
            item
            for item in self.items
            if item.member_id == member_id
        ]

    def filter_by_floor(
        self,
        floor_id: int,
    ) -> List[QuantityItem]:
        """
        Return all quantities belonging to a floor.
        """

        return [
            item
            for item in self.items
            if item.floor_id == floor_id
        ]

    # --------------------------------------------------------
    # AGGREGATION
    # --------------------------------------------------------

    def group(
        self,
    ) -> List[QuantityGroup]:
        """
        Aggregate quantities by:
            material type
            unit
            diameter
            grade
        """

        groups: Dict[tuple, QuantityGroup] = {}

        for item in self.items:
            key = item.key()

            if key not in groups:
                groups[key] = QuantityGroup(
                    material_type=item.material_type,
                    unit=item.unit,
                    metadata={
                        "diameter": item.diameter,
                        "grade": item.grade,
                    },
                )

            groups[key].add(item)

        return list(groups.values())

    def total(
        self,
        material_type: str,
        unit: Optional[str] = None,
    ) -> float:
        """
        Return total quantity for a material type.

        If unit is specified, only that unit is included.
        """

        total_quantity = 0.0

        for item in self.items:
            if item.material_type != material_type:
                continue

            if unit is not None and item.unit != unit:
                continue

            total_quantity += item.quantity

        return total_quantity

    # --------------------------------------------------------
    # MEMBER SUMMARY
    # --------------------------------------------------------

    def member_summary(
        self,
        member_id: int,
    ) -> Dict[str, float]:
        """
        Return material totals for a member.
        """

        result: Dict[str, float] = {}

        for item in self.filter_by_member(member_id):
            key = f"{item.material_type}:{item.unit}"

            result[key] = (
                result.get(key, 0.0)
                + item.quantity
            )

        return result

    # --------------------------------------------------------
    # FLOOR SUMMARY
    # --------------------------------------------------------

    def floor_summary(
        self,
        floor_id: int,
    ) -> Dict[str, float]:
        """
        Return material totals for a floor.
        """

        result: Dict[str, float] = {}

        for item in self.filter_by_floor(floor_id):
            key = f"{item.material_type}:{item.unit}"

            result[key] = (
                result.get(key, 0.0)
                + item.quantity
            )

        return result

    # --------------------------------------------------------
    # PROJECT SUMMARY
    # --------------------------------------------------------

    def project_summary(
        self,
    ) -> Dict[str, float]:
        """
        Return project-level material totals.
        """

        result: Dict[str, float] = {}

        for item in self.items:
            key = f"{item.material_type}:{item.unit}"

            result[key] = (
                result.get(key, 0.0)
                + item.quantity
            )

        return result

    # --------------------------------------------------------
    # REBAR SUMMARY
    # --------------------------------------------------------

    def rebar_summary(
        self,
    ) -> Dict[float, float]:
        """
        Return total rebar quantity by diameter.

        Returns:
            {
                12.0: 125.5,
                16.0: 840.2,
                20.0: 1250.7
            }

        The values are expected to be in the unit stored
        on the quantity items, normally kg.
        """

        result: Dict[float, float] = {}

        for item in self.items:
            if item.material_type != MATERIAL_REBAR:
                continue

            if item.diameter is None:
                continue

            diameter = float(item.diameter)

            result[diameter] = (
                result.get(diameter, 0.0)
                + item.quantity
            )

        return dict(
            sorted(
                result.items(),
                key=lambda pair: pair[0],
            )
        )

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    def to_rows(self) -> List[List[Any]]:
        """
        Convert quantities to table rows.

        Suitable for Excel/PDF generation.
        """

        rows: List[List[Any]] = []

        for index, item in enumerate(
            self.items,
            start=1,
        ):
            rows.append(
                [
                    index,
                    item.material_type,
                    item.description,
                    item.quantity,
                    item.unit,
                    item.diameter,
                    item.grade,
                    item.member_name,
                    item.floor_name,
                ]
            )

        return rows

    def to_dicts(self) -> List[Dict[str, Any]]:
        """
        Convert quantities to dictionaries.
        """

        result: List[Dict[str, Any]] = []

        for item in self.items:
            result.append(
                {
                    "material_type": item.material_type,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "member_id": item.member_id,
                    "floor_id": item.floor_id,
                    "member_name": item.member_name,
                    "floor_name": item.floor_name,
                    "description": item.description,
                    "diameter": item.diameter,
                    "grade": item.grade,
                    "metadata": dict(item.metadata),
                }
            )

        return result


# ============================================================
# FACTORY HELPERS
# ============================================================

def create_concrete_quantity(
    volume_m3: float,
    *,
    member_id: Optional[int] = None,
    floor_id: Optional[int] = None,
    member_name: Optional[str] = None,
    floor_name: Optional[str] = None,
    description: str = "",
) -> QuantityItem:
    """
    Create a concrete quantity.
    """

    validate_positive_number(
        volume_m3,
        field_name="concrete volume",
    )

    return QuantityItem(
        material_type=MATERIAL_CONCRETE,
        quantity=float(volume_m3),
        unit="m3",
        member_id=member_id,
        floor_id=floor_id,
        member_name=member_name,
        floor_name=floor_name,
        description=description,
    )


def create_rebar_quantity(
    weight_kg: float,
    *,
    diameter: Optional[float] = None,
    grade: Optional[str] = None,
    member_id: Optional[int] = None,
    floor_id: Optional[int] = None,
    member_name: Optional[str] = None,
    floor_name: Optional[str] = None,
    description: str = "",
) -> QuantityItem:
    """
    Create a reinforcement quantity.
    """

    validate_positive_number(
        weight_kg,
        field_name="rebar weight",
    )

    return QuantityItem(
        material_type=MATERIAL_REBAR,
        quantity=float(weight_kg),
        unit="kg",
        member_id=member_id,
        floor_id=floor_id,
        member_name=member_name,
        floor_name=floor_name,
        description=description,
        diameter=diameter,
        grade=grade,
    )


def create_piece_quantity(
    material_type: str,
    quantity: float,
    *,
    member_id: Optional[int] = None,
    floor_id: Optional[int] = None,
    member_name: Optional[str] = None,
    floor_name: Optional[str] = None,
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> QuantityItem:
    """
    Create a piece-based material quantity.

    Examples:
        polystyrene
        block
        joist
        coupler
    """

    if material_type not in SUPPORTED_MATERIALS:
        raise ValidationError(
            f"Unsupported material type: {material_type}"
        )

    validate_positive_number(
        quantity,
        field_name="piece quantity",
    )

    return QuantityItem(
        material_type=material_type,
        quantity=float(quantity),
        unit="piece",
        member_id=member_id,
        floor_id=floor_id,
        member_name=member_name,
        floor_name=floor_name,
        description=description,
        metadata=metadata or {},
    )


def create_formwork_quantity(
    area_m2: float,
    *,
    member_id: Optional[int] = None,
    floor_id: Optional[int] = None,
    member_name: Optional[str] = None,
    floor_name: Optional[str] = None,
    description: str = "",
) -> QuantityItem:
    """
    Create formwork quantity.
    """

    validate_positive_number(
        area_m2,
        field_name="formwork area",
    )

    return QuantityItem(
        material_type=MATERIAL_FORMWORK,
        quantity=float(area_m2),
        unit="m2",
        member_id=member_id,
        floor_id=floor_id,
        member_name=member_name,
        floor_name=floor_name,
        description=description,
    )


# ============================================================
# BBS CONVERSION
# ============================================================

def quantities_from_bbs(
    bbs_schedule: Any,
    *,
    member_id: Optional[int] = None,
    floor_id: Optional[int] = None,
    member_name: Optional[str] = None,
    floor_name: Optional[str] = None,
) -> QuantityTakeoff:
    """
    Convert a BBS schedule into rebar quantities.

    Expected BBS item properties:
        diameter
        quantity
        total_length
        weight

    The function intentionally accepts Any so that the BBS module
    remains loosely coupled to this module.
    """

    takeoff = QuantityTakeoff()

    items = getattr(
        bbs_schedule,
        "items",
        [],
    )

    for bbs_item in items:
        diameter = getattr(
            bbs_item,
            "diameter",
            None,
        )

        quantity = getattr(
            bbs_item,
            "quantity",
            0,
        )

        total_length = getattr(
            bbs_item,
            "total_length",
            None,
        )

        weight = getattr(
            bbs_item,
            "weight",
            None,
        )

        if weight is None:
            continue

        if weight <= 0:
            continue

        bar_mark = getattr(
            bbs_item,
            "bar_mark",
            "",
        )

        bar_type = getattr(
            bbs_item,
            "bar_type",
            "",
        )

        grade = getattr(
            bbs_item,
            "grade",
            None,
        )

        description = (
            f"{bar_mark}"
            f"{' - ' + bar_type if bar_type else ''}"
        )

        metadata = {
            "source": "bbs",
            "quantity": quantity,
            "total_length": total_length,
            "bar_mark": bar_mark,
        }

        takeoff.add(
            create_rebar_quantity(
                float(weight),
                diameter=diameter,
                grade=grade,
                member_id=member_id,
                floor_id=floor_id,
                member_name=member_name,
                floor_name=floor_name,
                description=description,
            )
        )

        takeoff.items[-1].metadata.update(
            metadata
        )

    return takeoff


# ============================================================
# CUT LIST CONVERSION
# ============================================================

def quantities_from_cut_list(
    cut_list: Any,
    *,
    member_id: Optional[int] = None,
    floor_id: Optional[int] = None,
    member_name: Optional[str] = None,
    floor_name: Optional[str] = None,
) -> QuantityTakeoff:
    """
    Convert Cut List information into rebar quantities.

    Expected:
        diameter
        quantity
        piece_length
        total_weight OR weight

    If total weight is not directly available, the function
    attempts to calculate it using the reinforcement module.
    """

    takeoff = QuantityTakeoff()

    plans = getattr(
        cut_list,
        "plans",
        None,
    )

    if plans is None:
        plans = getattr(
            cut_list,
            "diameter_plans",
            [],
        )

    for plan in plans:
        diameter = getattr(
            plan,
            "diameter",
            None,
        )

        grade = getattr(
            plan,
            "grade",
            None,
        )

        pieces = getattr(
            plan,
            "pieces",
            [],
        )

        plan_weight = getattr(
            plan,
            "total_weight",
            None,
        )

        if plan_weight is not None:
            if plan_weight > 0:
                takeoff.add(
                    create_rebar_quantity(
                        float(plan_weight),
                        diameter=diameter,
                        grade=grade,
                        member_id=member_id,
                        floor_id=floor_id,
                        member_name=member_name,
                        floor_name=floor_name,
                        description="Cut List",
                    )
                )

            continue

        # ----------------------------------------------------
        # FALLBACK: calculate from physical pieces
        # ----------------------------------------------------

        total_weight = 0.0

        for piece in pieces:
            piece_length = getattr(
                piece,
                "length",
                None,
            )

            quantity = getattr(
                piece,
                "quantity",
                1,
            )

            if (
                piece_length is None
                or diameter is None
            ):
                continue

            try:
                from core.reinforcement import (
                    rebar_weight_per_meter,
                )

                kg_per_meter = (
                    rebar_weight_per_meter(
                        float(diameter)
                    )
                )

                total_weight += (
                    float(piece_length)
                    * float(quantity)
                    * kg_per_meter
                )

            except (
                ImportError,
                ValueError,
                TypeError,
            ):
                continue

        if total_weight > 0:
            takeoff.add(
                create_rebar_quantity(
                    total_weight,
                    diameter=diameter,
                    grade=grade,
                    member_id=member_id,
                    floor_id=floor_id,
                    member_name=member_name,
                    floor_name=floor_name,
                    description="Cut List",
                )
            )

    return takeoff


# ============================================================
# MERGE
# ============================================================

def merge_takeoffs(
    *takeoffs: QuantityTakeoff,
) -> QuantityTakeoff:
    """
    Merge multiple quantity takeoffs.

    Useful for:
        foundation + columns + beams + slabs
    """

    merged = QuantityTakeoff()

    for takeoff in takeoffs:
        if takeoff is None:
            continue

        merged.add_many(
            takeoff.items
        )

    return merged


# ============================================================
# VALIDATION
# ============================================================

def validate_quantity_item(
    item: QuantityItem,
) -> List[str]:
    """
    Validate a quantity item.

    Returns a list of errors.
    """

    errors: List[str] = []

    if item.material_type not in SUPPORTED_MATERIALS:
        errors.append(
            f"Unsupported material type: "
            f"{item.material_type}"
        )

    if item.quantity <= 0:
        errors.append(
            "Quantity must be greater than zero."
        )

    if not item.unit:
        errors.append(
            "Quantity unit cannot be empty."
        )

    if (
        item.diameter is not None
        and item.diameter <= 0
    ):
        errors.append(
            "Rebar diameter must be greater than zero."
        )

    return errors


def validate_takeoff(
    takeoff: QuantityTakeoff,
) -> List[str]:
    """
    Validate the complete quantity takeoff.
    """

    errors: List[str] = []

    for index, item in enumerate(
        takeoff.items,
        start=1,
    ):
        item_errors = validate_quantity_item(
            item
        )

        for error in item_errors:
            errors.append(
                f"Item {index}: {error}"
            )

    return errors


def ensure_valid_takeoff(
    takeoff: QuantityTakeoff,
) -> None:
    """
    Raise ValidationError if the takeoff is invalid.
    """

    errors = validate_takeoff(
        takeoff
    )

    if errors:
        raise ValidationError(
            "\n".join(errors)
        )


# ============================================================
# TELEGRAM SUMMARY
# ============================================================

MATERIAL_LABELS_FA = {
    MATERIAL_CONCRETE: "🧱 بتن",
    MATERIAL_REBAR: "🔩 میلگرد",
    MATERIAL_POLYSTYRENE: "🟨 یونولیت",
    MATERIAL_BLOCK: "🧱 بلوک",
    MATERIAL_JOIST: "📏 تیرچه",
    MATERIAL_FORMWORK: "🪵 قالب‌بندی",
    MATERIAL_COUPLER: "🔗 کوپلر",
    MATERIAL_OTHER: "📦 سایر مصالح",
}


def telegram_summary(
    takeoff: QuantityTakeoff,
    *,
    title: str = "🧮 برآورد مصالح",
    digits: int = 2,
) -> str:
    """
    Generate a concise Telegram-friendly quantity summary.
    """

    ensure_valid_takeoff(
        takeoff
    )

    lines: List[str] = [
        title,
        "",
    ]

    groups = takeoff.group()

    if not groups:
        lines.append(
            "موردی برای نمایش وجود ندارد."
        )
        return "\n".join(lines)

    # --------------------------------------------------------
    # Rebar grouped by diameter
    # --------------------------------------------------------

    rebar_groups = [
        group
        for group in groups
        if group.material_type == MATERIAL_REBAR
    ]

    if rebar_groups:
        lines.append(
            MATERIAL_LABELS_FA[MATERIAL_REBAR]
        )

        for group in rebar_groups:
            diameter = group.metadata.get(
                "diameter"
            )

            grade = group.metadata.get(
                "grade"
            )

            label = (
                f"Ø{diameter:g}"
                if isinstance(
                    diameter,
                    (int, float),
                )
                else "نامشخص"
            )

            if grade:
                label += f" | {grade}"

            lines.append(
                f"• {label}: "
                f"{group.total_quantity:.{digits}f} "
                f"{group.unit}"
            )

        lines.append("")

    # --------------------------------------------------------
    # Other materials
    # --------------------------------------------------------

    for group in groups:
        if group.material_type == MATERIAL_REBAR:
            continue

        label = MATERIAL_LABELS_FA.get(
            group.material_type,
            group.material_type,
        )

        lines.append(
            f"{label}: "
            f"{group.total_quantity:.{digits}f} "
            f"{group.unit}"
        )

    return "\n".join(lines)


# ============================================================
# PROJECT TOTALS
# ============================================================

def project_material_totals(
    takeoff: QuantityTakeoff,
) -> Dict[str, Dict[str, float]]:
    """
    Return totals grouped by material and unit.

    Example:
        {
            "concrete": {
                "m3": 120.5
            },
            "rebar": {
                "kg": 8500.0
            }
        }
    """

    result: Dict[
        str,
        Dict[str, float],
    ] = {}

    for item in takeoff.items:
        material = item.material_type

        if material not in result:
            result[material] = {}

        result[material][item.unit] = (
            result[material].get(
                item.unit,
                0.0,
            )
            + item.quantity
        )

    return result


# ============================================================
# MEMBER TOTALS
# ============================================================

def member_material_totals(
    takeoff: QuantityTakeoff,
    member_id: int,
) -> Dict[str, Dict[str, float]]:
    """
    Return material totals for a member.
    """

    filtered = takeoff.filter_by_member(
        member_id
    )

    temporary = QuantityTakeoff(
        project_id=takeoff.project_id,
        items=filtered,
    )

    return project_material_totals(
        temporary
    )


# ============================================================
# FLOOR TOTALS
# ============================================================

def floor_material_totals(
    takeoff: QuantityTakeoff,
    floor_id: int,
) -> Dict[str, Dict[str, float]]:
    """
    Return material totals for a floor.
    """

    filtered = takeoff.filter_by_floor(
        floor_id
    )

    temporary = QuantityTakeoff(
        project_id=takeoff.project_id,
        items=filtered,
    )

    return project_material_totals(
        temporary
    )


# ============================================================
# REBAR TOTAL WEIGHT
# ============================================================

def total_rebar_weight(
    takeoff: QuantityTakeoff,
) -> float:
    """
    Return total reinforcement weight in kg.

    Only quantities with:
        material_type = rebar
        unit = kg

    are included.
    """

    return sum(
        item.quantity
        for item in takeoff.items
        if (
            item.material_type
            == MATERIAL_REBAR
            and item.unit == "kg"
        )
    )


# ============================================================
# CONCRETE TOTAL VOLUME
# ============================================================

def total_concrete_volume(
    takeoff: QuantityTakeoff,
) -> float:
    """
    Return total concrete volume in m3.
    """

    return sum(
        item.quantity
        for item in takeoff.items
        if (
            item.material_type
            == MATERIAL_CONCRETE
            and item.unit == "m3"
        )
    )


# ============================================================
# QUANTITY SUMMARY DICT
# ============================================================

def summary_dict(
    takeoff: QuantityTakeoff,
) -> Dict[str, Any]:
    """
    Create a structured summary suitable for:
        - API
        - database
        - reports
        - AI
        - Telegram
    """

    return {
        "project_id": takeoff.project_id,
        "item_count": len(takeoff.items),
        "concrete_m3": round(
            total_concrete_volume(
                takeoff
            ),
            3,
        ),
        "rebar_kg": round(
            total_rebar_weight(
                takeoff
            ),
            3,
        ),
        "rebar_by_diameter": {
            str(diameter): round(
                weight,
                3,
            )
            for diameter, weight
            in takeoff.rebar_summary().items()
        },
        "materials": project_material_totals(
            takeoff
        ),
    }


# ============================================================
# MODULE EXPORTS
# ============================================================

__all__ = [
    # Material constants
    "MATERIAL_CONCRETE",
    "MATERIAL_REBAR",
    "MATERIAL_POLYSTYRENE",
    "MATERIAL_BLOCK",
    "MATERIAL_JOIST",
    "MATERIAL_FORMWORK",
    "MATERIAL_COUPLER",
    "MATERIAL_OTHER",
    "SUPPORTED_MATERIALS",

    # Data classes
    "QuantityItem",
    "QuantityGroup",
    "QuantityTakeoff",

    # Factory helpers
    "create_concrete_quantity",
    "create_rebar_quantity",
    "create_piece_quantity",
    "create_formwork_quantity",

    # Converters
    "quantities_from_bbs",
    "quantities_from_cut_list",

    # Aggregation
    "merge_takeoffs",
    "project_material_totals",
    "member_material_totals",
    "floor_material_totals",

    # Validation
    "validate_quantity_item",
    "validate_takeoff",
    "ensure_valid_takeoff",

    # Totals
    "total_rebar_weight",
    "total_concrete_volume",

    # Output
    "telegram_summary",
    "summary_dict",
]
