"""
StructuralBot - Rebar Cut List

This module converts actual reinforcement pieces from BBS
into optimized stock-bar cutting plans.

Responsibilities:
- Group physical pieces by diameter / grade
- Validate piece lengths
- Optimize pieces into stock bars
- Track used length
- Track waste
- Track reusable leftovers
- Calculate waste percentage
- Generate cutting-plan data
- Provide Telegram/report-ready summaries

Important:
This module does NOT determine engineering reinforcement.
BBS/detailing provides the actual physical pieces.

Flow:

    Engineering Calculation
            ↓
        Detailing
            ↓
           BBS
            ↓
      Physical Pieces
            ↓
         Cut List
            ↓
     12 m Stock Bars
            ↓
       Waste / Leftovers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

DEFAULT_STOCK_LENGTH_M = 12.0
DEFAULT_TOLERANCE_M = 1e-9


# ---------------------------------------------------------
# ERRORS
# ---------------------------------------------------------

class CutListError(Exception):
    """Base exception for Cut List errors."""


class CutListValidationError(CutListError):
    """Raised when Cut List input is invalid."""


class CutListOptimizationError(CutListError):
    """Raised when Cut List optimization cannot be completed."""


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _positive_float(
    value: float,
    field_name: str,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise CutListValidationError(
            f"{field_name} must be numeric."
        ) from exc

    if result <= 0:
        raise CutListValidationError(
            f"{field_name} must be greater than zero."
        )

    return result


def _non_negative_float(
    value: float,
    field_name: str,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise CutListValidationError(
            f"{field_name} must be numeric."
        ) from exc

    if result < 0:
        raise CutListValidationError(
            f"{field_name} cannot be negative."
        )

    return result


def _positive_int(
    value: int,
    field_name: str,
) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise CutListValidationError(
            f"{field_name} must be an integer."
        ) from exc

    if result <= 0:
        raise CutListValidationError(
            f"{field_name} must be greater than zero."
        )

    return result


# ---------------------------------------------------------
# CUT PIECE
# ---------------------------------------------------------

@dataclass
class CutPiece:
    """
    One physical reinforcement piece.

    Example:

        Bar mark: B-016
        Piece no: 1
        Diameter: 16 mm
        Length: 5.80 m
        Shape: 21
    """

    bar_mark: str
    piece_number: int
    diameter: float
    length: float

    shape_code: Optional[str] = None

    grade: Optional[str] = None

    member_id: Optional[int] = None
    member_name: Optional[str] = None

    floor_id: Optional[int] = None
    floor_name: Optional[str] = None

    location: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:

        self.bar_mark = str(
            self.bar_mark
        ).strip()

        if not self.bar_mark:
            raise CutListValidationError(
                "bar_mark cannot be empty."
            )

        self.piece_number = _positive_int(
            self.piece_number,
            "piece_number",
        )

        self.diameter = _positive_float(
            self.diameter,
            "diameter",
        )

        self.length = _positive_float(
            self.length,
            "length",
        )

    @property
    def identifier(self) -> str:
        """
        Unique human-readable piece identifier.
        """

        return (
            f"{self.bar_mark}-"
            f"{self.piece_number:03d}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bar_mark": self.bar_mark,
            "piece_number": self.piece_number,
            "diameter": self.diameter,
            "length": self.length,
            "shape_code": self.shape_code,
            "grade": self.grade,
            "member_id": self.member_id,
            "member_name": self.member_name,
            "floor_id": self.floor_id,
            "floor_name": self.floor_name,
            "location": self.location,
            "metadata": dict(self.metadata),
        }


# ---------------------------------------------------------
# STOCK BAR
# ---------------------------------------------------------

@dataclass
class StockBar:
    """
    One stock reinforcement bar.

    Default commercial stock length is 12 m.

    A StockBar contains multiple physical CutPiece objects.
    """

    stock_id: int
    diameter: float
    stock_length: float = DEFAULT_STOCK_LENGTH_M

    grade: Optional[str] = None

    pieces: List[CutPiece] = field(
        default_factory=list
    )

    used_length: float = 0.0
    leftover_length: float = 0.0

    def __post_init__(self) -> None:

        self.stock_id = _positive_int(
            self.stock_id,
            "stock_id",
        )

        self.diameter = _positive_float(
            self.diameter,
            "diameter",
        )

        self.stock_length = _positive_float(
            self.stock_length,
            "stock_length",
        )

        self.recalculate()

    # -----------------------------------------------------
    # CAPACITY
    # -----------------------------------------------------

    @property
    def remaining_length(self) -> float:
        """
        Remaining usable capacity of the stock bar.
        """

        return max(
            0.0,
            self.stock_length - self.used_length,
        )

    @property
    def utilization_percentage(self) -> float:
        """
        Percentage of stock bar utilized.
        """

        if self.stock_length <= 0:
            return 0.0

        return (
            self.used_length
            / self.stock_length
        ) * 100.0

    # -----------------------------------------------------
    # PIECES
    # -----------------------------------------------------

    def can_fit(
        self,
        piece: CutPiece,
        tolerance: float = DEFAULT_TOLERANCE_M,
    ) -> bool:
        """
        Check whether a physical piece can fit in this stock bar.
        """

        if piece.diameter != self.diameter:
            return False

        if (
            self.grade is not None
            and piece.grade is not None
            and self.grade != piece.grade
        ):
            return False

        return (
            self.used_length
            + piece.length
            <= self.stock_length + tolerance
        )

    def add_piece(
        self,
        piece: CutPiece,
        tolerance: float = DEFAULT_TOLERANCE_M,
    ) -> None:
        """
        Add ONE physical piece.

        IMPORTANT:
        This method deliberately adds only one piece.
        Quantity expansion must happen before reaching Cut List.
        """

        if not self.can_fit(
            piece,
            tolerance=tolerance,
        ):
            raise CutListOptimizationError(
                f"Piece {piece.identifier} "
                f"cannot fit into stock bar "
                f"{self.stock_id}."
            )

        self.pieces.append(piece)

        self.recalculate()

    def recalculate(self) -> None:
        """
        Recalculate used and leftover lengths.
        """

        self.used_length = sum(
            piece.length
            for piece in self.pieces
        )

        self.leftover_length = max(
            0.0,
            self.stock_length - self.used_length,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stock_id": self.stock_id,
            "diameter": self.diameter,
            "grade": self.grade,
            "stock_length": self.stock_length,
            "used_length": self.used_length,
            "leftover_length": self.leftover_length,
            "utilization_percentage": (
                self.utilization_percentage
            ),
            "pieces": [
                piece.to_dict()
                for piece in self.pieces
            ],
        }


# ---------------------------------------------------------
# DIAMETER CUT PLAN
# ---------------------------------------------------------

@dataclass
class DiameterCutPlan:
    """
    Cut List optimization result for one diameter/grade group.
    """

    diameter: float

    stock_length: float = DEFAULT_STOCK_LENGTH_M

    grade: Optional[str] = None

    pieces: List[CutPiece] = field(
        default_factory=list
    )

    stock_bars: List[StockBar] = field(
        default_factory=list
    )

    total_required_length: float = 0.0
    total_stock_length: float = 0.0
    total_waste: float = 0.0
    waste_percentage: float = 0.0

    reusable_leftover: float = 0.0

    def __post_init__(self) -> None:

        self.diameter = _positive_float(
            self.diameter,
            "diameter",
        )

        self.stock_length = _positive_float(
            self.stock_length,
            "stock_length",
        )

        self.recalculate()

    def recalculate(self) -> None:
        """
        Recalculate all summary values.
        """

        self.total_required_length = sum(
            piece.length
            for piece in self.pieces
        )

        self.total_stock_length = sum(
            bar.stock_length
            for bar in self.stock_bars
        )

        self.total_waste = max(
            0.0,
            self.total_stock_length
            - self.total_required_length,
        )

        if self.total_stock_length > 0:
            self.waste_percentage = (
                self.total_waste
                / self.total_stock_length
            ) * 100.0
        else:
            self.waste_percentage = 0.0

        self.reusable_leftover = sum(
            bar.leftover_length
            for bar in self.stock_bars
        )

    @property
    def stock_bar_count(self) -> int:
        return len(self.stock_bars)

    @property
    def piece_count(self) -> int:
        return len(self.pieces)

    @property
    def utilization_percentage(self) -> float:
        if self.total_stock_length <= 0:
            return 0.0

        return (
            self.total_required_length
            / self.total_stock_length
        ) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diameter": self.diameter,
            "grade": self.grade,
            "stock_length": self.stock_length,
            "piece_count": self.piece_count,
            "stock_bar_count": self.stock_bar_count,
            "total_required_length": (
                self.total_required_length
            ),
            "total_stock_length": (
                self.total_stock_length
            ),
            "total_waste": self.total_waste,
            "waste_percentage": (
                self.waste_percentage
            ),
            "reusable_leftover": (
                self.reusable_leftover
            ),
            "utilization_percentage": (
                self.utilization_percentage
            ),
            "stock_bars": [
                bar.to_dict()
                for bar in self.stock_bars
            ],
        }


# ---------------------------------------------------------
# CUT LIST RESULT
# ---------------------------------------------------------

@dataclass
class CutListResult:
    """
    Complete project Cut List result.
    """

    stock_length: float = DEFAULT_STOCK_LENGTH_M

    plans: List[DiameterCutPlan] = field(
        default_factory=list
    )

    project_id: Optional[int] = None
    project_name: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    @property
    def total_stock_bars(self) -> int:
        return sum(
            plan.stock_bar_count
            for plan in self.plans
        )

    @property
    def total_pieces(self) -> int:
        return sum(
            plan.piece_count
            for plan in self.plans
        )

    @property
    def total_required_length(self) -> float:
        return sum(
            plan.total_required_length
            for plan in self.plans
        )

    @property
    def total_stock_length(self) -> float:
        return sum(
            plan.total_stock_length
            for plan in self.plans
        )

    @property
    def total_waste(self) -> float:
        return sum(
            plan.total_waste
            for plan in self.plans
        )

    @property
    def waste_percentage(self) -> float:
        if self.total_stock_length <= 0:
            return 0.0

        return (
            self.total_waste
            / self.total_stock_length
        ) * 100.0

    @property
    def utilization_percentage(self) -> float:
        if self.total_stock_length <= 0:
            return 0.0

        return (
            self.total_required_length
            / self.total_stock_length
        ) * 100.0

    @property
    def reusable_leftover(self) -> float:
        return sum(
            plan.reusable_leftover
            for plan in self.plans
        )

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "stock_length": self.stock_length,
            "total_stock_bars": (
                self.total_stock_bars
            ),
            "total_pieces": self.total_pieces,
            "total_required_length": (
                self.total_required_length
            ),
            "total_stock_length": (
                self.total_stock_length
            ),
            "total_waste": self.total_waste,
            "waste_percentage": (
                self.waste_percentage
            ),
            "utilization_percentage": (
                self.utilization_percentage
            ),
            "reusable_leftover": (
                self.reusable_leftover
            ),
            "plans": [
                plan.to_dict()
                for plan in self.plans
            ],
            "metadata": dict(self.metadata),
        }

    def to_rows(self) -> List[Dict[str, Any]]:
        """
        Flatten Cut List into report-friendly rows.
        """

        rows: List[Dict[str, Any]] = []

        for plan in self.plans:

            for stock_bar in plan.stock_bars:

                piece_details = [
                    {
                        "piece_id": piece.identifier,
                        "bar_mark": piece.bar_mark,
                        "piece_number": (
                            piece.piece_number
                        ),
                        "length_m": piece.length,
                    }
                    for piece in stock_bar.pieces
                ]

                rows.append(
                    {
                        "diameter_mm": plan.diameter,
                        "grade": plan.grade,
                        "stock_id": stock_bar.stock_id,
                        "stock_length_m": (
                            stock_bar.stock_length
                        ),
                        "used_length_m": (
                            stock_bar.used_length
                        ),
                        "leftover_m": (
                            stock_bar.leftover_length
                        ),
                        "utilization_percent": (
                            stock_bar.utilization_percentage
                        ),
                        "pieces": piece_details,
                    }
                )

        return rows


# ---------------------------------------------------------
# PIECE CONVERSION
# ---------------------------------------------------------

def expand_cut_pieces(
    pieces: Iterable[Any],
) -> List[CutPiece]:
    """
    Convert BBS-like records into physical CutPiece objects.

    Supported input styles:

    1. Existing CutPiece objects.

    2. Dict objects containing:
        bar_mark
        piece_number
        diameter
        length

    3. BBS-like objects containing:
        bar_mark
        diameter
        quantity
        piece_length / length

    Quantity is expanded into individual physical pieces.

    This is a critical protection against the classic error:

        quantity × piece_length

    being treated as one oversized piece.
    """

    result: List[CutPiece] = []

    for source in pieces:

        if isinstance(source, CutPiece):
            result.append(source)
            continue

        # -------------------------------------------------
        # DICT INPUT
        # -------------------------------------------------

        if isinstance(source, dict):

            bar_mark = source.get(
                "bar_mark"
            )

            diameter = source.get(
                "diameter"
            )

            length = source.get(
                "piece_length",
                source.get("length"),
            )

            quantity = source.get(
                "quantity",
                1,
            )

            if bar_mark is None:
                raise CutListValidationError(
                    "Missing bar_mark."
                )

            if diameter is None:
                raise CutListValidationError(
                    f"{bar_mark}: missing diameter."
                )

            if length is None:
                raise CutListValidationError(
                    f"{bar_mark}: missing length."
                )

            quantity = _positive_int(
                quantity,
                "quantity",
            )

            for index in range(
                1,
                quantity + 1,
            ):

                result.append(
                    CutPiece(
                        bar_mark=bar_mark,
                        piece_number=index,
                        diameter=diameter,
                        length=length,
                        shape_code=source.get(
                            "shape_code"
                        ),
                        grade=source.get(
                            "grade"
                        ),
                        member_id=source.get(
                            "member_id"
                        ),
                        member_name=source.get(
                            "member_name"
                        ),
                        floor_id=source.get(
                            "floor_id"
                        ),
                        floor_name=source.get(
                            "floor_name"
                        ),
                        location=source.get(
                            "location"
                        ),
                        metadata=source.get(
                            "metadata",
                            {},
                        ),
                    )
                )

            continue

        # -------------------------------------------------
        # OBJECT INPUT
        # -------------------------------------------------

        bar_mark = getattr(
            source,
            "bar_mark",
            None,
        )

        diameter = getattr(
            source,
            "diameter",
            None,
        )

        length = getattr(
            source,
            "piece_length",
            None,
        )

        if length is None:
            length = getattr(
                source,
                "length",
                None,
            )

        quantity = getattr(
            source,
            "quantity",
            1,
        )

        if bar_mark is None:
            raise CutListValidationError(
                "Source object is missing bar_mark."
            )

        if diameter is None:
            raise CutListValidationError(
                f"{bar_mark}: missing diameter."
            )

        if length is None:
            raise CutListValidationError(
                f"{bar_mark}: missing length."
            )

        quantity = _positive_int(
            quantity,
            "quantity",
        )

        for index in range(
            1,
            quantity + 1,
        ):

            result.append(
                CutPiece(
                    bar_mark=bar_mark,
                    piece_number=index,
                    diameter=diameter,
                    length=length,
                    shape_code=getattr(
                        source,
                        "shape_code",
                        None,
                    ),
                    grade=getattr(
                        source,
                        "grade",
                        None,
                    ),
                    member_id=getattr(
                        source,
                        "member_id",
                        None,
                    ),
                    member_name=getattr(
                        source,
                        "member_name",
                        None,
                    ),
                    floor_id=getattr(
                        source,
                        "floor_id",
                        None,
                    ),
                    floor_name=getattr(
                        source,
                        "floor_name",
                        None,
                    ),
                    location=getattr(
                        source,
                        "location",
                        None,
                    ),
                )
            )

    return result


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_cut_piece(
    piece: CutPiece,
    stock_length: float = DEFAULT_STOCK_LENGTH_M,
) -> List[str]:
    """
    Validate a physical reinforcement piece.
    """

    errors: List[str] = []

    if piece.diameter <= 0:
        errors.append(
            f"{piece.identifier}: invalid diameter."
        )

    if piece.length <= 0:
        errors.append(
            f"{piece.identifier}: invalid length."
        )

    if piece.length > stock_length:
        errors.append(
            f"{piece.identifier}: piece length "
            f"{piece.length:.3f} m exceeds "
            f"stock length "
            f"{stock_length:.3f} m."
        )

    return errors


def validate_cut_pieces(
    pieces: Sequence[CutPiece],
    stock_length: float = DEFAULT_STOCK_LENGTH_M,
) -> List[str]:
    """
    Validate a list of physical pieces.
    """

    stock_length = _positive_float(
        stock_length,
        "stock_length",
    )

    errors: List[str] = []

    for piece in pieces:
        errors.extend(
            validate_cut_piece(
                piece,
                stock_length=stock_length,
            )
        )

    return errors


# ---------------------------------------------------------
# GROUPING
# ---------------------------------------------------------

def _group_key(
    piece: CutPiece,
) -> Tuple[Any, ...]:
    """
    Grouping key for stock-bar compatibility.

    Diameter and grade are kept separate.

    In production, additional compatibility rules can be
    added here if the selected material specification requires it.
    """

    return (
        piece.diameter,
        piece.grade,
    )


def group_cut_pieces(
    pieces: Sequence[CutPiece],
) -> Dict[
    Tuple[Any, ...],
    List[CutPiece]
]:
    """
    Group physical pieces by diameter and grade.
    """

    groups: Dict[
        Tuple[Any, ...],
        List[CutPiece]
    ] = {}

    for piece in pieces:

        key = _group_key(piece)

        groups.setdefault(
            key,
            [],
        ).append(piece)

    return groups


# ---------------------------------------------------------
# OPTIMIZATION
# ---------------------------------------------------------

def optimize_diameter_group(
    pieces: Sequence[CutPiece],
    *,
    stock_length: float = DEFAULT_STOCK_LENGTH_M,
    start_stock_id: int = 1,
    strategy: str = "best_fit_decreasing",
) -> DiameterCutPlan:
    """
    Optimize one diameter/grade group.

    Supported strategies:

        best_fit_decreasing
        first_fit_decreasing

    Default:
        best_fit_decreasing

    Why physical pieces are sorted:
        Larger pieces are placed first. This generally
        improves packing efficiency compared with arbitrary
        ordering.

    This is a practical heuristic, not a mathematical guarantee
    of global optimum.
    """

    stock_length = _positive_float(
        stock_length,
        "stock_length",
    )

    if not pieces:
        raise CutListOptimizationError(
            "Cannot optimize an empty piece group."
        )

    strategy = (
        strategy
        .strip()
        .lower()
    )

    if strategy not in {
        "best_fit_decreasing",
        "first_fit_decreasing",
    }:
        raise CutListOptimizationError(
            f"Unsupported Cut List strategy: {strategy}"
        )

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    errors = validate_cut_pieces(
        pieces,
        stock_length=stock_length,
    )

    if errors:
        raise CutListValidationError(
            "\n".join(errors)
        )

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    ordered_pieces = sorted(
        pieces,
        key=lambda piece: piece.length,
        reverse=True,
    )

    diameter = ordered_pieces[0].diameter
    grade = ordered_pieces[0].grade

    plan = DiameterCutPlan(
        diameter=diameter,
        stock_length=stock_length,
        grade=grade,
        pieces=list(ordered_pieces),
    )

    next_stock_id = start_stock_id

    # -----------------------------------------------------
    # PACKING
    # -----------------------------------------------------

    for piece in ordered_pieces:

        compatible_bars = [
            bar
            for bar in plan.stock_bars
            if bar.can_fit(piece)
        ]

        if strategy == "first_fit_decreasing":

            if compatible_bars:
                target_bar = compatible_bars[0]

            else:
                target_bar = StockBar(
                    stock_id=next_stock_id,
                    diameter=diameter,
                    stock_length=stock_length,
                    grade=grade,
                )

                next_stock_id += 1

                plan.stock_bars.append(
                    target_bar
                )

        else:

            # BEST FIT:
            # Choose the bar that leaves the smallest
            # remaining space after placing this piece.
            if compatible_bars:

                target_bar = min(
                    compatible_bars,
                    key=lambda bar: (
                        bar.remaining_length
                        - piece.length
                    ),
                )

            else:

                target_bar = StockBar(
                    stock_id=next_stock_id,
                    diameter=diameter,
                    stock_length=stock_length,
                    grade=grade,
                )

                next_stock_id += 1

                plan.stock_bars.append(
                    target_bar
                )

        target_bar.add_piece(piece)

    plan.recalculate()

    return plan


def optimize_cut_list(
    pieces: Iterable[Any],
    *,
    stock_length: float = DEFAULT_STOCK_LENGTH_M,
    strategy: str = "best_fit_decreasing",
    project_id: Optional[int] = None,
    project_name: Optional[str] = None,
) -> CutListResult:
    """
    Build the complete Cut List.

    Steps:

        1. Expand BBS quantities into physical pieces.
        2. Validate pieces.
        3. Group by diameter/grade.
        4. Optimize each group independently.
        5. Combine into project-level result.
    """

    stock_length = _positive_float(
        stock_length,
        "stock_length",
    )

    physical_pieces = expand_cut_pieces(
        pieces
    )

    if not physical_pieces:
        return CutListResult(
            stock_length=stock_length,
            project_id=project_id,
            project_name=project_name,
        )

    errors = validate_cut_pieces(
        physical_pieces,
        stock_length=stock_length,
    )

    if errors:
        raise CutListValidationError(
            "\n".join(errors)
        )

    groups = group_cut_pieces(
        physical_pieces
    )

    result = CutListResult(
        stock_length=stock_length,
        project_id=project_id,
        project_name=project_name,
    )

    next_stock_id = 1

    for _, group in sorted(
        groups.items(),
        key=lambda item: item[0],
    ):

        plan = optimize_diameter_group(
            group,
            stock_length=stock_length,
            start_stock_id=next_stock_id,
            strategy=strategy,
        )

        result.plans.append(
            plan
        )

        next_stock_id += (
            plan.stock_bar_count
        )

    return result


# ---------------------------------------------------------
# REUSABLE LEFTOVERS
# ---------------------------------------------------------

def get_reusable_leftovers(
    result: CutListResult,
    *,
    minimum_length: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Return leftover pieces that meet the minimum reusable length.

    Leftovers are separated by diameter and grade.

    They can later be fed into an advanced optimizer so that
    compatible future pieces can consume existing leftovers.
    """

    minimum_length = _non_negative_float(
        minimum_length,
        "minimum_length",
    )

    leftovers: List[Dict[str, Any]] = []

    for plan in result.plans:

        for stock_bar in plan.stock_bars:

            if (
                stock_bar.leftover_length
                < minimum_length
            ):
                continue

            leftovers.append(
                {
                    "diameter": plan.diameter,
                    "grade": plan.grade,
                    "stock_id": stock_bar.stock_id,
                    "leftover_length": (
                        stock_bar.leftover_length
                    ),
                }
            )

    return leftovers


