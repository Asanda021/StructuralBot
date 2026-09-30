"""
StructuralBot - Pytest Configuration

Shared pytest configuration and fixtures for the test suite.

Goals:
- Keep tests isolated from real environment variables.
- Prevent tests from depending on a real Telegram bot token.
- Provide safe temporary paths for test databases/files.
- Avoid accidental production-side effects during automated testing.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# SAFE TEST ENVIRONMENT
# ---------------------------------------------------------------------------

TEST_BOT_TOKEN = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk"
TEST_DB_PATH = "tests/.test_structuralbot.db"


def pytest_configure(config: pytest.Config) -> None:
    """
    Configure a safe environment before test modules are imported.
    """

    os.environ.setdefault("BOT_TOKEN", TEST_BOT_TOKEN)
    os.environ.setdefault("DATABASE_PATH", TEST_DB_PATH)

    # AI must remain disabled during normal unit/integration tests.
    os.environ.setdefault("AI_ENABLED", "false")

    # Never use real external providers during tests.
    os.environ.setdefault("AI_PROVIDER", "placeholder")

    # Keep payment integrations disabled.
    os.environ.setdefault("PAYMENT_PROVIDER", "placeholder")

    # Explicit test environment marker.
    os.environ.setdefault("STRUCTURALBOT_TESTING", "true")


# ---------------------------------------------------------------------------
# SESSION FIXTURE
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_environment() -> dict[str, str]:
    """
    Return the controlled environment used by the test suite.
    """

    return {
        "BOT_TOKEN": os.environ["BOT_TOKEN"],
        "DATABASE_PATH": os.environ["DATABASE_PATH"],
        "AI_ENABLED": os.environ["AI_ENABLED"],
        "AI_PROVIDER": os.environ["AI_PROVIDER"],
        "PAYMENT_PROVIDER": os.environ["PAYMENT_PROVIDER"],
        "STRUCTURALBOT_TESTING": os.environ["STRUCTURALBOT_TESTING"],
    }


# ---------------------------------------------------------------------------
# TEMPORARY DIRECTORY
# ---------------------------------------------------------------------------

@pytest.fixture
def temporary_directory(tmp_path: Path) -> Path:
    """
    Provide an isolated temporary directory for file-producing tests.
    """

    directory = tmp_path / "structuralbot_test"

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


# ---------------------------------------------------------------------------
# TEST DATABASE PATH
# ---------------------------------------------------------------------------

@pytest.fixture
def test_database_path(tmp_path: Path) -> Path:
    """
    Provide an isolated SQLite database path for database tests.
    """

    return tmp_path / "structuralbot_test.db"


# ---------------------------------------------------------------------------
# ENVIRONMENT OVERRIDE HELPER
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_environment(monkeypatch: pytest.MonkeyPatch):
    """
    Helper fixture for tests that need controlled environment variables.

    Usage:

        def test_something(clean_environment):
            clean_environment("SOME_KEY", "some_value")
    """

    def _set(name: str, value: str) -> None:
        monkeypatch.setenv(name, value)

    return _set


# ---------------------------------------------------------------------------
# TELEGRAM TOKEN PATCH
# ---------------------------------------------------------------------------

@pytest.fixture
def dummy_bot_token(monkeypatch: pytest.MonkeyPatch) -> str:
    """
    Replace BOT_TOKEN with a deterministic test-only token.
    """

    monkeypatch.setenv(
        "BOT_TOKEN",
        TEST_BOT_TOKEN,
    )

    return TEST_BOT_TOKEN


# ---------------------------------------------------------------------------
# AI SAFETY
# ---------------------------------------------------------------------------

@pytest.fixture
def disable_external_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensure tests never accidentally call a real AI provider.
    """

    monkeypatch.setenv(
        "AI_ENABLED",
        "false",
    )

    monkeypatch.setenv(
        "AI_PROVIDER",
        "placeholder",
    )

    monkeypatch.delenv(
        "AI_API_KEY",
        raising=False,
    )

    monkeypatch.delenv(
        "OPENAI_API_KEY",
        raising=False,
    )


# ---------------------------------------------------------------------------
# PAYMENT SAFETY
# ---------------------------------------------------------------------------

@pytest.fixture
def disable_external_payments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Ensure billing tests never contact a real payment gateway.
    """

    monkeypatch.setenv(
        "PAYMENT_PROVIDER",
        "placeholder",
    )

    monkeypatch.setenv(
        "PAYMENT_GATEWAY_ENABLED",
        "false",
    )


# ---------------------------------------------------------------------------
# FILE CLEANUP
# ---------------------------------------------------------------------------

@pytest.fixture
def cleanup_file():
    """
    Return a helper that safely removes a generated test file.
    """

    def _cleanup(path: str | Path) -> None:
        file_path = Path(path)

        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
        except OSError:
            # Tests should not fail merely because cleanup was impossible.
            pass

    return _cleanup


# ---------------------------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def project_root() -> Path:
    """
    Return the StructuralBot project root.
    """

    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# BASIC ARCHITECTURE ASSERTION
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def verify_project_root(project_root: Path) -> None:
    """
    Basic sanity check that pytest is running from the expected project.
    """

    required_directories = (
        "core",
        "codes",
        "handlers",
        "ai",
        "billing",
        "tests",
    )

    missing = [
        directory
        for directory in required_directories
        if not (project_root / directory).is_dir()
    ]

    if missing:
        raise RuntimeError(
            "StructuralBot test environment is incomplete. "
            f"Missing directories: {', '.join(missing)}"
        )
