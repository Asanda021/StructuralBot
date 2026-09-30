"""
StructuralBot - Telegram Bot Entry Point

Main application bootstrap.

Architecture:

    Telegram
        ↓
    bot.py
        ↓
    handlers/
        ↓
    application services
        ↓
    core / codes / billing / ai

Important:
    - Engineering calculations do NOT belong here.
    - Billing logic does NOT belong here.
    - AI logic does NOT belong here.
    - bot.py is only the Telegram application bootstrap
      and central routing layer.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# ENVIRONMENT
# =========================================================

try:
    from dotenv import load_dotenv

    load_dotenv(
        PROJECT_ROOT / ".env"
    )

except ImportError:
    pass


# =========================================================
# TELEGRAM
# =========================================================

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


# =========================================================
# CONFIG
# =========================================================

from config import (
    BOT_TOKEN,
    validate_config,
)


# =========================================================
# DATABASE
# =========================================================

from database import (
    initialize_database,
)


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format=(
        "%(asctime)s | "
        "%(name)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
    level=logging.INFO,
)

logger = logging.getLogger(
    "StructuralBot"
)


# =========================================================
# HANDLER IMPORTS
# =========================================================

# ---------------------------------------------------------
# START
# ---------------------------------------------------------

from handlers.start import (
    start_command,
    language_callback,
)


# ---------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------

from handlers.main_menu import (
    main_menu_callback,
    navigation_callback,
)


# ---------------------------------------------------------
# PROJECTS
# ---------------------------------------------------------

from handlers.projects import (
    projects_callback,
    project_name_message,
)


# ---------------------------------------------------------
# CALCULATIONS
# ---------------------------------------------------------

from handlers.calculations import (
    calculations_callback,
)


# ---------------------------------------------------------
# FOUNDATION
# ---------------------------------------------------------

from handlers.foundation import (
    foundation_callback,
)


# ---------------------------------------------------------
# COLUMNS
# ---------------------------------------------------------

from handlers.columns import (
    columns_callback,
    receive_column_manual_input,
)


# ---------------------------------------------------------
# BEAMS
# ---------------------------------------------------------

from handlers.beams import (
    beams_callback,
    receive_beam_manual_input,
)


# ---------------------------------------------------------
# SLABS
# ---------------------------------------------------------

from handlers.slabs import (
    slabs_callback,
    receive_slab_manual_input,
)


# ---------------------------------------------------------
# REBAR
# ---------------------------------------------------------

from handlers.rebar import (
    rebar_callback,
)


# ---------------------------------------------------------
# EQUIVALENCY
# ---------------------------------------------------------

from handlers.equivalency import (
    equivalency_callback,
    equivalency_message,
)


# ---------------------------------------------------------
# QUANTITIES
# ---------------------------------------------------------

from handlers.quantities import (
    quantities_callback,
    quantities_message,
)


# ---------------------------------------------------------
# REPORTS
# ---------------------------------------------------------

from handlers.reports import (
    reports_callback,
)


# ---------------------------------------------------------
# AI
# ---------------------------------------------------------

from handlers.ai import (
    ai_callback,
    ai_message,
)


# ---------------------------------------------------------
# ACCOUNT
# ---------------------------------------------------------

from handlers.account import (
    account_callback,
)


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

from handlers.settings import (
    settings_callback,
)


# ---------------------------------------------------------
# DESIGN CODES
# ---------------------------------------------------------

from handlers.codes import (
    code_callback,
)


# =========================================================
# RUNTIME STATE
# =========================================================

class BotRuntime:
    """
    Runtime information for the Telegram application.
    """

    def __init__(self) -> None:

        self.database_initialized = False
        self.application: Optional[
            Application
        ] = None

        self.handlers_registered = False


runtime = BotRuntime()


# =========================================================
# START ROUTER
# =========================================================

async def start_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Central /start entry point.

    The actual onboarding logic lives in handlers/start.py.
    """

    await start_command(
        update,
        context,
    )


# =========================================================
# LANGUAGE ROUTER
# =========================================================

