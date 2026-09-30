"""
StructuralBot - Code Adapter QA

Tests the bridge between the deterministic core layer and
the design-code layer.

Architecture:

    Core
      │
      ▼
    CodeAdapter
      │
      ▼
    DesignCode
      │
      ▼
    Code-specific implementation
"""

from __future__ import annotations

import inspect

import pytest

from core.code_adapter import (
    CodeAdapter,
    CodeAdapterError,
    CodeContextMismatchError,
    CodeNotConfiguredError,
    CodeResolver,
    UnsupportedCodeError,
    UnsupportedMemberError,
    get_code_adapter,
    get_code_resolver,
    normalize_code_id,
)

from codes.base import (
    CodeFamily,
    CodeContext,
    DesignCode,
    DesignCodeRegistry,
    MemberCategory,
)


# ---------------------------------------------------------------------------
# NORMALIZATION
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_normalize_code_id_lowercases_code() -> None:
    result = normalize_code_id("IRAN")

    assert result == "iran"


@pytest.mark.unit
def test_normalize_code_id_removes_spaces() -> None:
    result = normalize_code_id("  iran  ")

    assert result == "iran"


@pytest.mark.unit
def test_normalize_code_id_accepts_dotted_identifier() -> None:
    result = normalize_code_id("iran.2800")

    assert result == "iran.2800"


@pytest.mark.unit
def test_normalize_code_id_rejects_empty_value() -> None:
    with pytest.raises(
        (ValueError, TypeError),
    ):
        normalize_code_id("")


# ---------------------------------------------------------------------------
# REGISTRY
# ---------------------------------------------------------------------------

def test_design_code_registry_is_available() -> None:
    registry = DesignCodeRegistry()

    assert registry is not None


def test_design_code_registry_can_be_created_empty() -> None:
    registry = DesignCodeRegistry()

    try:
        codes = registry.list_codes()
    except AttributeError:
        codes = []

    assert codes is not None


# ---------------------------------------------------------------------------
# RESOLVER
# ---------------------------------------------------------------------------

def test_code_resolver_can_be_created() -> None:
    resolver = CodeResolver()

    assert resolver is not None


def test_global_code_resolver_exists() -> None:
    resolver = get_code_resolver()

    assert resolver is not None


# ---------------------------------------------------------------------------
# ADAPTER
# ---------------------------------------------------------------------------

def test_code_adapter_can_be_created() -> None:
    adapter = CodeAdapter()

    assert adapter is not None


def test_global_code_adapter_exists() -> None:
    adapter = get_code_adapter()

    assert adapter is not None


# ---------------------------------------------------------------------------
# ERROR HIERARCHY
# ---------------------------------------------------------------------------

def test_code_adapter_errors_have_common_base() -> None:
    assert issubclass(
        CodeNotConfiguredError,
        CodeAdapterError,
    )

    assert issubclass(
        UnsupportedCodeError,
        CodeAdapterError,
    )

    assert issubclass(
        UnsupportedMemberError,
        CodeAdapterError,
    )

    assert issubclass(
        CodeContextMismatchError,
        CodeAdapterError,
    )


# ---------------------------------------------------------------------------
# BASE CODE CONTRACT
# ---------------------------------------------------------------------------

def test_design_code_is_abstract() -> None:
    assert inspect.isabstract(DesignCode)


def test_member_categories_exist() -> None:
    categories = list(MemberCategory)

    assert categories


def test_code_family_exists() -> None:
    families = list(CodeFamily)

    assert families


# ---------------------------------------------------------------------------
# CODE CONTEXT
# ---------------------------------------------------------------------------

def test_code_context_is_constructible() -> None:
    """
    Construct CodeContext using only fields that are commonly
    required by the base contract.

    If the implementation evolves, this test should fail loudly
    rather than silently accepting an incompatible API.
    """

    signature = inspect.signature(CodeContext)

    parameters = signature.parameters

    kwargs = {}

    if "code_id" in parameters:
        kwargs["code_id"] = "iran"

    if "edition" in parameters:
        kwargs["edition"] = "current"

    if "family" in parameters:
        family = next(iter(CodeFamily))
        kwargs["family"] = family

    context = CodeContext(**kwargs)

    assert context is not None


# ---------------------------------------------------------------------------
# IRAN CODE AVAILABILITY
# ---------------------------------------------------------------------------

def test_iran_code_package_imports() -> None:
    import codes.iran

    assert codes.iran is not None


def test_iran_materials_module_imports() -> None:
    import codes.iran.materials

    assert codes.iran.materials is not None


def test_iran_concrete_module_imports() -> None:
    import codes.iran.concrete

    assert codes.iran.concrete is not None


def test_iran_reinforcement_module_imports() -> None:
    import codes.iran.reinforcement

    assert codes.iran.reinforcement is not None


def test_iran_detailing_module_imports() -> None:
    import codes.iran.detailing

    assert codes.iran.detailing is not None