# ---------------------------------------------------------
# DIAMETER SUMMARY
# ---------------------------------------------------------

def cut_list_summary_by_diameter(
    result: CutListResult,
) -> Dict[
    float,
    Dict[str, float]
]:
    """
    Return compact summary grouped by diameter.
    """

    summary: Dict[
        float,
        Dict[str, float]
    ] = {}

    for plan in result.plans:

        diameter = plan.diameter

        if diameter not in summary:
            summary[diameter] = {
                "piece_count": 0,
                "stock_bars": 0,
                "required_length": 0.0,
                "stock_length": 0.0,
                "waste": 0.0,
                "waste_percentage": 0.0,
            }

        summary[diameter]["piece_count"] += (
            plan.piece_count
        )

        summary[diameter]["stock_bars"] += (
            plan.stock_bar_count
        )

        summary[diameter]["required_length"] += (
            plan.total_required_length
        )

        summary[diameter]["stock_length"] += (
            plan.total_stock_length
        )

        summary[diameter]["waste"] += (
            plan.total_waste
        )

    for diameter, data in summary.items():

        if data["stock_length"] > 0:

            data["waste_percentage"] = (
                data["waste"]
                / data["stock_length"]
            ) * 100.0

    return summary


# ---------------------------------------------------------
# TELEGRAM SUMMARY
# ---------------------------------------------------------

