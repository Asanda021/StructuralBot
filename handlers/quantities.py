"""
StructuralBot - Quantities Handler

User-facing handler for material quantity takeoff.

The calculation layer is intentionally kept in core.quantities.
This module only handles Telegram navigation, input flow, and
presentation.
"""

from __future__ import annotations

from typing import Any, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes


# ---------------------------------------------------------
# OPTIONAL CORE IMPORT
# ---------------------------------------------------------

try:
    from core.quantities import (
        QuantityTakeoff,
        QuantityItem,
        create_concrete_quantity,
        create_rebar_quantity,
        create_piece_quantity,
        create_formwork_quantity,
    )
except ImportError:
    QuantityTakeoff = Any
    QuantityItem = Any
    create_concrete_quantity = None
    create_rebar_quantity = None
    create_piece_quantity = None
    create_formwork_quantity = None


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

QUANTITY_TYPES = {
    "concrete": "بتن",
    "rebar": "میلگرد",
    "formwork": "قالب‌بندی",
    "block": "بلوک",
    "polystyrene": "یونولیت / پلی‌استایرن",
    "joist": "تیرچه",
    "coupler": "کوپلر",
    "other": "سایر",
}

QUANTITY_UNITS = {
    "concrete": "m³",
    "rebar": "kg",
    "formwork": "m²",
    "block": "m²",
    "polystyrene": "m²",
    "joist": "m",
    "coupler": "pcs",
    "other": "unit",
}


# ---------------------------------------------------------
# KEYBOARDS
# ---------------------------------------------------------

def quantities_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🏗 برآورد پروژه",
                    callback_data="quantity:project",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏢 برآورد طبقه",
                    callback_data="quantity:floor",
                ),
                InlineKeyboardButton(
                    "🧱 برآورد عضو",
                    callback_data="quantity:member",
                ),
            ],
            [
                InlineKeyboardButton(
                    "➕ ثبت آیتم دستی",
                    callback_data="quantity:add",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 جمع‌بندی",
                    callback_data="quantity:summary",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📄 گزارش",
                    callback_data="quantity:report",
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


def quantity_type_keyboard() -> InlineKeyboardMarkup:
    rows = []

    row = []

    for key, title in QUANTITY_TYPES.items():
        row.append(
            InlineKeyboardButton(
                title,
                callback_data=f"quantity_type:{key}",
            )
        )

        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append(
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="quantity:menu",
            )
        ]
    )

    return InlineKeyboardMarkup(rows)


def quantity_unit_keyboard(
    quantity_type: str,
) -> InlineKeyboardMarkup:
    unit = QUANTITY_UNITS.get(quantity_type, "unit")

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"واحد: {unit}",
                    callback_data=f"quantity_unit:{unit}",
                )
            ],
            [
                InlineKeyboardButton(
                    "✏️ ورود مقدار",
                    callback_data="quantity_value:manual",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 انتخاب نوع",
                    callback_data="quantity:add",
                )
            ],
        ]
    )


def summary_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data="quantity:summary",
                ),
                InlineKeyboardButton(
                    "➕ افزودن آیتم",
                    callback_data="quantity:add",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📄 گزارش",
                    callback_data="quantity:report",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="nav:home",
                )
            ],
        ]
    )


# ---------------------------------------------------------
# STORAGE HELPERS
# ---------------------------------------------------------

def get_takeoff(context: ContextTypes.DEFAULT_TYPE) -> Any:
    """
    Get the current in-memory takeoff.

    Persistent project storage will be connected later through
    database/project services.
    """

    takeoff = context.user_data.get("quantity_takeoff")

    if takeoff is None and QuantityTakeoff is not Any:
        try:
            takeoff = QuantityTakeoff()
            context.user_data["quantity_takeoff"] = takeoff
        except Exception:
            takeoff = None

    return takeoff


def get_manual_items(
    context: ContextTypes.DEFAULT_TYPE,
) -> list[dict[str, Any]]:
    items = context.user_data.get("quantity_manual_items")

    if not isinstance(items, list):
        items = []
        context.user_data["quantity_manual_items"] = items

    return items


