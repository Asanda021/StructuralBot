"""
StructuralBot - Engineering Pipeline QA

Validates the high-level deterministic engineering data flow:

Member
  -> Calculation
  -> Reinforcement
  -> BBS
  -> Cut List
  -> Quantities

This test intentionally avoids Telegram, AI, billing and payment layers.
"""

from __future__ import annotations

import math

import pytest

from core.bbs import (
    BBSDimension,
    BBSItem,
    BBSShape,
    BBSSchedule,
    bbs_to_cut_pieces,
)
from core.cutlist import (
    build_cut_list,
    calculate_total_cut_length,
    calculate_total_weight,
)
from core.quantities import (
    QuantityTakeoff,
    quantities_from_bbs,
)
from core.reinforcement import (
    ReinforcementCollection,
    create_rebar,
    rebar_weight_per_meter,
)
from core.models import (
    MemberType,
    ReinforcementType,
    ReinforcementBar,
    StructuralMember,
    RectangularGeometry,
)


# ---------------------------------------------------------------------------
# BASIC CONSTANTS
# ---------------------------------------------------------------------------

TOLERANCE = 1e-6


# ---------------------------------------------------------------------------
# REINFORCEMENT
# ---------------------------------------------------------------------------

def test_rebar_weight_per_meter() -> None:
    """
    Verify the standard theoretical steel-weight relationship.
    """

    weight = rebar_weight_per_meter(16)

    expected = 16 * 16 / 162.0

    assert math.isclose(
        weight,
        expected,
        rel_tol=1e-9,
        abs_tol=TOLERANCE,
    )


def test_create_rebar_returns_valid_bar() -> None:
    """
    Verify creation of a standard reinforcement bar.
    """

    bar = create_rebar(
        diameter=16,
        length=5.0,
        quantity=4,
        role="main",
    )

    assert bar.diameter == 16
    assert bar.length == 5.0
    assert bar.quantity == 4
    assert bar.role == "main"

    assert bar.weight > 0


def test_reinforcement_collection() -> None:
    """
    Verify multiple reinforcement bars can be collected.
    """

    collection = ReinforcementCollection()

    first = create_rebar(
        diameter=16,
        length=5.0,
        quantity=4,
        role="main",
    )

    second = create_rebar(
        diameter=8,
        length=1.2,
        quantity=12,
        role="stirrup",
    )

    collection.add(first)
    collection.add(second)

    assert len(collection) == 2

    total_weight = collection.total_weight()

    assert total_weight > 0


# ---------------------------------------------------------------------------
# BBS
# ---------------------------------------------------------------------------

def _build_sample_bbs() -> BBSSchedule:
    """
    Build a deterministic sample BBS schedule.
    """

    shape = BBSShape(
        code="B01",
        name="Straight Bar",
        dimensions=[
            BBSDimension(
                name="L",
                value=5.0,
                unit="m",
            )
        ],
    )

    item = BBSItem(
        mark="B01",
        diameter=16,
        quantity=4,
        shape=shape,
        length=5.0,
        unit_weight=rebar_weight_per_meter(16),
        total_weight=(
            4
            * 5.0
            * rebar_weight_per_meter(16)
        ),
        member_id="BEAM-01",
        role="main",
    )

    schedule = BBSSchedule(
        project_id="PROJECT-01",
        items=[item],
    )

    return schedule


def test_bbs_schedule_creation() -> None:
    """
    Verify BBS schedule contains expected data.
    """

    schedule = _build_sample_bbs()

    assert len(schedule.items) == 1

    item = schedule.items[0]

    assert item.mark == "B01"
    assert item.diameter == 16
    assert item.quantity == 4
    assert item.length == 5.0


def test_bbs_to_cut_pieces() -> None:
    """
    BBS quantity must become physical cut pieces.
    """

    schedule = _build_sample_bbs()

    pieces = bbs_to_cut_pieces(schedule)

    assert len(pieces) == 4

    for piece in pieces:
        assert piece.diameter == 16
        assert piece.length == 5.0


# ---------------------------------------------------------------------------
# CUT LIST
# ---------------------------------------------------------------------------

def test_cut_list_never_creates_oversized_stock_piece() -> None:
    """
    Four 5 m pieces require multiple 12 m stock bars.
    """

    schedule = _build_sample_bbs()

    pieces = bbs_to_cut_pieces(schedule)

    result = build_cut_list(
        pieces,
        stock_length=12.0,
    )

    assert result is not None

    for stock_bar in result.stock_bars:
        assert stock_bar.length <= 12.0 + TOLERANCE

        for piece in stock_bar.pieces:
            assert piece.length <= 12.0 + TOLERANCE


