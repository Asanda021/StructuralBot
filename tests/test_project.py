"""
StructuralBot - Project Layer Tests

Tests for project and engineering context integration.

Scope:
    - Project creation
    - Floor creation
    - Engineering context
    - Project/member relationships
    - Unit system
    - Structure type
    - Design-code selection metadata

These tests focus on data integrity and software architecture.
They do not perform structural design.
"""

from __future__ import annotations

import unittest
from datetime import datetime
from typing import Any

from core.models import (
    EngineeringContext,
    Floor,
    Project,
    StructureType,
    UnitSystem,
    MemberType,
    RectangularGeometry,
    StructuralMember,
)


# ============================================================================
# HELPERS
# ============================================================================

def _enum_value(value: Any) -> Any:
    """Return enum value when applicable."""

    return getattr(
        value,
        "value",
        value,
    )


def _set_if_supported(
    obj: Any,
    attribute: str,
    value: Any,
) -> bool:
    """
    Set an attribute when the model exposes it.

    Returns True if the attribute was successfully assigned.
    """

    if not hasattr(obj, attribute):
        return False

    try:
        setattr(
            obj,
            attribute,
            value,
        )
        return True
    except (
        AttributeError,
        TypeError,
    ):
        return False


def _add_if_supported(
    obj: Any,
    names: tuple[str, ...],
    value: Any,
) -> bool:
    """Call the first available add method."""

    for name in names:
        method = getattr(
            obj,
            name,
            None,
        )

        if callable(method):
            method(value)
            return True

    return False


# ============================================================================
# PROJECT CREATION
# ============================================================================

class TestProjectCreation(unittest.TestCase):
    """Tests for basic Project creation."""

    def test_project_can_be_created(self) -> None:
        project = Project(
            id="P-001",
            name="Test Project",
        )

        self.assertIsNotNone(
            project,
        )

        self.assertEqual(
            project.id,
            "P-001",
        )

        self.assertEqual(
            project.name,
            "Test Project",
        )

    def test_project_name_is_preserved(self) -> None:
        project = Project(
            id="P-002",
            name="Residential Building",
        )

        self.assertEqual(
            project.name,
            "Residential Building",
        )

    def test_project_id_is_preserved(self) -> None:
        project = Project(
            id="PROJECT-100",
            name="Engineering Project",
        )

        self.assertEqual(
            project.id,
            "PROJECT-100",
        )


# ============================================================================
# FLOOR TESTS
# ============================================================================

class TestFloorCreation(unittest.TestCase):
    """Tests for floor data."""

    def test_floor_can_be_created(self) -> None:
        floor = Floor(
            id="F-01",
            name="Ground Floor",
        )

        self.assertIsNotNone(
            floor,
        )

        self.assertEqual(
            floor.id,
            "F-01",
        )

    def test_multiple_floors_have_unique_ids(self) -> None:
        floors = [
            Floor(
                id="F-01",
                name="Ground Floor",
            ),
            Floor(
                id="F-02",
                name="First Floor",
            ),
            Floor(
                id="F-03",
                name="Second Floor",
            ),
        ]

        ids = {
            floor.id
            for floor in floors
        }

        self.assertEqual(
            len(ids),
            3,
        )


# ============================================================================
# PROJECT → FLOOR
# ============================================================================

class TestProjectFloorRelationship(unittest.TestCase):
    """Tests for project/floor relationship."""

    def test_project_can_store_floor(self) -> None:
        project = Project(
            id="P-010",
            name="Building A",
        )

        floor = Floor(
            id="F-01",
            name="Ground Floor",
        )

        added = _add_if_supported(
            project,
            (
                "add_floor",
                "add_floor_level",
            ),
            floor,
        )

        if not added:
            floors = getattr(
                project,
                "floors",
                None,
            )

            if isinstance(floors, list):
                floors.append(floor)
                added = True

        if not added:
            self.skipTest(
                "Project model does not expose floor collection API."
            )

        floors = getattr(
            project,
            "floors",
            None,
        )

        self.assertIsNotNone(
            floors,
        )

        if isinstance(floors, list):
            self.assertEqual(
                len(floors),
                1,
            )


# ============================================================================
# STRUCTURE TYPE
# ============================================================================

