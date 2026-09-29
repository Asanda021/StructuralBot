"""
StructuralBot - Column Handler

User-facing Telegram handler for reinforced concrete columns.

This module is intentionally separated from the calculation engine.
It is responsible for:
- Column type selection
- Geometry input navigation
- Material input navigation
- Reinforcement input navigation
- Load input navigation
- Detailing navigation
- Calculation routing
- Navigation/back handling

Engineering calculations must be performed by the core/code layers.
"""

from __future__ import annotations

from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# ---------------------------------------------------------------------
# COLUMN TYPES
# ---------------------------------------------------------------------

COLUMN_TYPES = {
    "rectangular": "مستطیلی",
    "circular": "دایره‌ای",
}


# ---------------------------------------------------------------------
# TEXT HELPERS
# ---------------------------------------------------------------------

def _project_title(project_id: Optional[str]) -> str:
    if project_id:
        return f"📁 پروژه: {project_id}"
    return "📁 پروژه فعلی"


def _safe_project_id(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    return context.user_data.get("project_id")


# ---------------------------------------------------------------------
# MAIN COLUMN MENU
# ---------------------------------------------------------------------

def get_column_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "▣ ستون مستطیلی",
                callback_data="column:type:rectangular",
            ),
            InlineKeyboardButton(
                "◯ ستون دایره‌ای",
                callback_data="column:type:circular",
            ),
        ],
        [
            InlineKeyboardButton(
                "📐 هندسه",
                callback_data="column:input:geometry",
            ),
            InlineKeyboardButton(
                "🧱 مصالح",
                callback_data="column:input:materials",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔩 میلگرد طولی",
                callback_data="column:input:longitudinal",
            ),
            InlineKeyboardButton(
                "〰️ خاموت",
                callback_data="column:input:ties",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚖️ بارگذاری",
                callback_data="column:input:loads",
            ),
            InlineKeyboardButton(
                "📏 دیتیلینگ",
                callback_data="column:input:detailing",
            ),
        ],
        [
            InlineKeyboardButton(
                "🧮 محاسبه ستون",
                callback_data="column:calculate",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="calc:concrete",
            ),
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="nav:home",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# INPUT MENUS
# ---------------------------------------------------------------------

def get_column_geometry_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📏 عرض b",
                callback_data="column_input:width",
            ),
            InlineKeyboardButton(
                "📏 عمق h",
                callback_data="column_input:depth",
            ),
        ],
        [
            InlineKeyboardButton(
                "⭕ قطر ستون",
                callback_data="column_input:diameter",
            ),
        ],
        [
            InlineKeyboardButton(
                "📐 ارتفاع ستون",
                callback_data="column_input:height",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 پوشش بتن",
                callback_data="column_input:cover",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="column:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_column_material_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🧱 مقاومت بتن f'c",
                callback_data="column_input:fc",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔩 نوع میلگرد",
                callback_data="column_input:rebar_grade",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ فولاد سازه‌ای",
                callback_data="column_input:steel_grade",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="column:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_column_longitudinal_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🔩 تعداد میلگرد",
                callback_data="column_input:longitudinal_count",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 قطر میلگرد",
                callback_data="column_input:longitudinal_diameter",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 معادل‌سازی میلگرد",
                callback_data="column_input:equivalency",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="column:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_column_ties_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "〰️ قطر خاموت",
                callback_data="column_input:tie_diameter",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 فاصله خاموت",
                callback_data="column_input:tie_spacing",
            ),
        ],
        [
            InlineKeyboardButton(
                "📐 ناحیه بحرانی",
                callback_data="column_input:critical_region",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="column:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_column_loads_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "⬇️ نیروی محوری N",
                callback_data="column_input:axial_load",
            ),
        ],
        [
            InlineKeyboardButton(
                "↔️ لنگر Mx",
                callback_data="column_input:moment_x",
            ),
            InlineKeyboardButton(
                "↕️ لنگر My",
                callback_data="column_input:moment_y",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 ضریب بار",
                callback_data="column_input:load_factor",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="column:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_column_detailing_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📏 طول مهاری",
                callback_data="column_input:development",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔗 طول وصله",
                callback_data="column_input:lap",
            ),
        ],
        [
            InlineKeyboardButton(
                "📐 ناحیه ویژه",
                callback_data="column_input:special_region",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="column:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# DISPLAY FUNCTIONS
# ---------------------------------------------------------------------

async def show_column_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    project_id = _safe_project_id(context)

    text = (
        "🏛 <b>طراحی و محاسبات ستون</b>\n\n"
        f"{_project_title(project_id)}\n\n"
        "نوع ستون را انتخاب کنید و سپس اطلاعات موردنیاز را وارد کنید.\n\n"
        "🔹 هندسه\n"
        "🔹 مصالح\n"
        "🔹 میلگرد طولی\n"
        "🔹 خاموت و نواحی بحرانی\n"
        "🔹 بارگذاری\n"
        "🔹 دیتیلینگ\n\n"
        "⚠️ محاسبات نهایی بر اساس سیستم واحد و آیین‌نامه انتخاب‌شده "
        "انجام خواهد شد."
    )

    keyboard = get_column_menu_keyboard()

    query = update.callback_query

    if query:
        await query.answer()
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    if update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# COLUMN TYPE
# ---------------------------------------------------------------------

async def select_column_type(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    column_type: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    if column_type not in COLUMN_TYPES:
        if query:
            await query.edit_message_text(
                "❌ نوع ستون نامعتبر است."
            )
        return

    context.user_data["column_type"] = column_type

    title = COLUMN_TYPES[column_type]

    if column_type == "rectangular":
        geometry_text = (
            "📐 ستون مستطیلی انتخاب شد.\n\n"
            "پارامترهای اصلی:\n"
            "• عرض b\n"
            "• عمق h\n"
            "• ارتفاع ستون\n"
            "• پوشش بتن"
        )
    else:
        geometry_text = (
            "⭕ ستون دایره‌ای انتخاب شد.\n\n"
            "پارامترهای اصلی:\n"
            "• قطر ستون\n"
            "• ارتفاع ستون\n"
            "• پوشش بتن"
        )

    text = (
        f"🏛 <b>{title}</b>\n\n"
        f"{geometry_text}\n\n"
        "از منوی زیر بخش موردنظر را انتخاب کنید."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_column_menu_keyboard(),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# INPUT MENU ROUTER
# ---------------------------------------------------------------------

async def column_input_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    section: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    menus = {
        "geometry": (
            "📐 <b>هندسه ستون</b>\n\n"
            "پارامتر هندسی موردنظر را انتخاب کنید.",
            get_column_geometry_keyboard(),
        ),
        "materials": (
            "🧱 <b>مصالح ستون</b>\n\n"
            "مقاومت بتن و مشخصات مصالح را تعیین کنید.",
            get_column_material_keyboard(),
        ),
        "longitudinal": (
            "🔩 <b>میلگردهای طولی</b>\n\n"
            "تعداد و قطر میلگردهای طولی را مشخص کنید.",
            get_column_longitudinal_keyboard(),
        ),
        "ties": (
            "〰️ <b>خاموت ستون</b>\n\n"
            "قطر، فاصله و نواحی بحرانی خاموت را مشخص کنید.",
            get_column_ties_keyboard(),
        ),
        "loads": (
            "⚖️ <b>بارگذاری ستون</b>\n\n"
            "نیروی محوری و لنگرهای طراحی را وارد کنید.",
            get_column_loads_keyboard(),
        ),
        "detailing": (
            "📏 <b>دیتیلینگ ستون</b>\n\n"
            "پارامترهای مهاری، وصله و نواحی ویژه را مشخص کنید.",
            get_column_detailing_keyboard(),
        ),
    }

    if section not in menus:
        if query:
            await query.edit_message_text(
                "❌ بخش انتخاب‌شده معتبر نیست."
            )
        return

    text, keyboard = menus[section]

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# INPUT PLACEHOLDER
# ---------------------------------------------------------------------

INPUT_LABELS = {
    "width": "عرض ستون b",
    "depth": "عمق ستون h",
    "diameter": "قطر ستون",
    "height": "ارتفاع ستون",
    "cover": "پوشش بتن",
    "fc": "مقاومت بتن f'c",
    "rebar_grade": "گرید میلگرد",
    "steel_grade": "گرید فولاد",
    "longitudinal_count": "تعداد میلگرد طولی",
    "longitudinal_diameter": "قطر میلگرد طولی",
    "equivalency": "معادل‌سازی میلگرد",
    "tie_diameter": "قطر خاموت",
    "tie_spacing": "فاصله خاموت",
    "critical_region": "ناحیه بحرانی",
    "axial_load": "نیروی محوری",
    "moment_x": "لنگر Mx",
    "moment_y": "لنگر My",
    "load_factor": "ضریب بار",
    "development": "طول مهاری",
    "lap": "طول وصله",
    "special_region": "ناحیه ویژه",
}


async def column_input_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    field: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    label = INPUT_LABELS.get(field)

    if not label:
        if query:
            await query.edit_message_text(
                "❌ پارامتر نامعتبر است."
            )
        return

    context.user_data["column_pending_field"] = field

    # These are deliberately input placeholders.
    # Real numeric validation and engineering logic belong to core/validation.py
    # and the relevant design-code modules.

    presets = _get_presets(field)

    keyboard = []

    if presets:
        row = []
        for value in presets[:3]:
            row.append(
                InlineKeyboardButton(
                    str(value),
                    callback_data=f"column_value:{field}:{value}",
                )
            )
        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "⌨️ ورود دستی",
                callback_data=f"column_manual:{field}",
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="column:menu",
            )
        ]
    )

    text = (
        f"✏️ <b>{label}</b>\n\n"
        "مقدار موردنظر را انتخاب کنید یا به‌صورت دستی وارد کنید.\n\n"
        "واحد ورودی مطابق سیستم واحد انتخاب‌شده پروژه خواهد بود."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )


def _get_presets(field: str) -> list[str]:
    presets = {
        "width": ["300", "400", "500"],
        "depth": ["300", "400", "500"],
        "diameter": ["400", "500", "600"],
        "height": ["3", "3.5", "4"],
        "cover": ["40", "50", "60"],
        "fc": ["20", "25", "30"],
        "longitudinal_count": ["4", "6", "8"],
        "longitudinal_diameter": ["16", "20", "25"],
        "tie_diameter": ["8", "10", "12"],
        "tie_spacing": ["100", "150", "200"],
        "axial_load": ["500", "1000", "1500"],
        "moment_x": ["0", "50", "100"],
        "moment_y": ["0", "50", "100"],
        "load_factor": ["1.0", "1.2", "1.4"],
    }

    return presets.get(field, [])


# ---------------------------------------------------------------------
# PRESET VALUE
# ---------------------------------------------------------------------

async def column_preset_value(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    field: str,
    value: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    context.user_data[f"column_{field}"] = value

    label = INPUT_LABELS.get(field, field)

    text = (
        f"✅ <b>{label}</b>\n\n"
        f"مقدار انتخاب‌شده: <b>{value}</b>\n\n"
        "برای ادامه، بخش دیگری را انتخاب کنید."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_column_menu_keyboard(),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# MANUAL INPUT
# ---------------------------------------------------------------------

async def column_manual_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    field: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    context.user_data["column_pending_field"] = field
    context.user_data["column_waiting_manual_input"] = True

    label = INPUT_LABELS.get(field, field)

    text = (
        f"⌨️ <b>ورود دستی — {label}</b>\n\n"
        "مقدار را در پیام بعدی ارسال کنید.\n\n"
        "مثال:\n"
        "<code>400</code>\n\n"
        "⚠️ کنترل بازه، واحد و اعتبار مهندسی مقدار "
        "در مرحله اعتبارسنجی انجام می‌شود."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "❌ لغو",
                            callback_data="column:menu",
                        )
                    ]
                ]
            ),
            parse_mode="HTML",
        )