def cut_list_text_summary(
    result: CutListResult,
) -> str:
    """
    Create a vertical Telegram-friendly summary.

    Intentionally avoids wide horizontal tables.
    """

    lines = [
        "✂️ CUT LIST",
        "",
        f"تعداد قطعات: "
        f"{result.total_pieces:,}",
        f"تعداد شاخه ۱۲ متری: "
        f"{result.total_stock_bars:,}",
        f"طول موردنیاز: "
        f"{result.total_required_length:,.2f} m",
        f"طول شاخه خریداری‌شده: "
        f"{result.total_stock_length:,.2f} m",
        f"پرت کل: "
        f"{result.total_waste:,.2f} m",
        f"درصد پرت: "
        f"{result.waste_percentage:.2f}%",
        "",
    ]

    for plan in result.plans:

        lines.extend(
            [
                (
                    f"🔩 Ø{plan.diameter:g} mm"
                    + (
                        f" | {plan.grade}"
                        if plan.grade
                        else ""
                    )
                ),
                f"قطعات: {plan.piece_count:,}",
                f"شاخه: {plan.stock_bar_count:,}",
                (
                    f"موردنیاز: "
                    f"{plan.total_required_length:,.2f} m"
                ),
                (
                    f"پرت: "
                    f"{plan.total_waste:,.2f} m"
                ),
                (
                    f"درصد پرت: "
                    f"{plan.waste_percentage:.2f}%"
                ),
                "",
            ]
        )

    return "\n".join(lines)


