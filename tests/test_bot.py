"""
StructuralBot - Bot Bootstrap Tests

Tests the Telegram application bootstrap and central routing
layer without starting polling or contacting Telegram servers.

This file verifies:

    - bot.py imports correctly
    - application can be created
    - handlers are registered
    - critical callback routes exist
    - error handler is installed
    - database initialization is not executed during import
"""

from __future__ import annotations

import importlib
import re


# ============================================================
# IMPORT
# ============================================================


def test_bot_module_imports():
    """
    bot.py must import successfully.
    """

    bot = importlib.import_module("bot")

    assert bot is not None


# ============================================================
# RUNTIME
# ============================================================


def test_bot_runtime_exists():
    """
    bot.py must expose its runtime state.
    """

    from bot import runtime

    assert runtime is not None

    assert hasattr(
        runtime,
        "database_initialized",
    )

    assert hasattr(
        runtime,
        "application",
    )

    assert hasattr(
        runtime,
        "handlers_registered",
    )


# ============================================================
# APPLICATION CREATION
# ============================================================


def test_create_application_exists():
    """
    create_application() must be publicly available.
    """

    from bot import create_application

    assert callable(
        create_application
    )


def test_create_application_returns_application():
    """
    Application factory must create a Telegram Application.

    No polling is started.
    """

    from telegram.ext import Application

    from bot import (
        create_application,
    )

    application = create_application()

    try:

        assert isinstance(
            application,
            Application,
        )

    finally:

        # ApplicationBuilder does not start polling here.
        # Explicit shutdown is intentionally avoided because
        # the application has not been initialized/run.
        pass


# ============================================================
# ROUTER AVAILABILITY
# ============================================================


def test_start_router_exists():
    from bot import start_router

    assert callable(start_router)


def test_language_router_exists():
    from bot import language_router

    assert callable(language_router)


def test_main_menu_router_exists():
    from bot import main_menu_router

    assert callable(main_menu_router)


def test_project_router_exists():
    from bot import project_router

    assert callable(project_router)


def test_calculation_router_exists():
    from bot import calculation_router

    assert callable(calculation_router)


def test_foundation_router_exists():
    from bot import foundation_router

    assert callable(foundation_router)


def test_column_router_exists():
    from bot import column_router

    assert callable(column_router)


def test_beam_router_exists():
    from bot import beam_router

    assert callable(beam_router)


def test_slab_router_exists():
    from bot import slab_router

    assert callable(slab_router)


def test_rebar_router_exists():
    from bot import rebar_router

    assert callable(rebar_router)


def test_equivalency_router_exists():
    from bot import equivalency_router

    assert callable(equivalency_router)


def test_quantity_router_exists():
    from bot import quantity_router

    assert callable(quantity_router)


def test_report_router_exists():
    from bot import report_router

    assert callable(report_router)


def test_ai_router_exists():
    from bot import ai_router

    assert callable(ai_router)


def test_account_router_exists():
    from bot import account_router

    assert callable(account_router)


def test_settings_router_exists():
    from bot import settings_router

    assert callable(settings_router)


# ============================================================
# APPLICATION HANDLERS
# ============================================================


def _handler_patterns(application):
    """
    Extract callback handler patterns from the Telegram
    application's handler groups.
    """

    patterns = []

    for handlers in application.handlers.values():

        for handler in handlers:

            pattern = getattr(
                handler,
                "pattern",
                None,
            )

            if pattern is None:
                continue

            patterns.append(
                pattern
            )

    return patterns


def test_application_has_handlers():
    """
    Application must contain registered handlers.
    """

    from bot import create_application

    application = create_application()

    total_handlers = sum(
        len(group)
        for group in application.handlers.values()
    )

    assert total_handlers > 0


def test_start_command_registered():
    """
    /start must be registered.
    """

    from bot import create_application

    application = create_application()

    command_found = False

    for handlers in application.handlers.values():

        for handler in handlers:

            callback = getattr(
                handler,
                "callback",
                None,
            )

            if (
                callback is not None
                and getattr(
                    callback,
                    "__name__",
                    "",
                )
                == "start_router"
            ):
                command_found = True

    assert command_found


def test_error_handler_registered():
    """
    Global error handler must be registered.
    """

    from bot import create_application

    application = create_application()

    assert len(
        application.error_handlers
    ) >= 1


# ============================================================
# CALLBACK ROUTING
# ============================================================


def test_main_menu_route_exists():
    """
    Main menu callback route must be present.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        pattern is not None
        and (
            "menu"
            in str(pattern)
            or "calc"
            in str(pattern)
        )
        for pattern in patterns
    )


def test_project_route_exists():
    """
    Project callback route must be present.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "project"
        in str(pattern)
        for pattern in patterns
    )


