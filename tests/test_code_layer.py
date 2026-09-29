"""
StructuralBot - Design Code Layer Tests

Basic integration tests for the design-code architecture.

These tests verify:
- Code registration
- Code resolution
- Member mapping
- Material access
- Requirement access
- Detailing-rule access
- Basic code checks
- Adapter/context compatibility

These are structural/integration tests.
They are not a substitute for engineering validation against
official code examples and benchmark calculations.
"""

from __future__ import annotations

import unittest

from codes.base import (
    CodeFamily,
    CodeContext,
    DesignCode,
    MemberCategory,
    default_code_registry,
)

from codes.iran.concrete import (
    IranConcrete,
    create_iran_concrete_code,
)

from codes.iran.detailing import (
    IranDetailing,
    create_iran_detailing_code,
)

from codes.iran.reinforcement import (
    IranReinforcement,
    create_iran_reinforcement_code,
)

from core.code_adapter import (
    CodeAdapter,
    CodeContextMismatchError,
    CodeNotConfiguredError,
    UnsupportedMemberError,
    member_category_from_member,
)


# ---------------------------------------------------------------------------
# TEST MEMBER MAPPING
# ---------------------------------------------------------------------------

class TestMemberMapping(unittest.TestCase):

    def test_foundation_mapping(self) -> None:
        self.assertEqual(
            member_category_from_member("foundation"),
            MemberCategory.FOUNDATION,
        )

    def test_footing_mapping(self) -> None:
        self.assertEqual(
            member_category_from_member("footing"),
            MemberCategory.FOUNDATION,
        )

    def test_column_mapping(self) -> None:
        self.assertEqual(
            member_category_from_member("column"),
            MemberCategory.COLUMN,
        )

    def test_beam_mapping(self) -> None:
        self.assertEqual(
            member_category_from_member("beam"),
            MemberCategory.BEAM,
        )

    def test_slab_mapping(self) -> None:
        self.assertEqual(
            member_category_from_member("slab"),
            MemberCategory.SLAB,
        )

    def test_wall_mapping(self) -> None:
        self.assertEqual(
            member_category_from_member("wall"),
            MemberCategory.WALL,
        )

    def test_stair_mapping(self) -> None:
        self.assertEqual(
            member_category_from_member("stair"),
            MemberCategory.STAIR,
        )

    def test_alias_mapping(self) -> None:
        self.assertEqual(
            member_category_from_member("beam_main"),
            MemberCategory.BEAM,
        )

        self.assertEqual(
            member_category_from_member("roof_slab"),
            MemberCategory.SLAB,
        )

        self.assertEqual(
            member_category_from_member("column_rect"),
            MemberCategory.COLUMN,
        )

    def test_invalid_member(self) -> None:
        with self.assertRaises(ValueError):
            member_category_from_member("unknown_member")


# ---------------------------------------------------------------------------
# TEST IRAN CODE FACTORIES
# ---------------------------------------------------------------------------

class TestIranCodeFactories(unittest.TestCase):

    def test_concrete_factory(self) -> None:
        code = create_iran_concrete_code()

        self.assertIsInstance(
            code,
            IranConcrete,
        )

        self.assertEqual(
            code.family,
            CodeFamily.IRAN,
        )

    def test_reinforcement_factory(self) -> None:
        code = create_iran_reinforcement_code()

        self.assertIsInstance(
            code,
            IranReinforcement,
        )

        self.assertEqual(
            code.family,
            CodeFamily.IRAN,
        )

    def test_detailing_factory(self) -> None:
        code = create_iran_detailing_code()

        self.assertIsInstance(
            code,
            IranDetailing,
        )

        self.assertEqual(
            code.family,
            CodeFamily.IRAN,
        )


# ---------------------------------------------------------------------------
# TEST CODE REGISTRY
# ---------------------------------------------------------------------------

class TestCodeRegistry(unittest.TestCase):

    def test_registry_exists(self) -> None:
        self.assertIsNotNone(
            default_code_registry,
        )

    def test_registry_has_expected_interface(self) -> None:
        self.assertTrue(
            hasattr(default_code_registry, "register")
            or hasattr(default_code_registry, "add")
        )


