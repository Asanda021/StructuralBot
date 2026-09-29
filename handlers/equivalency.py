"""
StructuralBot - Rebar Equivalency Handler

User-facing handler for reinforcement bar equivalency.

This module is intentionally separated from the calculation engine.
The actual engineering equivalency logic belongs to core.reinforcement
and code-specific validation belongs to the selected design-code layer.
"""

from __future__ import annotations

import math
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes


# ---------------------------------------------------------
# STANDARD REBAR DIAMETERS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------

def bar_area(diameter_mm: float) -> float:
    """Return cross-sectional area of one bar in mm²."""
    if diameter_mm <= 0:
        raise ValueError("Diameter must be positive.")

    return math.pi * diameter_mm**2 / 4.0


def equivalent_count(
    source_diameter: float,
    source_count: int,
    target_diameter: float,
) -> int:
    """
    Calculate the minimum target-bar count providing at least
    the same theoretical steel area.

    This is an area-equivalency calculation only.
    It is NOT a final code-compliant reinforcement substitution.
    """
    if source_diameter <= 0:
        raise ValueError("Source diameter must be positive.")

    if target_diameter <= 0:
        raise ValueError("Target diameter must be positive.")

    if source_count <= 0:
        raise ValueError("Source count must be positive.")

    source_area = source_count * bar_area(source_diameter)
    target_area = bar_area(target_diameter)

    return max(1, math.ceil(source_area / target_area))


def equivalent_area(
    source_diameter: float,
    source_count: int,
) -> float:
    """Return total theoretical steel area in mm²."""
    return source_count * bar_area(source_diameter)


# ---------------------------------------------------------
# KEYBOARDS
# ---------------------------------------------------------

def equivalency_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 معادل‌سازی میلگرد",
                    callback_data="equiv:start",
                )
            ],
            [
                InlineKeyboardButton(
                    "📐 تبدیل بر اساس قطر",
                    callback_data="equiv:diameter",
                ),
                InlineKeyboardButton(
                    "📊 محاسبه سطح مقطع",
                    callback_data="equiv:area",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📚 توضیحات",
                    callback_data="equiv:info",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="nav:back",
                ),
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="nav:home",
                ),
            ],
        ]
    )


def source_diameter_keyboard() -> InlineKeyboardMarkup:
    rows = []

    row = []

    for diameter in STANDARD_DIAMETERS:
        row.append(
            InlineKeyboardButton(
                f"Ø{diameter}",
                callback_data=f"equiv_source:{diameter}",
            )
        )

        if len(row) == 4:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append(
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="equiv:menu",
            )
        ]
    )

    return InlineKeyboardMarkup(rows)


def target_diameter_keyboard(
    source_diameter: float,
) -> InlineKeyboardMarkup:
    rows = []

    row = []

    for diameter in STANDARD_DIAMETERS:
        if diameter == source_diameter:
            continue

        row.append(
            InlineKeyboardButton(
                f"Ø{diameter}",
                callback_data=f"equiv_target:{diameter}",
            )
        )

        if len(row) == 4:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append(
        [
            InlineKeyboardButton(
                "🔙 انتخاب مجدد قطر مبدأ",
                callback_data="equiv:start",
            )
        ]
    )

    return InlineKeyboardMarkup(rows)


def count_keyboard() -> InlineKeyboardMarkup:
    counts = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20]

    rows = []
    row = []

    for count in counts:
        row.append(
            InlineKeyboardButton(
                str(count),
                callback_data=f"equiv_count:{count}",
            )
        )

        if len(row) == 4:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append(
        [
            InlineKeyboardButton(
                "✏️ ورود دستی",
                callback_data="equiv_count:manual",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="equiv:start",
            )
        ]
    )

    return InlineKeyboardMarkup(rows)


def result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 معادل‌سازی جدید",
                    callback_data="equiv:start",
                )
            ],
            [
                InlineKeyboardButton(
                    "📐 محاسبه سطح مقطع",
                    callback_data="equiv:area",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="nav:home",
                ),
            ],
        ]
    )


# ---------------------------------------------------------
# SCREEN HELPERS
# ---------------------------------------------------------