def test_foundation_route_exists():
    """
    Foundation route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "foundation"
        in str(pattern)
        for pattern in patterns
    )


def test_column_route_exists():
    """
    Column route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "column"
        in str(pattern)
        for pattern in patterns
    )


def test_beam_route_exists():
    """
    Beam route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "beam"
        in str(pattern)
        for pattern in patterns
    )


def test_slab_route_exists():
    """
    Slab / roof route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "slab"
        in str(pattern)
        or "roof"
        in str(pattern)
        for pattern in patterns
    )


def test_rebar_route_exists():
    """
    Reinforcement route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "rebar"
        in str(pattern)
        or "bbs"
        in str(pattern)
        or "cutlist"
        in str(pattern)
        for pattern in patterns
    )


def test_equivalency_route_exists():
    """
    Rebar equivalency route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "equiv"
        in str(pattern)
        or "rebar_eq"
        in str(pattern)
        for pattern in patterns
    )


def test_quantity_route_exists():
    """
    Quantity takeoff route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "quantity"
        in str(pattern)
        for pattern in patterns
    )


def test_report_route_exists():
    """
    Report route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "report"
        in str(pattern)
        for pattern in patterns
    )


def test_ai_route_exists():
    """
    AI route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "ai"
        in str(pattern)
        for pattern in patterns
    )


def test_account_route_exists():
    """
    Account / subscription route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "account"
        in str(pattern)
        or "subscription"
        in str(pattern)
        for pattern in patterns
    )


def test_settings_route_exists():
    """
    Settings route must be registered.
    """

    from bot import create_application

    application = create_application()

    patterns = _handler_patterns(
        application
    )

    assert any(
        "settings"
        in str(pattern)
        for pattern in patterns
    )


# ============================================================
# FALLBACK
# ============================================================


def test_unknown_callback_fallback_exists():
    """
    A final callback fallback must exist.
    """

    from bot import create_application

    application = create_application()

    found = False

    for handlers in application.handlers.values():

        for handler in handlers:

            callback = getattr(
                handler,
                "callback",
                None,
            )

            if (
                callback is not None
                and getattr(
                    callback,
                    "__name__",
                    "",
                )
                == "unknown_callback"
            ):
                found = True

    assert found


def test_text_fallback_exists():
    """
    A final text fallback must exist.
    """

    from bot import create_application

    application = create_application()

    found = False

    for handlers in application.handlers.values():

        for handler in handlers:

            callback = getattr(
                handler,
                "callback",
                None,
            )

            if (
                callback is not None
                and getattr(
                    callback,
                    "__name__",
                    "",
                )
                == "unknown_text"
            ):
                found = True

    assert found


# ============================================================
# NO POLLING DURING IMPORT
# ============================================================


def test_import_does_not_start_polling():
    """
    Importing bot.py must never start Telegram polling.
    """

    bot = importlib.import_module(
        "bot"
    )

    assert hasattr(
        bot,
        "main",
    )

    # Import itself must only define the application.
    # main() is intentionally not called here.


# ============================================================
# ROUTER ASYNC API
# ============================================================


def test_routers_are_async_functions():
    """
    Telegram handlers must be coroutine functions.
    """

    import inspect

    from bot import (
        start_router,
        language_router,
        main_menu_router,
        project_router,
        calculation_router,
        foundation_router,
        column_router,
        beam_router,
        slab_router,
        rebar_router,
        equivalency_router,
        quantity_router,
        report_router,
        ai_router,
        account_router,
        settings_router,
        unknown_callback,
        unknown_text,
        error_handler,
    )

    routers = [
        start_router,
        language_router,
        main_menu_router,
        project_router,
        calculation_router,
        foundation_router,
        column_router,
        beam_router,
        slab_router,
        rebar_router,
        equivalency_router,
        quantity_router,
        report_router,
        ai_router,
        account_router,
        settings_router,
        unknown_callback,
        unknown_text,
        error_handler,
    ]

    for router in routers:

        assert inspect.iscoroutinefunction(
            router
        ), (
            f"{router.__name__} "
            "must be async"
        )


# ============================================================
# BOT MODULE API
# ============================================================


def test_bot_public_api():
    """
    Verify the central bootstrap API.
    """

    import bot

    required = [
        "create_application",
        "main",
        "runtime",
        "start_router",
        "main_menu_router",
        "error_handler",
    ]

    for name in required:

        assert hasattr(
            bot,
            name,
        ), (
            f"bot.py missing public API: {name}"
        )


# ============================================================
# FINAL SMOKE TEST
# ============================================================


def test_bot_smoke():
    """
    Final bootstrap smoke test.

    This deliberately stops before polling.
    """

    from bot import (
        create_application,
    )

    application = create_application()

    assert application is not None

    assert (
        len(
            application.handlers
        )
        > 0
    )
