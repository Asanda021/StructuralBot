"""
StructuralBot - Project Import / Dependency QA

Central smoke test for the StructuralBot package.

Purpose:
    - Verify that project modules can be imported.
    - Detect circular imports.
    - Detect missing modules.
    - Detect broken package exports.
    - Verify the main architectural layers are loadable.

This test intentionally does NOT execute Telegram polling,
payment requests, external AI requests, or network operations.

It is safe to run locally/offline.
"""

from __future__ import annotations

import importlib
import os
import py_compile
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ============================================================
# EXPECTED PACKAGE STRUCTURE
# ============================================================


EXPECTED_PACKAGES = [
    "core",
    "codes",
    "codes.iran",
    "handlers",
    "ai",
    "billing",
    "tests",
]


EXPECTED_MODULES = [
    # --------------------------------------------------------
    # Core
    # --------------------------------------------------------

    "core.models",
    "core.validation",
    "core.calculations",
    "core.reinforcement",
    "core.bbs",
    "core.cutlist",
    "core.quantities",
    "core.code_adapter",

    # --------------------------------------------------------
    # Codes
    # --------------------------------------------------------

    "codes.base",
    "codes.iran",
    "codes.iran.materials",
    "codes.iran.concrete",
    "codes.iran.reinforcement",
    "codes.iran.detailing",
    "codes.iran.validation",

    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    "ai.service",
    "ai.providers",
    "ai.config",
    "ai.context",
    "ai.prompts",
    "ai.safety",
    "ai.usage",
    "ai.manager",

    # --------------------------------------------------------
    # Billing
    # --------------------------------------------------------

    "billing.plans",
    "billing.credits",
    "billing.subscription",
    "billing.entitlements",
    "billing.gateway",
    "billing.orders",
    "billing.checkout",
    "billing.products",
    "billing.fulfillment",
    "billing.invoice",
    "billing.service",
    "billing.repository",
    "billing.audit",
    "billing.events",
    "billing.webhooks",
    "billing.notifications",
    "billing.notification_service",
    "billing.transport",
    "billing.gateway_registry",
    "billing.integration",

    # --------------------------------------------------------
    # Handlers
    # --------------------------------------------------------

    "handlers.start",
    "handlers.main_menu",
    "handlers.projects",
    "handlers.calculations",
    "handlers.foundation",
    "handlers.columns",
    "handlers.beams",
    "handlers.slabs",
    "handlers.rebar",
    "handlers.equivalency",
    "handlers.quantities",
    "handlers.reports",
    "handlers.ai",
    "handlers.account",
    "handlers.settings",
]


# ============================================================
# OPTIONAL APPLICATION MODULES
# ============================================================


OPTIONAL_MODULES = [
    "config",
    "database",
    "bot",
]


# ============================================================
# IMPORT HELPER
# ============================================================


def _import_module(module_name: str):
    """
    Import a module and return the loaded module.

    The function deliberately lets ImportError and other
    exceptions propagate so pytest reports the exact failure.
    """

    return importlib.import_module(module_name)


# ============================================================
# PACKAGE TESTS
# ============================================================


def test_project_root_exists():
    """
    StructuralBot root must exist.
    """

    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT.is_dir()


def test_required_packages_exist():
    """
    Required package directories must exist.
    """

    for package in EXPECTED_PACKAGES:
        package_path = PROJECT_ROOT.joinpath(
            *package.split(".")
        )

        assert package_path.exists(), (
            f"Missing package directory: {package}"
        )

        assert package_path.is_dir(), (
            f"Expected directory: {package_path}"
        )


# ============================================================
# IMPORT TESTS
# ============================================================


def test_all_core_modules_import():
    """
    Core calculation layer must import completely.
    """

    core_modules = [
        module
        for module in EXPECTED_MODULES
        if module.startswith("core.")
    ]

    for module_name in core_modules:
        module = _import_module(module_name)
        assert module is not None


def test_all_code_modules_import():
    """
    Design-code layer must import completely.
    """

    code_modules = [
        module
        for module in EXPECTED_MODULES
        if module.startswith("codes.")
    ]

    for module_name in code_modules:
        module = _import_module(module_name)
        assert module is not None


def test_all_ai_modules_import():
    """
    AI layer must import completely without requiring
    a configured external AI provider.
    """

    ai_modules = [
        module
        for module in EXPECTED_MODULES
        if module.startswith("ai.")
    ]

    for module_name in ai_modules:
        module = _import_module(module_name)
        assert module is not None