# ---------------------------------------------------------
# DETAILED CUTTING PLAN
# ---------------------------------------------------------

def detailed_cutting_plan(
    result: CutListResult,
) -> List[Dict[str, Any]]:
    """
    Return a detailed cutting plan.

    Each stock bar is represented separately.

    Example:

        {
            "stock_id": 1,
            "diameter": 16,
            "stock_length": 12,
            "cuts": [
                {
                    "piece_id": "B-016-001",
                    "length": 5.8
                },
                ...
            ],
            "used": 11.6,
            "waste": 0.4
        }
    """

    output: List[Dict[str, Any]] = []

    for plan in result.plans:

        for stock_bar in plan.stock_bars:

            output.append(
                {
                    "stock_id": stock_bar.stock_id,
                    "diameter": plan.diameter,
                    "grade": plan.grade,
                    "stock_length": (
                        stock_bar.stock_length
                    ),
                    "cuts": [
                        {
                            "piece_id": piece.identifier,
                            "bar_mark": piece.bar_mark,
                            "piece_number": (
                                piece.piece_number
                            ),
                            "length": piece.length,
                        }
                        for piece in stock_bar.pieces
                    ],
                    "used_length": (
                        stock_bar.used_length
                    ),
                    "waste": (
                        stock_bar.leftover_length
                    ),
                    "utilization_percentage": (
                        stock_bar.utilization_percentage
                    ),
                }
            )

    return output


