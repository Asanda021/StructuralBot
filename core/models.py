"""
StructuralBot - Core Models

Central domain models for StructuralBot.

Design principles:
- Domain models contain data, not engineering calculations.
- Core models are independent from Telegram, AI, billing and reports.
- Engineering traceability is preserved through project/member/calculation
  identifiers and revisions.
- Units, structure type, member type and design code remain independent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence


# =====================================================================
# COMMON ENUMS
# =====================================================================

class UnitSystem(str, Enum):
    METRIC = "metric"
    SI = "si"


class StructureType(str, Enum):
    CONCRETE = "concrete"
    STEEL = "steel"
    COMPOSITE = "composite"
    MASONRY = "masonry"
    TIMBER = "timber"
    OTHER = "other"


class MemberType(str, Enum):
    FOUNDATION_ISOLATED = "foundation_iso"
    FOUNDATION_STRIP = "foundation_strip"
    FOUNDATION_RAFT = "foundation_raft"

    COLUMN_RECT = "column_rect"
    COLUMN_ROUND = "column_round"

    BEAM_MAIN = "beam_main"
    BEAM_SECONDARY = "beam_secondary"
    TIE_BEAM = "tie_beam"

    SLAB = "slab"
    ROOF_SLAB = "roof_slab"
    WALL = "wall"
    STAIR = "stair"


class FoundationType(str, Enum):
    ISOLATED = "isolated"
    STRIP = "strip"
    RAFT = "raft"


class ColumnType(str, Enum):
    RECTANGULAR = "rectangular"
    CIRCULAR = "circular"


class BeamType(str, Enum):
    MAIN = "main"
    SECONDARY = "secondary"
    TIE = "tie"


class SlabType(str, Enum):
    ONE_WAY = "one_way"
    TWO_WAY = "two_way"
    FLAT = "flat"
    ROOF = "roof"


class ReinforcementType(str, Enum):
    LONGITUDINAL = "longitudinal"
    TRANSVERSE = "transverse"
    STIRRUP = "stirrup"
    TIE = "tie"
    MESH = "mesh"
    DISTRIBUTION = "distribution"
    TEMPERATURE = "temperature"
    TOP = "top"
    BOTTOM = "bottom"
    SIDE = "side"
    OTHER = "other"


class SpliceType(str, Enum):
    LAP = "lap"
    MECHANICAL = "mechanical"
    WELDED = "welded"
    NONE = "none"


class CalculationStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    CALCULATED = "calculated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    FAILED = "failed"


# =====================================================================
# HELPERS
# =====================================================================

def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def enum_value(value: Any) -> Any:
    """Return enum value when applicable."""
    if isinstance(value, Enum):
        return value.value
    return value


def _serialize(value: Any) -> Any:
    """Recursively convert domain objects into JSON-friendly structures."""
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        return value.isoformat()

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()

    if isinstance(value, Mapping):
        return {
            str(key): _serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [_serialize(item) for item in value]

    return value


# =====================================================================
# MATERIALS
# =====================================================================

@dataclass(slots=True)
class ConcreteMaterial:
    """Concrete material definition."""

    grade: str = "C25"
    fc_mpa: float = 25.0
    density_kg_m3: float = 2400.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grade": self.grade,
            "fc_mpa": self.fc_mpa,
            "density_kg_m3": self.density_kg_m3,
        }


@dataclass(slots=True)
class SteelMaterial:
    """Reinforcing steel definition."""

    grade: str = "A3"
    fy_mpa: float = 400.0
    fu_mpa: Optional[float] = 600.0
    density_kg_m3: float = 7850.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grade": self.grade,
            "fy_mpa": self.fy_mpa,
            "fu_mpa": self.fu_mpa,
            "density_kg_m3": self.density_kg_m3,
        }


@dataclass(slots=True)
class MaterialSet:
    """Collection of materials used by a structural calculation."""

    concrete: Optional[ConcreteMaterial] = None
    reinforcement: Optional[SteelMaterial] = None
    structural_steel: Optional[SteelMaterial] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concrete": _serialize(self.concrete),
            "reinforcement": _serialize(self.reinforcement),
            "structural_steel": _serialize(self.structural_steel),
        }


# =====================================================================
# PROJECT / FLOOR
# =====================================================================

@dataclass(slots=True)
class Project:
    """Top-level engineering project."""

    project_id: str
    name: str

    structure_type: StructureType = StructureType.CONCRETE
    unit_system: UnitSystem = UnitSystem.METRIC

    design_code: Optional[str] = None
    code_edition: Optional[str] = None

    revision: int = 1

    description: str = ""
    owner_id: Optional[str] = None

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    status: CalculationStatus = CalculationStatus.DRAFT

    metadata: Dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def next_revision(self) -> int:
        self.revision += 1
        self.touch()
        return self.revision

    @property
    def revision_id(self) -> str:
        return f"{self.project_id}-R{self.revision:02d}"

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "project_id": self.project_id,
            "name": self.name,
            "structure_type": self.structure_type,
            "unit_system": self.unit_system,
            "design_code": self.design_code,
            "code_edition": self.code_edition,
            "revision": self.revision,
            "revision_id": self.revision_id,
            "description": self.description,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "metadata": self.metadata,
        })


@dataclass(slots=True)
class Floor:
    """Project floor/storey."""

    floor_id: str
    project_id: str

    name: str
    level: int = 0
    elevation_m: float = 0.0

    revision: int = 1

    metadata: Dict[str, Any] = field(default_factory=dict)

    def next_revision(self) -> int:
        self.revision += 1
        return self.revision

    @property
    def revision_id(self) -> str:
        return f"{self.floor_id}-R{self.revision:02d}"

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "floor_id": self.floor_id,
            "project_id": self.project_id,
            "name": self.name,
            "level": self.level,
            "elevation_m": self.elevation_m,
            "revision": self.revision,
            "revision_id": self.revision_id,
            "metadata": self.metadata,
        })


# =====================================================================
# GEOMETRY
# =====================================================================

@dataclass(slots=True)
class RectangularGeometry:
    width_m: float
    depth_m: float
    height_m: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "rectangular",
            "width_m": self.width_m,
            "depth_m": self.depth_m,
            "height_m": self.height_m,
        }


@dataclass(slots=True)
class CircularGeometry:
    diameter_m: float
    height_m: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "circular",
            "diameter_m": self.diameter_m,
            "height_m": self.height_m,
        }


@dataclass(slots=True)
class SlabGeometry:
    length_m: float
    width_m: float
    thickness_m: float

    support_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "slab",
            "length_m": self.length_m,
            "width_m": self.width_m,
            "thickness_m": self.thickness_m,
            "support_type": self.support_type,
        }


# =====================================================================
# STRUCTURAL MEMBER
# =====================================================================

@dataclass(slots=True)
class StructuralMember:
    """
    Generic structural member.

    This model deliberately does not contain engineering formulas.
    It is the common data contract between handlers, core calculations,
    code adapters, reinforcement and reporting.
    """

    member_id: str
    project_id: str
    member_type: MemberType

    name: str = ""

    floor_id: Optional[str] = None
    mark: Optional[str] = None

    structure_type: StructureType = StructureType.CONCRETE

    geometry: Optional[Any] = None
    materials: Optional[MaterialSet] = None

    cover_mm: Optional[float] = None

    revision: int = 1
    status: CalculationStatus = CalculationStatus.DRAFT

    metadata: Dict[str, Any] = field(default_factory=dict)

    def next_revision(self) -> int:
        self.revision += 1
        return self.revision

    @property
    def revision_id(self) -> str:
        return f"{self.member_id}-R{self.revision:02d}"

    @property
    def member_mark(self) -> str:
        return self.mark or self.member_id

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "member_id": self.member_id,
            "project_id": self.project_id,
            "member_type": self.member_type,
            "name": self.name,
            "floor_id": self.floor_id,
            "mark": self.mark,
            "member_mark": self.member_mark,
            "structure_type": self.structure_type,
            "geometry": self.geometry,
            "materials": self.materials,
            "cover_mm": self.cover_mm,
            "revision": self.revision,
            "revision_id": self.revision_id,
            "status": self.status,
            "metadata": self.metadata,
        })


# =====================================================================
# REBAR SHAPE / REINFORCEMENT
# =====================================================================

@dataclass(slots=True)
class RebarShape:
    """Geometric description of a reinforcing bar shape."""

    shape_code: str = "STRAIGHT"

    dimensions_mm: Dict[str, float] = field(default_factory=dict)

    hook_start: Optional[str] = None
    hook_end: Optional[str] = None

    bend_angles_deg: List[float] = field(default_factory=list)

    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "shape_code": self.shape_code,
            "dimensions_mm": self.dimensions_mm,
            "hook_start": self.hook_start,
            "hook_end": self.hook_end,
            "bend_angles_deg": self.bend_angles_deg,
            "description": self.description,
        })


@dataclass(slots=True)
class ReinforcementBar:
    """
    Engineering reinforcement item.

    This object is intentionally richer than a simple diameter/quantity
    record so BBS, Cut List and reports can preserve traceability.
    """

    bar_id: str

    member_id: str
    project_id: str

    diameter_mm: float
    quantity: int

    length_m: float

    reinforcement_type: ReinforcementType = ReinforcementType.LONGITUDINAL

    grade: Optional[str] = None

    spacing_mm: Optional[float] = None

    role: Optional[str] = None
    region: Optional[str] = None

    shape: Optional[RebarShape] = None

    development_length_m: float = 0.0
    lap_length_m: float = 0.0

    splice_type: SpliceType = SpliceType.NONE

    bar_mark: Optional[str] = None

    floor_id: Optional[str] = None

    source_calculation_id: Optional[str] = None
    source_revision: Optional[int] = None

    notes: str = ""

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def mark(self) -> str:
        return self.bar_mark or self.bar_id

    @property
    def theoretical_weight_kg(self) -> float:
        """
        Approximate steel weight using the standard mass approximation:

            kg/m ≈ d² / 162

        This is a physical property helper, not a design rule.
        """
        return (self.diameter_mm ** 2 / 162.0) * self.length_m * self.quantity

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "bar_id": self.bar_id,
            "member_id": self.member_id,
            "project_id": self.project_id,
            "diameter_mm": self.diameter_mm,
            "quantity": self.quantity,
            "length_m": self.length_m,
            "reinforcement_type": self.reinforcement_type,
            "grade": self.grade,
            "spacing_mm": self.spacing_mm,
            "role": self.role,
            "region": self.region,
            "shape": self.shape,
            "development_length_m": self.development_length_m,
            "lap_length_m": self.lap_length_m,
            "splice_type": self.splice_type,
            "bar_mark": self.mark,
            "floor_id": self.floor_id,
            "source_calculation_id": self.source_calculation_id,
            "source_revision": self.source_revision,
            "theoretical_weight_kg": self.theoretical_weight_kg,
            "notes": self.notes,
            "metadata": self.metadata,
        })


@dataclass(slots=True)
class Splice:
    """Reinforcement splice information."""

    splice_id: str

    member_id: str
    bar_id: str

    splice_type: SpliceType

    position_m: Optional[float] = None
    length_m: Optional[float] = None

    region: Optional[str] = None

    source_calculation_id: Optional[str] = None

    notes: str = ""

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "splice_id": self.splice_id,
            "member_id": self.member_id,
            "bar_id": self.bar_id,
            "splice_type": self.splice_type,
            "position_m": self.position_m,
            "length_m": self.length_m,
            "region": self.region,
            "source_calculation_id": self.source_calculation_id,
            "notes": self.notes,
            "metadata": self.metadata,
        })


# =====================================================================
# ENGINEERING CHECKS / CALCULATION RESULTS
# =====================================================================

@dataclass(slots=True)
class CheckResult:
    """Result of one engineering/code check."""

    check_id: str

    name: str

    passed: bool

    status: str = "ok"

    value: Optional[float] = None
    limit: Optional[float] = None
    unit: Optional[str] = None

    clause: Optional[str] = None
    code: Optional[str] = None
    edition: Optional[str] = None

    message: str = ""

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "check_id": self.check_id,
            "name": self.name,
            "passed": self.passed,
            "status": self.status,
            "value": self.value,
            "limit": self.limit,
            "unit": self.unit,
            "clause": self.clause,
            "code": self.code,
            "edition": self.edition,
            "message": self.message,
            "metadata": self.metadata,
        })


@dataclass(slots=True)
class CalculationResult:
    """
    Unified engineering calculation result.

    All downstream modules should consume this contract rather than
    depending on a particular calculation implementation.
    """

    calculation_id: str

    project_id: str
    member_id: str

    member_type: MemberType

    status: CalculationStatus = CalculationStatus.CALCULATED

    revision: int = 1

    code: Optional[str] = None
    code_edition: Optional[str] = None

    inputs: Dict[str, Any] = field(default_factory=dict)

    values: Dict[str, Any] = field(default_factory=dict)

    checks: List[CheckResult] = field(default_factory=list)

    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    reinforcement: List[ReinforcementBar] = field(default_factory=list)

    created_at: datetime = field(default_factory=utc_now)

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def revision_id(self) -> str:
        return f"{self.calculation_id}-R{self.revision:02d}"

    @property
    def passed(self) -> bool:
        return bool(self.errors == []) and all(
            check.passed for check in self.checks
        )

    def add_check(self, check: CheckResult) -> None:
        self.checks.append(check)

    def add_warning(self, message: str) -> None:
        if message and message not in self.warnings:
            self.warnings.append(message)

    def add_error(self, message: str) -> None:
        if message and message not in self.errors:
            self.errors.append(message)
        self.status = CalculationStatus.FAILED

    def add_reinforcement(self, bar: ReinforcementBar) -> None:
        self.reinforcement.append(bar)

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "calculation_id": self.calculation_id,
            "project_id": self.project_id,
            "member_id": self.member_id,
            "member_type": self.member_type,
            "status": self.status,
            "revision": self.revision,
            "revision_id": self.revision_id,
            "code": self.code,
            "code_edition": self.code_edition,
            "inputs": self.inputs,
            "values": self.values,
            "checks": self.checks,
            "warnings": self.warnings,
            "errors": self.errors,
            "reinforcement": self.reinforcement,
            "created_at": self.created_at,
            "metadata": self.metadata,
        })


# =====================================================================
# BBS / CUT LIST
# =====================================================================

@dataclass(slots=True)
class CutPiece:
    """
    One physical cutting piece.

    Important:
    A quantity of 10 means ten physical pieces, not one piece with
    quantity=10 for optimization purposes.
    """

    piece_id: str

    bar_mark: str

    diameter_mm: float
    length_m: float

    quantity: int = 1

    member_id: Optional[str] = None
    project_id: Optional[str] = None

    floor_id: Optional[str] = None

    source_calculation_id: Optional[str] = None
    source_bbs_id: Optional[str] = None

    shape_code: Optional[str] = None

    region: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "piece_id": self.piece_id,
            "bar_mark": self.bar_mark,
            "diameter_mm": self.diameter_mm,
            "length_m": self.length_m,
            "quantity": self.quantity,
            "member_id": self.member_id,
            "project_id": self.project_id,
            "floor_id": self.floor_id,
            "source_calculation_id": self.source_calculation_id,
            "source_bbs_id": self.source_bbs_id,
            "shape_code": self.shape_code,
            "region": self.region,
            "metadata": self.metadata,
        })


@dataclass(slots=True)
class StockBar:
    """Physical stock bar used by the Cut List optimizer."""

    stock_id: str

    diameter_mm: float
    length_m: float

    pieces: List[CutPiece] = field(default_factory=list)

    def used_length_m(self) -> float:
        return sum(piece.length_m for piece in self.pieces)

    def remaining_length_m(self) -> float:
        return max(0.0, self.length_m - self.used_length_m())

    def add_piece(self, piece: CutPiece) -> bool:
        """
        Add one physical piece if it fits.

        Quantity is deliberately ignored here; callers should expand
        quantities into physical pieces before optimization.
        """
        if piece.length_m <= self.remaining_length_m() + 1e-9:
            self.pieces.append(piece)
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "stock_id": self.stock_id,
            "diameter_mm": self.diameter_mm,
            "length_m": self.length_m,
            "pieces": self.pieces,
            "used_length_m": self.used_length_m(),
            "remaining_length_m": self.remaining_length_m(),
        })


@dataclass(slots=True)
class CutListResult:
    """Complete optimized cutting result."""

    project_id: Optional[str] = None

    stock_length_m: float = 12.0

    stock_bars: List[StockBar] = field(default_factory=list)

    unallocated_pieces: List[CutPiece] = field(default_factory=list)

    total_stock_length_m: float = 0.0
    total_required_length_m: float = 0.0
    total_waste_length_m: float = 0.0

    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_totals(self) -> None:
        self.total_stock_length_m = sum(
            stock.length_m for stock in self.stock_bars
        )

        self.total_required_length_m = sum(
            piece.length_m
            for stock in self.stock_bars
            for piece in stock.pieces
        )

        self.total_waste_length_m = max(
            0.0,
            self.total_stock_length_m - self.total_required_length_m,
        )

    @property
    def waste_percentage(self) -> float:
        if self.total_stock_length_m <= 0:
            return 0.0

        return (
            self.total_waste_length_m
            / self.total_stock_length_m
            * 100.0
        )

    def to_dict(self) -> Dict[str, Any]:
        self.calculate_totals()

        return _serialize({
            "project_id": self.project_id,
            "stock_length_m": self.stock_length_m,
            "stock_bars": self.stock_bars,
            "unallocated_pieces": self.unallocated_pieces,
            "total_stock_length_m": self.total_stock_length_m,
            "total_required_length_m": self.total_required_length_m,
            "total_waste_length_m": self.total_waste_length_m,
            "waste_percentage": self.waste_percentage,
            "metadata": self.metadata,
        })


# =====================================================================
# MATERIAL QUANTITIES
# =====================================================================

@dataclass(slots=True)
class MaterialQuantity:
    """One material quantity item."""

    item_id: str

    project_id: str

    material_type: str

    quantity: float

    unit: str

    member_id: Optional[str] = None
    floor_id: Optional[str] = None

    description: str = ""

    source_calculation_id: Optional[str] = None
    source_bbs_id: Optional[str] = None
    source_cutlist_id: Optional[str] = None

    revision: int = 1

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "item_id": self.item_id,
            "project_id": self.project_id,
            "material_type": self.material_type,
            "quantity": self.quantity,
            "unit": self.unit,
            "member_id": self.member_id,
            "floor_id": self.floor_id,
            "description": self.description,
            "source_calculation_id": self.source_calculation_id,
            "source_bbs_id": self.source_bbs_id,
            "source_cutlist_id": self.source_cutlist_id,
            "revision": self.revision,
            "metadata": self.metadata,
        })


# =====================================================================
# USER SETTINGS
# =====================================================================

@dataclass(slots=True)
class UserSettings:
    """User-level application settings."""

    user_id: str

    language: str = "fa"
    unit_system: UnitSystem = UnitSystem.METRIC

    default_structure_type: StructureType = StructureType.CONCRETE

    default_design_code: Optional[str] = None
    default_code_edition: Optional[str] = None

    profession: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "user_id": self.user_id,
            "language": self.language,
            "unit_system": self.unit_system,
            "default_structure_type": self.default_structure_type,
            "default_design_code": self.default_design_code,
            "default_code_edition": self.default_code_edition,
            "profession": self.profession,
            "metadata": self.metadata,
        })


# =====================================================================
# ENGINEERING CONTEXT
# =====================================================================

@dataclass(slots=True)
class EngineeringContext:
    """
    Runtime engineering context shared between calculation modules.

    It carries configuration and traceability information, but does not
    perform engineering calculations.
    """

    project: Optional[Project] = None
    floor: Optional[Floor] = None
    member: Optional[StructuralMember] = None

    structure_type: Optional[StructureType] = None

    design_code: Optional[str] = None
    code_edition: Optional[str] = None

    unit_system: UnitSystem = UnitSystem.METRIC

    revision: int = 1

    calculation_id: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def resolve_structure_type(self) -> Optional[StructureType]:
        """
        Resolve structure type explicitly.

        Priority:
        1. Explicit context
        2. Member
        3. Project

        No silent fallback to concrete is performed.
        """
        if self.structure_type is not None:
            return self.structure_type

        if self.member is not None:
            return self.member.structure_type

        if self.project is not None:
            return self.project.structure_type

        return None

    def resolve_code(self) -> Optional[str]:
        if self.design_code:
            return self.design_code

        if self.project is not None:
            return self.project.design_code

        return None

    def resolve_code_edition(self) -> Optional[str]:
        if self.code_edition:
            return self.code_edition

        if self.project is not None:
            return self.project.code_edition

        return None

    def next_revision(self) -> int:
        self.revision += 1
        return self.revision

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "project": self.project,
            "floor": self.floor,
            "member": self.member,
            "structure_type": self.resolve_structure_type(),
            "design_code": self.resolve_code(),
            "code_edition": self.resolve_code_edition(),
            "unit_system": self.unit_system,
            "revision": self.revision,
            "calculation_id": self.calculation_id,
            "metadata": self.metadata,
        })


# =====================================================================
# TRACEABILITY HELPERS
# =====================================================================

@dataclass(slots=True)
class EngineeringTrace:
    """
    Traceability record connecting an engineering output to its source.

    This is intentionally lightweight so it can be embedded into
    metadata of calculations, reinforcement, BBS, Cut List and reports.
    """

    project_id: str

    project_revision: int

    member_id: Optional[str] = None
    member_revision: Optional[int] = None

    calculation_id: Optional[str] = None
    calculation_revision: Optional[int] = None

    bar_id: Optional[str] = None
    bar_mark: Optional[str] = None

    bbs_id: Optional[str] = None
    cutlist_id: Optional[str] = None

    report_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _serialize({
            "project_id": self.project_id,
            "project_revision": self.project_revision,
            "member_id": self.member_id,
            "member_revision": self.member_revision,
            "calculation_id": self.calculation_id,
            "calculation_revision": self.calculation_revision,
            "bar_id": self.bar_id,
            "bar_mark": self.bar_mark,
            "bbs_id": self.bbs_id,
            "cutlist_id": self.cutlist_id,
            "report_id": self.report_id,
        })


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    # Enums
    "UnitSystem",
    "StructureType",
    "MemberType",
    "FoundationType",
    "ColumnType",
    "BeamType",
    "SlabType",
    "ReinforcementType",
    "SpliceType",
    "CalculationStatus",

    # Helpers
    "utc_now",
    "enum_value",

    # Materials
    "ConcreteMaterial",
    "SteelMaterial",
    "MaterialSet",

    # Project
    "Project",
    "Floor",

    # Geometry
    "RectangularGeometry",
    "CircularGeometry",
    "SlabGeometry",

    # Structural members
    "StructuralMember",

    # Reinforcement
    "RebarShape",
    "ReinforcementBar",
    "Splice",

    # Calculation
    "CheckResult",
    "CalculationResult",

    # Cut List
    "CutPiece",
    "StockBar",
    "CutListResult",

    # Quantities
    "MaterialQuantity",

    # Settings/context
    "UserSettings",
    "EngineeringContext",

    # Traceability
    "EngineeringTrace",
]
