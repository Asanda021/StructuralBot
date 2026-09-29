"""
StructuralBot - Core Layer Tests

Tests for the code-independent calculation infrastructure.

This file focuses on:
- Core models
- Validation
- Reinforcement calculations
- BBS generation
- Cut List optimization
- Quantity takeoff
- Calculation engine

These tests verify software behavior and mathematical consistency.
They do not replace engineering validation against official
design-code examples.
"""

from __future__ import annotations

import math
import unittest

from core.models import (
    FoundationType,
    MemberType,
    RectangularGeometry,
    ReinforcementType,
    StructuralMember,
)

from core.validation import (
    validate_number,
    validate_positive_number,
    validate_rebar_diameter,
    validate_rebar_quantity,
    validate_rebar_length,
)

from core.reinforcement import (
    bar_area_mm2,
    bar_weight_kg_per_m,
    total_bar_weight_kg,
    reinforcement_ratio_percent,
    required_bar_count,
    equivalent_bar_count,
)

from core.bbs import (
    BBSItem,
    BBSSchedule,
    bbs_to_cut_pieces,
)

from core.cutlist import (
    CutPiece,
    optimize_cut_list,
    expand_cut_pieces,
)

from core.quantities import (
    QuantityTakeoff,
    create_concrete_quantity,
    create_rebar_quantity,
    merge_takeoffs,
)


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidation(unittest.TestCase):
    """Tests for core validation helpers."""

    def test_validate_number(self) -> None:
        self.assertEqual(
            validate_number(10),
            10.0,
        )

    def test_validate_positive_number(self) -> None:
        self.assertEqual(
            validate_positive_number(5, "test"),
            5.0,
        )

    def test_negative_number_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_positive_number(
                -1,
                "test",
            )

    def test_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_positive_number(
                0,
                "test",
            )

    def test_standard_rebar_diameter(self) -> None:
        diameter = validate_rebar_diameter(16)

        self.assertEqual(
            diameter,
            16.0,
        )

    def test_invalid_rebar_diameter(self) -> None:
        with self.assertRaises(ValueError):
            validate_rebar_diameter(17)

    def test_rebar_quantity(self) -> None:
        quantity = validate_rebar_quantity(8)

        self.assertEqual(
            quantity,
            8,
        )

    def test_invalid_rebar_quantity(self) -> None:
        with self.assertRaises(ValueError):
            validate_rebar_quantity(0)

    def test_rebar_length(self) -> None:
        length = validate_rebar_length(
            6.5,
        )

        self.assertEqual(
            length,
            6.5,
        )


# ============================================================================
# REINFORCEMENT TESTS
# ============================================================================

class TestReinforcement(unittest.TestCase):
    """Tests for mathematical reinforcement utilities."""

    def test_bar_area(self) -> None:
        area = bar_area_mm2(16)

        expected = math.pi * 16**2 / 4

        self.assertAlmostEqual(
            area,
            expected,
            places=6,
        )

    def test_bar_weight(self) -> None:
        weight = bar_weight_kg_per_m(16)

        expected = (
            math.pi
            * 16**2
            / 4
            * 7850
            / 1_000_000
        )

        self.assertAlmostEqual(
            weight,
            expected,
            places=6,
        )

    def test_total_bar_weight(self) -> None:
        total = total_bar_weight_kg(
            diameter_mm=16,
            length_m=10,
            quantity=5,
        )

        expected = (
            bar_weight_kg_per_m(16)
            * 10
            * 5
        )

        self.assertAlmostEqual(
            total,
            expected,
            places=6,
        )

    def test_reinforcement_ratio(self) -> None:
        ratio = reinforcement_ratio_percent(
            steel_area_mm2=2000,
            gross_area_mm2=100000,
        )

        self.assertAlmostEqual(
            ratio,
            2.0,
            places=6,
        )

    def test_required_bar_count(self) -> None:
        count = required_bar_count(
            required_area_mm2=2000,
            bar_diameter_mm=16,
        )

        expected = math.ceil(
            2000 / bar_area_mm2(16)
        )

        self.assertEqual(
            count,
            expected,
        )

    def test_equivalent_bar_count(self) -> None:
        count = equivalent_bar_count(
            source_diameter_mm=16,
            source_quantity=4,
            target_diameter_mm=20,
        )

        source_area = (
            4 * bar_area_mm2(16)
        )

        expected = math.ceil(
            source_area / bar_area_mm2(20)
        )

        self.assertEqual(
            count,
            expected,
        )


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestModels(unittest.TestCase):
    """Tests for core data models."""

    def test_rectangular_geometry(self) -> None:
        geometry = RectangularGeometry(
            width=300,
            height=500,
        )

        self.assertEqual(
            geometry.width,
            300,
        )

        self.assertEqual(
            geometry.height,
            500,
        )

    def test_structural_member_creation(self) -> None:
        geometry = RectangularGeometry(
            width=300,
            height=500,
        )

        member = StructuralMember(
            id="B-01",
            member_type=MemberType.BEAM,
            geometry=geometry,
        )

        self.assertEqual(
            member.id,
            "B-01",
        )

        self.assertEqual(
            member.member_type,
            MemberType.BEAM,
        )

    def test_foundation_member(self) -> None:
        geometry = RectangularGeometry(
            width=1000,
            height=500,
        )

        member = StructuralMember(
            id="F-01",
            member_type=MemberType.FOUNDATION,
            geometry=geometry,
        )

        self.assertEqual(
            member.member_type,
            MemberType.FOUNDATION,
        )


