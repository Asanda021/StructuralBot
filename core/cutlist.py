from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from .models import CutPiece


MAX_STOCK_LENGTH_MM = 12000.0


class CutListError(Exception):
    pass


class CutListValidationError(CutListError):
    pass


@dataclass
class StockBar:
    stock_id: str
    diameter_mm: float
    grade: str
    length_mm: float = MAX_STOCK_LENGTH_MM
    pieces: list[CutPiece] = field(default_factory=list)

    def __post_init__(self):
        self.diameter_mm = float(self.diameter_mm)
        self.length_mm = float(self.length_mm)

        if self.diameter_mm <= 0:
            raise ValueError("Stock diameter must be positive.")
        if self.length_mm <= 0:
            raise ValueError("Stock length must be positive.")

    @property
    def used_length_mm(self) -> float:
        return sum(float(piece.length_mm) for piece in self.pieces)

    @property
    def waste_mm(self) -> float:
        return max(0.0, self.length_mm - self.used_length_mm)

    def can_fit(self, piece: CutPiece) -> bool:
        if float(piece.diameter_mm) != self.diameter_mm:
            return False
        if str(piece.grade) != str(self.grade):
            return False
        return self.used_length_mm + float(piece.length_mm) <= self.length_mm + 1e-9

    def add_piece(self, piece: CutPiece) -> bool:
        if not self.can_fit(piece):
            return False
        self.pieces.append(piece)
        return True


@dataclass
class CutListResult:
    pieces: list[CutPiece] = field(default_factory=list)
    stock_bars: list[StockBar] = field(default_factory=list)
    unassigned: list[CutPiece] = field(default_factory=list)

    @property
    def total_required_length_mm(self) -> float:
        return sum(float(x.length_mm) * int(x.quantity) for x in self.pieces)

    @property
    def total_stock_length_mm(self) -> float:
        return sum(x.length_mm for x in self.stock_bars)

    @property
    def total_waste_mm(self) -> float:
        return sum(x.waste_mm for x in self.stock_bars)

    @property
    def waste_percent(self) -> float:
        if self.total_stock_length_mm <= 0:
            return 0.0
        return 100.0 * self.total_waste_mm / self.total_stock_length_mm

    def summary(self) -> dict[str, Any]:
        return {
            "piece_types": len(self.pieces),
            "stock_bars": len(self.stock_bars),
            "unassigned": len(self.unassigned),
            "required_length_m": round(
                self.total_required_length_mm / 1000.0, 3
            ),
            "stock_length_m": round(
                self.total_stock_length_mm / 1000.0, 3
            ),
            "waste_m": round(self.total_waste_mm / 1000.0, 3),
            "waste_percent": round(self.waste_percent, 2),
        }


def expand_cut_pieces(
    pieces: Iterable[CutPiece],
    *,
    max_stock_length_mm: float = MAX_STOCK_LENGTH_MM,
) -> list[CutPiece]:
    result: list[CutPiece] = []

    for piece in pieces:
        length = float(piece.length_mm)
        quantity = int(piece.quantity)

        if quantity < 1:
            raise CutListValidationError(
                f"{piece.mark}: quantity must be at least 1."
            )

        if length <= 0:
            raise CutListValidationError(
                f"{piece.mark}: length must be positive."
            )

        if length > max_stock_length_mm:
            raise CutListValidationError(
                f"{piece.mark}: piece length {length:.0f} mm exceeds "
                f"{max_stock_length_mm:.0f} mm."
            )

        for index in range(quantity):
            result.append(
                CutPiece(
                    mark=f"{piece.mark}-{index + 1}",
                    diameter_mm=piece.diameter_mm,
                    grade=piece.grade,
                    length_mm=piece.length_mm,
                    quantity=1,
                    source_ref=getattr(piece, "source_ref", None),
                )
            )

    return result


def _piece_sort_key(piece: CutPiece):
    return (
        -float(piece.length_mm),
        float(piece.diameter_mm),
        str(piece.grade),
        str(piece.mark),
    )


def optimize_cut_list(
    pieces: Iterable[CutPiece],
    *,
    stock_length_mm: float = MAX_STOCK_LENGTH_MM,
) -> CutListResult:
    if stock_length_mm <= 0:
        raise ValueError("Stock length must be positive.")

    expanded = expand_cut_pieces(
        pieces,
        max_stock_length_mm=stock_length_mm,
    )

    expanded.sort(key=_piece_sort_key)

    result = CutListResult(pieces=list(pieces))

    stock_counter = 1

    for piece in expanded:
        placed = False

        compatible = [
            bar
            for bar in result.stock_bars
            if bar.can_fit(piece)
        ]

        compatible.sort(key=lambda x: x.waste_mm)

        for bar in compatible:
            if bar.add_piece(piece):
                placed = True
                break

        if not placed:
            bar = StockBar(
                stock_id=f"SB-{stock_counter:04d}",
                diameter_mm=piece.diameter_mm,
                grade=piece.grade,
                length_mm=stock_length_mm,
            )
            stock_counter += 1

            if not bar.add_piece(piece):
                result.unassigned.append(piece)
            else:
                result.stock_bars.append(bar)

    return result


def validate_cut_list(
    pieces: Iterable[CutPiece],
    *,
    max_stock_length_mm: float = MAX_STOCK_LENGTH_MM,
) -> list[str]:
    errors: list[str] = []

    for piece in pieces:
        length = float(piece.length_mm)
        quantity = int(piece.quantity)

        if quantity < 1:
            errors.append(f"{piece.mark}: invalid quantity.")

        if length <= 0:
            errors.append(f"{piece.mark}: invalid length.")

        if length > max_stock_length_mm:
            errors.append(
                f"{piece.mark}: {length:.0f} mm exceeds "
                f"{max_stock_length_mm:.0f} mm stock length."
            )

    return errors


def cutlist_from_bbs(schedule, *, stock_length_mm: float = MAX_STOCK_LENGTH_MM):
    from .bbs import bbs_to_cut_pieces

    pieces = bbs_to_cut_pieces(
        schedule,
        max_stock_length_mm=stock_length_mm,
    )

    return optimize_cut_list(
        pieces,
        stock_length_mm=stock_length_mm,
    )


def cutlist_summary(result: CutListResult) -> dict[str, Any]:
    return result.summary()


__all__ = [
    "MAX_STOCK_LENGTH_MM",
    "CutListError",
    "CutListValidationError",
    "StockBar",
    "CutListResult",
    "expand_cut_pieces",
    "optimize_cut_list",
    "validate_cut_list",
    "cutlist_from_bbs",
    "cutlist_summary",
]