def test_all_billing_modules_import():
    """
    Billing layer must import completely without requiring
    a real payment gateway.
    """

    billing_modules = [
        module
        for module in EXPECTED_MODULES
        if module.startswith("billing.")
    ]

    for module_name in billing_modules:
        module = _import_module(module_name)
        assert module is not None


def test_all_handler_modules_import():
    """
    Handler layer must import completely.

    This catches broken imports between:
        handlers
        core
        billing
        AI
        reports
    """

    handler_modules = [
        module
        for module in EXPECTED_MODULES
        if module.startswith("handlers.")
    ]

    for module_name in handler_modules:
        module = _import_module(module_name)
        assert module is not None


# ============================================================
# PACKAGE EXPORT TESTS
# ============================================================


def test_core_package_import():
    """
    core package must be importable.
    """

    module = _import_module("core")

    assert module is not None


def test_codes_package_import():
    """
    codes package must be importable.
    """

    module = _import_module("codes")

    assert module is not None


def test_ai_package_import():
    """
    AI package __init__.py must be internally consistent.
    """

    module = _import_module("ai")

    assert module is not None


def test_billing_package_import():
    """
    Billing package __init__.py must remain compatible with
    the existing billing public API.
    """

    module = _import_module("billing")

    assert module is not None


def test_handlers_package_import():
    """
    handlers package must be importable.
    """

    module = _import_module("handlers")

    assert module is not None


# ============================================================
# CRITICAL PUBLIC API TESTS
# ============================================================


def test_core_public_api():
    """
    Critical core objects must remain available.
    """

    from core.calculations import (
        CalculationEngine,
        CalculationRegistry,
    )

    from core.reinforcement import (
        ReinforcementDesign,
    )

    from core.bbs import (
        BBSSchedule,
    )

    from core.cutlist import (
        CutListResult,
    )

    from core.quantities import (
        QuantityTakeoff,
    )

    assert CalculationEngine is not None
    assert CalculationRegistry is not None
    assert ReinforcementDesign is not None
    assert BBSSchedule is not None
    assert CutListResult is not None
    assert QuantityTakeoff is not None


def test_code_layer_public_api():
    """
    Critical code-adapter objects must remain available.
    """

    from codes.base import (
        DesignCode,
        DesignCodeRegistry,
        CodeContext,
    )

    from core.code_adapter import (
        CodeAdapter,
        CodeResolver,
    )

    assert DesignCode is not None
    assert DesignCodeRegistry is not None
    assert CodeContext is not None
    assert CodeAdapter is not None
    assert CodeResolver is not None


def test_ai_public_api():
    """
    Critical AI objects must remain available.
    """

    from ai.service import (
        AIService,
        AIRequest,
        AIResponse,
    )

    from ai.manager import (
        AIManager,
        AIManagerRequest,
        AIManagerResponse,
    )

    from ai.config import (
        AIConfig,
    )

    assert AIService is not None
    assert AIRequest is not None
    assert AIResponse is not None
    assert AIManager is not None
    assert AIManagerRequest is not None
    assert AIManagerResponse is not None
    assert AIConfig is not None


def test_billing_public_api():
    """
    Critical billing objects must remain available.
    """

    from billing.plans import (
        Plan,
        PlanFeature,
    )

    from billing.credits import (
        CreditManager,
    )

    from billing.subscription import (
        SubscriptionManager,
    )

    from billing.integration import (
        BillingIntegration,
    )

    assert Plan is not None
    assert PlanFeature is not None
    assert CreditManager is not None
    assert SubscriptionManager is not None
    assert BillingIntegration is not None


# ============================================================
# OPTIONAL MODULE TESTS
# ============================================================


def test_optional_application_modules_report_status():
    """
    Application-level modules are checked separately.

    They may legitimately be absent while the lower layers
    are being developed.

    This test does not fail when an optional module is absent.
    It only verifies that an existing module can import.
    """

    for module_name in OPTIONAL_MODULES:

        module_path = PROJECT_ROOT.joinpath(
            *module_name.split(".")
        )

        py_file = module_path.with_suffix(".py")

        package_dir = PROJECT_ROOT.joinpath(
            *module_name.split(".")
        )

        package_init = package_dir / "__init__.py"

        exists = (
            py_file.exists()
            or package_init.exists()
        )

        if not exists:
            continue

        module = _import_module(module_name)

        assert module is not None


