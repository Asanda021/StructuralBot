import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN, validate_config
from database import initialize_database


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# START COMMAND
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Initial /start handler.

    The full onboarding system will be moved to
    handlers/start.py in the next stage.
    """

    user = update.effective_user

    if user is None:
        return

    first_name = user.first_name or "کاربر"

    await update.message.reply_text(
        f"👋 سلام {first_name}\n\n"
        "🏗 به StructuralBot خوش آمدی.\n\n"
        "نسخه پایه بات با موفقیت اجرا شد."
    )


# =========================================================
# APPLICATION
# =========================================================

def create_application() -> Application:
    """
    Create and configure the Telegram application.
    """

    validate_config()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start_command)
    )

    return application


# =========================================================
# MAIN
# =========================================================

def main() -> None:
    """
    Application entry point.
    """

    logger.info("Initializing database...")

    initialize_database()

    logger.info("Creating Telegram application...")

    application = create_application()

    logger.info("StructuralBot is starting...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()