def test_cut_list_piece_count_is_preserved() -> None:
    """
    Optimization must never lose or duplicate physical pieces.
    """

    schedule = _build_sample_bbs()

    pieces = bbs_to_cut_pieces(schedule)

    result = build_cut_list(
        pieces,
        stock_length=12.0,
    )

    optimized_pieces = [
        piece
        for stock_bar in result.stock_bars
        for piece in stock_bar.pieces
    ]

    assert len(optimized_pieces) == len(pieces)

    original_lengths = sorted(
        round(piece.length, 6)
        for piece in pieces
    )

    optimized_lengths = sorted(
        round(piece.length, 6)
        for piece in optimized_pieces
    )

    assert optimized_lengths == original_lengths


def test_cut_list_total_length() -> None:
    """
    Total cut length must equal the sum of all physical pieces.
    """

    schedule = _build_sample_bbs()

    pieces = bbs_to_cut_pieces(schedule)

    expected = 4 * 5.0

    total = calculate_total_cut_length(pieces)

    assert math.isclose(
        total,
        expected,
        rel_tol=1e-9,
        abs_tol=TOLERANCE,
    )


def test_cut_list_weight_is_positive() -> None:
    """
    Cut-list steel weight must be positive.
    """

    schedule = _build_sample_bbs()

    pieces = bbs_to_cut_pieces(schedule)

    weight = calculate_total_weight(pieces)

    assert weight > 0


# ---------------------------------------------------------------------------
# QUANTITIES
# ---------------------------------------------------------------------------

def test_quantities_from_bbs() -> None:
    """
    BBS data should generate a material quantity takeoff.
    """

    schedule = _build_sample_bbs()

    takeoff = quantities_from_bbs(schedule)

    assert takeoff is not None

    assert isinstance(
        takeoff,
        QuantityTakeoff,
    )

    assert len(takeoff.items) > 0


def test_quantity_takeoff_can_be_summarized() -> None:
    """
    Quantity takeoff should expose usable totals.
    """

    schedule = _build_sample_bbs()

    takeoff = quantities_from_bbs(schedule)

    total_weight = takeoff.total_rebar_weight()

    assert total_weight > 0


# ---------------------------------------------------------------------------
# END-TO-END
# ---------------------------------------------------------------------------

def test_full_rebar_data_pipeline() -> None:
    """
    Complete deterministic pipeline:

        BBS
         ↓
        physical pieces
         ↓
        cut list
         ↓
        quantities

    The number of physical pieces and total cut length
    must remain consistent throughout the pipeline.
    """

    schedule = _build_sample_bbs()

    pieces = bbs_to_cut_pieces(schedule)

    assert len(pieces) == 4

    cut_list = build_cut_list(
        pieces,
        stock_length=12.0,
    )

    assert cut_list is not None

    optimized_pieces = [
        piece
        for stock_bar in cut_list.stock_bars
        for piece in stock_bar.pieces
    ]

    assert len(optimized_pieces) == 4

    total_length_before = calculate_total_cut_length(
        pieces
    )

    total_length_after = calculate_total_cut_length(
        optimized_pieces
    )

    assert math.isclose(
        total_length_before,
        total_length_after,
        rel_tol=1e-9,
        abs_tol=TOLERANCE,
    )

    takeoff = quantities_from_bbs(schedule)

    assert takeoff.total_rebar_weight() > 0


# ---------------------------------------------------------------------------
# ENGINEERING SANITY
# ---------------------------------------------------------------------------

@pytest.mark.engineering
def test_standard_rebar_weight_is_reasonable() -> None:
    """
    Basic engineering sanity check for 16 mm reinforcement.
    """

    weight = rebar_weight_per_meter(16)

    assert 1.5 < weight < 1.7


@pytest.mark.engineering
def test_standard_stock_length_constraint() -> None:
    """
    Standard commercial stock length used by the project
    must remain 12 m unless explicitly overridden.
    """

    schedule = _build_sample_bbs()

    pieces = bbs_to_cut_pieces(schedule)

    result = build_cut_list(pieces)

    for stock_bar in result.stock_bars:
        assert stock_bar.length <= 12.0 + TOLERANCE