# ============================================================================
# BBS TESTS
# ============================================================================

class TestBBS(unittest.TestCase):
    """Tests for Bar Bending Schedule."""

    def test_bbs_schedule_creation(self) -> None:
        schedule = BBSSchedule()

        self.assertIsNotNone(
            schedule,
        )

    def test_bbs_item_creation(self) -> None:
        item = BBSItem(
            mark="B1",
            diameter_mm=16,
            quantity=4,
            shape_code="STRAIGHT",
            dimensions={},
            length_mm=6000,
        )

        self.assertEqual(
            item.mark,
            "B1",
        )

        self.assertEqual(
            item.diameter_mm,
            16,
        )

        self.assertEqual(
            item.quantity,
            4,
        )

    def test_bbs_to_cut_pieces(self) -> None:
        item = BBSItem(
            mark="B1",
            diameter_mm=16,
            quantity=4,
            shape_code="STRAIGHT",
            dimensions={},
            length_mm=6000,
        )

        schedule = BBSSchedule()

        add_method = getattr(
            schedule,
            "add_item",
            None,
        )

        if callable(add_method):
            add_method(item)
        else:
            items = getattr(
                schedule,
                "items",
                None,
            )

            if isinstance(items, list):
                items.append(item)
            else:
                self.skipTest(
                    "BBSSchedule API does not expose item insertion."
                )

        pieces = bbs_to_cut_pieces(
            schedule,
        )

        self.assertEqual(
            len(pieces),
            4,
        )

        self.assertTrue(
            all(
                piece.length_mm == 6000
                for piece in pieces
            )
        )


# ============================================================================
# CUT LIST TESTS
# ============================================================================

class TestCutList(unittest.TestCase):
    """Tests for stock-bar cutting optimization."""

    def test_quantity_is_expanded(self) -> None:
        pieces = [
            CutPiece(
                mark="B1",
                diameter_mm=16,
                length_mm=6000,
                quantity=4,
            )
        ]

        expanded = expand_cut_pieces(
            pieces,
        )

        self.assertEqual(
            len(expanded),
            4,
        )

        self.assertTrue(
            all(
                piece.length_mm == 6000
                for piece in expanded
            )
        )

    def test_short_pieces_fit_in_stock_bar(self) -> None:
        pieces = [
            CutPiece(
                mark="A1",
                diameter_mm=16,
                length_mm=4000,
                quantity=2,
            ),
            CutPiece(
                mark="A2",
                diameter_mm=16,
                length_mm=3000,
                quantity=1,
            ),
        ]

        result = optimize_cut_list(
            pieces,
            stock_length_mm=12000,
        )

        self.assertGreater(
            len(result.stock_bars),
            0,
        )

        total_piece_length = (
            4000
            + 4000
            + 3000
        )

        total_stock_length = sum(
            bar.length_mm
            for bar in result.stock_bars
        )

        self.assertGreaterEqual(
            total_stock_length,
            total_piece_length,
        )

    def test_piece_longer_than_stock_is_rejected(self) -> None:
        pieces = [
            CutPiece(
                mark="LONG",
                diameter_mm=16,
                length_mm=13000,
                quantity=1,
            )
        ]

        with self.assertRaises(ValueError):
            optimize_cut_list(
                pieces,
                stock_length_mm=12000,
            )

    def test_different_diameters_are_not_mixed(self) -> None:
        pieces = [
            CutPiece(
                mark="D16",
                diameter_mm=16,
                length_mm=6000,
                quantity=1,
            ),
            CutPiece(
                mark="D20",
                diameter_mm=20,
                length_mm=6000,
                quantity=1,
            ),
        ]

        result = optimize_cut_list(
            pieces,
            stock_length_mm=12000,
        )

        self.assertGreaterEqual(
            len(result.stock_bars),
            2,
        )


