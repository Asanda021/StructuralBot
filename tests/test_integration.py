"""
StructuralBot - Integration Tests

Integration tests for the main engineering architecture.

Covered flow:

    Design Code
        ↓
    Code Adapter
        ↓
    Core Calculation Layer
        ↓
    Reinforcement
        ↓
    BBS
        ↓
    Cut List
        ↓
    Quantity Takeoff

These tests focus on software integration and mathematical consistency.
They are not a substitute for validation against official design-code
examples, laboratory data, or professional engineering review.
"""

from __future__ import annotations

import math
import unittest
from dataclasses import dataclass
from typing import Any, Optional

from core.bbs import (
    BBSItem,
    BBSSchedule,
    bbs_to_cut_pieces,
)

from core.code_adapter import (
    CodeAdapter,
    get_member_category,
    member_category_from_member,
)

from core.cutlist import (
    CutPiece,
    expand_cut_pieces,
    optimize_cut_list,
)

from core.quantities import (
    QuantityTakeoff,
    create_concrete_quantity,
    create_rebar_quantity,
    merge_takeoffs,
)

from core.reinforcement import (
    bar_area_mm2,
    bar_weight_kg_per_m,
    required_bar_count,
    total_bar_weight_kg,
)

from codes.base import (
    CodeFamily,
    MemberCategory,
)

from codes.iran.concrete import (
    create_iran_concrete_code,
)

from codes.iran.reinforcement import (
    create_iran_reinforcement_code,
)

from codes.iran.detailing import (
    create_iran_detailing_code,
)


# ============================================================================
# TEST HELPERS
# ============================================================================