async def language_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route language-selection callbacks to start.py.
    """

    await language_callback(
        update,
        context,
    )


# =========================================================
# MAIN MENU ROUTER
# =========================================================

async def main_menu_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route main-menu callbacks.

    Examples:

        menu:...
        navigation:...
        calc:...
        restart:...
        home
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("navigation:")
        or data.startswith("menu:")
        or data.startswith("calc:")
        or data.startswith("restart:")
        or data in {
            "home",
            "main_menu",
            "navigation:main",
        }
    ):
        await main_menu_callback(
            update,
            context,
        )

        return

    # Keep navigation callback available for legacy
    # navigation identifiers.
    if data.startswith(
        "navigation_"
    ):
        await navigation_callback(
            update,
            context,
        )


# =========================================================
# PROJECT ROUTER
# =========================================================

async def project_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route project-related callbacks.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if data.startswith(
        "project:"
    ) or data.startswith(
        "projects:"
    ):
        await projects_callback(
            update,
            context,
        )


# =========================================================
# CALCULATION ROUTER
# =========================================================

async def calculation_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route general calculation callbacks.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if data.startswith(
        "calculation:"
    ) or data.startswith(
        "calculations:"
    ):
        await calculations_callback(
            update,
            context,
        )


# =========================================================
# FOUNDATION ROUTER
# =========================================================

async def foundation_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route foundation calculations.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if data.startswith(
        "foundation"
    ):
        await foundation_callback(
            update,
            context,
        )


# =========================================================
# COLUMN ROUTER
# =========================================================

async def column_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route column calculations.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("column")
        or data.startswith("columns")
    ):
        await columns_callback(
            update,
            context,
        )


# =========================================================
# BEAM ROUTER
# =========================================================

async def beam_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route beam calculations.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("beam")
        or data.startswith("beams")
    ):
        await beams_callback(
            update,
            context,
        )


# =========================================================
# SLAB ROUTER
# =========================================================

async def slab_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route slab / roof calculations.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("slab")
        or data.startswith("slabs")
        or data.startswith("roof")
    ):
        await slabs_callback(
            update,
            context,
        )


# =========================================================
# REBAR ROUTER
# =========================================================

async def rebar_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route reinforcement, BBS and Cut List callbacks.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("rebar")
        or data.startswith("bbs")
        or data.startswith("cutlist")
    ):
        await rebar_callback(
            update,
            context,
        )


# =========================================================
# EQUIVALENCY ROUTER
# =========================================================

async def equivalency_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route rebar equivalency callbacks.

    Supports the callback families currently used by
    equivalency.py.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("equiv:")
        or data.startswith("equiv_")
        or data.startswith("equiv_diameter:")
        or data.startswith("rebar_eq:")
    ):
        await equivalency_callback(
            update,
            context,
        )


# =========================================================
# QUANTITY ROUTER
# =========================================================

async def quantity_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route material quantity callbacks.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("quantity:")
        or data.startswith("quantities:")
    ):
        await quantities_callback(
            update,
            context,
        )


# =========================================================
# REPORT ROUTER
# =========================================================

async def report_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route report callbacks.

    Supports the report.py callback family:

        report:
        report_
        report...
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("report:")
        or data.startswith("report_")
        or data.startswith("report")
    ):
        await reports_callback(
            update,
            context,
        )


# =========================================================
# AI ROUTER
# =========================================================

async def ai_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route AI assistant callbacks.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("ai:")
        or data.startswith("ai_")
    ):
        await ai_callback(
            update,
            context,
        )


# =========================================================
# ACCOUNT ROUTER
# =========================================================

async def account_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route account, subscription and credit callbacks.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("account:")
        or data.startswith("account_")
        or data.startswith("subscription:")
        or data.startswith("credits:")
        or data.startswith("menu:subscription")
    ):
        await account_callback(
            update,
            context,
        )


# =========================================================
# SETTINGS ROUTER
# =========================================================

async def settings_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Route settings callbacks.
    """

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    if (
        data.startswith("settings:")
        or data.startswith("settings_")
    ):
        await settings_callback(
            update,
            context,
        )


# =========================================================
# UNKNOWN CALLBACK
# =========================================================