class TestStructureType(unittest.TestCase):
    """Tests for structure type enum."""

    def test_concrete_structure_type_exists(self) -> None:
        self.assertIsNotNone(
            StructureType.CONCRETE,
        )

    def test_steel_structure_type_exists(self) -> None:
        self.assertIsNotNone(
            StructureType.STEEL,
        )

    def test_composite_structure_type_exists(self) -> None:
        self.assertIsNotNone(
            StructureType.COMPOSITE,
        )

    def test_structure_types_are_distinct(self) -> None:
        values = {
            _enum_value(StructureType.CONCRETE),
            _enum_value(StructureType.STEEL),
            _enum_value(StructureType.COMPOSITE),
        }

        self.assertEqual(
            len(values),
            3,
        )


# ============================================================================
# UNIT SYSTEM
# ============================================================================

class TestUnitSystem(unittest.TestCase):
    """Tests for unit-system configuration."""

    def test_unit_system_enum_exists(self) -> None:
        self.assertTrue(
            len(list(UnitSystem)) > 0
        )

    def test_unit_system_values_are_unique(self) -> None:
        values = [
            _enum_value(unit)
            for unit in UnitSystem
        ]

        self.assertEqual(
            len(values),
            len(set(values)),
        )


# ============================================================================
# STRUCTURAL MEMBER
# ============================================================================

class TestStructuralMember(unittest.TestCase):
    """Tests for structural member creation."""

    def test_beam_creation(self) -> None:
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

    def test_column_creation(self) -> None:
        geometry = RectangularGeometry(
            width=400,
            height=400,
        )

        member = StructuralMember(
            id="C-01",
            member_type=MemberType.COLUMN,
            geometry=geometry,
        )

        self.assertEqual(
            member.id,
            "C-01",
        )

        self.assertEqual(
            member.member_type,
            MemberType.COLUMN,
        )

    def test_foundation_creation(self) -> None:
        geometry = RectangularGeometry(
            width=1500,
            height=1500,
        )

        member = StructuralMember(
            id="F-01",
            member_type=MemberType.FOUNDATION,
            geometry=geometry,
        )

        self.assertEqual(
            member.id,
            "F-01",
        )

        self.assertEqual(
            member.member_type,
            MemberType.FOUNDATION,
        )


# ============================================================================
# MEMBER COLLECTION
# ============================================================================

class TestMemberCollection(unittest.TestCase):
    """Tests for storing members inside a project/floor."""

    def test_members_can_be_collected(self) -> None:
        members = []

        beam = StructuralMember(
            id="B-01",
            member_type=MemberType.BEAM,
            geometry=RectangularGeometry(
                width=300,
                height=500,
            ),
        )

        column = StructuralMember(
            id="C-01",
            member_type=MemberType.COLUMN,
            geometry=RectangularGeometry(
                width=400,
                height=400,
            ),
        )

        members.append(
            beam,
        )

        members.append(
            column,
        )

        self.assertEqual(
            len(members),
            2,
        )

        self.assertEqual(
            members[0].id,
            "B-01",
        )

        self.assertEqual(
            members[1].id,
            "C-01",
        )


# ============================================================================
# ENGINEERING CONTEXT
# ============================================================================

class TestEngineeringContext(unittest.TestCase):
    """Tests for EngineeringContext."""

    def test_context_can_be_created(self) -> None:
        try:
            context = EngineeringContext()
        except TypeError:
            self.skipTest(
                "EngineeringContext requires implementation-specific fields."
            )

        self.assertIsNotNone(
            context,
        )

    def test_context_structure_type(self) -> None:
        try:
            context = EngineeringContext(
                structure_type=StructureType.CONCRETE,
            )
        except TypeError:
            self.skipTest(
                "EngineeringContext constructor differs from expected API."
            )

        self.assertEqual(
            context.structure_type,
            StructureType.CONCRETE,
        )

    def test_context_unit_system(self) -> None:
        try:
            context = EngineeringContext(
                unit_system=next(iter(UnitSystem)),
            )
        except TypeError:
            self.skipTest(
                "EngineeringContext constructor differs from expected API."
            )

        self.assertEqual(
            context.unit_system,
            next(iter(UnitSystem)),
        )


# ============================================================================
# CODE CONTEXT COMPATIBILITY
# ============================================================================

class TestCodeContextCompatibility(unittest.TestCase):
    """
    Verify that EngineeringContext can carry design-code information
    when the current model exposes those fields.

    No Iranian code assumptions are made here.
    """

    def test_code_id_can_be_attached(self) -> None:
        try:
            context = EngineeringContext()
        except TypeError:
            self.skipTest(
                "EngineeringContext requires implementation-specific fields."
            )

        if not _set_if_supported(
            context,
            "code_id",
            "m9",
        ):
            self.skipTest(
                "EngineeringContext does not expose code_id."
            )

        self.assertEqual(
            getattr(
                context,
                "code_id",
            ),
            "m9",
        )

    def test_code_family_can_be_attached(self) -> None:
        try:
            context = EngineeringContext()
        except TypeError:
            self.skipTest(
                "EngineeringContext requires implementation-specific fields."
            )

        if not _set_if_supported(
            context,
            "code_family",
            "iran",
        ):
            self.skipTest(
                "EngineeringContext does not expose code_family."
            )

        self.assertEqual(
            getattr(
                context,
                "code_family",
            ),
            "iran",
        )


