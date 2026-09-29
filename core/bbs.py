"""
StructuralBot - Bar Bending Schedule (BBS)

This module is responsible for:
- BBS item creation
- Rebar shape information
- Bar marks
- Piece length calculation
- Total length calculation
- Weight calculation
- Grouping and summarizing reinforcement
- Export-ready BBS data

Important:
This module does NOT decide engineering reinforcement requirements.
Those decisions belong to calculation and code/detailing modules.

BBS converts engineering reinforcement results into actual
reinforcement pieces suitable for schedules, reports and Cut List.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .reinforcement import (
    calculate_rebar_weight,
    rebar_weight_per_meter,
)


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

DEFAULT_STOCK_LENGTH_M = 12.0


# ---------------------------------------------------------
# ERRORS
# ---------------------------------------------------------

class BBSError(Exception):
    """Base exception for BBS-related errors."""


class BBSValidationError(BBSError):
    """Raised when BBS input data is invalid."""


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _positive_number(
    value: float,
    field_name: str,
) -> float:
    """
    Validate a positive numeric value.
    """

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise BBSValidationError(
            f"{field_name} must be a numeric value."
        ) from exc

    if number <= 0:
        raise BBSValidationError(
            f"{field_name} must be greater than zero."
        )

    return number


def _positive_integer(
    value: int,
    field_name: str,
) -> int:
    """
    Validate a positive integer.
    """

    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise BBSValidationError(
            f"{field_name} must be an integer."
        ) from exc

    if number <= 0:
        raise BBSValidationError(
            f"{field_name} must be greater than zero."
        )

    return number


def _normalize_diameter(
    diameter: float,
) -> float:
    """
    Normalize reinforcement diameter to mm.
    """

    return _positive_number(
        diameter,
        "diameter",
    )


def _normalize_length(
    length: float,
) -> float:
    """
    Normalize length to meters.
    """

    return _positive_number(
        length,
        "piece_length",
    )


# ---------------------------------------------------------
# BBS DIMENSION
# ---------------------------------------------------------

@dataclass(frozen=True)
class BBSDimension:
    """
    One dimension of a reinforcement shape.

    Example:

        A = 4.80 m
        B = 0.20 m
        C = 4.80 m
    """

    name: str
    value: float
    unit: str = "m"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise BBSValidationError(
                "Dimension name cannot be empty."
            )

        _positive_number(
            self.value,
            f"dimension {self.name}",
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
        }


# ---------------------------------------------------------
# BBS SHAPE
# ---------------------------------------------------------

@dataclass
class BBSShape:
    """
    Parametric reinforcement shape.

    shape_code:
        Engineering / bending shape identifier.

    dimensions:
        A/B/C/... dimensions of the actual bar.

    total_length:
        Developed length of one physical piece.

    The exact developed-length calculation should be supplied
    by the detailing/code layer when bends, hooks and radii
    require code-specific treatment.
    """

    shape_code: str
    dimensions: List[BBSDimension] = field(default_factory=list)
    total_length: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.shape_code = str(self.shape_code).strip()

        if not self.shape_code:
            raise BBSValidationError(
                "shape_code cannot be empty."
            )

        if self.total_length is not None:
            _positive_number(
                self.total_length,
                "total_length",
            )

    def add_dimension(
        self,
        name: str,
        value: float,
        unit: str = "m",
    ) -> None:
        """
        Add a dimension to the shape.
        """

        self.dimensions.append(
            BBSDimension(
                name=name,
                value=value,
                unit=unit,
            )
        )

    def get_dimension(
        self,
        name: str,
    ) -> Optional[BBSDimension]:
        """
        Return a dimension by name.
        """

        normalized = name.strip().upper()

        for dimension in self.dimensions:
            if dimension.name.strip().upper() == normalized:
                return dimension

        return None

    def dimension_map(self) -> Dict[str, float]:
        """
        Return dimensions as:

            {"A": 4.8, "B": 0.2, "C": 4.8}
        """

        return {
            dimension.name: dimension.value
            for dimension in self.dimensions
        }

    def calculate_total_length(
        self,
        fallback_sum: bool = True,
    ) -> float:
        """
        Calculate developed length.

        If total_length is already explicitly supplied,
        it is returned.

        Otherwise, when fallback_sum=True, the sum of the
        parametric dimensions is used.

        NOTE:
        For production code compliance, the preferred value
        should come from the detailing/code layer, especially
        for bends, hooks and bend radii.
        """

        if self.total_length is not None:
            return float(self.total_length)

        if not fallback_sum:
            raise BBSValidationError(
                "Shape total length has not been calculated."
            )

        if not self.dimensions:
            raise BBSValidationError(
                "Shape has no dimensions."
            )

        length = sum(
            dimension.value
            for dimension in self.dimensions
            if dimension.unit == "m"
        )

        if length <= 0:
            raise BBSValidationError(
                "Calculated shape length must be greater than zero."
            )

        self.total_length = length

        return length

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shape_code": self.shape_code,
            "dimensions": [
                dimension.to_dict()
                for dimension in self.dimensions
            ],
            "total_length": self.total_length,
            "metadata": dict(self.metadata),
        }


# ---------------------------------------------------------
# BBS ITEM
# ---------------------------------------------------------

@dataclass
class BBSItem:
    """
    One BBS row.

    A BBS item represents one reinforcement definition.

    Example:

        Mark: B-016
        Diameter: Ø16
        Shape: 21
        Quantity: 24
        Piece length: 5.80 m
        Total length: 139.20 m
        Weight: ...
    """

    bar_mark: str
    diameter: float
    quantity: int
    piece_length: float

    bar_type: str = "longitudinal"
    grade: Optional[str] = None

    shape: Optional[BBSShape] = None

    member_id: Optional[int] = None
    member_name: Optional[str] = None
    member_type: Optional[str] = None
    floor_id: Optional[int] = None
    floor_name: Optional[str] = None

    location: Optional[str] = None
    description: Optional[str] = None

    total_length: Optional[float] = None
    total_weight: Optional[float] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.bar_mark = str(self.bar_mark).strip()

        if not self.bar_mark:
            raise BBSValidationError(
                "bar_mark cannot be empty."
            )

        self.diameter = _normalize_diameter(
            self.diameter
        )

        self.quantity = _positive_integer(
            self.quantity,
            "quantity",
        )

        self.piece_length = _normalize_length(
            self.piece_length
        )

        self.calculate_totals()

    # -----------------------------------------------------
    # CALCULATIONS
    # -----------------------------------------------------

    def calculate_totals(self) -> None:
        """
        Calculate total length and total weight.
        """

        if self.shape is not None:
            shape_length = self.shape.calculate_total_length()

            # The BBS item length is the actual physical
            # piece length. Shape data is therefore allowed
            # to supply it when explicitly calculated.
            self.piece_length = shape_length

        self.total_length = (
            self.piece_length * self.quantity
        )

        self.total_weight = calculate_rebar_weight(
            diameter_mm=self.diameter,
            length_m=self.total_length,
        )

    def weight_per_meter(self) -> float:
        """
        Return kg/m for the selected diameter.
        """

        return rebar_weight_per_meter(
            self.diameter
        )

    # -----------------------------------------------------
    # UPDATE
    # -----------------------------------------------------

    def update_quantity(
        self,
        quantity: int,
    ) -> None:
        """
        Update quantity and recalculate totals.
        """

        self.quantity = _positive_integer(
            quantity,
            "quantity",
        )

        self.calculate_totals()

    def update_piece_length(
        self,
        piece_length: float,
    ) -> None:
        """
        Update physical piece length and recalculate totals.
        """

        self.piece_length = _normalize_length(
            piece_length
        )

        if self.shape is not None:
            self.shape.total_length = self.piece_length

        self.calculate_totals()

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bar_mark": self.bar_mark,
            "diameter": self.diameter,
            "quantity": self.quantity,
            "piece_length": self.piece_length,
            "bar_type": self.bar_type,
            "grade": self.grade,
            "shape": (
                self.shape.to_dict()
                if self.shape is not None
                else None
            ),
            "member_id": self.member_id,
            "member_name": self.member_name,
            "member_type": self.member_type,
            "floor_id": self.floor_id,
            "floor_name": self.floor_name,
            "location": self.location,
            "description": self.description,
            "total_length": self.total_length,
            "total_weight": self.total_weight,
            "metadata": dict(self.metadata),
        }


# ---------------------------------------------------------
# BBS SCHEDULE
# ---------------------------------------------------------

class BBSSchedule:
    """
    Collection of BBS items.

    This class provides:
    - adding items
    - removing items
    - searching by mark
    - grouping
    - project summaries
    - diameter summaries
    - member summaries
    - export-ready data
    """

    def __init__(
        self,
        project_id: Optional[int] = None,
        project_name: Optional[str] = None,
    ) -> None:

        self.project_id = project_id
        self.project_name = project_name

        self.items: List[BBSItem] = []

    # -----------------------------------------------------
    # BASIC OPERATIONS
    # -----------------------------------------------------

    def add_item(
        self,
        item: BBSItem,
    ) -> BBSItem:
        """
        Add a BBS item.

        Bar marks should normally be unique inside one
        schedule.
        """

        if not isinstance(item, BBSItem):
            raise TypeError(
                "item must be an instance of BBSItem."
            )

        if self.get_item(item.bar_mark) is not None:
            raise BBSValidationError(
                f"Duplicate bar mark: {item.bar_mark}"
            )

        self.items.append(item)

        return item

    def add(
        self,
        bar_mark: str,
        diameter: float,
        quantity: int,
        piece_length: float,
        **kwargs: Any,
    ) -> BBSItem:
        """
        Convenience method for creating and adding an item.
        """

        item = BBSItem(
            bar_mark=bar_mark,
            diameter=diameter,
            quantity=quantity,
            piece_length=piece_length,
            **kwargs,
        )

        return self.add_item(item)

    def remove_item(
        self,
        bar_mark: str,
    ) -> bool:
        """
        Remove an item by bar mark.
        """

        for index, item in enumerate(self.items):
            if item.bar_mark == bar_mark:
                del self.items[index]
                return True

        return False

    def get_item(
        self,
        bar_mark: str,
    ) -> Optional[BBSItem]:
        """
        Find an item by bar mark.
        """

        for item in self.items:
            if item.bar_mark == bar_mark:
                return item

        return None

    def clear(self) -> None:
        """
        Remove all BBS items.
        """

        self.items.clear()

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    # -----------------------------------------------------
    # FILTERING
    # -----------------------------------------------------

    def filter_by_diameter(
        self,
        diameter: float,
    ) -> List[BBSItem]:
        """
        Return all items for a diameter.
        """

        diameter = _normalize_diameter(diameter)

        return [
            item
            for item in self.items
            if item.diameter == diameter
        ]

    def filter_by_member(
        self,
        member_id: int,
    ) -> List[BBSItem]:
        """
        Return all items belonging to a member.
        """

        return [
            item
            for item in self.items
            if item.member_id == member_id
        ]

    def filter_by_floor(
        self,
        floor_id: int,
    ) -> List[BBSItem]:
        """
        Return all items belonging to a floor.
        """

        return [
            item
            for item in self.items
            if item.floor_id == floor_id
        ]

    def filter_by_bar_type(
        self,
        bar_type: str,
    ) -> List[BBSItem]:
        """
        Return items by reinforcement type.
        """

        normalized = bar_type.strip().lower()

        return [
            item
            for item in self.items
            if item.bar_type.strip().lower() == normalized
        ]

    # -----------------------------------------------------
    # SORTING
    # -----------------------------------------------------

    def sorted_items(
        self,
        by: str = "bar_mark",
    ) -> List[BBSItem]:
        """
        Return sorted BBS items without changing original order.
        """

        if by == "diameter":
            return sorted(
                self.items,
                key=lambda item: (
                    item.diameter,
                    item.bar_mark,
                ),
            )

        if by == "quantity":
            return sorted(
                self.items,
                key=lambda item: (
                    item.quantity,
                    item.bar_mark,
                ),
            )

        if by == "piece_length":
            return sorted(
                self.items,
                key=lambda item: (
                    item.piece_length,
                    item.bar_mark,
                ),
            )

        if by == "weight":
            return sorted(
                self.items,
                key=lambda item: (
                    item.total_weight or 0,
                    item.bar_mark,
                ),
            )

        return sorted(
            self.items,
            key=lambda item: item.bar_mark,
        )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    def total_rebar_length(self) -> float:
        """
        Total reinforcement length in meters.
        """

        return sum(
            item.total_length or 0
            for item in self.items
        )

    def total_rebar_weight(self) -> float:
        """
        Total reinforcement weight in kilograms.
        """

        return sum(
            item.total_weight or 0
            for item in self.items
        )

    def total_piece_count(self) -> int:
        """
        Total number of physical reinforcement pieces.
        """

        return sum(
            item.quantity
            for item in self.items
        )

    def summary_by_diameter(
        self,
    ) -> Dict[float, Dict[str, float]]:
        """
        Group BBS quantities by diameter.

        Example:

        {
            16: {
                "piece_count": 24,
                "length": 120.5,
                "weight": 190.2
            }
        }
        """

        result: Dict[
            float,
            Dict[str, float]
        ] = {}

        for item in self.items:

            if item.diameter not in result:
                result[item.diameter] = {
                    "piece_count": 0,
                    "length": 0.0,
                    "weight": 0.0,
                }

            result[item.diameter]["piece_count"] += (
                item.quantity
            )

            result[item.diameter]["length"] += (
                item.total_length or 0.0
            )

            result[item.diameter]["weight"] += (
                item.total_weight or 0.0
            )

        return result

    def summary_by_member(
        self,
    ) -> Dict[str, Dict[str, float]]:
        """
        Group reinforcement by member.
        """

        result: Dict[
            str,
            Dict[str, float]
        ] = {}

        for item in self.items:

            key = (
                item.member_name
                or (
                    str(item.member_id)
                    if item.member_id is not None
                    else "unknown"
                )
            )

            if key not in result:
                result[key] = {
                    "piece_count": 0,
                    "length": 0.0,
                    "weight": 0.0,
                }

            result[key]["piece_count"] += (
                item.quantity
            )

            result[key]["length"] += (
                item.total_length or 0.0
            )

            result[key]["weight"] += (
                item.total_weight or 0.0
            )

        return result

    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Convert complete BBS schedule to a serializable dict.
        """

        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "item_count": len(self.items),
            "total_piece_count": self.total_piece_count(),
            "total_length": self.total_rebar_length(),
            "total_weight": self.total_rebar_weight(),
            "items": [
                item.to_dict()
                for item in self.items
            ],
        }

    def to_rows(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Return flat rows suitable for Excel/PDF generation.

        This is intentionally independent from the report layer.
        """

        rows: List[Dict[str, Any]] = []

        for item in self.sorted_items("bar_mark"):

            dimensions = {}

            if item.shape is not None:
                dimensions = item.shape.dimension_map()

            rows.append(
                {
                    "bar_mark": item.bar_mark,
                    "diameter_mm": item.diameter,
                    "bar_type": item.bar_type,
                    "grade": item.grade,
                    "shape_code": (
                        item.shape.shape_code
                        if item.shape is not None
                        else None
                    ),
                    "quantity": item.quantity,
                    "piece_length_m": item.piece_length,
                    "total_length_m": item.total_length,
                    "weight_kg": item.total_weight,
                    "member": item.member_name,
                    "member_type": item.member_type,
                    "floor": item.floor_name,
                    "location": item.location,
                    "description": item.description,
                    "dimensions": dimensions,
                }
            )

        return rows


# ---------------------------------------------------------
# BBS FACTORY FUNCTIONS
# ---------------------------------------------------------

def create_bbs_item(
    bar_mark: str,
    diameter: float,
    quantity: int,
    piece_length: float,
    *,
    bar_type: str = "longitudinal",
    grade: Optional[str] = None,
    shape_code: Optional[str] = None,
    dimensions: Optional[
        Sequence[Tuple[str, float]]
    ] = None,
    member_id: Optional[int] = None,
    member_name: Optional[str] = None,
    member_type: Optional[str] = None,
    floor_id: Optional[int] = None,
    floor_name: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> BBSItem:
    """
    Create a BBS item from simple parameters.
    """

    shape: Optional[BBSShape] = None

    if shape_code is not None:

        shape = BBSShape(
            shape_code=shape_code,
        )

        if dimensions:
            for name, value in dimensions:
                shape.add_dimension(
                    name=name,
                    value=value,
                )

        # The explicitly supplied physical piece length
        # remains authoritative.
        shape.total_length = piece_length

    return BBSItem(
        bar_mark=bar_mark,
        diameter=diameter,
        quantity=quantity,
        piece_length=piece_length,
        bar_type=bar_type,
        grade=grade,
        shape=shape,
        member_id=member_id,
        member_name=member_name,
        member_type=member_type,
        floor_id=floor_id,
        floor_name=floor_name,
        location=location,
        description=description,
        metadata=metadata or {},
    )


def create_bbs_from_reinforcement(
    reinforcement_items: Iterable[Any],
) -> BBSSchedule:
    """
    Build a BBS schedule from reinforcement-like objects.

    The function intentionally accepts generic objects rather
    than tightly coupling BBS to one particular database model.

    Expected attributes:

        bar_mark
        diameter
        quantity
        length
        bar_type
        grade
        shape_code
        shape_data
        member_id
        member_name
        member_type
        floor_id
        floor_name
        location

    Missing optional attributes are handled safely.
    """

    schedule = BBSSchedule()

    for reinforcement in reinforcement_items:

        bar_mark = getattr(
            reinforcement,
            "bar_mark",
            None,
        )

        diameter = getattr(
            reinforcement,
            "diameter",
            None,
        )

        quantity = getattr(
            reinforcement,
            "quantity",
            None,
        )

        piece_length = getattr(
            reinforcement,
            "length",
            None,
        )

        if bar_mark is None:
            raise BBSValidationError(
                "Reinforcement item is missing bar_mark."
            )

        if diameter is None:
            raise BBSValidationError(
                f"Reinforcement {bar_mark} is missing diameter."
            )

        if quantity is None:
            raise BBSValidationError(
                f"Reinforcement {bar_mark} is missing quantity."
            )

        if piece_length is None:
            raise BBSValidationError(
                f"Reinforcement {bar_mark} is missing length."
            )

        shape_code = getattr(
            reinforcement,
            "shape_code",
            None,
        )

        shape_data = getattr(
            reinforcement,
            "shape_data",
            None,
        )

        dimensions = None

        if isinstance(shape_data, dict):
            dimensions = [
                (str(name), float(value))
                for name, value in shape_data.items()
                if isinstance(value, (int, float))
            ]

        item = create_bbs_item(
            bar_mark=bar_mark,
            diameter=diameter,
            quantity=quantity,
            piece_length=piece_length,
            bar_type=getattr(
                reinforcement,
                "bar_type",
                "longitudinal",
            ),
            grade=getattr(
                reinforcement,
                "grade",
                None,
            ),
            shape_code=shape_code,
            dimensions=dimensions,
            member_id=getattr(
                reinforcement,
                "member_id",
                None,
            ),
            member_name=getattr(
                reinforcement,
                "member_name",
                None,
            ),
            member_type=getattr(
                reinforcement,
                "member_type",
                None,
            ),
            floor_id=getattr(
                reinforcement,
                "floor_id",
                None,
            ),
            floor_name=getattr(
                reinforcement,
                "floor_name",
                None,
            ),
            location=getattr(
                reinforcement,
                "location",
                None,
            ),
        )

        schedule.add_item(item)

    return schedule


# ---------------------------------------------------------
# BBS MERGING
# ---------------------------------------------------------

def merge_bbs_items(
    items: Sequence[BBSItem],
    *,
    merge_same_geometry: bool = False,
) -> List[BBSItem]:
    """
    Merge compatible BBS items.

    By default only exact bar-mark duplicates are considered
    compatible.

    If merge_same_geometry=True, items with the same physical
    properties may be merged.

    NOTE:
    Bar marks are engineering identifiers. Automatic merging
    should therefore be used carefully.
    """

    if not items:
        return []

    if not merge_same_geometry:
        result: Dict[str, BBSItem] = {}

        for item in items:

            if item.bar_mark not in result:
                result[item.bar_mark] = item
                continue

            existing = result[item.bar_mark]

            if (
                existing.diameter != item.diameter
                or existing.piece_length != item.piece_length
                or existing.bar_type != item.bar_type
            ):
                raise BBSValidationError(
                    "Cannot merge BBS items with the same "
                    f"bar mark but different properties: "
                    f"{item.bar_mark}"
                )

            existing.quantity += item.quantity
            existing.calculate_totals()

        return list(result.values())

    grouped: Dict[
        Tuple[Any, ...],
        BBSItem
    ] = {}

    for item in items:

        key = (
            item.diameter,
            item.quantity,
            item.piece_length,
            item.bar_type,
            item.grade,
            (
                item.shape.shape_code
                if item.shape is not None
                else None
            ),
            item.member_id,
            item.floor_id,
            item.location,
        )

        if key not in grouped:
            grouped[key] = item
            continue

        existing = grouped[key]

        existing.quantity += item.quantity
        existing.calculate_totals()

    return list(grouped.values())


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_bbs_item(
    item: BBSItem,
    stock_length_m: float = DEFAULT_STOCK_LENGTH_M,
) -> List[str]:
    """
    Validate one BBS item.

    Returns a list of warnings/errors.

    Engineering decision rules are intentionally not implemented
    here.
    """

    errors: List[str] = []

    if item.quantity <= 0:
        errors.append(
            f"{item.bar_mark}: quantity must be positive."
        )

    if item.diameter <= 0:
        errors.append(
            f"{item.bar_mark}: diameter must be positive."
        )

    if item.piece_length <= 0:
        errors.append(
            f"{item.bar_mark}: piece length must be positive."
        )

    if item.piece_length > stock_length_m:
        errors.append(
            f"{item.bar_mark}: piece length "
            f"{item.piece_length:.3f} m exceeds "
            f"stock length {stock_length_m:.3f} m."
        )

    return errors


def validate_schedule(
    schedule: BBSSchedule,
    stock_length_m: float = DEFAULT_STOCK_LENGTH_M,
) -> List[str]:
    """
    Validate an entire BBS schedule.
    """

    errors: List[str] = []

    if stock_length_m <= 0:
        errors.append(
            "Stock length must be greater than zero."
        )
        return errors

    for item in schedule:
        errors.extend(
            validate_bbs_item(
                item,
                stock_length_m=stock_length_m,
            )
        )

    return errors


# ---------------------------------------------------------
# REPORT HELPERS
# ---------------------------------------------------------

def bbs_text_summary(
    schedule: BBSSchedule,
) -> str:
    """
    Create a compact text summary suitable for Telegram.
    """

    lines = [
        "📋 BBS | لیستوفر میلگرد",
        "",
        f"تعداد آیتم‌ها: {len(schedule)}",
        f"تعداد قطعات: {schedule.total_piece_count():,}",
        f"طول کل: {schedule.total_rebar_length():,.2f} m",
        f"وزن کل: {schedule.total_rebar_weight():,.2f} kg",
        "",
    ]

    for item in schedule.sorted_items("bar_mark"):

        lines.extend(
            [
                f"🔹 {item.bar_mark}",
                f"قطر: Ø{item.diameter:g} mm",
                f"تعداد: {item.quantity:,}",
                f"طول هر قطعه: {item.piece_length:.2f} m",
                f"طول کل: {item.total_length:.2f} m",
                f"وزن: {item.total_weight:.2f} kg",
                "",
            ]
        )

    return "\n".join(lines)


# ---------------------------------------------------------
# CUT LIST INPUT
# ---------------------------------------------------------

def bbs_to_cut_pieces(
    schedule: BBSSchedule,
) -> List[Dict[str, Any]]:
    """
    Convert BBS items into physical piece records for Cut List.

    IMPORTANT:
    This function expands quantities into individual physical
    pieces.

    Example:

        BBS:
            Ø16
            quantity = 4
            piece length = 5.8 m

        becomes:

            4 physical pieces × 5.8 m

    This avoids the common error of treating
    quantity × length as one oversized piece.
    """

    pieces: List[Dict[str, Any]] = []

    for item in schedule:

        for index in range(1, item.quantity + 1):

            pieces.append(
                {
                    "bar_mark": item.bar_mark,
                    "piece_number": index,
                    "diameter": item.diameter,
                    "length": item.piece_length,
                    "shape_code": (
                        item.shape.shape_code
                        if item.shape is not None
                        else None
                    ),
                    "member_id": item.member_id,
                    "member_name": item.member_name,
                    "floor_id": item.floor_id,
                    "floor_name": item.floor_name,
                    "location": item.location,
                }
            )

    return pieces


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

__all__ = [
    "DEFAULT_STOCK_LENGTH_M",
    "BBSError",
    "BBSValidationError",
    "BBSDimension",
    "BBSShape",
    "BBSItem",
    "BBSSchedule",
    "create_bbs_item",
    "create_bbs_from_reinforcement",
    "merge_bbs_items",
    "validate_bbs_item",
    "validate_schedule",
    "bbs_text_summary",
    "bbs_to_cut_pieces",
]
