"""
StructuralBot - Design Code Adapter

Connects the code-independent calculation engine to the selected
design-code implementation.

Architecture:

    User Settings
         ↓
    EngineeringContext
         ↓
    DesignCode
         ↓
    CodeAdapter
         ↓
    Calculation Engine
         ↓
    Reinforcement / Detailing / BBS / Cut List

Important:
    The core calculation layer must not contain country-specific code rules.

    This adapter provides a stable interface between:
        core/
    and:
        codes/

    Therefore, future code families such as ACI, Eurocode, AISC, etc.
    can be added without rewriting the core calculation engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from core.models import (
    EngineeringContext,
    MemberType,
    StructureType,
)

from codes.base import (
    CodeCheck,
    CodeEdition,
    CodeFamily,
    CodeRequirement,
    DetailingRule,
    DesignCode,
    MaterialRequirement,
    MemberCategory,
)


# ---------------------------------------------------------------------------
# EXCEPTIONS
# ---------------------------------------------------------------------------

class CodeAdapterError(Exception):
    """Base exception for code-adapter errors."""


class CodeNotConfiguredError(CodeAdapterError):
    """Raised when no design code has been configured."""


class UnsupportedCodeError(CodeAdapterError):
    """Raised when the requested design code is unavailable."""


class UnsupportedMemberError(CodeAdapterError):
    """Raised when the selected code does not support a member."""


class CodeContextMismatchError(CodeAdapterError):
    """Raised when the code and engineering context are incompatible."""


# ---------------------------------------------------------------------------
# MEMBER MAPPING
# ---------------------------------------------------------------------------

_MEMBER_MAP: Dict[Any, MemberCategory] = {
    # Core MemberType values
    "foundation": MemberCategory.FOUNDATION,
    "column": MemberCategory.COLUMN,
    "beam": MemberCategory.BEAM,
    "slab": MemberCategory.SLAB,
    "wall": MemberCategory.WALL,
    "stair": MemberCategory.STAIR,

    # Common aliases
    "footing": MemberCategory.FOUNDATION,
    "foundation_iso": MemberCategory.FOUNDATION,
    "foundation_strip": MemberCategory.FOUNDATION,
    "foundation_raft": MemberCategory.FOUNDATION,

    "column_rect": MemberCategory.COLUMN,
    "column_round": MemberCategory.COLUMN,

    "beam_main": MemberCategory.BEAM,
    "beam_secondary": MemberCategory.BEAM,
    "tie_beam": MemberCategory.BEAM,

    "slab_one_way": MemberCategory.SLAB,
    "slab_two_way": MemberCategory.SLAB,
    "roof_slab": MemberCategory.SLAB,

    "structural_wall": MemberCategory.WALL,
    "shear_wall": MemberCategory.WALL,
}


def member_category_from_member(
    member: Any,
) -> MemberCategory:
    """
    Convert a core member or member identifier to MemberCategory.

    The function intentionally accepts multiple representations because
    the bot may receive:
        - MemberType enum
        - string
        - object with member_type
        - object with type
    """

    if member is None:
        raise ValueError("Member cannot be None.")

    # Direct enum/value
    if isinstance(member, MemberCategory):
        return member

    if isinstance(member, MemberType):
        value = member.value.lower().strip()

        if value in _MEMBER_MAP:
            return _MEMBER_MAP[value]

    # String
    if isinstance(member, str):
        normalized = member.strip().lower()

        if normalized in _MEMBER_MAP:
            return _MEMBER_MAP[normalized]

        # Enum-name fallback
        normalized = normalized.replace("-", "_").replace(" ", "_")

        if normalized in _MEMBER_MAP:
            return _MEMBER_MAP[normalized]

    # Object attribute fallback
    for attribute in ("member_type", "type", "category"):
        if hasattr(member, attribute):
            value = getattr(member, attribute)

            if value is member:
                continue

            try:
                return member_category_from_member(value)
            except (ValueError, TypeError):
                pass

    raise ValueError(
        f"Unable to map member to a code category: {member!r}"
    )


# ---------------------------------------------------------------------------
# STRUCTURE TYPE HELPERS
# ---------------------------------------------------------------------------

def structure_type_from_context(
    context: Optional[EngineeringContext],
) -> Optional[StructureType]:
    """
    Safely obtain structure type from EngineeringContext.
    """

    if context is None:
        return None

    value = getattr(context, "structure_type", None)

    if value is None:
        return None

    if isinstance(value, StructureType):
        return value

    try:
        return StructureType(str(value).lower())
    except (ValueError, TypeError):
        return None


def normalize_code_family(
    value: Any,
) -> CodeFamily:
    """
    Convert a string/enum into CodeFamily.
    """

    if isinstance(value, CodeFamily):
        return value

    if value is None:
        raise ValueError("Code family cannot be None.")

    normalized = str(value).strip().lower()

    for family in CodeFamily:
        if normalized in {
            family.value.lower(),
            family.name.lower(),
        }:
            return family

    raise ValueError(
        f"Unsupported code family: {value!r}"
    )


# ---------------------------------------------------------------------------
# CODE ADAPTER
# ---------------------------------------------------------------------------

class CodeAdapter:
    """
    Stable adapter around DesignCode.

    The adapter exposes a predictable API to the calculation layer while
    keeping code-specific implementations inside `codes/`.
    """

    def __init__(
        self,
        design_code: Optional[DesignCode] = None,
        *,
        context: Optional[EngineeringContext] = None,
    ) -> None:

        self._design_code = design_code
        self._context = context

        if design_code is not None and context is not None:
            self.validate_context(context)

    # ------------------------------------------------------------------
    # PROPERTIES
    # ------------------------------------------------------------------

    @property
    def design_code(self) -> DesignCode:
        """
        Return the active design code.
        """

        if self._design_code is None:
            raise CodeNotConfiguredError(
                "No design code has been configured."
            )

        return self._design_code

    @property
    def context(self) -> Optional[EngineeringContext]:
        return self._context

    @property
    def edition(self) -> CodeEdition:
        return self.design_code.edition

    @property
    def code_id(self) -> str:
        return self.design_code.code_id

    @property
    def family(self) -> CodeFamily:
        return self.design_code.family

    # ------------------------------------------------------------------
    # CONFIGURATION
    # ------------------------------------------------------------------

    def set_design_code(
        self,
        design_code: DesignCode,
    ) -> None:
        """
        Replace the active design code.
        """

        if not isinstance(design_code, DesignCode):
            raise TypeError(
                "design_code must be an instance of DesignCode."
            )

        if self._context is not None:
            self.validate_context(
                self._context,
                design_code=design_code,
            )

        self._design_code = design_code

    def set_context(
        self,
        context: EngineeringContext,
    ) -> None:
        """
        Set engineering context and validate compatibility.
        """

        self.validate_context(
            context,
            design_code=self._design_code,
        )

        self._context = context

    # ------------------------------------------------------------------
    # CONTEXT VALIDATION
    # ------------------------------------------------------------------

    def validate_context(
        self,
        context: EngineeringContext,
        *,
        design_code: Optional[DesignCode] = None,
    ) -> bool:
        """
        Validate that the engineering context is compatible with the
        selected design code.

        This intentionally performs only compatibility checks.

        It does not perform structural design.
        """

        if context is None:
            raise CodeContextMismatchError(
                "Engineering context cannot be None."
            )

        code = design_code or self._design_code

        if code is None:
            raise CodeNotConfiguredError(
                "A design code is required to validate the context."
            )

        context_code = getattr(context, "code_id", None)

        if context_code is not None:
            if str(context_code).strip().lower() != str(
                code.code_id
            ).strip().lower():
                raise CodeContextMismatchError(
                    "Engineering context code_id does not match "
                    "the selected design code."
                )

        context_family = getattr(context, "code_family", None)

        if context_family is not None:
            try:
                normalized_context_family = normalize_code_family(
                    context_family
                )
            except ValueError as exc:
                raise CodeContextMismatchError(
                    str(exc)
                ) from exc

            if normalized_context_family != code.family:
                raise CodeContextMismatchError(
                    "Engineering context code family does not match "
                    "the selected design code."
                )

        return True

    # ------------------------------------------------------------------
    # MEMBER SUPPORT
    # ------------------------------------------------------------------

    def supports_member(
        self,
        member: Any,
    ) -> bool:
        """
        Return True if the active code supports the member category.
        """

        category = member_category_from_member(member)

        return category in self.design_code.supported_members()

    def require_member_support(
        self,
        member: Any,
    ) -> MemberCategory:
        """
        Validate member support and return MemberCategory.
        """

        category = member_category_from_member(member)

        if category not in self.design_code.supported_members():
            raise UnsupportedMemberError(
                f"Design code '{self.code_id}' does not support "
                f"member category '{category.value}'."
            )

        return category

    # ------------------------------------------------------------------
    # REQUIREMENTS
    # ------------------------------------------------------------------

    def get_requirement(
        self,
        member: Any,
        key: str,
    ) -> Optional[CodeRequirement]:
        """
        Get a code requirement for a member.
        """

        category = self.require_member_support(member)

        return self.design_code.get_requirement(
            category,
            key,
        )

    def get_material_requirement(
        self,
        member: Any,
    ) -> Optional[CodeRequirement]:
        """
        Get material requirement for a member.
        """

        category = self.require_member_support(member)

        return self.design_code.get_material_requirement(
            category,
        )

    def get_detailing_rule(
        self,
        member: Any,
        key: str,
    ) -> Optional[DetailingRule]:
        """
        Get a detailing rule for a member.
        """

        category = self.require_member_support(member)

        return self.design_code.get_detailing_rule(
            category,
            key,
        )

    # ------------------------------------------------------------------
    # CHECKS
    # ------------------------------------------------------------------

    def run_check(
        self,
        *,
        member: Any,
        **kwargs: Any,
    ) -> CodeCheck:
        """
        Run a code-specific check.

        The concrete DesignCode implementation decides how the check
        is interpreted.
        """

        category = self.require_member_support(member)

        return self.design_code.run_check(
            member_category=category,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # METADATA
    # ------------------------------------------------------------------

    def metadata(self) -> Dict[str, Any]:
        """
        Return adapter and code metadata.
        """

        code_metadata: Dict[str, Any] = {}

        code_metadata_method = getattr(
            self.design_code,
            "metadata",
            None,
        )

        if callable(code_metadata_method):
            result = code_metadata_method()

            if isinstance(result, dict):
                code_metadata = dict(result)

        return {
            "adapter": "StructuralBot CodeAdapter",
            "code_id": self.code_id,
            "code_family": self.family.value,
            "edition": self.edition.edition,
            "title": self.edition.title,
            "code_metadata": code_metadata,
            "context_configured": self._context is not None,
        }


# ---------------------------------------------------------------------------
# CODE REGISTRY ADAPTER
# ---------------------------------------------------------------------------

class CodeResolver:
    """
    Resolves a code from a DesignCodeRegistry.

    This keeps the bot and calculation engine independent from the
    implementation details of individual code packages.
    """

    def __init__(
        self,
        registry: Any,
    ) -> None:

        if registry is None:
            raise ValueError("Code registry cannot be None.")

        self.registry = registry

    def resolve(
        self,
        code_id: str,
    ) -> DesignCode:
        """
        Resolve a registered design code.

        Supports registries exposing:
            get()
        or:
            resolve()
        """

        if not code_id:
            raise ValueError("code_id cannot be empty.")

        normalized = str(code_id).strip()

        resolver = getattr(
            self.registry,
            "get",
            None,
        )

        if callable(resolver):
            code = resolver(normalized)

            if code is not None:
                return code

        resolver = getattr(
            self.registry,
            "resolve",
            None,
        )

        if callable(resolver):
            code = resolver(normalized)

            if code is not None:
                return code

        raise UnsupportedCodeError(
            f"Design code '{normalized}' is not registered."
        )

    def list_codes(self) -> List[Any]:
        """
        Return available codes from the registry.
        """

        method = getattr(
            self.registry,
            "list_codes",
            None,
        )

        if callable(method):
            result = method()

            return list(result)

        codes = getattr(
            self.registry,
            "_codes",
            None,
        )

        if isinstance(codes, dict):
            return list(codes.keys())

        return []


# ---------------------------------------------------------------------------
# FACTORY
# ---------------------------------------------------------------------------

def create_code_adapter(
    design_code: DesignCode,
    *,
    context: Optional[EngineeringContext] = None,
) -> CodeAdapter:
    """
    Create a CodeAdapter.
    """

    return CodeAdapter(
        design_code=design_code,
        context=context,
    )


def create_code_adapter_from_registry(
    registry: Any,
    code_id: str,
    *,
    context: Optional[EngineeringContext] = None,
) -> CodeAdapter:
    """
    Resolve a design code from a registry and create an adapter.
    """

    resolver = CodeResolver(registry)

    design_code = resolver.resolve(code_id)

    return CodeAdapter(
        design_code=design_code,
        context=context,
    )


# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def get_member_category(
    member: Any,
) -> MemberCategory:
    """
    Public helper for member mapping.
    """

    return member_category_from_member(member)


def code_supports_member(
    design_code: DesignCode,
    member: Any,
) -> bool:
    """
    Check member support without explicitly creating an adapter.
    """

    category = member_category_from_member(member)

    return category in design_code.supported_members()


def get_code_requirement(
    design_code: DesignCode,
    member: Any,
    key: str,
) -> Optional[CodeRequirement]:
    """
    Convenience function for code requirement lookup.
    """

    adapter = CodeAdapter(design_code)

    return adapter.get_requirement(
        member,
        key,
    )


def get_detailing_rule(
    design_code: DesignCode,
    member: Any,
    key: str,
) -> Optional[DetailingRule]:
    """
    Convenience function for detailing-rule lookup.
    """

    adapter = CodeAdapter(design_code)

    return adapter.get_detailing_rule(
        member,
        key,
    )


# ---------------------------------------------------------------------------
# EXPORTS
# ---------------------------------------------------------------------------

__all__ = [
    "CodeAdapterError",
    "CodeNotConfiguredError",
    "UnsupportedCodeError",
    "UnsupportedMemberError",
    "CodeContextMismatchError",
    "member_category_from_member",
    "structure_type_from_context",
    "normalize_code_family",
    "CodeAdapter",
    "CodeResolver",
    "create_code_adapter",
    "create_code_adapter_from_registry",
    "get_member_category",
    "code_supports_member",
    "get_code_requirement",
    "get_detailing_rule",
]