async def show_equivalency_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
        "در این بخش می‌توانید معادل تئوریک میلگردها را "
        "بر اساس سطح مقطع فولاد محاسبه کنید.\n\n"
        "مثال:\n"
        "4Ø16 → چند Ø20 لازم است؟\n\n"
        "⚠️ توجه:\n"
        "این محاسبه بر اساس سطح مقطع اسمی میلگرد است و "
        "به‌تنهایی جایگزین کنترل ضوابط طراحی، حداقل و حداکثر "
        "آرماتور، فاصله‌گذاری، طول مهاری، وصله و الزامات اجرایی نیست."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=equivalency_menu_keyboard(),
        )


async def show_equivalency_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "📚 <b>راهنمای معادل‌سازی</b>\n\n"
        "مبنای محاسبه، مساحت اسمی مقطع میلگرد است:\n\n"
        "<code>A = π × d² / 4</code>\n\n"
        "سپس سطح مقطع کل میلگردهای موجود با سطح مقطع "
        "میلگرد جایگزین مقایسه می‌شود.\n\n"
        "مثلاً اگر سطح مقطع کل میلگردهای مبدأ برابر A باشد، "
        "تعداد میلگرد جایگزین از رابطه زیر به‌دست می‌آید:\n\n"
        "<code>n = ceil(A / A_bar)</code>\n\n"
        "⚠️ کنترل نهایی جایگزینی باید با توجه به عضو، "
        "مقررات طراحی انتخاب‌شده، قطر، فاصله، مهاری، وصله، "
        "جزئیات اجرایی و محدودیت‌های سازه انجام شود."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔄 شروع معادل‌سازی",
                        callback_data="equiv:start",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="equiv:menu",
                    )
                ],
            ]
        ),
    )


async def show_source_diameter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "🔹 <b>قطر میلگرد مبدأ</b>\n\n"
        "قطر میلگردی که در طرح فعلی استفاده شده است را انتخاب کنید:"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=source_diameter_keyboard(),
    )


async def show_target_diameter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    source_diameter: float,
) -> None:
    context.user_data["equiv_source_diameter"] = source_diameter

    text = (
        f"🔹 <b>قطر مبدأ:</b> Ø{source_diameter:g}\n\n"
        "حالا قطر میلگرد جایگزین را انتخاب کنید:"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=target_diameter_keyboard(source_diameter),
    )


async def show_count(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    source_diameter = context.user_data.get("equiv_source_diameter")
    target_diameter = context.user_data.get("equiv_target_diameter")

    if source_diameter is None or target_diameter is None:
        await show_source_diameter(update, context)
        return

    text = (
        f"🔹 <b>قطر مبدأ:</b> Ø{source_diameter:g}\n"
        f"🔹 <b>قطر جایگزین:</b> Ø{target_diameter:g}\n\n"
        "تعداد میلگردهای مبدأ را انتخاب کنید:"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=count_keyboard(),
    )


async def show_equivalency_result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    source_count: int,
) -> None:
    source_diameter = context.user_data.get("equiv_source_diameter")
    target_diameter = context.user_data.get("equiv_target_diameter")

    if source_diameter is None or target_diameter is None:
        await show_source_diameter(update, context)
        return

    result_count = equivalent_count(
        source_diameter=source_diameter,
        source_count=source_count,
        target_diameter=target_diameter,
    )

    source_total_area = equivalent_area(
        source_diameter,
        source_count,
    )

    target_total_area = equivalent_area(
        target_diameter,
        result_count,
    )

    extra_area = target_total_area - source_total_area

    text = (
        "🔄 <b>نتیجه معادل‌سازی</b>\n\n"
        f"میلگرد مبدأ:\n"
        f"• {source_count} عدد Ø{source_diameter:g}\n"
        f"• سطح مقطع کل: {source_total_area:,.1f} mm²\n\n"
        f"میلگرد جایگزین:\n"
        f"• {result_count} عدد Ø{target_diameter:g}\n"
        f"• سطح مقطع کل: {target_total_area:,.1f} mm²\n\n"
        f"افزایش سطح مقطع: {extra_area:,.1f} mm²\n\n"
        "⚠️ این نتیجه «معادل‌سازی سطح مقطع» است. "
        "تأیید نهایی جایگزینی نیازمند کنترل ضوابط طراحی "
        "و جزئیات عضو است."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=result_keyboard(),
    )