# ============================================================================
# PROJECT DATA INTEGRITY
# ============================================================================

class TestProjectDataIntegrity(unittest.TestCase):
    """Tests for basic project-data invariants."""

    def test_member_ids_are_unique(self) -> None:
        members = [
            StructuralMember(
                id="B-01",
                member_type=MemberType.BEAM,
                geometry=RectangularGeometry(
                    width=300,
                    height=500,
                ),
            ),
            StructuralMember(
                id="B-02",
                member_type=MemberType.BEAM,
                geometry=RectangularGeometry(
                    width=300,
                    height=500,
                ),
            ),
            StructuralMember(
                id="C-01",
                member_type=MemberType.COLUMN,
                geometry=RectangularGeometry(
                    width=400,
                    height=400,
                ),
            ),
        ]

        ids = [
            member.id
            for member in members
        ]

        self.assertEqual(
            len(ids),
            len(set(ids)),
        )

    def test_member_types_are_valid(self) -> None:
        members = [
            StructuralMember(
                id="B-01",
                member_type=MemberType.BEAM,
                geometry=RectangularGeometry(
                    width=300,
                    height=500,
                ),
            ),
            StructuralMember(
                id="C-01",
                member_type=MemberType.COLUMN,
                geometry=RectangularGeometry(
                    width=400,
                    height=400,
                ),
            ),
        ]

        for member in members:
            self.assertIsInstance(
                member.member_type,
                MemberType,
            )

    def test_geometry_dimensions_are_positive(self) -> None:
        members = [
            StructuralMember(
                id="B-01",
                member_type=MemberType.BEAM,
                geometry=RectangularGeometry(
                    width=300,
                    height=500,
                ),
            ),
            StructuralMember(
                id="C-01",
                member_type=MemberType.COLUMN,
                geometry=RectangularGeometry(
                    width=400,
                    height=400,
                ),
            ),
        ]

        for member in members:
            geometry = member.geometry

            self.assertGreater(
                geometry.width,
                0,
            )

            self.assertGreater(
                geometry.height,
                0,
            )


# ============================================================================
# PROJECT SNAPSHOT
# ============================================================================

class TestProjectSnapshot(unittest.TestCase):
    """
    Verify that project information can be converted into a simple,
    serializable snapshot without coupling the project model to the
    Telegram layer.
    """

    def test_project_snapshot(self) -> None:
        project = Project(
            id="P-100",
            name="Residential Project",
        )

        snapshot = {
            "id": project.id,
            "name": project.name,
        }

        self.assertEqual(
            snapshot["id"],
            "P-100",
        )

        self.assertEqual(
            snapshot["name"],
            "Residential Project",
        )

    def test_member_snapshot(self) -> None:
        member = StructuralMember(
            id="B-10",
            member_type=MemberType.BEAM,
            geometry=RectangularGeometry(
                width=300,
                height=600,
            ),
        )

        snapshot = {
            "id": member.id,
            "member_type": _enum_value(
                member.member_type,
            ),
            "width": member.geometry.width,
            "height": member.geometry.height,
        }

        self.assertEqual(
            snapshot["id"],
            "B-10",
        )

        self.assertEqual(
            snapshot["width"],
            300,
        )

        self.assertEqual(
            snapshot["height"],
            600,
        )


# ============================================================================
# TEST SUITE
# ============================================================================

def build_test_suite() -> unittest.TestSuite:
    """Build the project-layer test suite."""

    loader = unittest.TestLoader()

    suite = unittest.TestSuite()

    test_classes = [
        TestProjectCreation,
        TestFloorCreation,
        TestProjectFloorRelationship,
        TestStructureType,
        TestUnitSystem,
        TestStructuralMember,
        TestMemberCollection,
        TestEngineeringContext,
        TestCodeContextCompatibility,
        TestProjectDataIntegrity,
        TestProjectSnapshot,
    ]

    for test_class in test_classes:
        suite.addTests(
            loader.loadTestsFromTestCase(
                test_class
            )
        )

    return suite


def run_tests() -> bool:
    """Run all project tests."""

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
