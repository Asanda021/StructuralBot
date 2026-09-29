"""
StructuralBot - Reinforcement Handler

Telegram user interface for reinforcement utilities.

Responsibilities:
- Rebar diameter selection
- Rebar area / weight information
- Reinforcement equivalency
- Development/lap routing
- BBS and Cut List routing
- Project/member reinforcement navigation

Engineering calculations belong to core/ and codes/.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# ---------------------------------------------------------------------
# STANDARD DIAMETERS
# ---------------------------------------------------------------------

STANDARD_DIAMETERS = [
    8,
    10,
    12,
    14,
    16,
    18,
    20,
    22,
    25,
    28,
    32,
    36,
    40,
]


# ---------------------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------------------

def get_rebar_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📏 قطر و مشخصات میلگرد",
                callback_data="rebar:diameters",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚖️ وزن میلگرد",
                callback_data="rebar:weight",
            ),
            InlineKeyboardButton(
                "📐 سطح مقطع",
                callback_data="rebar:area",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 معادل‌سازی میلگرد",
                callback_data="rebar:equivalency",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 طول مهاری",
                callback_data="rebar:development",
            ),
            InlineKeyboardButton(
                "🔗 طول وصله",
                callback_data="rebar:lap",
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 BBS",
                callback_data="rebar:bbs",
            ),
            InlineKeyboardButton(
                "✂️ Cut List",
                callback_data="rebar:cutlist",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="nav:home",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# DIAMETERS
# ---------------------------------------------------------------------

def get_diameter_keyboard() -> InlineKeyboardMarkup:
    keyboard = []

    row = []

    for diameter in STANDARD_DIAMETERS:
        row.append(
            InlineKeyboardButton(
                f"Ø{diameter}",
                callback_data=f"rebar:diameter:{diameter}",
            )
        )

        if len(row) == 4:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="rebar:menu",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# WEIGHT / AREA INPUT
# ---------------------------------------------------------------------

def get_rebar_value_keyboard(
    operation: str,
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "Ø8",
                callback_data=f"rebar_value:{operation}:8",
            ),
            InlineKeyboardButton(
                "Ø10",
                callback_data=f"rebar_value:{operation}:10",
            ),
            InlineKeyboardButton(
                "Ø12",
                callback_data=f"rebar_value:{operation}:12",
            ),
        ],
        [
            InlineKeyboardButton(
                "Ø14",
                callback_data=f"rebar_value:{operation}:14",
            ),
            InlineKeyboardButton(
                "Ø16",
                callback_data=f"rebar_value:{operation}:16",
            ),
            InlineKeyboardButton(
                "Ø18",
                callback_data=f"rebar_value:{operation}:18",
            ),
        ],
        [
            InlineKeyboardButton(
                "Ø20",
                callback_data=f"rebar_value:{operation}:20",
            ),
            InlineKeyboardButton(
                "Ø22",
                callback_data=f"rebar_value:{operation}:22",
            ),
            InlineKeyboardButton(
                "Ø25",
                callback_data=f"rebar_value:{operation}:25",
            ),
        ],
        [
            InlineKeyboardButton(
                "Ø28",
                callback_data=f"rebar_value:{operation}:28",
            ),
            InlineKeyboardButton(
                "Ø32",
                callback_data=f"rebar_value:{operation}:32",
            ),
            InlineKeyboardButton(
                "Ø36",
                callback_data=f"rebar_value:{operation}:36",
            ),
        ],
        [
            InlineKeyboardButton(
                "Ø40",
                callback_data=f"rebar_value:{operation}:40",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="rebar:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# EQUIVALENCY MENU
# ---------------------------------------------------------------------

def get_equivalency_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "Ø8",
                callback_data="rebar_eq:source:8",
            ),
            InlineKeyboardButton(
                "Ø10",
                callback_data="rebar_eq:source:10",
            ),
            InlineKeyboardButton(
                "Ø12",
                callback_data="rebar_eq:source:12",
            ),
        ],
        [
            InlineKeyboardButton(
                "Ø14",
                callback_data="rebar_eq:source:14",
            ),
            InlineKeyboardButton(
                "Ø16",
                callback_data="rebar_eq:source:16",
            ),
            InlineKeyboardButton(
                "Ø18",
                callback_data="rebar_eq:source:18",
            ),
        ],
        [
            InlineKeyboardButton(
                "Ø20",
                callback_data="rebar_eq:source:20",
            ),
            InlineKeyboardButton(
                "Ø22",
                callback_data="rebar_eq:source:22",
            ),
            InlineKeyboardButton(
                "Ø25",
                callback_data="rebar_eq:source:25",
            ),
        ],
        [
            InlineKeyboardButton(
                "Ø28",
                callback_data="rebar_eq:source:28",
            ),
            InlineKeyboardButton(
                "Ø32",
                callback_data="rebar_eq:source:32",
            ),
            InlineKeyboardButton(
                "Ø36",
                callback_data="rebar_eq:source:36",
            ),
        ],
        [
            InlineKeyboardButton(
                "Ø40",
                callback_data="rebar_eq:source:40",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="rebar:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_equivalency_target_keyboard(
    source_diameter: int,
) -> InlineKeyboardMarkup:
    keyboard = []

    row = []

    for diameter in STANDARD_DIAMETERS:
        if diameter == source_diameter:
            continue

        row.append(
            InlineKeyboardButton(
                f"Ø{diameter}",
                callback_data=(
                    f"rebar_eq:target:"
                    f"{source_diameter}:{diameter}"
                ),
            )
        )

        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="rebar:equivalency",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# DISPLAY MAIN MENU
# ---------------------------------------------------------------------

async def show_rebar_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "🔩 <b>میلگرد و ابزارهای آرماتور</b>\n\n"
        "ابزارهای این بخش:\n\n"
        "📏 مشخصات قطرهای استاندارد\n"
        "⚖️ وزن میلگرد\n"
        "📐 سطح مقطع\n"
        "🔄 معادل‌سازی\n"
        "📏 طول مهاری\n"
        "🔗 طول وصله\n"
        "📋 BBS\n"
        "✂️ Cut List\n\n"
        "⚠️ محاسبات مهندسی وابسته به آیین‌نامه و عضو سازه‌ای "
        "باید از لایه code-specific انجام شوند."
    )

    query = update.callback_query

    if query:
        await query.answer()
        await query.edit_message_text(
            text=text,
            reply_markup=get_rebar_menu_keyboard(),
            parse_mode="HTML",
        )
        return

    if update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=get_rebar_menu_keyboard(),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# DIAMETER INFORMATION
# ---------------------------------------------------------------------

async def show_diameters(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "📏 <b>قطرهای استاندارد میلگرد</b>\n\n"
        "قطر موردنظر را انتخاب کنید."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_diameter_keyboard(),
            parse_mode="HTML",
        )


async def show_diameter_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    diameter: int,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    if diameter not in STANDARD_DIAMETERS:
        if query:
            await query.edit_message_text(
                "❌ قطر میلگرد نامعتبر است."
            )
        return

    area = 3.141592653589793 * diameter**2 / 4
    weight = area * 7850 / 1_000_000

    text = (
        f"🔩 <b>میلگرد Ø{diameter}</b>\n\n"
        f"سطح مقطع تقریبی: <b>{area:.2f} mm²</b>\n"
        f"وزن تقریبی: <b>{weight:.3f} kg/m</b>\n\n"
        "این مقادیر برای اطلاعات هندسی/وزنی هستند. "
        "ضوابط طراحی، حداقل‌ها، طول مهاری و وصله "
        "باید بر اساس آیین‌نامه انتخاب‌شده بررسی شوند."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📏 قطرهای دیگر",
                    callback_data="rebar:diameters",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="rebar:menu",
                )
            ],
        ]
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# AREA / WEIGHT
# ---------------------------------------------------------------------

async def show_area_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "📐 <b>سطح مقطع میلگرد</b>\n\n"
        "قطر موردنظر را انتخاب کنید."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_rebar_value_keyboard("area"),
            parse_mode="HTML",
        )


async def show_weight_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "⚖️ <b>وزن میلگرد</b>\n\n"
        "قطر موردنظر را انتخاب کنید."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_rebar_value_keyboard("weight"),
            parse_mode="HTML",
        )


async def show_rebar_value(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    operation: str,
    diameter: int,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    if diameter not in STANDARD_DIAMETERS:
        if query:
            await query.edit_message_text(
                "❌ قطر نامعتبر است."
            )
        return

    area = 3.141592653589793 * diameter**2 / 4
    weight = area * 7850 / 1_000_000

    if operation == "area":
        text = (
            f"📐 <b>سطح مقطع Ø{diameter}</b>\n\n"
            f"<b>{area:.2f} mm²</b>"
        )
    else:
        text = (
            f"⚖️ <b>وزن Ø{diameter}</b>\n\n"
            f"<b>{weight:.3f} kg/m</b>"
        )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 قطر دیگر",
                    callback_data=f"rebar:{operation}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="rebar:menu",
                )
            ],
        ]
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# EQUIVALENCY
# ---------------------------------------------------------------------

async def show_equivalency_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
        "ابتدا قطر میلگرد موجود را انتخاب کنید.\n\n"
        "معادل‌سازی بر اساس سطح مقطع انجام می‌شود؛ "
        "اما استفاده طراحی‌شده از نتیجه باید با کنترل "
        "حداقل/حداکثر آرماتور، فاصله، قطر مجاز و دیتیلینگ "
        "آیین‌نامه انجام شود."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_equivalency_keyboard(),
            parse_mode="HTML",
        )


async def select_equivalency_source(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    diameter: int,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    context.user_data["rebar_equivalency_source"] = diameter

    text = (
        f"🔄 <b>معادل‌سازی Ø{diameter}</b>\n\n"
        "قطر جایگزین را انتخاب کنید."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_equivalency_target_keyboard(
                diameter
            ),
            parse_mode="HTML",
        )


async def calculate_equivalency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    source: int,
    target: int,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    source_area = (
        3.141592653589793
        * source**2
        / 4
    )

    target_area = (
        3.141592653589793
        * target**2
        / 4
    )

    if target_area <= 0:
        if query:
            await query.edit_message_text(
                "❌ قطر جایگزین نامعتبر است."
            )
        return

    ratio = source_area / target_area

    text = (
        "🔄 <b>نتیجه معادل‌سازی</b>\n\n"
        f"میلگرد مبنا: <b>Ø{source}</b>\n"
        f"میلگرد جایگزین: <b>Ø{target}</b>\n\n"
        f"سطح مقطع Ø{source}: "
        f"<b>{source_area:.2f} mm²</b>\n"
        f"سطح مقطع Ø{target}: "
        f"<b>{target_area:.2f} mm²</b>\n\n"
        f"نسبت سطح مقطع هر میلگرد: <b>{ratio:.3f}</b>\n\n"
        "⚠️ این نتیجه فقط معادل‌سازی هندسی/سطح‌مقطع است. "
        "تعداد نهایی، فاصله، حداقل آرماتور، حداکثر آرماتور، "
        "قطر مجاز و دیتیلینگ باید جداگانه کنترل شوند."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 معادل‌سازی جدید",
                    callback_data="rebar:equivalency",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="rebar:menu",
                )
            ],
        ]
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# DEVELOPMENT / LAP / BBS / CUT LIST
# ---------------------------------------------------------------------

async def show_development_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "📏 <b>طول مهاری</b>\n\n"
        "طول مهاری به عضو، قطر میلگرد، مقاومت مصالح، "
        "نوع میلگرد، شرایط مهاری و آیین‌نامه انتخاب‌شده "
        "وابسته است.\n\n"
        "در نسخه نهایی مقدار آن توسط code adapter "
        "و ماژول دیتیلینگ محاسبه می‌شود.\n\n"
        "از اعمال ضریب ثابت عمومی مانند 40d بدون بررسی "
        "شرایط طراحی خودداری می‌شود."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="rebar:menu",
                )
            ]
        ]
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def show_lap_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "🔗 <b>طول وصله</b>\n\n"
        "طول وصله باید بر اساس آیین‌نامه انتخاب‌شده، "
        "نوع عضو، قطر و شرایط وصله تعیین شود.\n\n"
        "محل وصله نیز بخشی از دیتیلینگ عضو خواهد بود."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="rebar:menu",
                )
            ]
        ]
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def show_bbs_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "📋 <b>Bar Bending Schedule — BBS</b>\n\n"
        "BBS از داده واقعی آرماتور و دیتیلینگ ساخته می‌شود.\n\n"
        "زنجیره:\n"
        "Member\n"
        "↓\n"
        "Reinforcement\n"
        "↓\n"
        "Detailing\n"
        "↓\n"
        "Physical Bar Pieces\n"
        "↓\n"
        "BBS"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✂️ رفتن به Cut List",
                    callback_data="rebar:cutlist",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="rebar:menu",
                )
            ],
        ]
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def show_cutlist_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "✂️ <b>Cut List</b>\n\n"
        "Cut List قطعات واقعی BBS را دریافت کرده و آن‌ها را "
        "برای شاخه‌های استاندارد، به‌صورت بهینه گروه‌بندی می‌کند.\n\n"
        "خروجی نهایی:\n"
        "• شاخه‌های مصرفی\n"
        "• قطعات هر شاخه\n"
        "• پرت\n"
        "• باقیمانده قابل استفاده\n"
        "• وزن میلگرد\n\n"
        "طول استاندارد شاخه باید از تنظیمات/ورودی پروژه "
        "دریافت شود و نباید در محاسبات به‌صورت مخفی ثابت شود."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📋 BBS",
                    callback_data="rebar:bbs",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="rebar:menu",
                )
            ],
        ]
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# CALLBACK ROUTER
# ---------------------------------------------------------------------

async def rebar_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if data == "rebar:menu":
        await show_rebar_menu(update, context)
        return

    if data == "rebar:diameters":
        await show_diameters(update, context)
        return

    if data.startswith("rebar:diameter:"):
        diameter = int(data.split(":")[2])
        await show_diameter_info(
            update,
            context,
            diameter,
        )
        return

    if data == "rebar:area":
        await show_area_menu(update, context)
        return

    if data == "rebar:weight":
        await show_weight_menu(update, context)
        return

    if data.startswith("rebar_value:"):
        parts = data.split(":")

        if len(parts) != 3:
            await query.answer(
                "❌ داده نامعتبر است.",
                show_alert=True,
            )
            return

        operation = parts[1]
        diameter = int(parts[2])

        await show_rebar_value(
            update,
            context,
            operation,
            diameter,
        )
        return

    if data == "rebar:equivalency":
        await show_equivalency_menu(
            update,
            context,
        )
        return

    if data.startswith("rebar_eq:source:"):
        diameter = int(data.split(":")[2])

        await select_equivalency_source(
            update,
            context,
            diameter,
        )
        return

    if data.startswith("rebar_eq:target:"):
        parts = data.split(":")

        if len(parts) != 4:
            await query.answer(
                "❌ داده معادل‌سازی نامعتبر است.",
                show_alert=True,
            )
            return

        source = int(parts[2])
        target = int(parts[3])

        await calculate_equivalency(
            update,
            context,
            source,
            target,
        )
        return

    if data == "rebar:development":
        await show_development_menu(
            update,
            context,
        )
        return

    if data == "rebar:lap":
        await show_lap_menu(
            update,
            context,
        )
        return

    if data == "rebar:bbs":
        await show_bbs_menu(
            update,
            context,
        )
        return

    if data == "rebar:cutlist":
        await show_cutlist_menu(
            update,
            context,
        )
        return

    await query.answer(
        "❌ گزینه ناشناخته است.",
        show_alert=True,
    )


# ---------------------------------------------------------------------
# HANDLER FACTORY
# ---------------------------------------------------------------------

def get_rebar_callback_handler():
    from telegram.ext import CallbackQueryHandler

    return CallbackQueryHandler(
        rebar_callback,
        pattern=r"^rebar(?::|_)|^rebar_eq:",
    )


# ---------------------------------------------------------------------
# EXPORTS
# ---------------------------------------------------------------------

__all__ = [
    "STANDARD_DIAMETERS",
    "get_rebar_menu_keyboard",
    "get_diameter_keyboard",
    "get_rebar_value_keyboard",
    "get_equivalency_keyboard",
    "get_equivalency_target_keyboard",
    "show_rebar_menu",
    "show_diameters",
    "show_diameter_info",
    "show_area_menu",
    "show_weight_menu",
    "show_rebar_value",
    "show_equivalency_menu",
    "select_equivalency_source",
    "calculate_equivalency",
    "show_development_menu",
    "show_lap_menu",
    "show_bbs_menu",
    "show_cutlist_menu",
    "rebar_callback",
    "get_rebar_callback_handler",
]
