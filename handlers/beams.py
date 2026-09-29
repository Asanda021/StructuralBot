"""
StructuralBot - Beam Handler

Telegram user interface for reinforced concrete beams.

Responsibilities:
- Beam type selection
- Geometry
- Materials
- Loads
- Longitudinal reinforcement
- Stirrups
- Critical regions
- Detailing
- Calculation routing
- Navigation

Engineering calculations belong to core/ and codes/.
"""

from __future__ import annotations

from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# ---------------------------------------------------------------------
# BEAM TYPES
# ---------------------------------------------------------------------

BEAM_TYPES = {
    "main": "تیر اصلی",
    "secondary": "تیر فرعی",
    "tie": "کلاف / تیر رابط",
}


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def _project_id(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    return context.user_data.get("project_id")


def _project_title(context: ContextTypes.DEFAULT_TYPE) -> str:
    project_id = _project_id(context)

    if project_id:
        return f"📁 پروژه: {project_id}"

    return "📁 پروژه فعلی"


# ---------------------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------------------

def get_beam_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🏗 تیر اصلی",
                callback_data="beam:type:main",
            ),
            InlineKeyboardButton(
                "🏗 تیر فرعی",
                callback_data="beam:type:secondary",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔗 کلاف / رابط",
                callback_data="beam:type:tie",
            ),
        ],
        [
            InlineKeyboardButton(
                "📐 هندسه",
                callback_data="beam:input:geometry",
            ),
            InlineKeyboardButton(
                "🧱 مصالح",
                callback_data="beam:input:materials",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚖️ بارگذاری",
                callback_data="beam:input:loads",
            ),
            InlineKeyboardButton(
                "🔩 میلگرد طولی",
                callback_data="beam:input:longitudinal",
            ),
        ],
        [
            InlineKeyboardButton(
                "〰️ خاموت",
                callback_data="beam:input:stirrups",
            ),
            InlineKeyboardButton(
                "📏 دیتیلینگ",
                callback_data="beam:input:detailing",
            ),
        ],
        [
            InlineKeyboardButton(
                "🧮 محاسبه تیر",
                callback_data="beam:calculate",
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
# GEOMETRY
# ---------------------------------------------------------------------

def get_beam_geometry_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📏 عرض b",
                callback_data="beam_input:width",
            ),
            InlineKeyboardButton(
                "📏 ارتفاع h",
                callback_data="beam_input:depth",
            ),
        ],
        [
            InlineKeyboardButton(
                "📐 طول دهانه",
                callback_data="beam_input:length",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 پوشش بتن",
                callback_data="beam_input:cover",
            ),
        ],
        [
            InlineKeyboardButton(
                "↔️ عرض مؤثر",
                callback_data="beam_input:effective_width",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="beam:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# MATERIALS
# ---------------------------------------------------------------------

def get_beam_material_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🧱 مقاومت بتن f'c",
                callback_data="beam_input:fc",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔩 گرید میلگرد",
                callback_data="beam_input:rebar_grade",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ فولاد سازه‌ای",
                callback_data="beam_input:steel_grade",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="beam:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# LOADS
# ---------------------------------------------------------------------

def get_beam_loads_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "⬇️ بار مرده",
                callback_data="beam_input:dead_load",
            ),
            InlineKeyboardButton(
                "⬆️ بار زنده",
                callback_data="beam_input:live_load",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 بار خطی",
                callback_data="beam_input:line_load",
            ),
        ],
        [
            InlineKeyboardButton(
                "↔️ لنگر طراحی",
                callback_data="beam_input:moment",
            ),
            InlineKeyboardButton(
                "↕️ برش طراحی",
                callback_data="beam_input:shear",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 ضریب بار",
                callback_data="beam_input:load_factor",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="beam:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# LONGITUDINAL REINFORCEMENT
# ---------------------------------------------------------------------

def get_beam_longitudinal_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "⬇️ میلگرد پایین",
                callback_data="beam_input:bottom_count",
            ),
            InlineKeyboardButton(
                "⬆️ میلگرد بالا",
                callback_data="beam_input:top_count",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 قطر پایین",
                callback_data="beam_input:bottom_diameter",
            ),
            InlineKeyboardButton(
                "📏 قطر بالا",
                callback_data="beam_input:top_diameter",
            ),
        ],
        [
            InlineKeyboardButton(
                "↔️ میلگرد کناری",
                callback_data="beam_input:side_rebar",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 معادل‌سازی میلگرد",
                callback_data="beam_input:equivalency",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="beam:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# STIRRUPS
# ---------------------------------------------------------------------

def get_beam_stirrups_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "〰️ قطر خاموت",
                callback_data="beam_input:stirrup_diameter",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 فاصله خاموت",
                callback_data="beam_input:stirrup_spacing",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔥 ناحیه بحرانی",
                callback_data="beam_input:critical_region",
            ),
        ],
        [
            InlineKeyboardButton(
                "📍 ناحیه میانی",
                callback_data="beam_input:middle_region",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="beam:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# DETAILING
# ---------------------------------------------------------------------

def get_beam_detailing_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📏 طول مهاری",
                callback_data="beam_input:development",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔗 طول وصله",
                callback_data="beam_input:lap",
            ),
        ],
        [
            InlineKeyboardButton(
                "🪝 قلاب / خم",
                callback_data="beam_input:hook",
            ),
        ],
        [
            InlineKeyboardButton(
                "📍 محل وصله",
                callback_data="beam_input:splice_location",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="beam:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# DISPLAY MAIN MENU
# ---------------------------------------------------------------------

async def show_beam_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "🏗 <b>طراحی و محاسبات تیر</b>\n\n"
        f"{_project_title(context)}\n\n"
        "نوع تیر را انتخاب کنید و سپس اطلاعات طراحی را وارد کنید.\n\n"
        "🔹 هندسه\n"
        "🔹 مصالح\n"
        "🔹 بارگذاری\n"
        "🔹 میلگردهای طولی\n"
        "🔹 خاموت و نواحی بحرانی\n"
        "🔹 دیتیلینگ\n\n"
        "در مرحله محاسبه، نتیجه طراحی به زنجیره "
        "Reinforcement → BBS → Cut List متصل خواهد شد."
    )

    keyboard = get_beam_menu_keyboard()

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
# TYPE SELECTION
# ---------------------------------------------------------------------

async def select_beam_type(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    beam_type: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    if beam_type not in BEAM_TYPES:
        if query:
            await query.edit_message_text(
                "❌ نوع تیر نامعتبر است."
            )
        return

    context.user_data["beam_type"] = beam_type

    text = (
        f"🏗 <b>{BEAM_TYPES[beam_type]}</b>\n\n"
        "نوع تیر ثبت شد.\n\n"
        "اکنون می‌توانید هندسه، مصالح، بارگذاری، "
        "میلگرد و دیتیلینگ را وارد کنید."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_beam_menu_keyboard(),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# SECTION ROUTER
# ---------------------------------------------------------------------

async def beam_input_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    section: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    menus = {
        "geometry": (
            "📐 <b>هندسه تیر</b>\n\n"
            "ابعاد و طول دهانه تیر را مشخص کنید.",
            get_beam_geometry_keyboard(),
        ),
        "materials": (
            "🧱 <b>مصالح تیر</b>\n\n"
            "مشخصات بتن و فولاد را تعیین کنید.",
            get_beam_material_keyboard(),
        ),
        "loads": (
            "⚖️ <b>بارگذاری تیر</b>\n\n"
            "بارها و اثرات طراحی را وارد کنید.",
            get_beam_loads_keyboard(),
        ),
        "longitudinal": (
            "🔩 <b>میلگرد طولی تیر</b>\n\n"
            "آرماتورهای بالا، پایین و کناری را تعیین کنید.",
            get_beam_longitudinal_keyboard(),
        ),
        "stirrups": (
            "〰️ <b>خاموت تیر</b>\n\n"
            "قطر، فاصله و نواحی بحرانی خاموت را تعیین کنید.",
            get_beam_stirrups_keyboard(),
        ),
        "detailing": (
            "📏 <b>دیتیلینگ تیر</b>\n\n"
            "طول مهاری، وصله، خم و محل وصله را تعیین کنید.",
            get_beam_detailing_keyboard(),
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
# INPUT LABELS
# ---------------------------------------------------------------------

INPUT_LABELS = {
    "width": "عرض تیر b",
    "depth": "ارتفاع تیر h",
    "length": "طول دهانه",
    "cover": "پوشش بتن",
    "effective_width": "عرض مؤثر",
    "fc": "مقاومت بتن f'c",
    "rebar_grade": "گرید میلگرد",
    "steel_grade": "گرید فولاد",
    "dead_load": "بار مرده",
    "live_load": "بار زنده",
    "line_load": "بار خطی",
    "moment": "لنگر طراحی",
    "shear": "برش طراحی",
    "load_factor": "ضریب بار",
    "bottom_count": "تعداد میلگرد پایین",
    "top_count": "تعداد میلگرد بالا",
    "bottom_diameter": "قطر میلگرد پایین",
    "top_diameter": "قطر میلگرد بالا",
    "side_rebar": "میلگردهای کناری",
    "equivalency": "معادل‌سازی میلگرد",
    "stirrup_diameter": "قطر خاموت",
    "stirrup_spacing": "فاصله خاموت",
    "critical_region": "ناحیه بحرانی",
    "middle_region": "ناحیه میانی",
    "development": "طول مهاری",
    "lap": "طول وصله",
    "hook": "قلاب / خم",
    "splice_location": "محل وصله",
}


# ---------------------------------------------------------------------
# PRESETS
# ---------------------------------------------------------------------

def _get_presets(field: str) -> list[str]:
    presets = {
        "width": ["250", "300", "400"],
        "depth": ["400", "500", "600"],
        "length": ["4", "5", "6"],
        "cover": ["30", "40", "50"],
        "fc": ["20", "25", "30"],
        "bottom_count": ["2", "3", "4"],
        "top_count": ["2", "3", "4"],
        "bottom_diameter": ["16", "20", "25"],
        "top_diameter": ["16", "20", "25"],
        "stirrup_diameter": ["8", "10", "12"],
        "stirrup_spacing": ["100", "150", "200"],
        "dead_load": ["5", "10", "15"],
        "live_load": ["2", "3", "5"],
        "load_factor": ["1.0", "1.2", "1.4"],
    }

    return presets.get(field, [])


# ---------------------------------------------------------------------
# INPUT REQUEST
# ---------------------------------------------------------------------

async def beam_input_request(
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

    context.user_data["beam_pending_field"] = field

    presets = _get_presets(field)

    keyboard = []

    if presets:
        keyboard.append(
            [
                InlineKeyboardButton(
                    str(value),
                    callback_data=f"beam_value:{field}:{value}",
                )
                for value in presets[:3]
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⌨️ ورود دستی",
                callback_data=f"beam_manual:{field}",
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="beam:menu",
            )
        ]
    )

    text = (
        f"✏️ <b>{label}</b>\n\n"
        "مقدار موردنظر را انتخاب کنید یا به‌صورت دستی وارد کنید.\n\n"
        "واحد مقدار مطابق سیستم واحد انتخاب‌شده پروژه خواهد بود."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# PRESET VALUE
# ---------------------------------------------------------------------

async def beam_preset_value(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    field: str,
    value: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    context.user_data[f"beam_{field}"] = value

    label = INPUT_LABELS.get(field, field)

    text = (
        f"✅ <b>{label}</b>\n\n"
        f"مقدار انتخاب‌شده: <b>{value}</b>\n\n"
        "پارامتر ثبت شد."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_beam_menu_keyboard(),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# MANUAL INPUT
# ---------------------------------------------------------------------

async def beam_manual_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    field: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    context.user_data["beam_pending_field"] = field
    context.user_data["beam_waiting_manual_input"] = True

    label = INPUT_LABELS.get(field, field)

    text = (
        f"⌨️ <b>ورود دستی — {label}</b>\n\n"
        "مقدار را در پیام بعدی ارسال کنید.\n\n"
        "مثال:\n"
        "<code>400</code>\n\n"
        "⚠️ اعتبارسنجی عدد، بازه، واحد و محدودیت‌های طراحی "
        "در لایه validation انجام می‌شود."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "❌ لغو",
                            callback_data="beam:menu",
                        )
                    ]
                ]
            ),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# RECEIVE MANUAL INPUT
# ---------------------------------------------------------------------

async def receive_beam_manual_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not context.user_data.get("beam_waiting_manual_input"):
        return

    if not update.message or not update.message.text:
        return

    field = context.user_data.get("beam_pending_field")

    if not field:
        context.user_data["beam_waiting_manual_input"] = False
        return

    value = update.message.text.strip()

    context.user_data[f"beam_{field}"] = value
    context.user_data["beam_waiting_manual_input"] = False
    context.user_data["beam_pending_field"] = None

    label = INPUT_LABELS.get(field, field)

    await update.message.reply_text(
        f"✅ {label} ثبت شد.\n\n"
        f"مقدار: <b>{value}</b>\n\n"
        "می‌توانید پارامتر بعدی را وارد کنید.",
        reply_markup=get_beam_menu_keyboard(),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------
# CALCULATE
# ---------------------------------------------------------------------

async def calculate_beam(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    beam_type = context.user_data.get(
        "beam_type",
        "main",
    )

    text = (
        "🧮 <b>محاسبه تیر</b>\n\n"
        f"نوع تیر: {BEAM_TYPES.get(beam_type, beam_type)}\n\n"
        "در نسخه نهایی موتور محاسبات این موارد را بررسی می‌کند:\n\n"
        "• خمش\n"
        "• برش\n"
        "• آرماتور حداقل و موردنیاز\n"
        "• آرماتور بالا و پایین\n"
        "• خاموت\n"
        "• نواحی بحرانی\n"
        "• طول مهاری\n"
        "• طول و محل وصله\n"
        "• دیتیلینگ\n"
        "• BBS\n"
        "• Cut List\n"
        "• وزن میلگرد\n"
        "• حجم بتن\n\n"
        "⚠️ این Handler جایگزین موتور محاسبات نیست؛ "
        "نتایج مهندسی باید از core/ و codes/ دریافت شوند."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔩 آرماتور و BBS",
                    callback_data="beam:reinforcement",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 گزارش تیر",
                    callback_data="beam:report",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="beam:menu",
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
# REINFORCEMENT
# ---------------------------------------------------------------------

async def beam_reinforcement(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "🔩 <b>آرماتورگذاری تیر</b>\n\n"
        "در مرحله اتصال موتور طراحی، مسیر زیر اجرا خواهد شد:\n\n"
        "Design Result\n"
        "↓\n"
        "Reinforcement\n"
        "↓\n"
        "Detailing\n"
        "↓\n"
        "BBS\n"
        "↓\n"
        "Cut List\n"
        "↓\n"
        "Stock Bars / Waste / Weight"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="beam:menu",
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
# REPORT
# ---------------------------------------------------------------------

async def beam_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "📊 <b>گزارش تیر</b>\n\n"
        "گزارش نهایی می‌تواند شامل موارد زیر باشد:\n\n"
        "• مشخصات پروژه و تیر\n"
        "• سیستم واحد\n"
        "• آیین‌نامه طراحی\n"
        "• ورودی‌های هندسی\n"
        "• مصالح\n"
        "• بارگذاری\n"
        "• نتایج کنترل خمش\n"
        "• نتایج کنترل برش\n"
        "• آرماتورهای طولی\n"
        "• خاموت\n"
        "• دیتیلینگ\n"
        "• BBS\n"
        "• Cut List\n"
        "• وزن میلگرد\n"
        "• حجم بتن\n\n"
        "خروجی Telegram، PDF و Excel از یک منبع داده مشترک تولید خواهد شد."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="beam:menu",
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

async def beam_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if data == "beam:menu":
        await show_beam_menu(update, context)
        return

    if data.startswith("beam:type:"):
        beam_type = data.split(":", 2)[2]

        await select_beam_type(
            update,
            context,
            beam_type,
        )
        return

    if data.startswith("beam:input:"):
        section = data.split(":", 2)[2]

        await beam_input_menu(
            update,
            context,
            section,
        )
        return

    if data.startswith("beam_input:"):
        field = data.split(":", 1)[1]

        await beam_input_request(
            update,
            context,
            field,
        )
        return

    if data.startswith("beam_value:"):
        parts = data.split(":", 2)

        if len(parts) != 3:
            await query.answer(
                "❌ مقدار نامعتبر است.",
                show_alert=True,
            )
            return

        field = parts[1]
        value = parts[2]

        await beam_preset_value(
            update,
            context,
            field,
            value,
        )
        return

    if data.startswith("beam_manual:"):
        field = data.split(":", 1)[1]

        await beam_manual_input(
            update,
            context,
            field,
        )
        return

    if data == "beam:calculate":
        await calculate_beam(
            update,
            context,
        )
        return

    if data == "beam:reinforcement":
        await beam_reinforcement(
            update,
            context,
        )
        return

    if data == "beam:report":
        await beam_report(
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

def get_beam_callback_handler():
    from telegram.ext import CallbackQueryHandler

    return CallbackQueryHandler(
        beam_callback,
        pattern=r"^beam(?::|_)",
    )


def get_beam_message_handler():
    from telegram.ext import MessageHandler, filters

    return MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_beam_manual_input,
    )


# ---------------------------------------------------------------------
# EXPORTS
# ---------------------------------------------------------------------

__all__ = [
    "BEAM_TYPES",
    "get_beam_menu_keyboard",
    "get_beam_geometry_keyboard",
    "get_beam_material_keyboard",
    "get_beam_loads_keyboard",
    "get_beam_longitudinal_keyboard",
    "get_beam_stirrups_keyboard",
    "get_beam_detailing_keyboard",
    "show_beam_menu",
    "select_beam_type",
    "beam_input_menu",
    "beam_input_request",
    "beam_preset_value",
    "beam_manual_input",
    "receive_beam_manual_input",
    "calculate_beam",
    "beam_reinforcement",
    "beam_report",
    "beam_callback",
    "get_beam_callback_handler",
    "get_beam_message_handler",
]
