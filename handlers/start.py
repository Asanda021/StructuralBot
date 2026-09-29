"""
StructuralBot - Start Handler

Handles:
- /start
- New user registration
- Returning user detection
- Language selection
- Initial onboarding flow
"""

from __future__ import annotations

from typing import Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)


# ---------------------------------------------------------------------
# SUPPORTED LANGUAGES
# ---------------------------------------------------------------------

SUPPORTED_LANGUAGES = {
    "fa": {
        "name": "🇮🇷 فارسی",
        "native_name": "فارسی",
    },
    "en": {
        "name": "🇬🇧 English",
        "native_name": "English",
    },
    "tr": {
        "name": "🇹🇷 Türkçe",
        "native_name": "Türkçe",
    },
    "ar": {
        "name": "🇸🇦 العربية",
        "native_name": "العربية",
    },
    "ru": {
        "name": "🇷🇺 Русский",
        "native_name": "Русский",
    },
    "de": {
        "name": "🇩🇪 Deutsch",
        "native_name": "Deutsch",
    },
    "zh-CN": {
        "name": "🇨🇳 简体中文",
        "native_name": "简体中文",
    },
}


# ---------------------------------------------------------------------
# TEXTS
# ---------------------------------------------------------------------

WELCOME_TEXT = (
    "🏗️ به StructuralBot خوش آمدید!\n\n"
    "دستیار تخصصی محاسبات سازه، جزئیات اجرایی، "
    "برآورد مصالح و مدیریت پروژه.\n\n"
    "🌍 لطفاً زبان خود را انتخاب کنید:"
)

RETURNING_TEXT = (
    "👋 خوش برگشتی!\n\n"
    "تنظیمات و پروژه‌های قبلی شما حفظ شده‌اند."
)

LANGUAGE_SELECTED_TEXT = {
    "fa": "🇮🇷 زبان فارسی انتخاب شد.",
    "en": "🇬🇧 English selected.",
    "tr": "🇹🇷 Türkçe seçildi.",
    "ar": "🇸🇦 تم اختيار اللغة العربية.",
    "ru": "🇷🇺 Выбран русский язык.",
    "de": "🇩🇪 Deutsch wurde ausgewählt.",
    "zh-CN": "🇨🇳 已选择简体中文。",
}


# ---------------------------------------------------------------------
# DATABASE IMPORT
# ---------------------------------------------------------------------

try:
    from database import get_user, create_user
except ImportError:
    get_user = None
    create_user = None


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def _telegram_user_id(update: Update) -> Optional[int]:
    """Return Telegram user ID safely."""
    if update.effective_user is None:
        return None

    return update.effective_user.id


def _is_existing_user(user_id: int) -> bool:
    """Check whether a Telegram user already exists."""
    if get_user is None:
        return False

    try:
        user = get_user(user_id)
        return user is not None
    except Exception:
        return False


def _create_user_safely(update: Update) -> None:
    """Create a new user record when database support is available."""
    if create_user is None:
        return

    user_id = _telegram_user_id(update)

    if user_id is None:
        return

    telegram_user = update.effective_user

    try:
        create_user(
            user_id=user_id,
            username=(
                telegram_user.username
                if telegram_user is not None
                else None
            ),
            first_name=(
                telegram_user.first_name
                if telegram_user is not None
                else None
            ),
            last_name=(
                telegram_user.last_name
                if telegram_user is not None
                else None
            ),
        )

    except TypeError:
        # Compatibility with a simpler database API.
        try:
            create_user(user_id)
        except Exception:
            pass

    except Exception:
        pass


# ---------------------------------------------------------------------
# LANGUAGE KEYBOARD
# ---------------------------------------------------------------------

def language_keyboard() -> InlineKeyboardMarkup:
    """
    Build the language selection keyboard.

    Layout:
        Persian | English
        Turkish | Arabic
        Russian | German
        Chinese
    """

    buttons = [
        InlineKeyboardButton(
            SUPPORTED_LANGUAGES["fa"]["name"],
            callback_data="language:fa",
        ),
        InlineKeyboardButton(
            SUPPORTED_LANGUAGES["en"]["name"],
            callback_data="language:en",
        ),
        InlineKeyboardButton(
            SUPPORTED_LANGUAGES["tr"]["name"],
            callback_data="language:tr",
        ),
        InlineKeyboardButton(
            SUPPORTED_LANGUAGES["ar"]["name"],
            callback_data="language:ar",
        ),
        InlineKeyboardButton(
            SUPPORTED_LANGUAGES["ru"]["name"],
            callback_data="language:ru",
        ),
        InlineKeyboardButton(
            SUPPORTED_LANGUAGES["de"]["name"],
            callback_data="language:de",
        ),
        InlineKeyboardButton(
            SUPPORTED_LANGUAGES["zh-CN"]["name"],
            callback_data="language:zh-CN",
        ),
    ]

    return InlineKeyboardMarkup(
        [
            buttons[0:2],
            buttons[2:4],
            buttons[4:6],
            buttons[6:7],
        ]
    )