async def show_area_calculator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "📊 <b>محاسبه سطح مقطع میلگرد</b>\n\n"
        "برای محاسبه سریع سطح مقطع، ابتدا قطر میلگرد مبدأ "
        "را انتخاب کنید."
    )

    context.user_data["equiv_mode"] = "area"

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=source_diameter_keyboard(),
    )


async def show_area_result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    count: int,
) -> None:
    diameter = context.user_data.get("equiv_source_diameter")

    if diameter is None:
        await show_source_diameter(update, context)
        return

    total_area = equivalent_area(diameter, count)

    text = (
        "📊 <b>سطح مقطع میلگرد</b>\n\n"
        f"قطر: Ø{diameter:g}\n"
        f"تعداد: {count}\n"
        f"سطح مقطع یک میلگرد: {bar_area(diameter):,.1f} mm²\n"
        f"سطح مقطع کل: {total_area:,.1f} mm²"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔄 محاسبه جدید",
                        callback_data="equiv:area",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 منوی اصلی",
                        callback_data="nav:home",
                    )
                ],
            ]
        ),
    )


# ---------------------------------------------------------
# CALLBACK ROUTER
# ---------------------------------------------------------

async def equivalency_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    # -----------------------------------------------------
    # MAIN MENU
    # -----------------------------------------------------

    if data == "equiv:menu":
        await show_equivalency_menu(update, context)
        return

    if data == "equiv:info":
        await show_equivalency_info(update, context)
        return

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    if data == "equiv:start":
        context.user_data["equiv_mode"] = "equivalency"
        context.user_data.pop("equiv_source_diameter", None)
        context.user_data.pop("equiv_target_diameter", None)

        await show_source_diameter(update, context)
        return

    # -----------------------------------------------------
    # SOURCE DIAMETER
    # -----------------------------------------------------

    if data.startswith("equiv_source:"):
        raw = data.split(":", 1)[1]

        try:
            diameter = float(raw)
        except ValueError:
            await query.edit_message_text(
                "❌ قطر میلگرد نامعتبر است.",
                reply_markup=equivalency_menu_keyboard(),
            )
            return

        mode = context.user_data.get("equiv_mode", "equivalency")

        if mode == "area":
            context.user_data["equiv_source_diameter"] = diameter

            text = (
                f"🔹 قطر انتخاب‌شده: Ø{diameter:g}\n\n"
                "تعداد میلگرد را انتخاب کنید:"
            )

            await query.edit_message_text(
                text=text,
                parse_mode="HTML",
                reply_markup=count_keyboard(),
            )
            return

        await show_target_diameter(
            update,
            context,
            diameter,
        )
        return

    # -----------------------------------------------------
    # TARGET DIAMETER
    # -----------------------------------------------------

    if data.startswith("equiv_target:"):
        raw = data.split(":", 1)[1]

        try:
            target_diameter = float(raw)
        except ValueError:
            await query.edit_message_text(
                "❌ قطر میلگرد نامعتبر است.",
                reply_markup=equivalency_menu_keyboard(),
            )
            return

        context.user_data["equiv_target_diameter"] = target_diameter

        await show_count(update, context)
        return

    # -----------------------------------------------------
    # COUNT
    # -----------------------------------------------------

    if data.startswith("equiv_count:"):
        raw = data.split(":", 1)[1]

        if raw == "manual":
            context.user_data["equiv_waiting_count"] = True

            await query.edit_message_text(
                "✏️ تعداد میلگردهای مبدأ را به صورت عدد صحیح "
                "ارسال کنید.\n\n"
                "مثال: <code>8</code>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 بازگشت",
                                callback_data="equiv:start",
                            )
                        ]
                    ]
                ),
            )
            return

        try:
            count = int(raw)
        except ValueError:
            await query.edit_message_text(
                "❌ تعداد نامعتبر است.",
                reply_markup=count_keyboard(),
            )
            return

        if count <= 0:
            await query.edit_message_text(
                "❌ تعداد باید بیشتر از صفر باشد.",
                reply_markup=count_keyboard(),
            )
            return

        mode = context.user_data.get("equiv_mode", "equivalency")

        if mode == "area":
            await show_area_result(
                update,
                context,
                count,
            )
            return

        await show_equivalency_result(
            update,
            context,
            count,
        )
        return

    # -----------------------------------------------------
    # AREA MODE
    # -----------------------------------------------------

    if data == "equiv:area":
        await show_area_calculator(update, context)
        return

    # -----------------------------------------------------
    # DIAMETER MODE
    # -----------------------------------------------------

    if data == "equiv:diameter":
        context.user_data["equiv_mode"] = "equivalency"
        await show_source_diameter(update, context)
        return


