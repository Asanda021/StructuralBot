from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from codes.base import (
    CheckStatus,
    CodeCheck,
    DesignCode,
    get_code,
)


class CodeAdapterError(Exception):
    pass


@dataclass
class CodeAdapterResult:
    code_id: str
    edition: str
    checks: list[CodeCheck]

    @property
    def passed(self) -> bool:
        return all(
            check.status == CheckStatus.PASS
            for check in self.checks
        )

    @property
    def failed(self) -> bool:
        return any(
            check.status == CheckStatus.FAIL
            for check in self.checks
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code_id": self.code_id,
            "edition": self.edition,
            "passed": self.passed,
            "failed": self.failed,
            "checks": [
                {
                    "name": x.name,
                    "status": x.status.value,
                    "value": x.value,
                    "limit": x.limit,
                    "unit": x.unit,
                    "message": x.message,
                    "clause": x.clause,
                }
                for x in self.checks
            ],
        }


class CodeAdapter:
    def __init__(
        self,
        code: DesignCode | str = "iran",
        *,
        edition: Optional[str] = None,
    ):
        if isinstance(code, str):
            self.code = get_code(code)
        else:
            self.code = code

        if edition is not None:
            self.edition = edition
        else:
            self.edition = self.code.edition

    @property
    def code_id(self) -> str:
        return self.code.code_id

    def supported_members(self) -> tuple[str, ...]:
        return tuple(self.code.supported_members())

    def get_requirement(
        self,
        member_type: str,
        requirement: str,
    ):
        return self.code.get_requirement(
            member_type,
            requirement,
        )

    def get_material_requirement(
        self,
        material_type: str,
        requirement: str,
    ):
        return self.code.get_material_requirement(
            material_type,
            requirement,
        )

    def get_detailing_rule(
        self,
        member_type: str,
        rule: str,
    ):
        return self.code.get_detailing_rule(
            member_type,
            rule,
        )

    def run_check(
        self,
        name: str,
        value: float,
        limit: float,
        *,
        relation: str = "<=",
        unit: str = "",
        clause: Optional[str] = None,
        message: str = "",
    ) -> CodeCheck:
        return self.code.run_check(
            name=name,
            value=value,
            limit=limit,
            relation=relation,
            unit=unit,
            clause=clause,
            message=message,
        )

    def check_minimum(
        self,
        name: str,
        value: float,
        minimum: float,
        *,
        unit: str = "",
        clause: Optional[str] = None,
    ) -> CodeCheck:
        return self.code.run_check(
            name=name,
            value=value,
            limit=minimum,
            relation=">=",
            unit=unit,
            clause=clause,
        )

    def check_maximum(
        self,
        name: str,
        value: float,
        maximum: float,
        *,
        unit: str = "",
        clause: Optional[str] = None,
    ) -> CodeCheck:
        return self.code.run_check(
            name=name,
            value=value,
            limit=maximum,
            relation="<=",
            unit=unit,
            clause=clause,
        )

    def check_range(
        self,
        name: str,
        value: float,
        minimum: float,
        maximum: float,
        *,
        unit: str = "",
        clause: Optional[str] = None,
    ) -> list[CodeCheck]:
        return [
            self.check_minimum(
                name=f"{name}_min",
                value=value,
                minimum=minimum,
                unit=unit,
                clause=clause,
            ),
            self.check_maximum(
                name=f"{name}_max",
                value=value,
                maximum=maximum,
                unit=unit,
                clause=clause,
            ),
        ]

    def validate_member(
        self,
        member_type: str,
        values: Optional[dict[str, float]] = None,
    ) -> CodeAdapterResult:
        values = values or {}
        checks: list[CodeCheck] = []

        for key, value in values.items():
            requirement = self.get_requirement(
                member_type,
                key,
            )

            if requirement is None:
                continue

            if getattr(requirement, "minimum", None) is not None:
                checks.append(
                    self.check_minimum(
                        key,
                        value,
                        requirement.minimum,
                        unit=getattr(requirement, "unit", ""),
                        clause=getattr(requirement, "clause", None),
                    )
                )

            if getattr(requirement, "maximum", None) is not None:
                checks.append(
                    self.check_maximum(
                        key,
                        value,
                        requirement.maximum,
                        unit=getattr(requirement, "unit", ""),
                        clause=getattr(requirement, "clause", None),
                    )
                )

        return CodeAdapterResult(
            code_id=self.code_id,
            edition=self.edition,
            checks=checks,
        )


def create_code_adapter(
    code: str = "iran",
    *,
    edition: Optional[str] = None,
) -> CodeAdapter:
    return CodeAdapter(code, edition=edition)


__all__ = [
    "CodeAdapterError",
    "CodeAdapterResult",
    "CodeAdapter",
    "create_code_adapter",
]
