from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol

from core.models import (
    CalculationResult,
    EngineeringContext,
    MemberType,
    StructuralMember,
    StructureType,
)
from core.validation import validate_engineering_context, validate_structural_member


class CalculationError(Exception):
    pass


class UnsupportedCalculationError(CalculationError):
    pass


class UnsupportedStructureTypeError(CalculationError):
    pass


class CalculationValidationError(CalculationError):
    pass


@dataclass(slots=True)
class CalculationRequest:
    calculation_id: str
    member: StructuralMember
    context: EngineeringContext
    parameters: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        member_result = validate_structural_member(self.member)
        if not member_result.valid:
            raise CalculationValidationError(
                "; ".join(
                    f"{x.field}: {x.message}"
                    for x in member_result.errors
                )
            )

        context_result = validate_engineering_context(self.context)
        if not context_result.valid:
            raise CalculationValidationError(
                "; ".join(
                    f"{x.field}: {x.message}"
                    for x in context_result.errors
                )
            )

        context_member = self.context.member
        if context_member is not None:
            if context_member.member_id != self.member.member_id:
                raise CalculationValidationError(
                    "Context member does not match calculation member."
                )


class CalculationModule(Protocol):
    calculation_id: str

    def calculate(
        self,
        request: CalculationRequest,
    ) -> CalculationResult:
        ...


@dataclass(slots=True)
class FunctionCalculationModule:
    calculation_id: str
    calculator: Callable[
        [CalculationRequest],
        CalculationResult,
    ]

    def calculate(
        self,
        request: CalculationRequest,
    ) -> CalculationResult:
        return self.calculator(request)


class CalculationRegistry:
    def __init__(self) -> None:
        self._modules: Dict[str, CalculationModule] = {}

    def register(
        self,
        module: CalculationModule,
        *,
        replace: bool = False,
    ) -> None:
        calculation_id = str(module.calculation_id).strip()

        if not calculation_id:
            raise ValueError("calculation_id cannot be empty.")

        if calculation_id in self._modules and not replace:
            raise ValueError(
                f"Calculation already registered: {calculation_id}"
            )

        self._modules[calculation_id] = module

    def unregister(self, calculation_id: str) -> None:
        self._modules.pop(calculation_id, None)

    def get(self, calculation_id: str) -> CalculationModule:
        module = self._modules.get(calculation_id)

        if module is None:
            raise UnsupportedCalculationError(
                f"Unknown calculation: {calculation_id}"
            )

        return module

    def exists(self, calculation_id: str) -> bool:
        return calculation_id in self._modules

    def list_ids(self) -> List[str]:
        return sorted(self._modules)

    def clear(self) -> None:
        self._modules.clear()


def _member_structure_type(
    member: StructuralMember,
) -> StructureType:
    structure_type = getattr(
        member,
        "structure_type",
        None,
    )

    if structure_type is None:
        raise UnsupportedStructureTypeError(
            "Member structure type is required."
        )

    if not isinstance(structure_type, StructureType):
        try:
            structure_type = StructureType(structure_type)
        except (ValueError, TypeError):
            raise UnsupportedStructureTypeError(
                f"Unsupported structure type: {structure_type}"
            )

    return structure_type


def _context_structure_type(
    context: EngineeringContext,
) -> StructureType:
    structure_type = context.resolve_structure_type()

    if structure_type is None:
        raise UnsupportedStructureTypeError(
            "Engineering context has no explicit structure type."
        )

    if not isinstance(structure_type, StructureType):
        try:
            structure_type = StructureType(structure_type)
        except (ValueError, TypeError):
            raise UnsupportedStructureTypeError(
                f"Unsupported structure type: {structure_type}"
            )

    return structure_type


class CalculationEngine:
    def __init__(
        self,
        registry: Optional[CalculationRegistry] = None,
    ) -> None:
        self.registry = registry or CalculationRegistry()

    def register(
        self,
        module: CalculationModule,
        *,
        replace: bool = False,
    ) -> None:
        self.registry.register(
            module,
            replace=replace,
        )

    def calculate(
        self,
        request: CalculationRequest,
    ) -> CalculationResult:
        request.validate()

        member_type = request.member.member_type

        if not isinstance(member_type, MemberType):
            try:
                member_type = MemberType(member_type)
            except (ValueError, TypeError):
                raise CalculationValidationError(
                    f"Unsupported member type: {request.member.member_type}"
                )

        member_structure = _member_structure_type(
            request.member
        )
        context_structure = _context_structure_type(
            request.context
        )

        if member_structure != context_structure:
            raise CalculationValidationError(
                "Member structure type and engineering context "
                "structure type do not match."
            )

        module = self.registry.get(
            request.calculation_id
        )

        result = module.calculate(request)

        if not isinstance(result, CalculationResult):
            raise CalculationError(
                "Calculation module must return CalculationResult."
            )

        if result.member_id != request.member.member_id:
            raise CalculationError(
                "Calculation result member_id does not match request."
            )

        if result.project_id != request.member.project_id:
            raise CalculationError(
                "Calculation result project_id does not match request."
            )

        return result

    def available(self) -> List[str]:
        return self.registry.list_ids()


def create_registry() -> CalculationRegistry:
    return CalculationRegistry()


default_registry = create_registry()
default_engine = CalculationEngine(default_registry)


def register_calculation(
    module: CalculationModule,
    *,
    replace: bool = False,
    registry: Optional[CalculationRegistry] = None,
) -> None:
    target = registry or default_registry
    target.register(
        module,
        replace=replace,
    )


def get_available_calculations(
    registry: Optional[CalculationRegistry] = None,
) -> List[str]:
    target = registry or default_registry
    return target.list_ids()


def has_calculation(
    calculation_id: str,
    registry: Optional[CalculationRegistry] = None,
) -> bool:
    target = registry or default_registry
    return target.exists(calculation_id)


def run_calculation(
    request: CalculationRequest,
    *,
    engine: Optional[CalculationEngine] = None,
) -> CalculationResult:
    target = engine or default_engine
    return target.calculate(request)


@dataclass(slots=True)
class CalculationPipeline:
    engine: CalculationEngine

    def run(
        self,
        request: CalculationRequest,
    ) -> CalculationResult:
        return self.engine.calculate(request)


default_pipeline = CalculationPipeline(
    engine=default_engine
)


__all__ = [
    "CalculationError",
    "UnsupportedCalculationError",
    "UnsupportedStructureTypeError",
    "CalculationValidationError",
    "CalculationRequest",
    "CalculationModule",
    "FunctionCalculationModule",
    "CalculationRegistry",
    "CalculationEngine",
    "CalculationPipeline",
    "default_registry",
    "default_engine",
    "default_pipeline",
    "create_registry",
    "register_calculation",
    "get_available_calculations",
    "has_calculation",
    "run_calculation",
]