# ---------------------------------------------------------------------------
# TEST CODE ADAPTER
# ---------------------------------------------------------------------------

class TestCodeAdapter(unittest.TestCase):

    def setUp(self) -> None:
        self.code = create_iran_concrete_code()

    def test_adapter_creation(self) -> None:
        adapter = CodeAdapter(
            self.code,
        )

        self.assertEqual(
            adapter.code_id,
            self.code.code_id,
        )

        self.assertEqual(
            adapter.family,
            self.code.family,
        )

    def test_adapter_edition(self) -> None:
        adapter = CodeAdapter(
            self.code,
        )

        self.assertEqual(
            adapter.edition,
            self.code.edition,
        )

    def test_supported_foundation(self) -> None:
        adapter = CodeAdapter(
            self.code,
        )

        self.assertTrue(
            adapter.supports_member("foundation")
        )

    def test_supported_column(self) -> None:
        adapter = CodeAdapter(
            self.code,
        )

        self.assertTrue(
            adapter.supports_member("column")
        )

    def test_supported_beam(self) -> None:
        adapter = CodeAdapter(
            self.code,
        )

        self.assertTrue(
            adapter.supports_member("beam")
        )

    def test_supported_slab(self) -> None:
        adapter = CodeAdapter(
            self.code,
        )

        self.assertTrue(
            adapter.supports_member("slab")
        )

    def test_supported_wall(self) -> None:
        adapter = CodeAdapter(
            self.code,
        )

        self.assertTrue(
            adapter.supports_member("wall")
        )

    def test_supported_stair(self) -> None:
        adapter = CodeAdapter(
            self.code,
        )

        self.assertTrue(
            adapter.supports_member("stair")
        )

    def test_unsupported_member_raises(self) -> None:
        class FakeMember:
            pass

        adapter = CodeAdapter(
            self.code,
        )

        with self.assertRaises(ValueError):
            adapter.supports_member(
                FakeMember()
            )

    def test_metadata(self) -> None:
        adapter = CodeAdapter(
            self.code,
        )

        metadata = adapter.metadata()

        self.assertIsInstance(
            metadata,
            dict,
        )

        self.assertEqual(
            metadata["code_id"],
            self.code.code_id,
        )

        self.assertEqual(
            metadata["code_family"],
            self.code.family.value,
        )


# ---------------------------------------------------------------------------
# TEST CONCRETE CODE
# ---------------------------------------------------------------------------

class TestIranConcrete(unittest.TestCase):

    def setUp(self) -> None:
        self.code = create_iran_concrete_code()

    def test_rectangular_section(self) -> None:
        section = self.code.rectangular_section(
            width_mm=300,
            height_mm=500,
        )

        self.assertIsNotNone(
            section,
        )

    def test_rectangular_volume(self) -> None:
        volume = self.code.rectangular_volume(
            width_mm=300,
            height_mm=500,
            length_m=10,
        )

        self.assertAlmostEqual(
            volume,
            1.5,
            places=6,
        )

    def test_circular_volume(self) -> None:
        volume = self.code.circular_volume(
            diameter_mm=500,
            length_m=10,
        )

        self.assertGreater(
            volume,
            0,
        )

    def test_concrete_strength_validation(self) -> None:
        result = self.code.validate_concrete(
            fc_mpa=25,
        )

        self.assertTrue(
            result.valid,
        )


# ---------------------------------------------------------------------------
# TEST REINFORCEMENT CODE
# ---------------------------------------------------------------------------

class TestIranReinforcement(unittest.TestCase):

    def setUp(self) -> None:
        self.code = create_iran_reinforcement_code()

    def test_bar_area(self) -> None:
        area = self.code.bar_area(
            diameter_mm=16,
        )

        self.assertGreater(
            area,
            0,
        )

    def test_bar_weight(self) -> None:
        weight = self.code.bar_weight_kg_per_m(
            diameter_mm=16,
        )

        self.assertGreater(
            weight,
            0,
        )

    def test_total_bar_weight(self) -> None:
        total = self.code.total_bar_weight(
            diameter_mm=16,
            length_m=10,
            quantity=5,
        )

        self.assertGreater(
            total,
            0,
        )

    def test_reinforcement_ratio(self) -> None:
        ratio = self.code.reinforcement_ratio(
            steel_area_mm2=2000,
            gross_area_mm2=150000,
        )

        self.assertGreater(
            ratio,
            0,
        )

    def test_standard_diameters(self) -> None:
        diameters = self.code.available_diameters()

        self.assertIsInstance(
            diameters,
            (list, tuple),
        )

        self.assertIn(
            16,
            diameters,
        )

    def test_standard_grades(self) -> None:
        grades = self.code.available_grades()

        self.assertIsInstance(
            grades,
            (list, tuple),
        )

        self.assertGreater(
            len(grades),
            0,
        )


