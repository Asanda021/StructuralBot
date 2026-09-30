"""
StructuralBot - Architecture QA

Checks:
- Required project directories
- Required package files
- Python syntax
- Importability of core modules
- Importability of code modules
- Importability of AI modules
- Importability of billing modules
- Importability of handlers
- No obvious circular-import failures
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


REQUIRED_DIRECTORIES = (
    "core",
    "codes",
    "codes/iran",
    "handlers",
    "ai",
    "billing",
    "localization",
    "reports",
    "tests",
)


REQUIRED_FILES = (
    "bot.py",
    "config.py",
    "database.py",
    "requirements.txt",
    "core/__init__.py",
    "codes/__init__.py",
    "codes/base.py",
    "codes/iran/__init__.py",
    "ai/__init__.py",
    "billing/__init__.py",
    "handlers/__init__.py",
)


CORE_MODULES = (
    "core.models",
    "core.validation",
    "core.calculations",
    "core.reinforcement",
    "core.bbs",
    "core.cutlist",
    "core.quantities",
    "core.code_adapter",
)


CODE_MODULES = (
    "codes.base",
    "codes.iran",
    "codes.iran.materials",
    "codes.iran.concrete",
    "codes.iran.reinforcement",
    "codes.iran.detailing",
    "codes.iran.validation",
)


AI_MODULES = (
    "ai.service",
    "ai.providers",
    "ai.config",
    "ai.context",
    "ai.prompts",
    "ai.safety",
    "ai.usage",
    "ai.manager",
)


BILLING_MODULES = (
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
)


HANDLER_MODULES = (
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
)


# ---------------------------------------------------------------------------
# PATH HELPERS
# ---------------------------------------------------------------------------

def path_exists(relative_path: str) -> bool:
    return (PROJECT_ROOT / relative_path).exists()


def module_to_path(module_name: str) -> Path:
    parts = module_name.split(".")
    return PROJECT_ROOT.joinpath(*parts).with_suffix(".py")


# ---------------------------------------------------------------------------
# DIRECTORY TESTS
# ---------------------------------------------------------------------------

def test_required_directories_exist() -> None:
    missing = [
        directory
        for directory in REQUIRED_DIRECTORIES
        if not path_exists(directory)
    ]

    assert not missing, (
        "Required project directories are missing: "
        + ", ".join(missing)
    )


def test_required_files_exist() -> None:
    missing = [
        file_name
        for file_name in REQUIRED_FILES
        if not path_exists(file_name)
    ]

    assert not missing, (
        "Required project files are missing: "
        + ", ".join(missing)
    )


# ---------------------------------------------------------------------------
# SYNTAX TESTS
# ---------------------------------------------------------------------------

def _python_files() -> list[Path]:
    return sorted(
        path
        for path in PROJECT_ROOT.rglob("*.py")
        if ".venv" not in path.parts
        and "venv" not in path.parts
        and "__pycache__" not in path.parts
        and ".git" not in path.parts
    )


def test_all_python_files_have_valid_syntax() -> None:
    syntax_errors: list[str] = []

    for path in _python_files():
        try:
            source = path.read_text(
                encoding="utf-8",
            )

            ast.parse(
                source,
                filename=str(path),
            )

        except (SyntaxError, UnicodeDecodeError) as exc:
            syntax_errors.append(
                f"{path.relative_to(PROJECT_ROOT)}: {exc}"
            )

    assert not syntax_errors, (
        "Python syntax errors found:\n"
        + "\n".join(syntax_errors)
    )


# ---------------------------------------------------------------------------
# IMPORT TESTS
# ---------------------------------------------------------------------------

def _assert_importable(
    modules: tuple[str, ...],
    category: str,
) -> None:
    failures: list[str] = []

    for module_name in modules:
        try:
            importlib.import_module(module_name)

        except Exception as exc:
            failures.append(
                f"{module_name}: "
                f"{type(exc).__name__}: {exc}"
            )

    assert not failures, (
        f"{category} import failures:\n"
        + "\n".join(failures)
    )


def test_core_modules_import() -> None:
    _assert_importable(
        CORE_MODULES,
        "Core",
    )


def test_code_modules_import() -> None:
    _assert_importable(
        CODE_MODULES,
        "Code",
    )


def test_ai_modules_import() -> None:
    _assert_importable(
        AI_MODULES,
        "AI",
    )


def test_billing_modules_import() -> None:
    _assert_importable(
        BILLING_MODULES,
        "Billing",
    )


def test_handler_modules_import() -> None:
    _assert_importable(
        HANDLER_MODULES,
        "Handler",
    )


# ---------------------------------------------------------------------------
# PACKAGE EXPORT TESTS
# ---------------------------------------------------------------------------

def test_core_package_imports() -> None:
    module = importlib.import_module("core")

    assert module is not None


def test_codes_package_imports() -> None:
    module = importlib.import_module("codes")

    assert module is not None


def test_ai_package_imports() -> None:
    module = importlib.import_module("ai")

    assert module is not None


def test_billing_package_imports() -> None:
    module = importlib.import_module("billing")

    assert module is not None


def test_handlers_package_imports() -> None:
    module = importlib.import_module("handlers")

    assert module is not None


# ---------------------------------------------------------------------------
# ARCHITECTURE BOUNDARY TESTS
# ---------------------------------------------------------------------------

def test_core_does_not_import_telegram_directly() -> None:
    forbidden = []

    for module_name in CORE_MODULES:
        path = module_to_path(module_name)

        if not path.exists():
            continue

        source = path.read_text(
            encoding="utf-8",
        )

        tree = ast.parse(
            source,
            filename=str(path),
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "telegram" or alias.name.startswith(
                        "telegram."
                    ):
                        forbidden.append(module_name)

            elif isinstance(node, ast.ImportFrom):
                if node.module == "telegram" or (
                    node.module and node.module.startswith("telegram.")
                ):
                    forbidden.append(module_name)

    assert not forbidden, (
        "Core modules must remain independent from Telegram: "
        + ", ".join(sorted(set(forbidden)))
    )


def test_billing_does_not_import_handlers() -> None:
    forbidden = []

    for module_name in BILLING_MODULES:
        path = module_to_path(module_name)

        if not path.exists():
            continue

        source = path.read_text(
            encoding="utf-8",
        )

        tree = ast.parse(
            source,
            filename=str(path),
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "handlers" or alias.name.startswith(
                        "handlers."
                    ):
                        forbidden.append(module_name)

            elif isinstance(node, ast.ImportFrom):
                if node.module == "handlers" or (
                    node.module and node.module.startswith("handlers.")
                ):
                    forbidden.append(module_name)

    assert not forbidden, (
        "Billing modules must not depend on Telegram handlers: "
        + ", ".join(sorted(set(forbidden)))
    )


# ---------------------------------------------------------------------------
# DUPLICATE MODULE NAME CHECK
# ---------------------------------------------------------------------------

def test_no_duplicate_python_module_paths() -> None:
    seen: dict[str, Path] = {}
    duplicates: list[str] = []

    for path in _python_files():
        relative = path.relative_to(PROJECT_ROOT)

        module_key = ".".join(
            relative.with_suffix("").parts
        )

        if module_key in seen:
            duplicates.append(
                f"{module_key}: "
                f"{seen[module_key]} / {relative}"
            )
        else:
            seen[module_key] = relative

    assert not duplicates, (
        "Duplicate Python module paths detected:\n"
        + "\n".join(duplicates)
    )


def test_production_config_requires_secret_key(monkeypatch):
    import importlib
    import config

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BOT_TOKEN", "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    importlib.reload(config)

    try:
        try:
            config.validate_config()
        except RuntimeError as exc:
            assert "SECRET_KEY" in str(exc)
        else:
            raise AssertionError("Production config must require SECRET_KEY.")
    finally:
        monkeypatch.setenv("APP_ENV", "development")
        importlib.reload(config)


def test_database_enables_foreign_keys(tmp_path, monkeypatch):
    import importlib
    import database

    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    import config
    importlib.reload(config)
    importlib.reload(database)

    with database.get_connection() as connection:
        enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]

    assert enabled == 1
