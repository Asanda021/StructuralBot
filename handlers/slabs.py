"""
StructuralBot - Slab Handler

Telegram user interface for reinforced concrete slabs and roof slabs.

Responsibilities:
- Slab type selection
- Geometry
- Materials
- Loads
- Reinforcement
- Detailing
- Critical/support regions
- Calculation routing
- BBS / Cut List routing
- Navigation

Engineering calculations belong to core/ and codes/.
"""

from __future__ import annotations

from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# ---------------------------------------------------------------------
# SLAB TYPES
# ---------------------------------------------------------------------

SLAB_TYPES = {
    "one_way": "دال یک‌طرفه",
    "two_way": "دال دوطرفه",
    "flat": "دال تخت",
    "roof": "سقف / دال بام",
}


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def _project_id(
    context: ContextTypes.DEFAULT_TYPE,
) -> Optional[str]:
    return context.user_data.get("project_id")


def _project_title(
    context: ContextTypes.DEFAULT_TYPE,
) -> str:
    project_id = _project_id(context)

    if project_id:
        return f"📁 پروژه: {project_id}"

    return "📁 پروژه فعلی"


# ---------------------------------------------------------------------
# MAIN SLAB MENU
# ---------------------------------------------------------------------

def get_slab_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "↔️ یک‌طرفه",
                callback_data="slab:type:one_way",
            ),
            InlineKeyboardButton(
                "↔️↕️ دوطرفه",
                callback_data="slab:type:two_way",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬜ دال تخت",
                callback_data="slab:type:flat",
            ),
            InlineKeyboardButton(
                "🏠 سقف / بام",
                callback_data="slab:type:roof",
            ),
        ],
        [
            InlineKeyboardButton(
                "📐 هندسه",
                callback_data="slab:input:geometry",
            ),
            InlineKeyboardButton(
                "🧱 مصالح",
                callback_data="slab:input:materials",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚖️ بارگذاری",
                callback_data="slab:input:loads",
            ),
            InlineKeyboardButton(
                "🔩 آرماتور",
                callback_data="slab:input:reinforcement",
            ),
        ],
        [
            InlineKeyboardButton(
                "📍 نواحی بحرانی",
                callback_data="slab:input:regions",
            ),
            InlineKeyboardButton(
                "📏 دیتیلینگ",
                callback_data="slab:input:detailing",
            ),
        ],
        [
            InlineKeyboardButton(
                "🧮 محاسبه دال / سقف",
                callback_data="slab:calculate",
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
# GEOMETRY MENU
# ---------------------------------------------------------------------

def get_slab_geometry_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📏 ضخامت h",
                callback_data="slab_input:thickness",
            ),
        ],
        [
            InlineKeyboardButton(
                "↔️ طول",
                callback_data="slab_input:length",
            ),
            InlineKeyboardButton(
                "↕️ عرض",
                callback_data="slab_input:width",
            ),
        ],
        [
            InlineKeyboardButton(
                "📐 دهانه کوتاه",
                callback_data="slab_input:short_span",
            ),
            InlineKeyboardButton(
                "📐 دهانه بلند",
                callback_data="slab_input:long_span",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 پوشش بتن",
                callback_data="slab_input:cover",
            ),
        ],
        [
            InlineKeyboardButton(
                "🏗 نوع تکیه‌گاه",
                callback_data="slab_input:support",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="slab:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# MATERIALS MENU
# ---------------------------------------------------------------------

def get_slab_material_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🧱 مقاومت بتن f'c",
                callback_data="slab_input:fc",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔩 گرید میلگرد",
                callback_data="slab_input:rebar_grade",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="slab:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# LOAD MENU
# ---------------------------------------------------------------------

def get_slab_loads_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "⬇️ بار مرده",
                callback_data="slab_input:dead_load",
            ),
            InlineKeyboardButton(
                "⬆️ بار زنده",
                callback_data="slab_input:live_load",
            ),
        ],
        [
            InlineKeyboardButton(
                "🧱 بار کف‌سازی",
                callback_data="slab_input:finish_load",
            ),
            InlineKeyboardButton(
                "⬇️ بار تیغه",
                callback_data="slab_input:partition_load",
            ),
        ],
        [
            InlineKeyboardButton(
                "🌧 بار بام",
                callback_data="slab_input:roof_load",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 ضریب بار",
                callback_data="slab_input:load_factor",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="slab:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# REINFORCEMENT MENU
# ---------------------------------------------------------------------

def get_slab_reinforcement_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "⬇️ آرماتور پایین X",
                callback_data="slab_input:bottom_x",
            ),
            InlineKeyboardButton(
                "⬇️ آرماتور پایین Y",
                callback_data="slab_input:bottom_y",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬆️ آرماتور بالا X",
                callback_data="slab_input:top_x",
            ),
            InlineKeyboardButton(
                "⬆️ آرماتور بالا Y",
                callback_data="slab_input:top_y",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 قطر آرماتور",
                callback_data="slab_input:rebar_diameter",
            ),
        ],
        [
            InlineKeyboardButton(
                "↔️ فاصله آرماتورها",
                callback_data="slab_input:rebar_spacing",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 معادل‌سازی میلگرد",
                callback_data="slab_input:equivalency",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="slab:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# CRITICAL / SUPPORT REGIONS
# ---------------------------------------------------------------------

def get_slab_regions_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📍 ناحیه تکیه‌گاه",
                callback_data="slab_input:support_region",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎯 ناحیه وسط دهانه",
                callback_data="slab_input:span_region",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔥 ناحیه بحرانی",
                callback_data="slab_input:critical_region",
            ),
        ],
        [
            InlineKeyboardButton(
                "📏 طول ناحیه",
                callback_data="slab_input:region_length",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="slab:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# DETAILING MENU
# ---------------------------------------------------------------------

def get_slab_detailing_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📏 طول مهاری",
                callback_data="slab_input:development",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔗 طول وصله",
                callback_data="slab_input:lap",
            ),
        ],
        [
            InlineKeyboardButton(
                "🪝 خم / قلاب",
                callback_data="slab_input:hook",
            ),
        ],
        [
            InlineKeyboardButton(
                "📍 محل وصله",
                callback_data="slab_input:splice_location",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="slab:menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------
# DISPLAY MAIN MENU
# ---------------------------------------------------------------------

async def show_slab_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "🏠 <b>طراحی و محاسبات دال / سقف</b>\n\n"
        f"{_project_title(context)}\n\n"
        "نوع دال یا سقف را انتخاب کنید.\n\n"
        "🔹 یک‌طرفه\n"
        "🔹 دوطرفه\n"
        "🔹 دال تخت\n"
        "🔹 سقف / بام\n\n"
        "سپس هندسه، مصالح، بارگذاری، آرماتور و دیتیلینگ "
        "قابل تنظیم است.\n\n"
        "زنجیره خروجی:\n"
        "Design → Reinforcement → BBS → Cut List → Quantities"
    )

    keyboard = get_slab_menu_keyboard()

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
# SLAB TYPE
# ---------------------------------------------------------------------

async def select_slab_type(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    slab_type: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    if slab_type not in SLAB_TYPES:
        if query:
            await query.edit_message_text(
                "❌ نوع دال / سقف نامعتبر است."
            )
        return

    context.user_data["slab_type"] = slab_type

    text = (
        f"✅ <b>{SLAB_TYPES[slab_type]}</b>\n\n"
        "نوع سیستم سقف ثبت شد.\n\n"
        "اکنون می‌توانید پارامترهای هندسی، مصالح، بارگذاری "
        "و آرماتورگذاری را تعیین کنید."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_slab_menu_keyboard(),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# SECTION MENU ROUTER
# ---------------------------------------------------------------------

async def slab_input_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    section: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    menus = {
        "geometry": (
            "📐 <b>هندسه دال / سقف</b>\n\n"
            "ضخامت، ابعاد، دهانه‌ها و تکیه‌گاه را مشخص کنید.",
            get_slab_geometry_keyboard(),
        ),
        "materials": (
            "🧱 <b>مصالح</b>\n\n"
            "مقاومت بتن و مشخصات میلگرد را تعیین کنید.",
            get_slab_material_keyboard(),
        ),
        "loads": (
            "⚖️ <b>بارگذاری</b>\n\n"
            "بارهای مرده، زنده، کف‌سازی، تیغه و بام را مشخص کنید.",
            get_slab_loads_keyboard(),
        ),
        "reinforcement": (
            "🔩 <b>آرماتورگذاری</b>\n\n"
            "آرماتورهای X و Y، بالا و پایین و فاصله آن‌ها را تعیین کنید.",
            get_slab_reinforcement_keyboard(),
        ),
        "regions": (
            "📍 <b>نواحی طراحی</b>\n\n"
            "نواحی تکیه‌گاه، دهانه و بحرانی را مشخص کنید.",
            get_slab_regions_keyboard(),
        ),
        "detailing": (
            "📏 <b>دیتیلینگ</b>\n\n"
            "طول مهاری، وصله و خم آرماتورها را تعیین کنید.",
            get_slab_detailing_keyboard(),
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
    "thickness": "ضخامت دال",
    "length": "طول دال",
    "width": "عرض دال",
    "short_span": "دهانه کوتاه",
    "long_span": "دهانه بلند",
    "cover": "پوشش بتن",
    "support": "نوع تکیه‌گاه",
    "fc": "مقاومت بتن f'c",
    "rebar_grade": "گرید میلگرد",
    "dead_load": "بار مرده",
    "live_load": "بار زنده",
    "finish_load": "بار کف‌سازی",
    "partition_load": "بار تیغه",
    "roof_load": "بار بام",
    "load_factor": "ضریب بار",
    "bottom_x": "آرماتور پایین X",
    "bottom_y": "آرماتور پایین Y",
    "top_x": "آرماتور بالا X",
    "top_y": "آرماتور بالا Y",
    "rebar_diameter": "قطر آرماتور",
    "rebar_spacing": "فاصله آرماتورها",
    "equivalency": "معادل‌سازی میلگرد",
    "support_region": "ناحیه تکیه‌گاه",
    "span_region": "ناحیه وسط دهانه",
    "critical_region": "ناحیه بحرانی",
    "region_length": "طول ناحیه",
    "development": "طول مهاری",
    "lap": "طول وصله",
    "hook": "خم / قلاب",
    "splice_location": "محل وصله",
}


# ---------------------------------------------------------------------
# PRESETS
# ---------------------------------------------------------------------

def _get_presets(field: str) -> list[str]:
    presets = {
        "thickness": ["120", "150", "200"],
        "length": ["4", "5", "6"],
        "width": ["3", "4", "5"],
        "short_span": ["3", "4", "5"],
        "long_span": ["4", "5", "6"],
        "cover": ["20", "25", "30"],
        "fc": ["20", "25", "30"],
        "dead_load": ["3", "5", "7"],
        "live_load": ["2", "3", "5"],
        "finish_load": ["1", "1.5", "2"],
        "partition_load": ["0", "1", "2"],
        "roof_load": ["0", "1", "2"],
        "load_factor": ["1.0", "1.2", "1.4"],
        "rebar_diameter": ["8", "10", "12"],
        "rebar_spacing": ["100", "150", "200"],
    }

    return presets.get(field, [])


# ---------------------------------------------------------------------
# INPUT REQUEST
# ---------------------------------------------------------------------

async def slab_input_request(
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

    context.user_data["slab_pending_field"] = field

    presets = _get_presets(field)

    keyboard = []

    if presets:
        keyboard.append(
            [
                InlineKeyboardButton(
                    str(value),
                    callback_data=f"slab_value:{field}:{value}",
                )
                for value in presets[:3]
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⌨️ ورود دستی",
                callback_data=f"slab_manual:{field}",
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="slab:menu",
            )
        ]
    )

    text = (
        f"✏️ <b>{label}</b>\n\n"
        "مقدار را انتخاب کنید یا به‌صورت دستی وارد کنید.\n\n"
        "واحد مطابق سیستم واحد انتخاب‌شده پروژه خواهد بود."
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

async def slab_preset_value(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    field: str,
    value: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    context.user_data[f"slab_{field}"] = value

    label = INPUT_LABELS.get(field, field)

    text = (
        f"✅ <b>{label}</b>\n\n"
        f"مقدار ثبت‌شده: <b>{value}</b>\n\n"
        "پارامتر ذخیره شد."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_slab_menu_keyboard(),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# MANUAL INPUT
# ---------------------------------------------------------------------

async def slab_manual_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    field: str,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    context.user_data["slab_pending_field"] = field
    context.user_data["slab_waiting_manual_input"] = True

    label = INPUT_LABELS.get(field, field)

    text = (
        f"⌨️ <b>ورود دستی — {label}</b>\n\n"
        "مقدار را در پیام بعدی ارسال کنید.\n\n"
        "مثال:\n"
        "<code>150</code>\n\n"
        "⚠️ مقدار پس از دریافت باید توسط لایه اعتبارسنجی "
        "کنترل شود."
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "❌ لغو",
                            callback_data="slab:menu",
                        )
                    ]
                ]
            ),
            parse_mode="HTML",
        )


# ---------------------------------------------------------------------
# RECEIVE MANUAL INPUT
# ---------------------------------------------------------------------

async def receive_slab_manual_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not context.user_data.get(
        "slab_waiting_manual_input"
    ):
        return

    if not update.message or not update.message.text:
        return

    field = context.user_data.get(
        "slab_pending_field"
    )

    if not field:
        context.user_data[
            "slab_waiting_manual_input"
        ] = False
        return

    value = update.message.text.strip()

    context.user_data[f"slab_{field}"] = value

    context.user_data[
        "slab_waiting_manual_input"
    ] = False

    context.user_data[
        "slab_pending_field"
    ] = None

    label = INPUT_LABELS.get(field, field)

    await update.message.reply_text(
        f"✅ {label} ثبت شد.\n\n"
        f"مقدار: <b>{value}</b>\n\n"
        "پارامتر بعدی را انتخاب کنید.",
        reply_markup=get_slab_menu_keyboard(),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------
# CALCULATION
# ---------------------------------------------------------------------

async def calculate_slab(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    slab_type = context.user_data.get(
        "slab_type",
        "one_way",
    )

    text = (
        "🧮 <b>محاسبه دال / سقف</b>\n\n"
        f"نوع: {SLAB_TYPES.get(slab_type, slab_type)}\n\n"
        "در نسخه نهایی موتور محاسبات این موارد را بررسی می‌کند:\n\n"
        "• تعیین سیستم باربری\n"
        "• خمش\n"
        "• برش\n"
        "• آرماتور حداقل و موردنیاز\n"
        "• آرماتور بالا و پایین\n"
        "• آرماتور X و Y\n"
        "• کنترل فاصله میلگردها\n"
        "• نواحی تکیه‌گاه و وسط دهانه\n"
        "• طول مهاری\n"
        "• وصله\n"
        "• دیتیلینگ\n"
        "• BBS\n"
        "• Cut List\n"
        "• وزن میلگرد\n"
        "• حجم بتن\n\n"
        "⚠️ این بخش رابط کاربر است و نتیجه مهندسی "
        "باید از موتور core/ و codes/ دریافت شود."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔩 آرماتور و BBS",
                    callback_data="slab:reinforcement",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 گزارش",
                    callback_data="slab:report",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="slab:menu",
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
# REINFORCEMENT ROUTE
# ---------------------------------------------------------------------

async def slab_reinforcement(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "🔩 <b>آرماتور و BBS دال</b>\n\n"
        "مسیر نهایی پردازش:\n\n"
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
        "Stock Bars\n"
        "↓\n"
        "Waste / Weight"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="slab:menu",
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

async def slab_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "📊 <b>گزارش دال / سقف</b>\n\n"
        "گزارش نهایی شامل:\n\n"
        "• مشخصات پروژه\n"
        "• نوع سقف\n"
        "• سیستم واحد\n"
        "• آیین‌نامه طراحی\n"
        "• هندسه\n"
        "• مصالح\n"
        "• بارگذاری\n"
        "• نتایج کنترل‌ها\n"
        "• آرماتور X و Y\n"
        "• نواحی تکیه‌گاه و دهانه\n"
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
                    callback_data="slab:menu",
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

async def slab_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if data == "slab:menu":
        await show_slab_menu(
            update,
            context,
        )
        return

    if data.startswith("slab:type:"):
        slab_type = data.split(":", 2)[2]

        await select_slab_type(
            update,
            context,
            slab_type,
        )
        return

    if data.startswith("slab:input:"):
        section = data.split(":", 2)[2]

        await slab_input_menu(
            update,
            context,
            section,
        )
        return

    if data.startswith("slab_input:"):
        field = data.split(":", 1)[1]

        await slab_input_request(
            update,
            context,
            field,
        )
        return

    if data.startswith("slab_value:"):
        parts = data.split(":", 2)

        if len(parts) != 3:
            await query.answer(
                "❌ مقدار نامعتبر است.",
                show_alert=True,
            )
            return

        field = parts[1]
        value = parts[2]

        await slab_preset_value(
            update,
            context,
            field,
            value,
        )
        return

    if data.startswith("slab_manual:"):
        field = data.split(":", 1)[1]

        await slab_manual_input(
            update,
            context,
            field,
        )
        return

    if data == "slab:calculate":
        await calculate_slab(
            update,
            context,
        )
        return

    if data == "slab:reinforcement":
        await slab_reinforcement(
            update,
            context,
        )
        return

    if data == "slab:report":
        await slab_report(
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

def get_slab_callback_handler():
    from telegram.ext import CallbackQueryHandler

    return CallbackQueryHandler(
        slab_callback,
        pattern=r"^slab(?::|_)",
    )


def get_slab_message_handler():
    from telegram.ext import MessageHandler, filters

    return MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_slab_manual_input,
    )


# ---------------------------------------------------------------------
# EXPORTS
# ---------------------------------------------------------------------

__all__ = [
    "SLAB_TYPES",
    "get_slab_menu_keyboard",
    "get_slab_geometry_keyboard",
    "get_slab_material_keyboard",
    "get_slab_loads_keyboard",
    "get_slab_reinforcement_keyboard",
    "get_slab_regions_keyboard",
    "get_slab_detailing_keyboard",
    "show_slab_menu",
    "select_slab_type",
    "slab_input_menu",
    "slab_input_request",
    "slab_preset_value",
    "slab_manual_input",
    "receive_slab_manual_input",
    "calculate_slab",
    "slab_reinforcement",
    "slab_report",
    "slab_callback",
    "get_slab_callback_handler",
    "get_slab_message_handler",
]
