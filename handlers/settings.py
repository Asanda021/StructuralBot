"""
StructuralBot - Settings Handler

User settings:
- Language
- Unit system
- Profession
- Calculation preferences
- Notification preferences
- Reset settings

This module only handles Telegram UI/state.
Persistent storage can be connected later through database.py.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler

try:
    from database import get_user, update_user
except Exception:
    get_user = None
    update_user = None


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

LANGUAGES = {
    "fa": "🇮🇷 فارسی",
    "en": "🇬🇧 English",
    "tr": "🇹🇷 Türkçe",
    "ar": "🇸🇦 العربية",
    "ru": "🇷🇺 Русский",
    "de": "🇩🇪 Deutsch",
    "zh-CN": "🇨🇳 中文",
}

UNIT_SYSTEMS = {
    "metric": "📏 Metric (SI)",
    "engineering": "🏗 Engineering",
    "imperial": "📐 Imperial",
}

PROFESSIONS = {
    "civil_engineer": "👷 Civil Engineer",
    "structural_engineer": "🏗 Structural Engineer",
    "architect": "📐 Architect",
    "contractor": "🔨 Contractor",
    "student": "🎓 Student",
    "other": "👤 Other",
}


# ---------------------------------------------------------
# FALLBACK USER SETTINGS
# ---------------------------------------------------------

_LOCAL_SETTINGS: Dict[int, Dict[str, Any]] = {}


def _default_settings() -> Dict[str, Any]:
    return {
        "language": "fa",
        "unit_system": "metric",
        "profession": None,
        "notifications": True,
        "confirm_before_calculation": True,
        "show_detailed_results": True,
        "auto_save_projects": True,
    }


def _get_settings(user_id: int) -> Dict[str, Any]:
    """
    Load user settings.

    Database integration is optional at this stage.
    A local in-memory fallback is used until the database layer
    is fully connected.
    """
    if user_id not in _LOCAL_SETTINGS:
        _LOCAL_SETTINGS[user_id] = _default_settings()

    settings = _LOCAL_SETTINGS[user_id].copy()

    if get_user is not None:
        try:
            user = get_user(user_id)

            if user:
                if isinstance(user, dict):
                    db_settings = user.get("settings")

                    if isinstance(db_settings, dict):
                        settings.update(db_settings)

        except Exception:
            pass

    return settings


def _save_settings(user_id: int, settings: Dict[str, Any]) -> bool:
    """
    Save settings.

    Database support is attempted first when available.
    Local storage remains as a fallback.
    """
    _LOCAL_SETTINGS[user_id] = settings.copy()

    if update_user is not None:
        try:
            update_user(
                user_id,
                settings=settings,
            )
            return True
        except Exception:
            pass

    return True


# ---------------------------------------------------------
# TEXT HELPERS
# ---------------------------------------------------------

def _lang(user_id: int) -> str:
    return _get_settings(user_id).get("language", "fa")


def _t(language: str, fa: str, en: str) -> str:
    """
    Minimal bilingual helper.

    Full localization is handled later by localization/.
    """
    if language == "fa":
        return fa

    return en


def _settings_title(language: str) -> str:
    return _t(
        language,
        "⚙️ تنظیمات",
        "⚙️ Settings",
    )


def _settings_text(language: str) -> str:
    return _t(
        language,
        "از این بخش می‌توانید تنظیمات حساب و محیط محاسبات را تغییر دهید.",
        "Manage your account and calculation environment settings.",
    )


# ---------------------------------------------------------
# MAIN SETTINGS KEYBOARD
# ---------------------------------------------------------

def get_settings_keyboard(
    language: str = "fa",
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🌐 زبان / Language",
                    callback_data="settings:language",
                )
            ],
            [
                InlineKeyboardButton(
                    "📏 واحدها / Units",
                    callback_data="settings:units",
                )
            ],
            [
                InlineKeyboardButton(
                    "👷 حرفه / Profession",
                    callback_data="settings:profession",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔔 اعلان‌ها / Notifications",
                    callback_data="settings:notifications",
                )
            ],
            [
                InlineKeyboardButton(
                    "🧮 تنظیمات محاسبات",
                    callback_data="settings:calculation",
                )
            ],
            [
                InlineKeyboardButton(
                    "💾 ذخیره خودکار پروژه",
                    callback_data="settings:autosave",
                )
            ],
            [
                InlineKeyboardButton(
                    "♻️ بازنشانی تنظیمات",
                    callback_data="settings:reset",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="menu:back",
                ),
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="menu:home",
                ),
            ],
        ]
    )


# ---------------------------------------------------------
# LANGUAGE KEYBOARD
# ---------------------------------------------------------

def get_language_keyboard() -> InlineKeyboardMarkup:

    rows = []

    for code, name in LANGUAGES.items():
        rows.append(
            [
                InlineKeyboardButton(
                    name,
                    callback_data=f"settings:language:{code}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="settings:main",
            )
        ]
    )

    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------
# UNIT KEYBOARD
# ---------------------------------------------------------

def get_unit_keyboard() -> InlineKeyboardMarkup:

    rows = []

    for code, name in UNIT_SYSTEMS.items():
        rows.append(
            [
                InlineKeyboardButton(
                    name,
                    callback_data=f"settings:units:{code}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="settings:main",
            )
        ]
    )

    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------
# PROFESSION KEYBOARD
# ---------------------------------------------------------

def get_profession_keyboard() -> InlineKeyboardMarkup:

    rows = []

    for code, name in PROFESSIONS.items():
        rows.append(
            [
                InlineKeyboardButton(
                    name,
                    callback_data=f"settings:profession:{code}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="settings:main",
            )
        ]
    )

    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------
# SETTINGS MAIN
# ---------------------------------------------------------

async def show_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    user = update.effective_user

    if not user:
        return

    user_id = user.id
    language = _lang(user_id)

    text = (
        f"{_settings_title(language)}\n\n"
        f"{_settings_text(language)}"
    )

    keyboard = get_settings_keyboard(language)

    if update.callback_query:
        query = update.callback_query

        try:
            await query.answer()
        except Exception:
            pass

        try:
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
            )
        except Exception:
            await query.message.reply_text(
                text=text,
                reply_markup=keyboard,
            )

    elif update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=keyboard,
        )


# ---------------------------------------------------------
# LANGUAGE MENU
# ---------------------------------------------------------

async def show_language_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    await query.answer()

    await query.edit_message_text(
        "🌐 انتخاب زبان / Select Language",
        reply_markup=get_language_keyboard(),
    )


# ---------------------------------------------------------
# UNIT MENU
# ---------------------------------------------------------

async def show_unit_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    await query.answer()

    await query.edit_message_text(
        "📏 انتخاب سیستم واحد / Select Unit System",
        reply_markup=get_unit_keyboard(),
    )


# ---------------------------------------------------------
# PROFESSION MENU
# ---------------------------------------------------------

async def show_profession_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    await query.answer()

    await query.edit_message_text(
        "👷 انتخاب حرفه / Select Profession",
        reply_markup=get_profession_keyboard(),
    )


# ---------------------------------------------------------
# NOTIFICATIONS
# ---------------------------------------------------------

async def toggle_notifications(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    settings = _get_settings(user.id)

    settings["notifications"] = not bool(
        settings.get("notifications", True)
    )

    _save_settings(user.id, settings)

    status = (
        "فعال ✅"
        if settings["notifications"]
        else "غیرفعال ❌"
    )

    await query.answer(
        f"اعلان‌ها: {status}",
        show_alert=False,
    )

    await show_settings(update, context)


# ---------------------------------------------------------
# CALCULATION SETTINGS
# ---------------------------------------------------------

async def show_calculation_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    settings = _get_settings(user.id)

    confirm = (
        "فعال ✅"
        if settings.get("confirm_before_calculation", True)
        else "غیرفعال ❌"
    )

    detailed = (
        "فعال ✅"
        if settings.get("show_detailed_results", True)
        else "غیرفعال ❌"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"تأیید قبل محاسبه: {confirm}",
                    callback_data="settings:toggle_confirm",
                )
            ],
            [
                InlineKeyboardButton(
                    f"نتایج تفصیلی: {detailed}",
                    callback_data="settings:toggle_detailed",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="settings:main",
                )
            ],
        ]
    )

    await query.answer()

    await query.edit_message_text(
        "🧮 تنظیمات محاسبات",
        reply_markup=keyboard,
    )


async def toggle_confirm_before_calculation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    settings = _get_settings(user.id)

    settings["confirm_before_calculation"] = not bool(
        settings.get("confirm_before_calculation", True)
    )

    _save_settings(user.id, settings)

    await query.answer()

    await show_calculation_settings(update, context)


async def toggle_detailed_results(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    settings = _get_settings(user.id)

    settings["show_detailed_results"] = not bool(
        settings.get("show_detailed_results", True)
    )

    _save_settings(user.id, settings)

    await query.answer()

    await show_calculation_settings(update, context)


# ---------------------------------------------------------
# AUTO SAVE
# ---------------------------------------------------------

async def toggle_autosave(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    settings = _get_settings(user.id)

    settings["auto_save_projects"] = not bool(
        settings.get("auto_save_projects", True)
    )

    _save_settings(user.id, settings)

    status = (
        "فعال ✅"
        if settings["auto_save_projects"]
        else "غیرفعال ❌"
    )

    await query.answer(
        f"ذخیره خودکار: {status}",
        show_alert=False,
    )

    await show_settings(update, context)


# ---------------------------------------------------------
# LANGUAGE / UNIT / PROFESSION SELECTION
# ---------------------------------------------------------

async def set_language(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    language_code: str,
) -> None:

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    if language_code not in LANGUAGES:
        await query.answer(
            "زبان نامعتبر است.",
            show_alert=True,
        )
        return

    settings = _get_settings(user.id)
    settings["language"] = language_code

    _save_settings(user.id, settings)

    await query.answer("Language updated ✅")

    await show_settings(update, context)


async def set_unit_system(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    unit_code: str,
) -> None:

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    if unit_code not in UNIT_SYSTEMS:
        await query.answer(
            "سیستم واحد نامعتبر است.",
            show_alert=True,
        )
        return

    settings = _get_settings(user.id)
    settings["unit_system"] = unit_code

    _save_settings(user.id, settings)

    await query.answer("Units updated ✅")

    await show_settings(update, context)


async def set_profession(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    profession_code: str,
) -> None:

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    if profession_code not in PROFESSIONS:
        await query.answer(
            "حرفه نامعتبر است.",
            show_alert=True,
        )
        return

    settings = _get_settings(user.id)
    settings["profession"] = profession_code

    _save_settings(user.id, settings)

    await query.answer("Profession updated ✅")

    await show_settings(update, context)


# ---------------------------------------------------------
# RESET SETTINGS
# ---------------------------------------------------------

async def show_reset_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    await query.answer()

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ بله، بازنشانی",
                    callback_data="settings:reset_confirm",
                ),
                InlineKeyboardButton(
                    "❌ لغو",
                    callback_data="settings:main",
                ),
            ]
        ]
    )

    await query.edit_message_text(
        "⚠️ آیا مطمئن هستید؟\n\n"
        "تمام تنظیمات کاربری به حالت پیش‌فرض برمی‌گردد.",
        reply_markup=keyboard,
    )


async def reset_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    settings = _default_settings()

    _save_settings(user.id, settings)

    await query.answer(
        "تنظیمات بازنشانی شد ✅",
        show_alert=False,
    )

    await show_settings(update, context)


# ---------------------------------------------------------
# CALLBACK ROUTER
# ---------------------------------------------------------

async def settings_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if data == "settings:main":
        await show_settings(update, context)
        return

    if data == "settings:language":
        await show_language_settings(update, context)
        return

    if data.startswith("settings:language:"):
        language_code = data.split(":", 2)[2]

        await set_language(
            update,
            context,
            language_code,
        )
        return

    if data == "settings:units":
        await show_unit_settings(update, context)
        return

    if data.startswith("settings:units:"):
        unit_code = data.split(":", 2)[2]

        await set_unit_system(
            update,
            context,
            unit_code,
        )
        return

    if data == "settings:profession":
        await show_profession_settings(update, context)
        return

    if data.startswith("settings:profession:"):
        profession_code = data.split(":", 2)[2]

        await set_profession(
            update,
            context,
            profession_code,
        )
        return

    if data == "settings:notifications":
        await toggle_notifications(update, context)
        return

    if data == "settings:calculation":
        await show_calculation_settings(update, context)
        return

    if data == "settings:toggle_confirm":
        await toggle_confirm_before_calculation(
            update,
            context,
        )
        return

    if data == "settings:toggle_detailed":
        await toggle_detailed_results(
            update,
            context,
        )
        return

    if data == "settings:autosave":
        await toggle_autosave(update, context)
        return

    if data == "settings:reset":
        await show_reset_confirmation(
            update,
            context,
        )
        return

    if data == "settings:reset_confirm":
        await reset_settings(update, context)
        return

    await query.answer()


# ---------------------------------------------------------
# HANDLER FACTORY
# ---------------------------------------------------------

def get_settings_callback_handler() -> CallbackQueryHandler:
    """
    Returns the callback handler for settings.
    """
    return CallbackQueryHandler(
        settings_callback,
        pattern=r"^settings(?::|$)",
    )


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

__all__ = [
    "LANGUAGES",
    "UNIT_SYSTEMS",
    "PROFESSIONS",
    "get_settings_keyboard",
    "show_settings",
    "show_language_settings",
    "show_unit_settings",
    "show_profession_settings",
    "toggle_notifications",
    "show_calculation_settings",
    "toggle_confirm_before_calculation",
    "toggle_detailed_results",
    "toggle_autosave",
    "set_language",
    "set_unit_system",
    "set_profession",
    "show_reset_confirmation",
    "reset_settings",
    "settings_callback",
    "get_settings_callback_handler",
]
