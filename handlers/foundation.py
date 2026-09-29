"""
StructuralBot - Foundation Handler

Handles foundation selection and input navigation.

Supported foundation types:
- Isolated footing
- Strip footing
- Raft foundation

Engineering calculations are delegated to core/ and codes/.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# =========================================================
# FOUNDATION TYPES
# =========================================================

FOUNDATION_TYPES = {
    "isolated": "⬛ فونداسیون منفرد",
    "strip": "▬ فونداسیون نواری",
    "raft": "▰ فونداسیون گسترده",
}


# =========================================================
# FOUNDATION MENU
# =========================================================

def get_foundation_keyboard(
    project_id: str | None = None,
) -> InlineKeyboardMarkup:
    """Build foundation type selection keyboard."""

    project_part = f":{project_id}" if project_id else ""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬛ منفرد",
                    callback_data=f"foundation:isolated{project_part}",
                ),
                InlineKeyboardButton(
                    "▬ نواری",
                    callback_data=f"foundation:strip{project_part}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "▰ گسترده",
                    callback_data=f"foundation:raft{project_part}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data=(
                        f"project:calculations:{project_id}"
                        if project_id
                        else "calc:open"
                    ),
                ),
            ],
        ]
    )


# =========================================================
# FOUNDATION INPUT KEYBOARD
# =========================================================

def get_foundation_input_keyboard(
    foundation_type: str,
    project_id: str | None = None,
) -> InlineKeyboardMarkup:
    """Build foundation input navigation."""

    project_part = f":{project_id}" if project_id else ""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📐 ابعاد",
                    callback_data=(
                        f"foundation_input:geometry:"
                        f"{foundation_type}{project_part}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "🧱 مصالح",
                    callback_data=(
                        f"foundation_input:materials:"
                        f"{foundation_type}{project_part}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔩 آرماتور",
                    callback_data=(
                        f"foundation_input:reinforcement:"
                        f"{foundation_type}{project_part}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 بارگذاری",
                    callback_data=(
                        f"foundation_input:loads:"
                        f"{foundation_type}{project_part}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚙️ جزئیات اجرایی",
                    callback_data=(
                        f"foundation_input:detailing:"
                        f"{foundation_type}{project_part}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "🧮 اجرای محاسبات",
                    callback_data=(
                        f"foundation_input:calculate:"
                        f"{foundation_type}{project_part}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data=(
                        f"foundation:list{project_part}"
                    ),
                ),
            ],
        ]
    )


# =========================================================
# FOUNDATION CALLBACK
# =========================================================

async def foundation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle foundation navigation."""

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("foundation:"):
        return

    parts = data.split(":")

    if len(parts) < 2:
        return

    action = parts[1]

    project_id = (
        parts[2]
        if len(parts) > 2
        else context.user_data.get(
            "current_project_id"
        )
    )

    # -----------------------------------------------------
    # FOUNDATION LIST
    # -----------------------------------------------------

    if action == "list":

        await query.edit_message_text(
            "🧱 <b>انتخاب نوع فونداسیون</b>\n\n"
            "نوع فونداسیون را انتخاب کنید.",
            reply_markup=get_foundation_keyboard(
                project_id
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # FOUNDATION TYPE
    # -----------------------------------------------------

    if action in FOUNDATION_TYPES:

        foundation_type = action

        context.user_data["foundation_type"] = (
            foundation_type
        )

        if project_id:
            context.user_data["current_project_id"] = (
                project_id
            )

        await query.edit_message_text(
            f"{FOUNDATION_TYPES[foundation_type]}\n\n"
            "📐 <b>مشخصات فونداسیون</b>\n\n"
            "بخش موردنظر را انتخاب کنید.",
            reply_markup=get_foundation_input_keyboard(
                foundation_type,
                project_id,
            ),
            parse_mode="HTML",
        )

        return


# =========================================================
# FOUNDATION INPUT CALLBACK
# =========================================================

async def foundation_input_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle foundation input sections."""

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("foundation_input:"):
        return

    parts = data.split(":")

    if len(parts) < 3:
        return

    section = parts[1]
    foundation_type = parts[2]

    project_id = (
        parts[3]
        if len(parts) > 3
        else context.user_data.get(
            "current_project_id"
        )
    )

    context.user_data["foundation_type"] = (
        foundation_type
    )

    if project_id:
        context.user_data["current_project_id"] = (
            project_id
        )

    # -----------------------------------------------------
    # GEOMETRY
    # -----------------------------------------------------

    if section == "geometry":

        context.user_data["foundation_input"] = (
            "geometry"
        )

        await query.edit_message_text(
            "📐 <b>هندسه فونداسیون</b>\n\n"
            "در این بخش ابعاد هندسی فونداسیون "
            "و ضخامت وارد می‌شود.\n\n"
            "نمونه:\n"
            "طول، عرض، ضخامت، عمق و تراز.",
            reply_markup=_back_keyboard(
                foundation_type,
                project_id,
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # MATERIALS
    # -----------------------------------------------------

    if section == "materials":

        context.user_data["foundation_input"] = (
            "materials"
        )

        await query.edit_message_text(
            "🧱 <b>مصالح</b>\n\n"
            "مشخصات بتن و فولاد انتخاب می‌شود.\n\n"
            "مقادیر باید مطابق آیین‌نامه انتخاب‌شده "
            "و مشخصات پروژه باشند.",
            reply_markup=_back_keyboard(
                foundation_type,
                project_id,
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # REINFORCEMENT
    # -----------------------------------------------------

    if section == "reinforcement":

        context.user_data["foundation_input"] = (
            "reinforcement"
        )

        await query.edit_message_text(
            "🔩 <b>آرماتور فونداسیون</b>\n\n"
            "قطر، تعداد یا فاصله میلگردها، "
            "کاور، نواحی مختلف آرماتوربندی و "
            "مشخصات اجرایی در این بخش وارد می‌شود.",
            reply_markup=_back_keyboard(
                foundation_type,
                project_id,
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # LOADS
    # -----------------------------------------------------

    if section == "loads":

        context.user_data["foundation_input"] = (
            "loads"
        )

        await query.edit_message_text(
            "📊 <b>بارگذاری</b>\n\n"
            "بارها و واکنش‌های لازم برای طراحی "
            "فونداسیون در این بخش وارد می‌شوند.\n\n"
            "این بخش جایگزین تحلیل کامل ETABS/SAP "
            "نیست و فقط داده‌های لازم برای ماژول "
            "طراحی فونداسیون را دریافت می‌کند.",
            reply_markup=_back_keyboard(
                foundation_type,
                project_id,
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # DETAILING
    # -----------------------------------------------------

    if section == "detailing":

        context.user_data["foundation_input"] = (
            "detailing"
        )

        await query.edit_message_text(
            "⚙️ <b>جزئیات اجرایی</b>\n\n"
            "کاور، فاصله میلگردها، خم، مهاری، "
            "وصله و سایر الزامات اجرایی "
            "بر اساس آیین‌نامه انتخاب‌شده بررسی می‌شوند.",
            reply_markup=_back_keyboard(
                foundation_type,
                project_id,
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # CALCULATE
    # -----------------------------------------------------

    if section == "calculate":

        context.user_data["calculation_member"] = (
            "foundation"
        )

        await query.edit_message_text(
            "🧮 <b>محاسبه فونداسیون</b>\n\n"
            "تمام ورودی‌های موردنیاز باید تکمیل شوند.\n\n"
            "پس از تکمیل ورودی‌ها، موتور محاسبات "
            "و لایه آیین‌نامه‌ای اجرا خواهد شد.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📐 تکمیل مشخصات",
                            callback_data=(
                                f"foundation:input:"
                                f"{foundation_type}"
                                + (
                                    f":{project_id}"
                                    if project_id
                                    else ""
                                )
                            ),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ بازگشت",
                            callback_data=(
                                f"foundation:{foundation_type}"
                                + (
                                    f":{project_id}"
                                    if project_id
                                    else ""
                                )
                            ),
                        )
                    ],
                ]
            ),
            parse_mode="HTML",
        )

        return


# =========================================================
# INPUT MENU
# =========================================================

async def foundation_input_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Display complete foundation input menu."""

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("foundation:input:"):
        return

    parts = data.split(":")

    if len(parts) < 3:
        return

    foundation_type = parts[2]

    project_id = (
        parts[3]
        if len(parts) > 3
        else context.user_data.get(
            "current_project_id"
        )
    )

    await query.edit_message_text(
        "📐 <b>اطلاعات فونداسیون</b>\n\n"
        "اطلاعات موردنیاز را از بخش‌های زیر تکمیل کنید.",
        reply_markup=get_foundation_input_keyboard(
            foundation_type,
            project_id,
        ),
        parse_mode="HTML",
    )


# =========================================================
# BACK KEYBOARD
# =========================================================

def _back_keyboard(
    foundation_type: str,
    project_id: str | None = None,
) -> InlineKeyboardMarkup:
    """Build back navigation keyboard."""

    project_part = f":{project_id}" if project_id else ""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ مشخصات فونداسیون",
                    callback_data=(
                        f"foundation:{foundation_type}"
                        f"{project_part}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="navigation:main",
                )
            ],
        ]
    )


# =========================================================
# HANDLER EXPORTS
# =========================================================

__all__ = [
    "FOUNDATION_TYPES",
    "get_foundation_keyboard",
    "get_foundation_input_keyboard",
    "foundation_callback",
    "foundation_input_callback",
    "foundation_input_menu",
]