# ============================================================
# PYTHON COMPILE TEST
# ============================================================


def _python_files():
    """
    Return all Python files in the project while excluding
    generated/cache directories.
    """

    ignored_parts = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "build",
        "dist",
    }

    for path in PROJECT_ROOT.rglob("*.py"):

        if any(
            part in ignored_parts
            for part in path.parts
        ):
            continue

        yield path


def test_all_python_files_compile():
    """
    Compile every Python file in StructuralBot.

    This catches:
        - SyntaxError
        - indentation errors
        - invalid Python syntax
        - malformed files

    It does not execute application logic.
    """

    python_files = list(
        _python_files()
    )

    assert python_files, (
        "No Python files found in project."
    )

    for path in python_files:

        py_compile.compile(
            str(path),
            doraise=True,
        )


# ============================================================
# DUPLICATE / ACCIDENTAL FILE CHECK
# ============================================================


def test_no_obvious_duplicate_python_files():
    """
    Detect suspicious duplicate files that often appear
    during manual project assembly.

    Examples:
        module (1).py
        module_copy.py
        module_backup.py
        module_new.py

    This does not fail on legitimate files. It only flags
    obvious accidental copies inside the same directory.
    """

    suspicious_suffixes = (
        " (1)",
        " (2)",
        "_copy",
        "_backup",
        "_old",
        "_new",
    )

    suspicious_files = []

    for path in PROJECT_ROOT.rglob("*.py"):

        if any(
            part in {
                ".git",
                ".venv",
                "venv",
                "__pycache__",
            }
            for part in path.parts
        ):
            continue

        stem = path.stem.lower()

        if any(
            stem.endswith(
                suffix.lower()
            )
            for suffix in suspicious_suffixes
        ):
            suspicious_files.append(
                str(path.relative_to(PROJECT_ROOT))
            )

    assert not suspicious_files, (
        "Possible duplicate Python files found:\n"
        + "\n".join(suspicious_files)
    )


# ============================================================
# ARCHITECTURE BOUNDARY TESTS
# ============================================================


def test_billing_does_not_require_telegram():
    """
    Billing must remain independent from Telegram runtime.
    """

    from billing.integration import (
        BillingIntegration,
    )

    integration = BillingIntegration()

    summary = integration.user_summary(
        "architecture-billing-user"
    )

    assert summary is not None


def test_ai_does_not_require_external_provider():
    """
    AI layer must be usable in placeholder mode without
    external API credentials.
    """

    from ai.config import (
        get_ai_config,
    )

    config = get_ai_config()

    assert config is not None
    assert hasattr(config, "enabled")


def test_core_does_not_require_telegram():
    """
    Engineering calculation core must remain independent
    from Telegram handlers.
    """

    from core.calculations import (
        default_engine,
    )

    assert default_engine is not None


# ============================================================
# ENVIRONMENT SANITY
# ============================================================


def test_project_has_no_hardcoded_runtime_secret_environment():
    """
    Basic sanity check: project source should not directly
    contain common secret assignments.

    This is intentionally lightweight and is not a security
    scanner.
    """

    forbidden_patterns = (
        "BOT_TOKEN = \"",
        "BOT_TOKEN='",
        "OPENAI_API_KEY = \"",
        "OPENAI_API_KEY='",
    )

    suspicious = []

    for path in _python_files():

        try:
            text = path.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError:
            continue

        for pattern in forbidden_patterns:

            if pattern in text:
                suspicious.append(
                    f"{path.relative_to(PROJECT_ROOT)}: "
                    f"{pattern}"
                )

    assert not suspicious, (
        "Possible hardcoded runtime secret found:\n"
        + "\n".join(suspicious)
    )


# ============================================================
# FINAL ARCHITECTURE SMOKE TEST
# ============================================================


def test_structuralbot_architecture_smoke():
    """
    Final high-level smoke test.

    Confirms that the major layers can coexist:

        Core
          ↓
        Codes
          ↓
        Billing
          ↓
        AI
          ↓
        Handlers
    """

    importlib.import_module(
        "core.models"
    )

    importlib.import_module(
        "codes.base"
    )

    importlib.import_module(
        "billing.integration"
    )

    importlib.import_module(
        "ai.manager"
    )

    importlib.import_module(
        "handlers.main_menu"
    )

    assert True