def _call_first_available(
    obj: Any,
    names: tuple[str, ...],
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Call the first available callable method.

    This helper makes the integration tests tolerant of small API
    differences between implementation revisions.
    """

    for name in names:
        method = getattr(obj, name, None)

        if callable(method):
            return method(*args, **kwargs)

    raise AttributeError(
        f"None of the methods {names!r} exist on {type(obj).__name__}."
    )


def _add_bbs_item(
    schedule: BBSSchedule,
    item: BBSItem,
) -> None:
    """
    Add an item to BBSSchedule using the supported API.
    """

    add_method = getattr(
        schedule,
        "add_item",
        None,
    )

    if callable(add_method):
        add_method(item)
        return

    items = getattr(
        schedule,
        "items",
        None,
    )

    if isinstance(items, list):
        items.append(item)
        return

    raise AttributeError(
        "BBSSchedule does not expose an item insertion API."
    )


# ============================================================================
# BASIC CODE + ADAPTER INTEGRATION
# ============================================================================

class TestCodeAdapterIntegration(unittest.TestCase):
    """Test design-code and adapter integration."""

    def setUp(self) -> None:
        self.code = create_iran_concrete_code()
        self.adapter = CodeAdapter(
            self.code,
        )

    def test_adapter_uses_iran_code(self) -> None:
        self.assertEqual(
            self.adapter.family,
            CodeFamily.IRAN,
        )

    def test_adapter_code_id_matches_code(self) -> None:
        self.assertEqual(
            self.adapter.code_id,
            self.code.code_id,
        )

    def test_foundation_mapping(self) -> None:
        category = get_member_category(
            "foundation",
        )

        self.assertEqual(
            category,
            MemberCategory.FOUNDATION,
        )

    def test_column_mapping(self) -> None:
        category = member_category_from_member(
            "column",
        )

        self.assertEqual(
            category,
            MemberCategory.COLUMN,
        )

    def test_beam_mapping(self) -> None:
        category = member_category_from_member(
            "beam",
        )

        self.assertEqual(
            category,
            MemberCategory.BEAM,
        )

    def test_slab_mapping(self) -> None:
        category = member_category_from_member(
            "slab",
        )

        self.assertEqual(
            category,
            MemberCategory.SLAB,
        )

    def test_code_supports_member(self) -> None:
        self.assertTrue(
            self.adapter.supports_member(
                "column",
            )
        )

        self.assertTrue(
            self.adapter.supports_member(
                "beam",
            )
        )

    def test_metadata(self) -> None:
        metadata = self.adapter.metadata()

        self.assertIsInstance(
            metadata,
            dict,
        )

        self.assertIn(
            "code_id",
            metadata,
        )

        self.assertIn(
            "code_family",
            metadata,
        )

        self.assertIn(
            "edition",
            metadata,
        )


# ============================================================================
# CONCRETE DESIGN CODE INTEGRATION
# ============================================================================

class TestConcreteCodeIntegration(unittest.TestCase):
    """Test concrete code calculations through the code layer."""

    def setUp(self) -> None:
        self.code = create_iran_concrete_code()

    def test_rectangular_volume(self) -> None:
        volume = self.code.rectangular_volume(
            width_mm=300,
            height_mm=500,
            length_m=10,
        )

        expected = (
            0.300
            * 0.500
            * 10.0
        )

        self.assertAlmostEqual(
            volume,
            expected,
            places=6,
        )

    def test_circular_volume(self) -> None:
        diameter_m = 0.500
        length_m = 10.0

        expected = (
            math.pi
            * diameter_m**2
            / 4
            * length_m
        )

        volume = self.code.circular_volume(
            diameter_mm=500,
            length_m=10,
        )

        self.assertAlmostEqual(
            volume,
            expected,
            places=6,
        )

    def test_concrete_validation(self) -> None:
        result = self.code.validate_concrete(
            fc_mpa=25,
        )

        self.assertTrue(
            result.valid,
        )


# ============================================================================
# REINFORCEMENT CODE INTEGRATION
# ============================================================================

class TestReinforcementCodeIntegration(unittest.TestCase):
    """Test reinforcement code calculations."""

    def setUp(self) -> None:
        self.code = create_iran_reinforcement_code()

    def test_bar_area_matches_core(self) -> None:
        code_area = self.code.bar_area(
            diameter_mm=16,
        )

        core_area = bar_area_mm2(
            16,
        )

        self.assertAlmostEqual(
            code_area,
            core_area,
            places=6,
        )

    def test_bar_weight_matches_core(self) -> None:
        code_weight = self.code.bar_weight_kg_per_m(
            diameter_mm=16,
        )

        core_weight = bar_weight_kg_per_m(
            16,
        )

        self.assertAlmostEqual(
            code_weight,
            core_weight,
            places=6,
        )

    def test_total_weight_matches_core(self) -> None:
        code_weight = self.code.total_bar_weight(
            diameter_mm=16,
            length_m=6,
            quantity=10,
        )

        core_weight = total_bar_weight_kg(
            diameter_mm=16,
            length_m=6,
            quantity=10,
        )

        self.assertAlmostEqual(
            code_weight,
            core_weight,
            places=6,
        )

    def test_required_bar_count(self) -> None:
        required_area = 2500.0

        core_count = required_bar_count(
            required_area_mm2=required_area,
            bar_diameter_mm=16,
        )

        self.assertGreater(
            core_count,
            0,
        )


# ============================================================================
# DETAILING CODE INTEGRATION
# ============================================================================

class TestDetailingIntegration(unittest.TestCase):
    """Test detailing-layer integration."""

    def setUp(self) -> None:
        self.detailing = create_iran_detailing_code()

    def test_cover_check(self) -> None:
        result = self.detailing.check_cover(
            cover_mm=40,
        )

        self.assertIsNotNone(
            result,
        )

    def test_spacing_check(self) -> None:
        result = self.detailing.check_spacing(
            spacing_mm=150,
        )

        self.assertIsNotNone(
            result,
        )

    def test_clear_spacing(self) -> None:
        clear = self.detailing.clear_spacing(
            center_spacing_mm=150,
            bar_diameter_mm=16,
        )

        self.assertGreater(
            clear,
            0,
        )


# ============================================================================
# REINFORCEMENT → BBS
# ============================================================================

class TestReinforcementToBBS(unittest.TestCase):
    """
    Test conversion from reinforcement definitions to physical BBS items.
    """

    def test_bbs_quantity_is_preserved(self) -> None:
        item = BBSItem(
            mark="B-01",
            diameter_mm=16,
            quantity=8,
            shape_code="STRAIGHT",
            dimensions={},
            length_mm=6000,
        )

        schedule = BBSSchedule()

        _add_bbs_item(
            schedule,
            item,
        )

        pieces = bbs_to_cut_pieces(
            schedule,
        )

        self.assertEqual(
            len(pieces),
            8,
        )

    def test_bbs_physical_length_is_preserved(self) -> None:
        item = BBSItem(
            mark="B-02",
            diameter_mm=20,
            quantity=5,
            shape_code="STRAIGHT",
            dimensions={},
            length_mm=7500,
        )

        schedule = BBSSchedule()

        _add_bbs_item(
            schedule,
            item,
        )

        pieces = bbs_to_cut_pieces(
            schedule,
        )

        self.assertEqual(
            len(pieces),
            5,
        )

        for piece in pieces:
            self.assertEqual(
                piece.length_mm,
                7500,
            )


# ============================================================================
# BBS → CUT LIST
# ============================================================================

class TestBBSToCutList(unittest.TestCase):
    """Test complete BBS to Cut List conversion."""

    def test_bbs_to_cut_list(self) -> None:
        item = BBSItem(
            mark="B-03",
            diameter_mm=16,
            quantity=6,
            shape_code="STRAIGHT",
            dimensions={},
            length_mm=5000,
        )

        schedule = BBSSchedule()

        _add_bbs_item(
            schedule,
            item,
        )

        pieces = bbs_to_cut_pieces(
            schedule,
        )

        self.assertEqual(
            len(pieces),
            6,
        )

        result = optimize_cut_list(
            pieces,
            stock_length_mm=12000,
        )

        self.assertGreater(
            len(result.stock_bars),
            0,
        )

    def test_no_piece_exceeds_stock_length(self) -> None:
        item = BBSItem(
            mark="B-04",
            diameter_mm=20,
            quantity=3,
            shape_code="STRAIGHT",
            dimensions={},
            length_mm=6000,
        )

        schedule = BBSSchedule()

        _add_bbs_item(
            schedule,
            item,
        )

        pieces = bbs_to_cut_pieces(
            schedule,
        )

        expanded = expand_cut_pieces(
            pieces,
        )

        for piece in expanded:
            self.assertLessEqual(
                piece.length_mm,
                12000,
            )


# ============================================================================
# CUT LIST PHYSICAL PIECE INVARIANTS
# ============================================================================

class TestCutListInvariants(unittest.TestCase):
    """Verify physical-piece accounting."""

    def test_quantity_expansion(self) -> None:
        pieces = [
            CutPiece(
                mark="C1",
                diameter_mm=16,
                length_mm=4000,
                quantity=3,
            ),
            CutPiece(
                mark="C2",
                diameter_mm=16,
                length_mm=2500,
                quantity=2,
            ),
        ]

        expanded = expand_cut_pieces(
            pieces,
        )

        self.assertEqual(
            len(expanded),
            5,
        )

    def test_total_length_is_preserved(self) -> None:
        pieces = [
            CutPiece(
                mark="C1",
                diameter_mm=16,
                length_mm=4000,
                quantity=3,
            ),
            CutPiece(
                mark="C2",
                diameter_mm=16,
                length_mm=2500,
                quantity=2,
            ),
        ]

        expanded = expand_cut_pieces(
            pieces,
        )

        total_length = sum(
            piece.length_mm
            for piece in expanded
        )

        expected = (
            3 * 4000
            + 2 * 2500
        )

        self.assertEqual(
            total_length,
            expected,
        )

    def test_diameters_are_separated(self) -> None:
        pieces = [
            CutPiece(
                mark="D16",
                diameter_mm=16,
                length_mm=5000,
                quantity=2,
            ),
            CutPiece(
                mark="D20",
                diameter_mm=20,
                length_mm=5000,
                quantity=2,
            ),
        ]

        result = optimize_cut_list(
            pieces,
            stock_length_mm=12000,
        )

        diameters = {
            bar.diameter_mm
            for bar in result.stock_bars
        }

        self.assertIn(
            16,
            diameters,
        )

        self.assertIn(
            20,
            diameters,
        )


# ============================================================================
# CUT LIST → REBAR QUANTITY
# ============================================================================

class TestCutListToQuantity(unittest.TestCase):
    """
    Verify that physical cut pieces can be converted into material weight.
    """

    def test_total_weight_from_physical_pieces(self) -> None:
        pieces = [
            CutPiece(
                mark="R1",
                diameter_mm=16,
                length_mm=6000,
                quantity=4,
            )
        ]

        expanded = expand_cut_pieces(
            pieces,
        )

        total_weight = 0.0

        for piece in expanded:
            total_weight += (
                bar_weight_kg_per_m(
                    piece.diameter_mm
                )
                * piece.length_mm
                / 1000.0
            )

        expected = total_bar_weight_kg(
            diameter_mm=16,
            length_m=6,
            quantity=4,
        )

        self.assertAlmostEqual(
            total_weight,
            expected,
            places=6,
        )


# ============================================================================
# QUANTITY TAKEOFF INTEGRATION
# ============================================================================

class TestQuantityIntegration(unittest.TestCase):
    """Test concrete and reinforcement quantity integration."""

    def test_concrete_and_rebar_takeoff(self) -> None:
        takeoff = QuantityTakeoff()

        concrete = create_concrete_quantity(
            member_id="F-01",
            volume_m3=4.25,
        )

        rebar = create_rebar_quantity(
            member_id="F-01",
            diameter_mm=16,
            weight_kg=325.0,
        )

        takeoff.add(
            concrete,
        )

        takeoff.add(
            rebar,
        )

        self.assertIsNotNone(
            takeoff,
        )

    def test_merge_project_takeoffs(self) -> None:
        foundation_takeoff = QuantityTakeoff()

        foundation_takeoff.add(
            create_concrete_quantity(
                member_id="F-01",
                volume_m3=5.0,
            )
        )

        beam_takeoff = QuantityTakeoff()

        beam_takeoff.add(
            create_concrete_quantity(
                member_id="B-01",
                volume_m3=2.0,
            )
        )

        merged = merge_takeoffs(
            foundation_takeoff,
            beam_takeoff,
        )

        self.assertIsNotNone(
            merged,
        )

        total_method = getattr(
            merged,
            "total_concrete_volume",
            None,
        )

        if callable(total_method):
            self.assertAlmostEqual(
                total_method(),
                7.0,
                places=6,
            )

    def test_rebar_quantity_is_positive(self) -> None:
        item = create_rebar_quantity(
            member_id="C-01",
            diameter_mm=20,
            weight_kg=180.0,
        )

        self.assertGreater(
            item.quantity,
            0,
        )


# ============================================================================
# END-TO-END MEMBER SCENARIO
# ============================================================================

class TestEndToEndMemberScenario(unittest.TestCase):
    """
    Simulate a simplified reinforced-concrete beam workflow.

    This is intentionally not a structural design calculation.

    The scenario assumes that the required reinforcement has already been
    determined by an engineering/design module.

    The purpose is to verify the software pipeline:

        member
          ↓
        reinforcement definition
          ↓
        BBS
          ↓
        physical pieces
          ↓
        cut list
          ↓
        material quantity
    """

    def test_beam_workflow(self) -> None:
        # ---------------------------------------------------------------
        # 1. Design code
        # ---------------------------------------------------------------

        concrete_code = create_iran_concrete_code()

        adapter = CodeAdapter(
            concrete_code,
        )

        self.assertTrue(
            adapter.supports_member(
                "beam",
            )
        )

        # ---------------------------------------------------------------
        # 2. Simplified member geometry
        # ---------------------------------------------------------------

        beam_width_mm = 300
        beam_height_mm = 500
        beam_length_m = 6.0

        concrete_volume = concrete_code.rectangular_volume(
            width_mm=beam_width_mm,
            height_mm=beam_height_mm,
            length_m=beam_length_m,
        )

        self.assertAlmostEqual(
            concrete_volume,
            0.9,
            places=6,
        )

        # ---------------------------------------------------------------
        # 3. Assumed reinforcement
        # ---------------------------------------------------------------

        bar_diameter_mm = 16
        bar_quantity = 6
        bar_length_m = 6.0

        reinforcement_weight = total_bar_weight_kg(
            diameter_mm=bar_diameter_mm,
            length_m=bar_length_m,
            quantity=bar_quantity,
        )

        self.assertGreater(
            reinforcement_weight,
            0,
        )

        # ---------------------------------------------------------------
        # 4. BBS
        # ---------------------------------------------------------------

        bbs_item = BBSItem(
            mark="B-01-MAIN",
            diameter_mm=bar_diameter_mm,
            quantity=bar_quantity,
            shape_code="STRAIGHT",
            dimensions={},
            length_mm=int(
                bar_length_m * 1000
            ),
        )

        schedule = BBSSchedule()

        _add_bbs_item(
            schedule,
            bbs_item,
        )

        # ---------------------------------------------------------------
        # 5. Physical pieces
        # ---------------------------------------------------------------

        cut_pieces = bbs_to_cut_pieces(
            schedule,
        )

        self.assertEqual(
            len(cut_pieces),
            bar_quantity,
        )

        # ---------------------------------------------------------------
        # 6. Cut List
        # ---------------------------------------------------------------

        cut_result = optimize_cut_list(
            cut_pieces,
            stock_length_mm=12000,
        )

        self.assertGreater(
            len(cut_result.stock_bars),
            0,
        )

        # ---------------------------------------------------------------
        # 7. Quantity Takeoff
        # ---------------------------------------------------------------

        takeoff = QuantityTakeoff()

        takeoff.add(
            create_concrete_quantity(
                member_id="B-01",
                volume_m3=concrete_volume,
            )
        )

        takeoff.add(
            create_rebar_quantity(
                member_id="B-01",
                diameter_mm=bar_diameter_mm,
                weight_kg=reinforcement_weight,
            )
        )

        self.assertIsNotNone(
            takeoff,
        )


# ============================================================================
# CROSS-LAYER CONSISTENCY
# ============================================================================

class TestCrossLayerConsistency(unittest.TestCase):
    """
    Verify that different layers agree on basic mathematical quantities.
    """

    def test_core_and_code_reinforcement_area_agree(self) -> None:
        core_area = bar_area_mm2(
            20,
        )

        code = create_iran_reinforcement_code()

        code_area = code.bar_area(
            diameter_mm=20,
        )

        self.assertAlmostEqual(
            core_area,
            code_area,
            places=6,
        )

    def test_core_and_code_reinforcement_weight_agree(self) -> None:
        core_weight = bar_weight_kg_per_m(
            20,
        )

        code = create_iran_reinforcement_code()

        code_weight = code.bar_weight_kg_per_m(
            diameter_mm=20,
        )

        self.assertAlmostEqual(
            core_weight,
            code_weight,
            places=6,
        )

    def test_code_family_is_not_hardcoded_in_core_math(self) -> None:
        """
        Basic architectural sanity check.

        Core reinforcement mathematics should produce a result without
        requiring an Iranian code object.
        """

        area = bar_area_mm2(
            25,
        )

        weight = bar_weight_kg_per_m(
            25,
        )

        self.assertGreater(
            area,
            0,
        )

        self.assertGreater(
            weight,
            0,
        )


# ============================================================================
# TEST SUITE
# ============================================================================

def build_test_suite() -> unittest.TestSuite:
    """Build the complete integration test suite."""

    loader = unittest.TestLoader()

    suite = unittest.TestSuite()

    test_classes = [
        TestCodeAdapterIntegration,
        TestConcreteCodeIntegration,
        TestReinforcementCodeIntegration,
        TestDetailingIntegration,
        TestReinforcementToBBS,
        TestBBSToCutList,
        TestCutListInvariants,
        TestCutListToQuantity,
        TestQuantityIntegration,
        TestEndToEndMemberScenario,
        TestCrossLayerConsistency,
    ]

    for test_class in test_classes:
        suite.addTests(
            loader.loadTestsFromTestCase(
                test_class
            )
        )

    return suite


def run_tests() -> bool:
    """Run all integration tests."""

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