def safe_float(value: str) -> Optional[float]:
    try:
        normalized = (
            value.strip()
            .replace(",", "")
            .replace("،", "")
        )

        # Persian / Arabic digits
        translation = str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
            "01234567890123456789",
        )

        normalized = normalized.translate(translation)

        return float(normalized)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------
# MAIN SCREEN
# ---------------------------------------------------------

async def show_quantities_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "🧮 <b>برآورد مصالح</b>\n\n"
        "در این بخش می‌توانید مقدار تقریبی مصالح پروژه را "
        "از اطلاعات محاسباتی یا آیتم‌های دستی جمع‌بندی کنید.\n\n"
        "موارد قابل مدیریت:\n"
        "• بتن\n"
        "• میلگرد\n"
        "• قالب‌بندی\n"
        "• بلوک\n"
        "• یونولیت / پلی‌استایرن\n"
        "• تیرچه\n"
        "• کوپلر\n"
        "• سایر اقلام\n\n"
        "⚠️ این بخش Quantity Takeoff است و با متره کامل "
        "و برآورد مالی/فهرست‌بهایی یکسان نیست."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=quantities_menu_keyboard(),
        )


# ---------------------------------------------------------
# PROJECT / FLOOR / MEMBER
# ---------------------------------------------------------

async def show_project_quantities(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    takeoff = get_takeoff(context)

    if takeoff is None:
        text = (
            "🏗 <b>برآورد پروژه</b>\n\n"
            "هنوز اطلاعات Quantity Takeoff برای پروژه "
            "در این نشست ثبت نشده است.\n\n"
            "ابتدا محاسبات اعضا را انجام دهید یا آیتم دستی "
            "ثبت کنید."
        )
    else:
        text = build_takeoff_summary(
            takeoff,
            title="🏗 برآورد پروژه",
        )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=summary_keyboard(),
    )


async def show_floor_quantities(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "🏢 <b>برآورد طبقه</b>\n\n"
        "انتخاب طبقه در نسخه بعدی از اطلاعات پروژه "
        "خوانده خواهد شد.\n\n"
        "ساختار سیستم از ابتدا طوری طراحی شده که مقدار "
        "مصالح بتواند به تفکیک پروژه، طبقه و عضو نگهداری شود."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=quantities_menu_keyboard(),
    )


async def show_member_quantities(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "🧱 <b>برآورد عضو</b>\n\n"
        "برآورد عضو باید مستقیماً از خروجی محاسبه همان عضو "
        "تغذیه شود.\n\n"
        "زنجیره نهایی:\n"
        "عضو → محاسبات → آرماتور → BBS → Cut List → مصالح"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=quantities_menu_keyboard(),
    )


# ---------------------------------------------------------
# ADD MANUAL ITEM
# ---------------------------------------------------------

async def show_quantity_type(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    context.user_data["quantity_mode"] = "manual"

    text = (
        "➕ <b>ثبت آیتم دستی</b>\n\n"
        "نوع مصالح را انتخاب کنید:"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=quantity_type_keyboard(),
    )


async def show_quantity_value(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    quantity_type: str,
) -> None:
    if quantity_type not in QUANTITY_TYPES:
        await update.callback_query.edit_message_text(
            "❌ نوع آیتم نامعتبر است.",
            reply_markup=quantities_menu_keyboard(),
        )
        return

    context.user_data["quantity_type"] = quantity_type
    context.user_data["quantity_unit"] = QUANTITY_UNITS[
        quantity_type
    ]

    title = QUANTITY_TYPES[quantity_type]
    unit = QUANTITY_UNITS[quantity_type]

    text = (
        f"➕ <b>{title}</b>\n\n"
        f"واحد: <b>{unit}</b>\n\n"
        "مقدار را وارد کنید.\n"
        "مثال:\n"
        "<code>125.5</code>"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=quantity_unit_keyboard(quantity_type),
    )


async def request_manual_quantity_value(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    quantity_type = context.user_data.get("quantity_type")

    if quantity_type not in QUANTITY_TYPES:
        await show_quantity_type(update, context)
        return

    context.user_data["quantity_waiting_value"] = True

    title = QUANTITY_TYPES[quantity_type]
    unit = QUANTITY_UNITS[quantity_type]

    await update.callback_query.edit_message_text(
        f"✏️ <b>ورود مقدار {title}</b>\n\n"
        f"مقدار را بر حسب <b>{unit}</b> ارسال کنید.\n\n"
        "مثال: <code>125.5</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data=f"quantity_type:{quantity_type}",
                    )
                ]
            ]
        ),
    )


