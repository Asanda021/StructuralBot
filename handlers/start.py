from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database import create_user, get_user_by_telegram_id


# =========================================================
# LANGUAGE OPTIONS
# =========================================================

LANGUAGES = {
    "fa": "🇮🇷 فارسی",
    "en": "🇬🇧 English",
    "tr": "🇹🇷 Türkçe",
    "ar": "🇸🇦 العربية",
    "ru": "🇷🇺 Русский",
    "de": "🇩🇪 Deutsch",
    "zh-CN": "🇨🇳 简体中文",
}


# =========================================================
# /START
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    user = update.effective_user

    if user is None or update.message is None:
        return

    telegram_id = user.id

    # -----------------------------------------------------
    # Check existing user
    # -----------------------------------------------------

    existing_user = get_user_by_telegram_id(telegram_id)

    if existing_user:
        await update.message.reply_text(
            f"👋 خوش آمدی {user.first_name or 'کاربر'}\n\n"
            "🏗 StructuralBot آماده است.\n\n"
            "از منوی اصلی می‌توانی پروژه‌ها و محاسبات خود را "
            "مدیریت کنی."
        )
        return

    # -----------------------------------------------------
    # Store Telegram profile temporarily
    # -----------------------------------------------------

    context.user_data["telegram_id"] = telegram_id
    context.user_data["username"] = user.username
    context.user_data["first_name"] = user.first_name
    context.user_data["last_name"] = user.last_name

    # -----------------------------------------------------
    # Language selection
    # -----------------------------------------------------

    keyboard = []

    language_items = list(LANGUAGES.items())

    for index in range(0, len(language_items), 2):

        row = []

        for code, title in language_items[index:index + 2]:

            row.append(
                InlineKeyboardButton(
                    title,
                    callback_data=f"language:{code}",
                )
            )

        keyboard.append(row)

    await update.message.reply_text(
        "🌐 زبان خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# LANGUAGE CALLBACK
# =========================================================

async def language_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("language:"):
        return

    language = data.split(":", 1)[1]

    if language not in LANGUAGES:
        return

    context.user_data["language"] = language

    # -----------------------------------------------------
    # Unit selection
    # -----------------------------------------------------

    keyboard = [
        [
            InlineKeyboardButton(
                "📏 متریک (SI)",
                callback_data="units:SI",
            ),
            InlineKeyboardButton(
                "🇺🇸 Imperial",
                callback_data="units:Imperial",
            ),
        ]
    ]

    await query.edit_message_text(
        "📏 سیستم واحدها را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# UNIT CALLBACK
# =========================================================

async def unit_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("units:"):
        return

    unit_system = data.split(":", 1)[1]

    if unit_system not in {"SI", "Imperial"}:
        return

    context.user_data["unit_system"] = unit_system

    # -----------------------------------------------------
    # Profession selection
    # -----------------------------------------------------

    keyboard = [
        [
            InlineKeyboardButton(
                "🏗 مهندس عمران",
                callback_data="profession:civil_engineer",
            ),
            InlineKeyboardButton(
                "📐 مهندس سازه",
                callback_data="profession:structural_engineer",
            ),
        ],
        [
            InlineKeyboardButton(
                "👷 پیمانکار",
                callback_data="profession:contractor",
            ),
            InlineKeyboardButton(
                "🏢 شرکت / دفتر مهندسی",
                callback_data="profession:company",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎓 دانشجو",
                callback_data="profession:student",
            ),
            InlineKeyboardButton(
                "🔧 سایر",
                callback_data="profession:other",
            ),
        ],
    ]

    await query.edit_message_text(
        "👷 زمینه کاری خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# PROFESSION CALLBACK
# =========================================================

async def profession_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("profession:"):
        return

    profession = data.split(":", 1)[1]

    context.user_data["profession"] = profession

    # -----------------------------------------------------
    # Create user
    # -----------------------------------------------------

    create_user(
        telegram_id=context.user_data["telegram_id"],
        username=context.user_data.get("username"),
        first_name=context.user_data.get("first_name"),
        last_name=context.user_data.get("last_name"),
        language=context.user_data.get("language", "fa"),
        unit_system=context.user_data.get("unit_system", "SI"),
        profession=profession,
    )

    # -----------------------------------------------------
    # Finish onboarding
    # -----------------------------------------------------

    await query.edit_message_text(
        "🚀 آماده‌ایم شروع کنیم؟\n\n"
        "تنظیمات اولیه با موفقیت ذخیره شد."
    )

    await query.message.reply_text(
        "🏠 منوی اصلی به‌زودی فعال می‌شود."
    )