# ---------------------------------------------------------
# SIMPLE VISUAL PLAN DATA
# ---------------------------------------------------------

def visual_cut_bar(
    stock_bar: StockBar,
) -> Dict[str, Any]:
    """
    Generate normalized coordinates for a visual
    cutting-bar diagram.

    The drawing layer can use these normalized values
    to render a 12 m bar without knowing engineering logic.
    """

    if stock_bar.stock_length <= 0:
        raise CutListValidationError(
            "Invalid stock length."
        )

    current_position = 0.0

    cuts: List[Dict[str, Any]] = []

    for piece in stock_bar.pieces:

        start = current_position

        end = (
            current_position
            + piece.length
        )

        cuts.append(
            {
                "piece_id": piece.identifier,
                "bar_mark": piece.bar_mark,
                "length": piece.length,
                "start": start,
                "end": end,
                "start_ratio": (
                    start
                    / stock_bar.stock_length
                ),
                "end_ratio": (
                    end
                    / stock_bar.stock_length
                ),
            }
        )

        current_position = end

    return {
        "stock_id": stock_bar.stock_id,
        "diameter": stock_bar.diameter,
        "grade": stock_bar.grade,
        "stock_length": stock_bar.stock_length,
        "cuts": cuts,
        "leftover_start": current_position,
        "leftover_length": (
            stock_bar.leftover_length
        ),
        "leftover_ratio": (
            stock_bar.leftover_length
            / stock_bar.stock_length
        ),
    }


def visual_cut_list(
    result: CutListResult,
) -> List[Dict[str, Any]]:
    """
    Generate visual data for all stock bars.
    """

    output: List[Dict[str, Any]] = []

    for plan in result.plans:

        for stock_bar in plan.stock_bars:

            output.append(
                visual_cut_bar(
                    stock_bar
                )
            )

    return output


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

__all__ = [
    "DEFAULT_STOCK_LENGTH_M",
    "DEFAULT_TOLERANCE_M",
    "CutListError",
    "CutListValidationError",
    "CutListOptimizationError",
    "CutPiece",
    "StockBar",
    "DiameterCutPlan",
    "CutListResult",
    "expand_cut_pieces",
    "validate_cut_piece",
    "validate_cut_pieces",
    "group_cut_pieces",
    "optimize_diameter_group",
    "optimize_cut_list",
    "get_reusable_leftovers",
    "cut_list_summary_by_diameter",
    "cut_list_text_summary",
    "detailed_cutting_plan",
    "visual_cut_bar",
    "visual_cut_list",
]