# ---------------------------------------------------------
# TEXT INPUT HANDLER
# ---------------------------------------------------------

async def equivalency_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handles manual count input.

    This handler is intentionally conservative and only reacts
    when the equivalency module explicitly requested a count.
    """

    if update.message is None:
        return

    if not context.user_data.get("equiv_waiting_count"):
        return

    raw = (update.message.text or "").strip()

    try:
        count = int(raw)
    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً فقط یک عدد صحیح وارد کنید.\n"
            "مثال: 8"
        )
        return

    if count <= 0:
        await update.message.reply_text(
            "❌ تعداد باید بیشتر از صفر باشد."
        )
        return

    context.user_data["equiv_waiting_count"] = False

    mode = context.user_data.get("equiv_mode", "equivalency")

    source_diameter = context.user_data.get("equiv_source_diameter")
    target_diameter = context.user_data.get("equiv_target_diameter")

    if source_diameter is None:
        await update.message.reply_text(
            "❌ ابتدا قطر میلگرد را انتخاب کنید."
        )
        return

    if mode == "area":
        total_area = equivalent_area(
            source_diameter,
            count,
        )

        await update.message.reply_text(
            "📊 <b>نتیجه</b>\n\n"
            f"قطر: Ø{source_diameter:g}\n"
            f"تعداد: {count}\n"
            f"سطح مقطع یک میلگرد: "
            f"{bar_area(source_diameter):,.1f} mm²\n"
            f"سطح مقطع کل: {total_area:,.1f} mm²",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 محاسبه جدید",
                            callback_data="equiv:area",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 منوی اصلی",
                            callback_data="nav:home",
                        )
                    ],
                ]
            ),
        )
        return

    if target_diameter is None:
        await update.message.reply_text(
            "❌ ابتدا قطر میلگرد جایگزین را انتخاب کنید."
        )
        return

    result_count = equivalent_count(
        source_diameter,
        count,
        target_diameter,
    )

    source_total_area = equivalent_area(
        source_diameter,
        count,
    )

    target_total_area = equivalent_area(
        target_diameter,
        result_count,
    )

    await update.message.reply_text(
        "🔄 <b>نتیجه معادل‌سازی</b>\n\n"
        f"مبدأ: {count} عدد Ø{source_diameter:g}\n"
        f"سطح مقطع مبدأ: {source_total_area:,.1f} mm²\n\n"
        f"جایگزین: {result_count} عدد Ø{target_diameter:g}\n"
        f"سطح مقطع جایگزین: {target_total_area:,.1f} mm²\n\n"
        "⚠️ نتیجه فوق صرفاً معادل‌سازی سطح مقطع است و "
        "تأیید نهایی جایگزینی باید بر اساس ضوابط عضو "
        "و Design Code انتخاب‌شده انجام شود.",
        parse_mode="HTML",
        reply_markup=result_keyboard(),
    )


# ---------------------------------------------------------
# HANDLER FACTORIES
# ---------------------------------------------------------

def get_equivalency_callback_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(
        equivalency_callback,
        pattern=r"^equiv(?:[:_]|$)",
    )


def get_equivalency_message_handler():
    """
    Return the message callback function.

    bot.py can register this with a MessageHandler using a
    suitable text/filter strategy.
    """
    return equivalency_message


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

__all__ = [
    "STANDARD_DIAMETERS",
    "bar_area",
    "equivalent_count",
    "equivalent_area",
    "show_equivalency_menu",
    "equivalency_callback",
    "equivalency_message",
    "get_equivalency_callback_handler",
    "get_equivalency_message_handler",
]