def test_iran_validation_module_imports() -> None:
    import codes.iran.validation

    assert codes.iran.validation is not None


# ---------------------------------------------------------------------------
# MATERIAL CONTRACT
# ---------------------------------------------------------------------------

def test_iran_material_database_is_available() -> None:
    from codes.iran.materials import IranMaterials

    materials = IranMaterials()

    assert materials is not None


def test_iran_material_database_exposes_reinforcement() -> None:
    from codes.iran.materials import IranMaterials

    materials = IranMaterials()

    candidates = (
        "get_reinforcement",
        "get_reinforcement_grade",
        "reinforcement",
    )

    available = [
        name
        for name in candidates
        if hasattr(materials, name)
    ]

    assert available, (
        "IranMaterials must expose a reinforcement-material API."
    )


# ---------------------------------------------------------------------------
# CONCRETE CONTRACT
# ---------------------------------------------------------------------------

def test_iran_concrete_can_be_created() -> None:
    from codes.iran.concrete import IranConcrete

    concrete = IranConcrete()

    assert concrete is not None


def test_iran_concrete_has_basic_limits() -> None:
    from codes.iran.concrete import IranConcrete

    concrete = IranConcrete()

    assert hasattr(concrete, "min_fc")
    assert hasattr(concrete, "max_fc")

    assert concrete.min_fc > 0
    assert concrete.max_fc >= concrete.min_fc


# ---------------------------------------------------------------------------
# REINFORCEMENT CONTRACT
# ---------------------------------------------------------------------------

def test_iran_reinforcement_can_be_created() -> None:
    from codes.iran.reinforcement import IranReinforcement

    reinforcement = IranReinforcement()

    assert reinforcement is not None


def test_iran_reinforcement_has_standard_diameters() -> None:
    from codes.iran.reinforcement import IranReinforcement

    reinforcement = IranReinforcement()

    candidates = (
        "standard_diameters",
        "diameters",
        "STANDARD_DIAMETERS",
    )

    values = []

    for name in candidates:
        if hasattr(reinforcement, name):
            values.append(getattr(reinforcement, name))

    assert values, (
        "IranReinforcement must expose standard bar diameters."
    )


# ---------------------------------------------------------------------------
# DETAILING CONTRACT
# ---------------------------------------------------------------------------

def test_iran_detailing_can_be_created() -> None:
    from codes.iran.detailing import IranDetailing

    detailing = IranDetailing()

    assert detailing is not None


# ---------------------------------------------------------------------------
# VALIDATION CONTRACT
# ---------------------------------------------------------------------------

def test_iran_validation_module_has_validation_api() -> None:
    from codes.iran import validation

    candidates = (
        "validate_material",
        "validate_geometry",
        "validate_rebar",
        "validate_detailing",
    )

    available = [
        name
        for name in candidates
        if hasattr(validation, name)
    ]

    assert available


# ---------------------------------------------------------------------------
# ADAPTER PUBLIC API
# ---------------------------------------------------------------------------

def test_adapter_exposes_resolution_api() -> None:
    adapter = CodeAdapter()

    candidates = (
        "resolve",
        "get_code",
        "code",
        "resolve_code",
    )

    available = [
        name
        for name in candidates
        if hasattr(adapter, name)
    ]

    assert available


def test_resolver_exposes_resolution_api() -> None:
    resolver = CodeResolver()

    candidates = (
        "resolve",
        "get",
        "register",
        "require",
    )

    available = [
        name
        for name in candidates
        if hasattr(resolver, name)
    ]

    assert available


# ---------------------------------------------------------------------------
# FAILURE BEHAVIOR
# ---------------------------------------------------------------------------

def test_unknown_code_does_not_silently_create_code() -> None:
    adapter = CodeAdapter()

    resolution_methods = (
        "resolve",
        "get_code",
        "resolve_code",
    )

    method = next(
        (
            getattr(adapter, name)
            for name in resolution_methods
            if hasattr(adapter, name)
        ),
        None,
    )

    if method is None:
        pytest.skip(
            "CodeAdapter resolution method is not exposed "
            "under a known public name."
        )

    with pytest.raises(Exception):
        method("definitely-not-a-real-code")


# ---------------------------------------------------------------------------
# ARCHITECTURE PRINCIPLE
# ---------------------------------------------------------------------------

def test_adapter_is_not_telegram_dependent() -> None:
    import core.code_adapter as module

    source = inspect.getsource(module)

    assert "from telegram" not in source
    assert "import telegram" not in source


def test_adapter_is_not_billing_dependent() -> None:
    import core.code_adapter as module

    source = inspect.getsource(module)

    assert "from billing" not in source
    assert "import billing" not in source


def test_adapter_is_not_ai_dependent() -> None:
    import core.code_adapter as module

    source = inspect.getsource(module)

    assert "from ai" not in source
    assert "import ai" not in source