async def unknown_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Final fallback for unknown callback data.

    This handler is intentionally placed in the last group.
    """

    query = update.callback_query

    if query is None:
        return

    try:
        await query.answer(
            "این گزینه در حال حاضر در دسترس نیست.",
            show_alert=False,
        )
    except Exception:
        logger.debug(
            "Could not answer unknown callback.",
            exc_info=True,
        )

    logger.warning(
        "Unhandled callback data: %s",
        query.data,
    )


# =========================================================
# TEXT FALLBACK
# =========================================================

async def unknown_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Fallback for plain text messages that are not handled
    by a conversation-specific handler.
    """

    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "لطفاً از منوی StructuralBot استفاده کن."
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Global Telegram error handler.

    Internal exceptions are logged.
    Stack traces are never sent to the user.
    """

    error = context.error

    logger.error(
        "Unhandled Telegram error: %s",
        error,
        exc_info=(
            error
            if isinstance(
                error,
                BaseException,
            )
            else None
        ),
    )

    try:

        if isinstance(
            update,
            Update,
        ):

            message = (
                update.effective_message
            )

            if message is not None:

                await message.reply_text(
                    "⚠️ یک خطای داخلی رخ داد.\n"
                    "لطفاً دوباره تلاش کن."
                )

    except Exception:

        logger.debug(
            "Could not send error message.",
            exc_info=True,
        )


# =========================================================
# APPLICATION
# =========================================================

def create_application() -> Application:
    """
    Create and configure the Telegram application.
    """

    # -----------------------------------------------------
    # Validate configuration
    # -----------------------------------------------------

    validate_config()

    # -----------------------------------------------------
    # Build application
    # -----------------------------------------------------

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    runtime.application = application

    # =====================================================
    # COMMANDS
    # =====================================================

    application.add_handler(
        CommandHandler(
            "start",
            start_router,
        )
    )

    # =====================================================
    # LANGUAGE
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            language_router,
            pattern=r"^(?:lang_|language:)(fa|en|tr|ar|ru|de|zh-CN)$",
        )
    )

    # =====================================================
    # MAIN MENU / NAVIGATION
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            main_menu_router,
            pattern=(
                r"^(?:"
                r"home"
                r"|main_menu"
                r"|navigation:.*"
                r"|navigation_.*"
                r"|menu:.*"
                r"|calc:.*"
                r"|restart:.*"
                r")$"
            ),
        )
    )

    # =====================================================
    # PROJECTS
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            project_router,
            pattern=r"^(?:project|projects):.*$",
        )
    )

    # =====================================================
    # DESIGN CODES
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            code_callback,
            pattern=r"^(?:codes:list|codecountry:.*|codeset:.*)$",
        ),
    )

    # =====================================================
    # GENERAL CALCULATIONS
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            calculation_router,
            pattern=(
                r"^(?:"
                r"calculation"
                r"|calculations"
                r"):.*$"
            ),
        )
    )

    # =====================================================
    # FOUNDATION
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            foundation_router,
            pattern=r"^foundation(?:[:_].*)?$",
        )
    )

    # =====================================================
    # COLUMNS
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            column_router,
            pattern=r"^(?:column|columns)(?:[:_].*)?$",
        )
    )

    # =====================================================
    # BEAMS
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            beam_router,
            pattern=r"^(?:beam|beams)(?:[:_].*)?$",
        )
    )

    # =====================================================
    # SLABS / ROOFS
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            slab_router,
            pattern=(
                r"^(?:"
                r"slab"
                r"|slabs"
                r"|roof"
                r")(?:[:_].*)?$"
            ),
        )
    )

    # =====================================================
    # REBAR / BBS / CUT LIST
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            rebar_router,
            pattern=(
                r"^(?:"
                r"rebar"
                r"|bbs"
                r"|cutlist"
                r")(?:[:_].*)?$"
            ),
        )
    )

    # =====================================================
    # REBAR EQUIVALENCY
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            equivalency_router,
            pattern=(
                r"^(?:"
                r"equiv:"
                r"|equiv_"
                r"|equiv_diameter:"
                r"|rebar_eq:"
                r").*$"
            ),
        )
    )

    # =====================================================
    # QUANTITIES
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            quantity_router,
            pattern=(
                r"^(?:"
                r"quantity:"
                r"|quantities:"
                r").*$"
            ),
        )
    )

    # =====================================================
    # REPORTS
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            report_router,
            pattern=r"^report(?:[:_].*)?$",
        )
    )

    # =====================================================
    # AI
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            ai_router,
            pattern=r"^ai(?:[:_].*)?$",
        )
    )

    # =====================================================
    # ACCOUNT / BILLING
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            account_router,
            pattern=(
                r"^(?:"
                r"account"
                r"|subscription"
                r"|credits"
                r"|menu:subscription"
                r")(?:[:_].*)?$"
            ),
        )
    )

    # =====================================================
    # SETTINGS
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            settings_router,
            pattern=r"^settings(?:[:_].*)?$",
        )
    )

    # =====================================================
    # UNKNOWN CALLBACK
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            unknown_callback,
            pattern=r"^.+$",
            block=False,
        ),
        group=999,
    )

    # =====================================================
    # =====================================================
    # STATEFUL TEXT ROUTER
    # =====================================================
    async def _stateful_text_router(update, context):
        if context.user_data.get("awaiting_project_name"):
            await project_name_message(update, context)
            return
        if context.user_data.get("column_waiting_manual_input"):
            await receive_column_manual_input(update, context)
            return
        if context.user_data.get("beam_waiting_manual_input"):
            await receive_beam_manual_input(update, context)
            return
        if context.user_data.get("slab_waiting_manual_input"):
            await receive_slab_manual_input(update, context)
            return
        if context.user_data.get("equiv_waiting_count"):
            await equivalency_message(update, context)
            return
        if context.user_data.get("quantity_waiting_value"):
            await quantities_message(update, context)
            return
        if context.user_data.get("ai_waiting_message"):
            await ai_message(update, context)
            return
        await unknown_text(update, context)

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            _stateful_text_router,
        ),
        group=0,
    )

    # TEXT FALLBACK
    # =====================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            unknown_text,
        ),
        group=999,
    )

    # =====================================================
    # ERROR HANDLER
    # =====================================================

    application.add_error_handler(
        error_handler
    )

    runtime.handlers_registered = True

    return application


# =========================================================
# MAIN
# =========================================================

def main() -> None:
    """
    Application entry point.
    """

    logger.info(
        "Initializing StructuralBot..."
    )

    # -----------------------------------------------------
    # Database
    # -----------------------------------------------------

    logger.info(
        "Initializing database..."
    )

    initialize_database()

    runtime.database_initialized = True

    # -----------------------------------------------------
    # Telegram application
    # -----------------------------------------------------

    logger.info(
        "Creating Telegram application..."
    )

    application = create_application()

    logger.info(
        "StructuralBot is starting..."
    )

    # -----------------------------------------------------
    # Polling
    # -----------------------------------------------------

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()