async def save_manual_quantity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    value: float,
) -> None:
    quantity_type = context.user_data.get("quantity_type")

    if quantity_type not in QUANTITY_TYPES:
        await update.message.reply_text(
            "❌ نوع مصالح مشخص نیست."
        )
        return

    title = QUANTITY_TYPES[quantity_type]
    unit = QUANTITY_UNITS[quantity_type]

    item = {
        "type": quantity_type,
        "name": title,
        "quantity": value,
        "unit": unit,
    }

    items = get_manual_items(context)
    items.append(item)

    context.user_data["quantity_waiting_value"] = False

    # Try to add to core QuantityTakeoff when possible.
    takeoff = get_takeoff(context)

    if takeoff is not None:
        try:
            quantity_item = QuantityItem(
                name=title,
                quantity=value,
                unit=unit,
                quantity_type=quantity_type,
            )
            takeoff.add_item(quantity_item)
        except Exception:
            # The in-memory fallback remains authoritative for now.
            pass

    await update.message.reply_text(
        "✅ <b>آیتم ثبت شد</b>\n\n"
        f"نوع: {title}\n"
        f"مقدار: {value:g} {unit}\n\n"
        "آیتم به جمع‌بندی فعلی اضافه شد.",
        parse_mode="HTML",
        reply_markup=summary_keyboard(),
    )


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

def build_manual_summary(
    context: ContextTypes.DEFAULT_TYPE,
) -> str:
    items = get_manual_items(context)

    if not items:
        return "هنوز آیتم دستی ثبت نشده است."

    grouped: dict[str, float] = {}

    for item in items:
        key = item["type"]
        grouped[key] = grouped.get(key, 0.0) + float(
            item["quantity"]
        )

    lines = []

    for key, quantity in grouped.items():
        title = QUANTITY_TYPES.get(key, key)
        unit = QUANTITY_UNITS.get(key, "unit")

        lines.append(
            f"• {title}: <b>{quantity:,.2f} {unit}</b>"
        )

    return "\n".join(lines)


def build_takeoff_summary(
    takeoff: Any,
    title: str = "📊 جمع‌بندی",
) -> str:
    """
    Build a tolerant summary from core QuantityTakeoff.

    This function avoids depending on a single future presentation
    API and can therefore survive small core-layer changes.
    """

    lines = [f"<b>{title}</b>", ""]

    try:
        total_items = len(takeoff.items)

        lines.append(
            f"تعداد آیتم‌ها: <b>{total_items}</b>"
        )
    except Exception:
        pass

    try:
        if hasattr(takeoff, "telegram_summary"):
            summary = takeoff.telegram_summary()

            if summary:
                lines.append("")
                lines.append(str(summary))
        else:
            lines.append(
                "اطلاعات مصالح در موتور Quantity Takeoff موجود است."
            )
    except Exception:
        lines.append(
            "اطلاعات مصالح در موتور Quantity Takeoff موجود است."
        )

    return "\n".join(lines)


