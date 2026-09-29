import os

from dotenv import load_dotenv


# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# TELEGRAM
# ---------------------------------------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

APP_NAME = "StructuralBot"
APP_VERSION = "1.0.0"

DEFAULT_LANGUAGE = "fa"
DEFAULT_UNIT_SYSTEM = "SI"


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "structural_bot.db"
)


# ---------------------------------------------------------
# SECURITY
# ---------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()


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