# ---------------------------------------------------------------------
# /START
# ---------------------------------------------------------------------

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle /start.

    New user:
        Register user
        Show language selection

    Existing user:
        Skip onboarding
        Continue toward main menu
    """

    if update.effective_message is None:
        return

    user_id = _telegram_user_id(update)

    if user_id is None:
        await update.effective_message.reply_text(
            "خطا در شناسایی کاربر."
        )
        return

    existing_user = _is_existing_user(user_id)

    if not existing_user:
        _create_user_safely(update)

        context.user_data["is_new_user"] = True
        context.user_data["onboarding_required"] = True
        context.user_data["language_selected"] = False

        await update.effective_message.reply_text(
            WELCOME_TEXT,
            reply_markup=language_keyboard(),
        )

        return

    context.user_data["is_new_user"] = False
    context.user_data["onboarding_required"] = False
    context.user_data["language_selected"] = True
    context.user_data["open_main_menu"] = True

    await update.effective_message.reply_text(
        RETURNING_TEXT
    )


# ---------------------------------------------------------------------
# LANGUAGE SELECTION
# ---------------------------------------------------------------------

async def language_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle language selection."""

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("language:"):
        return

    language = data.split(":", 1)[1]

    if language not in SUPPORTED_LANGUAGES:
        await query.answer(
            "Invalid language.",
            show_alert=True,
        )
        return

    # Save language in temporary session state.
    context.user_data["language"] = language
    context.user_data["language_selected"] = True
    context.user_data["onboarding_required"] = True

    selected_text = LANGUAGE_SELECTED_TEXT.get(
        language,
        LANGUAGE_SELECTED_TEXT["en"],
    )

    if query.message is not None:
        await query.message.edit_text(
            selected_text
            + "\n\n"
            + _next_step_text(language)
        )


# ---------------------------------------------------------------------
# NEXT ONBOARDING STEP
# ---------------------------------------------------------------------

def _next_step_text(language: str) -> str:
    """
    Return the next onboarding instruction.

    Unit-system selection will be handled by the onboarding/settings
    handler in the next stage.
    """

    texts = {
        "fa": (
            "⚙️ مرحله بعد:\n"
            "انتخاب سیستم واحد"
        ),
        "en": (
            "⚙️ Next step:\n"
            "Select your unit system."
        ),
        "tr": (
            "⚙️ Sonraki adım:\n"
            "Birim sisteminizi seçin."
        ),
        "ar": (
            "⚙️ الخطوة التالية:\n"
            "اختر نظام الوحدات."
        ),
        "ru": (
            "⚙️ Следующий шаг:\n"
            "Выберите систему единиц."
        ),
        "de": (
            "⚙️ Nächster Schritt:\n"
            "Wählen Sie Ihr Einheitensystem."
        ),
        "zh-CN": (
            "⚙️ 下一步：\n"
            "请选择单位制。"
        ),
    }

    return texts.get(language, texts["en"])


# ---------------------------------------------------------------------
# HANDLER FACTORIES
# ---------------------------------------------------------------------

def get_start_handler() -> CommandHandler:
    """Return the /start handler."""
    return CommandHandler(
        "start",
        start_command,
    )


def get_language_handler() -> CallbackQueryHandler:
    """Return the language selection callback handler."""
    return CallbackQueryHandler(
        language_callback,
        pattern=r"^language:",
    )


# ---------------------------------------------------------------------
# COMMON ALIASES
# ---------------------------------------------------------------------

start_handler = get_start_handler()
language_handler = get_language_handler()


# ---------------------------------------------------------------------
# EXPORTS
# ---------------------------------------------------------------------

__all__ = [
    "SUPPORTED_LANGUAGES",
    "language_keyboard",
    "start_command",
    "language_callback",
    "get_start_handler",
    "get_language_handler",
    "start_handler",
    "language_handler",
]
