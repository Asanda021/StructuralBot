"""
StructuralBot domain models.

This module defines the standard data models used across
projects, floors, structural members, materials,
reinforcement, calculations and calculation results.

The models are intentionally independent from:
- Telegram
- Database implementation
- Design codes
- Localization
- UI

This keeps the calculation engine portable and maintainable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================
# ENUMS
# ============================================================


class UnitSystem(str, Enum):
    SI = "SI"
    IMPERIAL = "Imperial"


class StructureType(str, Enum):
    CONCRETE = "concrete"
    STEEL = "steel"
    COMPOSITE = "composite"


class MemberType(str, Enum):
    FOUNDATION = "foundation"
    COLUMN = "column"
    BEAM = "beam"
    SLAB = "slab"
    STAIR = "stair"
    WALL = "wall"
    OTHER = "other"


class FoundationType(str, Enum):
    ISOLATED = "isolated"
    STRIP = "strip"
    RAFT = "raft"
    COMBINED = "combined"
    OTHER = "other"


class ColumnType(str, Enum):
    RECTANGULAR = "rectangular"
    ROUND = "round"


class BeamType(str, Enum):
    MAIN = "main"
    SECONDARY = "secondary"
    TIE = "tie"


class SlabType(str, Enum):
    SOLID = "solid"
    JOIST_BLOCK = "joist_block"
    JOIST_POLYSTYRENE = "joist_polystyrene"
    WAFFLE = "waffle"
    FLAT = "flat"
    ONE_WAY = "one_way"
    TWO_WAY = "two_way"
    VOIDED = "voided"
    OTHER = "other"


class ReinforcementType(str, Enum):
    LONGITUDINAL = "longitudinal"
    TRANSVERSE = "transverse"
    TOP = "top"
    BOTTOM = "bottom"
    DISTRIBUTION = "distribution"
    TEMPERATURE = "temperature"
    NEGATIVE = "negative"
    POSITIVE = "positive"
    STIRRUP = "stirrup"
    TIE = "tie"
    SHEAR = "shear"
    OTHER = "other"


class SpliceType(str, Enum):
    LAP = "lap"
    COUPLER = "coupler"
    OTHER = "other"


class CalculationStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"


# ============================================================
# MATERIAL MODELS
# ============================================================


@dataclass
class ConcreteMaterial:
    """
    Concrete material properties.

    Strength values are stored in MPa in the SI system.
    """

    grade: str
    fck: float
    density: float = 2400.0
    unit: str = "MPa"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grade": self.grade,
            "fck": self.fck,
            "density": self.density,
            "unit": self.unit,
        }


@dataclass
class SteelMaterial:
    """
    Reinforcing steel material properties.

    fy:
        Yield strength in MPa.

    fu:
        Ultimate strength in MPa.
    """

    grade: str
    fy: float
    fu: Optional[float] = None
    density: float = 7850.0
    unit: str = "MPa"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grade": self.grade,
            "fy": self.fy,
            "fu": self.fu,
            "density": self.density,
            "unit": self.unit,
        }


@dataclass
class MaterialSet:
    """
    Complete material definition for a structural member.
    """

    concrete: Optional[ConcreteMaterial] = None
    reinforcement: Optional[SteelMaterial] = None
    structural_steel: Optional[SteelMaterial] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concrete": (
                self.concrete.to_dict()
                if self.concrete
                else None
            ),
            "reinforcement": (
                self.reinforcement.to_dict()
                if self.reinforcement
                else None
            ),
            "structural_steel": (
                self.structural_steel.to_dict()
                if self.structural_steel
                else None
            ),
        }


# ============================================================
# PROJECT MODELS
# ============================================================


@dataclass
class Project:
    """
    Main structural project model.
    """

    id: Optional[int]
    user_id: int
    name: str

    description: str = ""

    structure_type: StructureType = StructureType.CONCRETE

    design_code: str = ""
    code_edition: str = ""

    unit_system: UnitSystem = UnitSystem.SI

    status: str = "active"

    floors: List["Floor"] = field(default_factory=list)
    members: List["StructuralMember"] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_floor(self, floor: "Floor") -> None:
        self.floors.append(floor)

    def add_member(self, member: "StructuralMember") -> None:
        self.members.append(member)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "structure_type": self.structure_type.value,
            "design_code": self.design_code,
            "code_edition": self.code_edition,
            "unit_system": self.unit_system.value,
            "status": self.status,
            "floors": [
                floor.to_dict()
                for floor in self.floors
            ],
            "members": [
                member.to_dict()
                for member in self.members
            ],
            "metadata": self.metadata,
        }


@dataclass
class Floor:
    """
    Building floor model.
    """

    id: Optional[int]
    project_id: int

    name: str
    floor_number: int

    height: Optional[float] = None

    members: List["StructuralMember"] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_member(self, member: "StructuralMember") -> None:
        self.members.append(member)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "floor_number": self.floor_number,
            "height": self.height,
            "members": [
                member.to_dict()
                for member in self.members
            ],
            "metadata": self.metadata,
        }


# ============================================================
# GEOMETRY MODELS
# ============================================================


@dataclass
class RectangularGeometry:
    """
    Rectangular section geometry.

    All dimensions are expressed in the selected unit system.
    """

    width: float
    height: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "rectangular",
            "width": self.width,
            "height": self.height,
        }


@dataclass
class CircularGeometry:
    """
    Circular section geometry.
    """

    diameter: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "circular",
            "diameter": self.diameter,
        }


@dataclass
class SlabGeometry:
    """
    Generic slab geometry.
    """

    length: float
    width: float
    thickness: float

    rib_height: Optional[float] = None
    rib_width: Optional[float] = None
    rib_spacing: Optional[float] = None

    opening_area: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "slab",
            "length": self.length,
            "width": self.width,
            "thickness": self.thickness,
            "rib_height": self.rib_height,
            "rib_width": self.rib_width,
            "rib_spacing": self.rib_spacing,
            "opening_area": self.opening_area,
        }


# ============================================================
# STRUCTURAL MEMBER
# ============================================================


@dataclass
class StructuralMember:
    """
    Generic structural member.

    Specific member types such as beams, columns,
    foundations and slabs use this model with
    specialized geometry/input dictionaries.

    The calculation engine should not depend on Telegram
    or database structures.
    """

    id: Optional[int]
    project_id: int

    member_type: MemberType

    name: str

    floor_id: Optional[int] = None

    geometry: Dict[str, Any] = field(default_factory=dict)
    material: MaterialSet = field(
        default_factory=MaterialSet
    )

    inputs: Dict[str, Any] = field(default_factory=dict)

    results: Dict[str, Any] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def set_input(self, key: str, value: Any) -> None:
        self.inputs[key] = value

    def get_input(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.inputs.get(key, default)

    def set_result(self, key: str, value: Any) -> None:
        self.results[key] = value

    def get_result(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.results.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "floor_id": self.floor_id,
            "member_type": self.member_type.value,
            "name": self.name,
            "geometry": self.geometry,
            "material": self.material.to_dict(),
            "inputs": self.inputs,
            "results": self.results,
            "metadata": self.metadata,
        }


# ============================================================
# REINFORCEMENT MODELS
# ============================================================


@dataclass
class RebarShape:
    """
    Parametric reinforcement shape.

    dimensions:
        Named dimensions such as A, B, C, etc.

    The actual drawing engine can later use this
    parametric definition to generate a visual shape.
    """

    shape_code: str

    dimensions: Dict[str, float] = field(
        default_factory=dict
    )

    hooks: Dict[str, Any] = field(
        default_factory=dict
    )

    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shape_code": self.shape_code,
            "dimensions": self.dimensions,
            "hooks": self.hooks,
            "notes": self.notes,
        }


@dataclass
class ReinforcementBar:
    """
    A real reinforcement bar definition.

    Important:
    length represents the actual cut piece length,
    not merely a theoretical total reinforcement length.
    """

    bar_mark: str

    diameter: float
    quantity: int

    length: float

    bar_type: ReinforcementType

    grade: str = ""

    location: str = ""

    shape: Optional[RebarShape] = None

    total_length: Optional[float] = None
    weight: Optional[float] = None

    member_id: Optional[int] = None
    floor_id: Optional[int] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_total_length(self) -> float:
        self.total_length = (
            self.length * self.quantity
        )
        return self.total_length

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bar_mark": self.bar_mark,
            "diameter": self.diameter,
            "quantity": self.quantity,
            "length": self.length,
            "total_length": self.total_length,
            "weight": self.weight,
            "bar_type": self.bar_type.value,
            "grade": self.grade,
            "location": self.location,
            "shape": (
                self.shape.to_dict()
                if self.shape
                else None
            ),
            "member_id": self.member_id,
            "floor_id": self.floor_id,
            "metadata": self.metadata,
        }


# ============================================================
# SPLICE MODELS
# ============================================================


@dataclass
class Splice:
    """
    Reinforcement splice.

    The actual splice length must be calculated by
    the selected design code and should never be
    hard-coded in this model.
    """

    splice_type: SpliceType

    diameter: float

    quantity: int

    location: str = ""

    length: Optional[float] = None

    member_id: Optional[int] = None
    floor_id: Optional[int] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "splice_type": self.splice_type.value,
            "diameter": self.diameter,
            "quantity": self.quantity,
            "location": self.location,
            "length": self.length,
            "member_id": self.member_id,
            "floor_id": self.floor_id,
            "metadata": self.metadata,
        }


# ============================================================
# CALCULATION RESULT MODELS
# ============================================================


@dataclass
class CheckResult:
    """
    Individual engineering check.

    utilization:
        Demand/capacity ratio when applicable.

    passed:
        True / False / None when a binary pass/fail
        result is not applicable.
    """

    name: str

    passed: Optional[bool]

    value: Optional[float] = None
    capacity: Optional[float] = None
    utilization: Optional[float] = None

    unit: str = ""

    message: str = ""

    code_reference: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "value": self.value,
            "capacity": self.capacity,
            "utilization": self.utilization,
            "unit": self.unit,
            "message": self.message,
            "code_reference": self.code_reference,
        }


@dataclass
class CalculationResult:
    """
    Standard output returned by the calculation engine.

    This object is shared by:
    - Telegram
    - PDF
    - Excel
    - API
    - AI assistant
    """

    calculation_type: str

    status: CalculationStatus

    member_id: Optional[int] = None

    summary: Dict[str, Any] = field(
        default_factory=dict
    )

    checks: List[CheckResult] = field(
        default_factory=list
    )

    reinforcement: List[ReinforcementBar] = field(
        default_factory=list
    )

    splices: List[Splice] = field(
        default_factory=list
    )

    quantities: Dict[str, Any] = field(
        default_factory=dict
    )

    warnings: List[str] = field(
        default_factory=list
    )

    errors: List[str] = field(
        default_factory=list
    )

    code: str = ""
    code_edition: str = ""

    calculation_details: Dict[str, Any] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def add_check(
        self,
        check: CheckResult,
    ) -> None:
        self.checks.append(check)

    def add_reinforcement(
        self,
        bar: ReinforcementBar,
    ) -> None:
        self.reinforcement.append(bar)

    def add_splice(
        self,
        splice: Splice,
    ) -> None:
        self.splices.append(splice)

    def add_warning(
        self,
        message: str,
    ) -> None:
        self.warnings.append(message)

    def add_error(
        self,
        message: str,
    ) -> None:
        self.errors.append(message)
        self.status = CalculationStatus.FAILED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calculation_type": self.calculation_type,
            "status": self.status.value,
            "member_id": self.member_id,
            "summary": self.summary,
            "checks": [
                check.to_dict()
                for check in self.checks
            ],
            "reinforcement": [
                bar.to_dict()
                for bar in self.reinforcement
            ],
            "splices": [
                splice.to_dict()
                for splice in self.splices
            ],
            "quantities": self.quantities,
            "warnings": self.warnings,
            "errors": self.errors,
            "code": self.code,
            "code_edition": self.code_edition,
            "calculation_details": self.calculation_details,
            "metadata": self.metadata,
        }


# ============================================================
# CUT LIST MODELS
# ============================================================


@dataclass
class CutPiece:
    """
    One actual cut piece of reinforcement.
    """

    bar_mark: str

    diameter: float

    length: float

    quantity: int = 1

    shape_code: str = ""

    shape_data: Dict[str, Any] = field(
        default_factory=dict
    )

    member_id: Optional[int] = None
    floor_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bar_mark": self.bar_mark,
            "diameter": self.diameter,
            "length": self.length,
            "quantity": self.quantity,
            "shape_code": self.shape_code,
            "shape_data": self.shape_data,
            "member_id": self.member_id,
            "floor_id": self.floor_id,
        }


@dataclass
class StockBar:
    """
    One stock reinforcement bar, normally 12 m.

    The cutting optimizer will place actual cut pieces
    into stock bars.
    """

    diameter: float

    stock_length: float = 12.0

    pieces: List[CutPiece] = field(
        default_factory=list
    )

    used_length: float = 0.0
    waste: float = 0.0

    def add_piece(
        self,
        piece: CutPiece,
    ) -> bool:
        """
        Add a piece if it fits into the remaining
        stock-bar length.
        """

        if (
            self.used_length
            + piece.length
            > self.stock_length
        ):
            return False

        self.pieces.append(piece)
        self.used_length += (
            piece.length * piece.quantity
        )

        self.waste = (
            self.stock_length
            - self.used_length
        )

        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diameter": self.diameter,
            "stock_length": self.stock_length,
            "pieces": [
                piece.to_dict()
                for piece in self.pieces
            ],
            "used_length": self.used_length,
            "waste": self.waste,
        }


@dataclass
class CutListResult:
    """
    Complete Cut List result.
    """

    stock_length: float = 12.0

    stock_bars: List[StockBar] = field(
        default_factory=list
    )

    total_stock_bars: int = 0
    total_used_length: float = 0.0
    total_waste: float = 0.0
    waste_percentage: float = 0.0

    by_diameter: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stock_length": self.stock_length,
            "stock_bars": [
                stock.to_dict()
                for stock in self.stock_bars
            ],
            "total_stock_bars": self.total_stock_bars,
            "total_used_length": self.total_used_length,
            "total_waste": self.total_waste,
            "waste_percentage": self.waste_percentage,
            "by_diameter": self.by_diameter,
        }


# ============================================================
# QUANTITY TAKEOFF
# ============================================================


@dataclass
class MaterialQuantity:
    """
    Basic project material quantity.

    This is intentionally a quantity model,
    not a full commercial BOQ/estimating model.
    """

    material_type: str

    quantity: float

    unit: str

    member_id: Optional[int] = None

    floor_id: Optional[int] = None

    details: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "material_type": self.material_type,
            "quantity": self.quantity,
            "unit": self.unit,
            "member_id": self.member_id,
            "floor_id": self.floor_id,
            "details": self.details,
        }


# ============================================================
# USER SETTINGS
# ============================================================


@dataclass
class UserSettings:
    """
    User-level preferences.

    Project-specific engineering settings belong to Project,
    not here.
    """

    language: str = "fa"

    unit_system: UnitSystem = UnitSystem.SI

    profession: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "unit_system": self.unit_system.value,
            "profession": self.profession,
            "metadata": self.metadata,
        }


# ============================================================
# ENGINEERING CONTEXT
# ============================================================


@dataclass
class EngineeringContext:
    """
    Runtime context passed to calculation modules.

    This is the bridge between project settings,
    selected design code and the calculation engine.

    It deliberately contains no Telegram-specific data.
    """

    language: str

    structure_type: StructureType

    design_code: str

    code_edition: str

    unit_system: UnitSystem

    project_id: Optional[int] = None

    member_id: Optional[int] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "structure_type": self.structure_type.value,
            "design_code": self.design_code,
            "code_edition": self.code_edition,
            "unit_system": self.unit_system.value,
            "project_id": self.project_id,
            "member_id": self.member_id,
            "metadata": self.metadata,
        }


# ============================================================
# SERIALIZATION HELPERS
# ============================================================


def enum_value(value: Any) -> Any:
    """
    Convert an Enum to its raw value.

    Useful for generic serializers and database adapters.
    """

    if isinstance(value, Enum):
        return value.value

    return value