# ---------------------------------------------------------------------------
# TEST DETAILING CODE
# ---------------------------------------------------------------------------

class TestIranDetailing(unittest.TestCase):

    def setUp(self) -> None:
        self.code = create_iran_detailing_code()

    def test_cover_validation(self) -> None:
        result = self.code.check_cover(
            cover_mm=40,
        )

        self.assertTrue(
            result.valid,
        )

    def test_spacing_validation(self) -> None:
        result = self.code.check_spacing(
            spacing_mm=150,
        )

        self.assertIsNotNone(
            result,
        )

    def test_clear_spacing(self) -> None:
        result = self.code.clear_spacing(
            center_spacing_mm=150,
            bar_diameter_mm=16,
        )

        self.assertGreater(
            result,
            0,
        )


# ---------------------------------------------------------------------------
# TEST CODE CHECKS
# ---------------------------------------------------------------------------

class TestCodeChecks(unittest.TestCase):

    def test_concrete_check(self) -> None:
        code = create_iran_concrete_code()

        result = code.run_check(
            member_category=MemberCategory.COLUMN,
            check_type="concrete_strength",
            fc_mpa=25,
        )

        self.assertIsNotNone(
            result,
        )

    def test_reinforcement_check(self) -> None:
        code = create_iran_reinforcement_code()

        result = code.run_check(
            member_category=MemberCategory.BEAM,
            check_type="reinforcement_ratio",
            ratio_percent=1.0,
        )

        self.assertIsNotNone(
            result,
        )


# ---------------------------------------------------------------------------
# TEST ADAPTER CHECK
# ---------------------------------------------------------------------------

class TestAdapterChecks(unittest.TestCase):

    def test_adapter_run_check(self) -> None:
        code = create_iran_concrete_code()

        adapter = CodeAdapter(
            code,
        )

        result = adapter.run_check(
            member="column",
            check_type="concrete_strength",
            fc_mpa=25,
        )

        self.assertIsNotNone(
            result,
        )


# ---------------------------------------------------------------------------
# TEST ERROR HANDLING
# ---------------------------------------------------------------------------

class TestErrorHandling(unittest.TestCase):

    def test_adapter_without_code(self) -> None:
        adapter = CodeAdapter()

        with self.assertRaises(CodeNotConfiguredError):
            _ = adapter.code_id

    def test_adapter_without_code_family(self) -> None:
        adapter = CodeAdapter()

        with self.assertRaises(CodeNotConfiguredError):
            _ = adapter.family

    def test_invalid_context(self) -> None:
        adapter = CodeAdapter()

        with self.assertRaises(CodeNotConfiguredError):
            adapter.set_context(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TEST SUITE
# ---------------------------------------------------------------------------

def build_test_suite() -> unittest.TestSuite:
    """Build the complete design-code test suite."""

    loader = unittest.TestLoader()

    suite = unittest.TestSuite()

    test_classes = [
        TestMemberMapping,
        TestIranCodeFactories,
        TestCodeRegistry,
        TestCodeAdapter,
        TestIranConcrete,
        TestIranReinforcement,
        TestIranDetailing,
        TestCodeChecks,
        TestAdapterChecks,
        TestErrorHandling,
    ]

    for test_class in test_classes:
        suite.addTests(
            loader.loadTestsFromTestCase(
                test_class
            )
        )

    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(
        verbosity=2,
    )

    result = runner.run(
        build_test_suite()
    )

    raise SystemExit(
        0 if result.wasSuccessful() else 1
    )