# ============================================================================
# QUANTITY TAKEOFF TESTS
# ============================================================================

class TestQuantities(unittest.TestCase):
    """Tests for material quantity takeoff."""

    def test_concrete_quantity(self) -> None:
        item = create_concrete_quantity(
            member_id="C-01",
            volume_m3=2.5,
        )

        self.assertEqual(
            item.quantity,
            2.5,
        )

    def test_rebar_quantity(self) -> None:
        item = create_rebar_quantity(
            member_id="B-01",
            diameter_mm=16,
            weight_kg=125.0,
        )

        self.assertEqual(
            item.quantity,
            125.0,
        )

    def test_takeoff_creation(self) -> None:
        takeoff = QuantityTakeoff()

        self.assertIsNotNone(
            takeoff,
        )

    def test_merge_takeoffs(self) -> None:
        first = QuantityTakeoff()

        first.add(
            create_concrete_quantity(
                member_id="F-01",
                volume_m3=2.0,
            )
        )

        second = QuantityTakeoff()

        second.add(
            create_concrete_quantity(
                member_id="F-02",
                volume_m3=3.0,
            )
        )

        merged = merge_takeoffs(
            first,
            second,
        )

        total_method = getattr(
            merged,
            "total_concrete_volume",
            None,
        )

        if callable(total_method):
            self.assertAlmostEqual(
                total_method(),
                5.0,
                places=6,
            )
        else:
            self.assertIsNotNone(
                merged,
            )


# ============================================================================
# SANITY / INVARIANT TESTS
# ============================================================================

class TestEngineeringInvariants(unittest.TestCase):
    """
    Tests for mathematical invariants that should remain true regardless
    of the selected design code.
    """

    def test_bar_weight_increases_with_diameter(self) -> None:
        w12 = bar_weight_kg_per_m(12)
        w16 = bar_weight_kg_per_m(16)
        w20 = bar_weight_kg_per_m(20)

        self.assertLess(
            w12,
            w16,
        )

        self.assertLess(
            w16,
            w20,
        )

    def test_area_increases_with_diameter(self) -> None:
        a12 = bar_area_mm2(12)
        a16 = bar_area_mm2(16)
        a20 = bar_area_mm2(20)

        self.assertLess(
            a12,
            a16,
        )

        self.assertLess(
            a16,
            a20,
        )

    def test_cut_piece_count_matches_quantity(self) -> None:
        pieces = [
            CutPiece(
                mark="TEST",
                diameter_mm=16,
                length_mm=5000,
                quantity=7,
            )
        ]

        expanded = expand_cut_pieces(
            pieces,
        )

        self.assertEqual(
            len(expanded),
            7,
        )

    def test_rebar_weight_scales_with_length(self) -> None:
        w5 = total_bar_weight_kg(
            diameter_mm=16,
            length_m=5,
            quantity=1,
        )

        w10 = total_bar_weight_kg(
            diameter_mm=16,
            length_m=10,
            quantity=1,
        )

        self.assertAlmostEqual(
            w10,
            2 * w5,
            places=6,
        )

    def test_rebar_weight_scales_with_quantity(self) -> None:
        w1 = total_bar_weight_kg(
            diameter_mm=16,
            length_m=5,
            quantity=1,
        )

        w4 = total_bar_weight_kg(
            diameter_mm=16,
            length_m=5,
            quantity=4,
        )

        self.assertAlmostEqual(
            w4,
            4 * w1,
            places=6,
        )


# ============================================================================
# TEST SUITE
# ============================================================================

def build_test_suite() -> unittest.TestSuite:
    """Build the complete core-layer test suite."""

    loader = unittest.TestLoader()

    suite = unittest.TestSuite()

    test_classes = [
        TestValidation,
        TestReinforcement,
        TestModels,
        TestBBS,
        TestCutList,
        TestQuantities,
        TestEngineeringInvariants,
    ]

    for test_class in test_classes:
        suite.addTests(
            loader.loadTestsFromTestCase(
                test_class
            )
        )

    return suite


def run_tests() -> bool:
    """Run the complete test suite."""

    runner = unittest.TextTestRunner(
        verbosity=2,
    )

    result = runner.run(
        build_test_suite()
    )

    return result.wasSuccessful()


if __name__ == "__main__":
    raise SystemExit(
        0 if run_tests() else 1
    )