async def receive_column_manual_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not context.user_data.get("column_waiting_manual_input"):
        return

    if not update.message or not update.message.text:
        return

    field = context.user_data.get("column_pending_field")

    if not field:
        context.user_data["column_waiting_manual_input"] = False
        return

    value = update.message.text.strip()

    context.user_data[f"column_{field}"] = value
    context.user_data["column_waiting_manual_input"] = False
    context.user_data["column_pending_field"] = None

    label = INPUT_LABELS.get(field, field)

    await update.message.reply_text(
        f"✅ {label} ثبت شد.\n\n"
        f"مقدار: <b>{value}</b>\n\n"
        "می‌توانید پارامتر بعدی را وارد کنید.",
        reply_markup=get_column_menu_keyboard(),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------
# CALCULATION
# ---------------------------------------------------------------------

async def calculate_column(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    column_type = context.user_data.get(
        "column_type",
        "rectangular",
    )

    text = (
        "🧮 <b>محاسبه ستون</b>\n\n"
        f"نوع ستون: {COLUMN_TYPES.get(column_type, column_type)}\n\n"
        "⏳ اطلاعات ورودی جمع‌آوری شد.\n\n"
        "در نسخه نهایی این مرحله به موتور محاسبات متصل می‌شود و "
        "موارد زیر را بررسی خواهد کرد:\n\n"
        "• ظرفیت فشاری/کششی\n"
        "• اثر لنگر و اندرکنش N-M\n"
        "• درصد آرماتور طولی\n"
        "• خاموت و محدودیت فاصله\n"
        "• نواحی بحرانی\n"
        "• طول مهاری و وصله\n"
        "• دیتیلینگ\n"
        "• BBS\n"
        "• Cut List\n"
        "• وزن میلگرد\n"
        "• حجم بتن\n\n"
        "⚠️ موتور واقعی محاسبات از core/ و codes/ استفاده خواهد کرد؛ "
        "این Handler صرفاً لایه رابط کاربر است."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔩 میلگرد و BBS",
                    callback_data="column:reinforcement",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 نتیجه و گزارش",
                    callback_data="column:report",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="column:menu",
                ),
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
# POST-CALCULATION ROUTES
# ---------------------------------------------------------------------

async def column_reinforcement(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "🔩 <b>آرماتورگذاری ستون</b>\n\n"
        "این بخش در مرحله اتصال موتور طراحی، "
        "Reinforcement → BBS → Cut List فعال خواهد شد.\n\n"
        "ساختار داده ستون برای این زنجیره آماده خواهد بود."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="column:menu",
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


async def column_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "📊 <b>گزارش ستون</b>\n\n"
        "پس از اتصال موتور محاسبات، گزارش شامل موارد زیر خواهد بود:\n\n"
        "• مشخصات ستون\n"
        "• ورودی‌های طراحی\n"
        "• نتایج کنترل‌ها\n"
        "• آرماتور طولی\n"
        "• خاموت\n"
        "• طول‌های مهاری و وصله\n"
        "• BBS\n"
        "• Cut List\n"
        "• وزن میلگرد\n"
        "• حجم بتن\n\n"
        "خروجی نهایی از منبع داده مشترک برای Telegram، PDF و Excel تولید می‌شود."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="column:menu",
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


# ---------------------------------------------------------------------
# CALLBACK ROUTER
# ---------------------------------------------------------------------

async def column_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if data == "column:menu":
        await show_column_menu(update, context)
        return

    if data.startswith("column:type:"):
        column_type = data.split(":", 2)[2]
        await select_column_type(
            update,
            context,
            column_type,
        )
        return

    if data.startswith("column:input:"):
        section = data.split(":", 2)[2]
        await column_input_menu(
            update,
            context,
            section,
        )
        return

    if data.startswith("column_input:"):
        field = data.split(":", 1)[1]
        await column_input_request(
            update,
            context,
            field,
        )
        return

    if data.startswith("column_value:"):
        parts = data.split(":", 2)

        if len(parts) != 3:
            await query.answer(
                "❌ مقدار نامعتبر است.",
                show_alert=True,
            )
            return

        field = parts[1]
        value = parts[2]

        await column_preset_value(
            update,
            context,
            field,
            value,
        )
        return

    if data.startswith("column_manual:"):
        field = data.split(":", 1)[1]

        await column_manual_input(
            update,
            context,
            field,
        )
        return

    if data == "column:calculate":
        await calculate_column(
            update,
            context,
        )
        return

    if data == "column:reinforcement":
        await column_reinforcement(
            update,
            context,
        )
        return

    if data == "column:report":
        await column_report(
            update,
            context,
        )
        return

    await query.answer(
        "❌ گزینه ناشناخته است.",
        show_alert=True,
    )


# ---------------------------------------------------------------------
# HANDLER FACTORIES
# ---------------------------------------------------------------------

def get_column_callback_handler():
    """
    Returns the callback handler object.

    Import telegram.ext.CallbackQueryHandler lazily so this module
    remains easy to import and test.
    """
    from telegram.ext import CallbackQueryHandler

    return CallbackQueryHandler(
        column_callback,
        pattern=r"^column(?::|_)",
    )


def get_column_message_handler():
    """
    Returns the message handler used for manual column input.
    """
    from telegram.ext import MessageHandler, filters

    return MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_column_manual_input,
    )


__all__ = [
    "COLUMN_TYPES",
    "get_column_menu_keyboard",
    "get_column_geometry_keyboard",
    "get_column_material_keyboard",
    "get_column_longitudinal_keyboard",
    "get_column_ties_keyboard",
    "get_column_loads_keyboard",
    "get_column_detailing_keyboard",
    "show_column_menu",
    "select_column_type",
    "column_input_menu",
    "column_input_request",
    "column_preset_value",
    "column_manual_input",
    "receive_column_manual_input",
    "calculate_column",
    "column_reinforcement",
    "column_report",
    "column_callback",
    "get_column_callback_handler",
    "get_column_message_handler",
]
