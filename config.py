import os
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------
# TELEGRAM
# ---------------------------------------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

APP_NAME = os.getenv("APP_NAME", "StructuralBot").strip() or "StructuralBot"
APP_VERSION = os.getenv("APP_VERSION", "1.0.0").strip() or "1.0.0"
APP_ENV = os.getenv("APP_ENV", "development").strip().lower() or "development"
DEBUG = os.getenv("DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}

DEFAULT_LANGUAGE = "fa"
DEFAULT_UNIT_SYSTEM = "SI"


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    str(PROJECT_ROOT / "data" / "structuralbot.db"),
).strip()


# ---------------------------------------------------------
# SECURITY
# ---------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

REDACT_SENSITIVE_DATA = os.getenv(
    "REDACT_SENSITIVE_DATA",
    "true",
).strip().lower() in {"1", "true", "yes", "on"}


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_config() -> None:
    """
    Validate required environment variables before
    starting the application.
    """

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not configured. "
            "Set BOT_TOKEN in the environment or .env file."
        )

    if ":" not in BOT_TOKEN or len(BOT_TOKEN) < 20:
        raise RuntimeError(
            "BOT_TOKEN does not look like a valid Telegram bot token."
        )

    if APP_ENV == "production" and not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is required when APP_ENV=production."
        )