async def show_quantity_summary(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    takeoff = get_takeoff(context)

    manual_summary = build_manual_summary(context)

    if takeoff is not None:
        core_summary = build_takeoff_summary(
            takeoff,
            title="📊 جمع‌بندی مصالح",
        )

        text = (
            f"{core_summary}\n\n"
            "<b>آیتم‌های دستی این نشست:</b>\n"
            f"{manual_summary}"
        )
    else:
        text = (
            "📊 <b>جمع‌بندی مصالح</b>\n\n"
            f"{manual_summary}"
        )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=summary_keyboard(),
    )


# ---------------------------------------------------------
# REPORT
# ---------------------------------------------------------

async def show_quantity_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "📄 <b>گزارش مصالح</b>\n\n"
        "ساختار گزارش در نسخه نهایی از همان داده مشترک "
        "Quantity Takeoff استفاده خواهد کرد.\n\n"
        "خروجی‌های هدف:\n"
        "• Telegram\n"
        "• PDF\n"
        "• Excel\n\n"
        "به این ترتیب اعداد بین گزارش تلگرام، PDF و Excel "
        "با یکدیگر اختلاف نخواهند داشت."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📊 جمع‌بندی",
                        callback_data="quantity:summary",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="quantity:menu",
                    ),
                    InlineKeyboardButton(
                        "🏠 منوی اصلی",
                        callback_data="nav:home",
                    ),
                ],
            ]
        ),
    )


# ---------------------------------------------------------
# CALLBACK ROUTER
# ---------------------------------------------------------

async def quantities_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    # -----------------------------------------------------
    # MAIN
    # -----------------------------------------------------

    if data == "quantity:menu":
        await show_quantities_menu(update, context)
        return

    if data == "quantity:project":
        await show_project_quantities(update, context)
        return

    if data == "quantity:floor":
        await show_floor_quantities(update, context)
        return

    if data == "quantity:member":
        await show_member_quantities(update, context)
        return

    if data == "quantity:add":
        await show_quantity_type(update, context)
        return

    if data == "quantity:summary":
        await show_quantity_summary(update, context)
        return

    if data == "quantity:report":
        await show_quantity_report(update, context)
        return

    # -----------------------------------------------------
    # TYPE
    # -----------------------------------------------------

    if data.startswith("quantity_type:"):
        quantity_type = data.split(":", 1)[1]

        await show_quantity_value(
            update,
            context,
            quantity_type,
        )
        return

    # -----------------------------------------------------
    # UNIT
    # -----------------------------------------------------

    if data.startswith("quantity_unit:"):
        quantity_type = context.user_data.get(
            "quantity_type"
        )

        if quantity_type:
            await request_manual_quantity_value(
                update,
                context,
            )
        else:
            await show_quantity_type(update, context)

        return

    # -----------------------------------------------------
    # VALUE
    # -----------------------------------------------------

    if data == "quantity_value:manual":
        await request_manual_quantity_value(
            update,
            context,
        )
        return


# ---------------------------------------------------------
# MESSAGE ROUTER
# ---------------------------------------------------------

async def quantities_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle manual numeric quantity input only when requested.
    """

    if update.message is None:
        return

    if not context.user_data.get(
        "quantity_waiting_value"
    ):
        return

    raw = (update.message.text or "").strip()

    value = safe_float(raw)

    if value is None:
        await update.message.reply_text(
            "❌ مقدار نامعتبر است.\n\n"
            "لطفاً فقط عدد وارد کنید.\n"
            "مثال: 125.5"
        )
        return

    if value <= 0:
        await update.message.reply_text(
            "❌ مقدار باید بیشتر از صفر باشد."
        )
        return

    await save_manual_quantity(
        update,
        context,
        value,
    )


# ---------------------------------------------------------
# HANDLER FACTORIES
# ---------------------------------------------------------

def get_quantities_callback_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(
        quantities_callback,
        pattern=r"^quantity(?:[:_]|$)",
    )


def get_quantities_message_handler():
    return quantities_message


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

__all__ = [
    "QUANTITY_TYPES",
    "QUANTITY_UNITS",
    "show_quantities_menu",
    "quantities_callback",
    "quantities_message",
    "get_quantities_callback_handler",
    "get_quantities_message_handler",
]
