from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional


@dataclass
class AIContext:
    """
    Controlled engineering context supplied to the AI layer.

    The AI layer is an explanatory assistant only. Deterministic
    calculations and code checks remain the source of truth.
    """

    user_id: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None

    structure_type: Optional[str] = None
    floor_id: Optional[str] = None
    floor_name: Optional[str] = None
    member_id: Optional[str] = None
    member_type: Optional[str] = None

    code_name: Optional[str] = None
    code_edition: Optional[str] = None

    units: str = "metric"
    language: str = "fa"

    inputs: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    checks: Dict[str, Any] = field(default_factory=dict)
    quantities: Dict[str, Any] = field(default_factory=dict)

    engineering_trace: list[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_input(self, key: str, value: Any) -> None:
        if key:
            self.inputs[key] = value

    def add_result(self, key: str, value: Any) -> None:
        if key:
            self.results[key] = value

    def add_check(self, key: str, value: Any) -> None:
        if key:
            self.checks[key] = value

    def add_quantity(self, key: str, value: Any) -> None:
        if key:
            self.quantities[key] = value

    def add_trace(self, item: Mapping[str, Any]) -> None:
        self.engineering_trace.append(dict(item))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "structure_type": self.structure_type,
            "floor_id": self.floor_id,
            "floor_name": self.floor_name,
            "member_id": self.member_id,
            "member_type": self.member_type,
            "code_name": self.code_name,
            "code_edition": self.code_edition,
            "units": self.units,
            "language": self.language,
            "inputs": dict(self.inputs),
            "results": dict(self.results),
            "checks": dict(self.checks),
            "quantities": dict(self.quantities),
            "engineering_trace": [
                dict(item) for item in self.engineering_trace
            ],
            "metadata": dict(self.metadata),
        }

    def compact(self) -> Dict[str, Any]:
        """
        Return only engineering-relevant information suitable for prompts.
        """

        return {
            "project": {
                "id": self.project_id,
                "name": self.project_name,
            },
            "structure": {
                "type": self.structure_type,
                "floor": self.floor_name or self.floor_id,
                "member": self.member_type or self.member_id,
            },
            "code": {
                "name": self.code_name,
                "edition": self.code_edition,
            },
            "units": self.units,
            "language": self.language,
            "inputs": dict(self.inputs),
            "results": dict(self.results),
            "checks": dict(self.checks),
            "quantities": dict(self.quantities),
            "trace": [
                dict(item) for item in self.engineering_trace
            ],
        }


def build_context(
    *,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    structure_type: Optional[str] = None,
    floor_id: Optional[str] = None,
    floor_name: Optional[str] = None,
    member_id: Optional[str] = None,
    member_type: Optional[str] = None,
    code_name: Optional[str] = None,
    code_edition: Optional[str] = None,
    units: str = "metric",
    language: str = "fa",
    inputs: Optional[Mapping[str, Any]] = None,
    results: Optional[Mapping[str, Any]] = None,
    checks: Optional[Mapping[str, Any]] = None,
    quantities: Optional[Mapping[str, Any]] = None,
    engineering_trace: Optional[Iterable[Mapping[str, Any]]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> AIContext:
    context = AIContext(
        user_id=user_id,
        project_id=project_id,
        project_name=project_name,
        structure_type=structure_type,
        floor_id=floor_id,
        floor_name=floor_name,
        member_id=member_id,
        member_type=member_type,
        code_name=code_name,
        code_edition=code_edition,
        units=units or "metric",
        language=language or "fa",
        inputs=dict(inputs or {}),
        results=dict(results or {}),
        checks=dict(checks or {}),
        quantities=dict(quantities or {}),
        metadata=dict(metadata or {}),
    )

    if engineering_trace:
        context.engineering_trace = [
            dict(item) for item in engineering_trace
        ]

    return context


def context_to_prompt(
    context: Optional[AIContext],
) -> str:
    if context is None:
        return "No verified engineering context was supplied."

    data = context.compact()

    sections = [
        f"Language: {data['language']}",
        f"Units: {data['units']}",
        f"Structure type: {data['structure']['type']}",
        f"Floor: {data['structure']['floor']}",
        f"Member: {data['structure']['member']}",
        f"Code: {data['code']['name']}",
        f"Code edition: {data['code']['edition']}",
        f"Inputs: {data['inputs']}",
        f"Verified results: {data['results']}",
        f"Checks: {data['checks']}",
        f"Quantities: {data['quantities']}",
        f"Engineering trace: {data['trace']}",
    ]

    return "\n".join(sections)


__all__ = [
    "AIContext",
    "build_context",
    "context_to_prompt",
]
