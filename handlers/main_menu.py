from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# =========================================================
# MAIN MENU
# =========================================================

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Build the main menu keyboard.
    """

    keyboard = [
        [
            InlineKeyboardButton(
                "🏗 پروژه‌های من",
                callback_data="project:list",
            ),
            InlineKeyboardButton(
                "📐 محاسبات سازه",
                callback_data="calculations:open",
            ),
        ],
        [
            InlineKeyboardButton(
                "🧮 برآورد مصالح",
                callback_data="quantity:menu",
            ),
            InlineKeyboardButton(
                "🔩 میلگرد و Cut List",
                callback_data="rebar:menu",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 معادل‌سازی میلگرد",
                callback_data="equiv:start",
            ),
            InlineKeyboardButton(
                "📊 گزارش‌ها",
                callback_data="report:menu",
            ),
        ],
        [
            InlineKeyboardButton(
                "🤖 دستیار هوشمند",
                callback_data="ai:menu",
            ),
            InlineKeyboardButton(
                "📚 ابزارهای مهندسی",
                callback_data="menu:tools",
            ),
        ],
        [
            InlineKeyboardButton(
                "👤 حساب کاربری",
                callback_data="account:menu",
            ),
            InlineKeyboardButton(
                "💳 اشتراک و اعتبار",
                callback_data="account:subscription",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ تنظیمات",
                callback_data="settings:main",
            ),
            InlineKeyboardButton(
                "❓ راهنما",
                callback_data="menu:help",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 شروع مجدد",
                callback_data="menu:restart",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# MAIN MENU MESSAGE
# =========================================================

async def show_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Display the main menu.
    """

    text = (
        "🏠 <b>منوی اصلی</b>\n\n"
        "از بخش موردنظر خود انتخاب کنید:"
    )

    if update.callback_query:

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )

    elif update.message:

        await update.message.reply_text(
            text=text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )


# =========================================================
# MAIN MENU CALLBACK
# =========================================================

async def main_menu_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle main menu selections.

    Individual modules will be connected here as they are
    implemented.
    """

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("menu:"):
        return

    action = data.split(":", 1)[1]

    # -----------------------------------------------------
    # PROJECTS
    # -----------------------------------------------------

    if action == "projects":
        await query.edit_message_text(
            "🏗 <b>پروژه‌های من</b>\n\n"
            "ماژول پروژه‌ها در حال اتصال است.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # CALCULATIONS
    # -----------------------------------------------------

    if action == "calculations":
        await query.edit_message_text(
            "📐 <b>محاسبات سازه</b>\n\n"
            "نوع سازه را انتخاب کنید.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏢 سازه بتنی",
                            callback_data="calc:concrete",
                        ),
                        InlineKeyboardButton(
                            "🏗 سازه فلزی",
                            callback_data="calc:steel",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🔀 سازه ترکیبی",
                            callback_data="calc:composite",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ بازگشت",
                            callback_data="navigation:main",
                        ),
                    ],
                ]
            ),
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # QUANTITIES
    # -----------------------------------------------------

    if action == "quantities":
        await query.edit_message_text(
            "🧮 <b>برآورد مصالح</b>\n\n"
            "ماژول برآورد مصالح در حال اتصال است.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # REBAR
    # -----------------------------------------------------

    if action == "rebar":
        await query.edit_message_text(
            "🔩 <b>میلگرد و Cut List</b>\n\n"
            "ماژول میلگرد و Cut List در حال اتصال است.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # REBAR EQUIVALENCY
    # -----------------------------------------------------

    if action == "equivalency":
        await query.edit_message_text(
            "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
            "تعداد و قطر میلگرد موجود را وارد کنید؛"
            "\n"
            "سپس قطر میلگرد جایگزین را انتخاب کنید."
            "\n\n"
            "تعداد میلگرد جایگزین بر اساس ضوابط "
            "آیین‌نامه محاسبه خواهد شد.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Ø8",
                            callback_data="equiv_diameter:8",
                        ),
                        InlineKeyboardButton(
                            "Ø10",
                            callback_data="equiv_diameter:10",
                        ),
                        InlineKeyboardButton(
                            "Ø12",
                            callback_data="equiv_diameter:12",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "Ø14",
                            callback_data="equiv_diameter:14",
                        ),
                        InlineKeyboardButton(
                            "Ø16",
                            callback_data="equiv_diameter:16",
                        ),
                        InlineKeyboardButton(
                            "Ø18",
                            callback_data="equiv_diameter:18",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "Ø20",
                            callback_data="equiv_diameter:20",
                        ),
                        InlineKeyboardButton(
                            "Ø22",
                            callback_data="equiv_diameter:22",
                        ),
                        InlineKeyboardButton(
                            "Ø25",
                            callback_data="equiv_diameter:25",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "Ø28",
                            callback_data="equiv_diameter:28",
                        ),
                        InlineKeyboardButton(
                            "Ø32",
                            callback_data="equiv_diameter:32",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ بازگشت",
                            callback_data="navigation:main",
                        ),
                    ],
                ]
            ),
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # REPORTS
    # -----------------------------------------------------

    if action == "reports":
        await query.edit_message_text(
            "📊 <b>گزارش‌ها</b>\n\n"
            "ماژول گزارش‌ها در حال اتصال است.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # AI
    # -----------------------------------------------------

    if action == "ai":
        await query.edit_message_text(
            "🤖 <b>دستیار هوشمند</b>\n\n"
            "ماژول هوش مصنوعی در حال اتصال است.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # ENGINEERING TOOLS
    # -----------------------------------------------------

    if action == "tools":
        await query.edit_message_text(
            "📚 <b>ابزارهای مهندسی</b>\n\n"
            "ابزارهای مهندسی در حال اتصال هستند.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # ACCOUNT
    # -----------------------------------------------------

    if action == "account":
        await query.edit_message_text(
            "👤 <b>حساب کاربری</b>\n\n"
            "بخش حساب کاربری در حال اتصال است.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # SUBSCRIPTION
    # -----------------------------------------------------

    if action == "subscription":
        await query.edit_message_text(
            "💳 <b>اشتراک و اعتبار</b>\n\n"
            "بخش اشتراک و اعتبار در حال اتصال است.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    if action == "settings":
        await query.edit_message_text(
            "⚙️ <b>تنظیمات</b>\n\n"
            "تنظیمات در حال اتصال است.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # HELP
    # -----------------------------------------------------

    if action == "help":
        await query.edit_message_text(
            "❓ <b>راهنما</b>\n\n"
            "راهنمای StructuralBot در حال آماده‌سازی است.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # RESTART
    # -----------------------------------------------------

    if action == "restart:confirm":
        language = context.user_data.get("language")
        unit_system = context.user_data.get("unit_system")
        context.user_data.clear()
        if language:
            context.user_data["language"] = language
        if unit_system:
            context.user_data["unit_system"] = unit_system
        await show_main_menu(update, context)
        return

    if action == "restart":

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ تأیید شروع مجدد",
                    callback_data="restart:confirm",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌ انصراف",
                    callback_data="navigation:main",
                ),
            ],
        ]

        await query.edit_message_text(
            "⚠️ <b>شروع مجدد</b>\n\n"
            "فرآیند جاری از ابتدا شروع می‌شود.\n"
            "پروژه‌های ذخیره‌شده حذف نخواهند شد.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return


# =========================================================
# NAVIGATION CALLBACK
# =========================================================

async def navigation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle general navigation actions.
    """

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if data == "navigation:main":
        await show_main_menu(update, context)
