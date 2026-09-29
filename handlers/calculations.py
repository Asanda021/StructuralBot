"""
StructuralBot - Calculations Handler

Handles the structural calculation navigation layer.

This module:
- Selects structure type
- Selects design-code family
- Selects structural member
- Keeps calculation context
- Routes the user to the appropriate member handler

Engineering calculations themselves are performed by core/ and codes/.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# =========================================================
# CONSTANTS
# =========================================================

STRUCTURE_TYPES = {
    "concrete": "🏢 بتن‌آرمه",
    "steel": "🏗 فولادی",
    "composite": "🔀 مرکب",
}


CODE_FAMILIES = {
    "iran": "🇮🇷 مقررات ملی ایران",
    "aci": "🇺🇸 ACI",
    "eurocode": "🇪🇺 Eurocode",
}


MEMBERS = {
    "foundation": "🧱 فونداسیون",
    "column": "🏛 ستون",
    "beam": "📏 تیر",
    "slab": "▰ دال / سقف",
    "wall": "🧱 دیوار سازه‌ای",
    "stair": "🪜 راه‌پله",
}


# =========================================================
# MAIN CALCULATION MENU
# =========================================================

def get_calculation_menu_keyboard(
    project_id: str | None = None,
) -> InlineKeyboardMarkup:
    """Build structure-type selection keyboard."""

    suffix = f":{project_id}" if project_id else ""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🏢 سازه بتنی",
                    callback_data=f"calc:concrete{suffix}",
                ),
                InlineKeyboardButton(
                    "🏗 سازه فولادی",
                    callback_data=f"calc:steel{suffix}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔀 سازه مرکب",
                    callback_data=f"calc:composite{suffix}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data=(
                        f"project:open:{project_id}"
                        if project_id
                        else "navigation:main"
                    ),
                )
            ],
        ]
    )


# =========================================================
# CODE FAMILY KEYBOARD
# =========================================================

def get_code_keyboard(
    structure_type: str,
    project_id: str | None = None,
) -> InlineKeyboardMarkup:
    """Build design-code selection keyboard."""

    project_part = f":{project_id}" if project_id else ""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🇮🇷 ایران",
                    callback_data=(
                        f"code:iran:{structure_type}{project_part}"
                    ),
                ),
                InlineKeyboardButton(
                    "🇺🇸 ACI",
                    callback_data=(
                        f"code:aci:{structure_type}{project_part}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "🇪🇺 Eurocode",
                    callback_data=(
                        f"code:eurocode:{structure_type}{project_part}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data=(
                        f"calc:back{project_part}"
                    ),
                )
            ],
        ]
    )


# =========================================================
# MEMBER KEYBOARD
# =========================================================

def get_member_keyboard(
    structure_type: str,
    code_family: str,
    project_id: str | None = None,
) -> InlineKeyboardMarkup:
    """Build structural-member selection keyboard."""

    project_part = f":{project_id}" if project_id else ""

    if structure_type == "concrete":
        members = [
            ("foundation", "🧱 فونداسیون"),
            ("column", "🏛 ستون"),
            ("beam", "📏 تیر"),
            ("slab", "▰ دال / سقف"),
            ("wall", "🧱 دیوار سازه‌ای"),
            ("stair", "🪜 راه‌پله"),
        ]

    elif structure_type == "steel":
        members = [
            ("foundation", "🧱 فونداسیون"),
            ("column", "🏛 ستون فولادی"),
            ("beam", "📏 تیر فولادی"),
        ]

    elif structure_type == "composite":
        members = [
            ("foundation", "🧱 فونداسیون"),
            ("column", "🏛 ستون"),
            ("beam", "📏 تیر مرکب"),
            ("slab", "▰ سقف مرکب"),
        ]

    else:
        members = []

    keyboard = []

    for member_key, title in members:
        keyboard.append(
            [
                InlineKeyboardButton(
                    title,
                    callback_data=(
                        f"member:{member_key}:"
                        f"{structure_type}:"
                        f"{code_family}"
                        f"{project_part}"
                    ),
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ انتخاب آیین‌نامه",
                callback_data=(
                    f"calc:code_back:"
                    f"{structure_type}"
                    f"{project_part}"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# CALCULATION CALLBACK
# =========================================================

async def calculations_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle calculation navigation."""

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("calc:"):
        return

    parts = data.split(":")

    action = parts[1] if len(parts) > 1 else ""

    # -----------------------------------------------------
    # OPEN CALCULATIONS
    # -----------------------------------------------------

    if action == "open":
        project_id = parts[2] if len(parts) > 2 else None

        context.user_data["calculation_active"] = True

        if project_id:
            context.user_data["current_project_id"] = project_id

        await query.edit_message_text(
            "📐 <b>محاسبات سازه</b>\n\n"
            "نوع سازه را انتخاب کنید.",
            reply_markup=get_calculation_menu_keyboard(
                project_id
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # BACK
    # -----------------------------------------------------

    if action == "back":
        project_id = parts[2] if len(parts) > 2 else None

        await query.edit_message_text(
            "📐 <b>محاسبات سازه</b>\n\n"
            "نوع سازه را انتخاب کنید.",
            reply_markup=get_calculation_menu_keyboard(
                project_id
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # CODE BACK
    # -----------------------------------------------------

    if action == "code_back":

        structure_type = (
            parts[2]
            if len(parts) > 2
            else context.user_data.get(
                "structure_type",
                "concrete",
            )
        )

        project_id = (
            parts[3]
            if len(parts) > 3
            else context.user_data.get(
                "current_project_id"
            )
        )

        await query.edit_message_text(
            "📚 <b>انتخاب آیین‌نامه</b>\n\n"
            "آیین‌نامه طراحی را انتخاب کنید.",
            reply_markup=get_code_keyboard(
                structure_type,
                project_id,
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # STRUCTURE TYPE
    # -----------------------------------------------------

    if action in STRUCTURE_TYPES:

        structure_type = action

        project_id = (
            parts[2]
            if len(parts) > 2
            else context.user_data.get(
                "current_project_id"
            )
        )

        context.user_data["structure_type"] = structure_type

        if project_id:
            context.user_data["current_project_id"] = project_id

        await query.edit_message_text(
            f"{STRUCTURE_TYPES[structure_type]}\n\n"
            "📚 <b>انتخاب آیین‌نامه طراحی</b>\n\n"
            "آیین‌نامه موردنظر را انتخاب کنید.",
            reply_markup=get_code_keyboard(
                structure_type,
                project_id,
            ),
            parse_mode="HTML",
        )

        return


# =========================================================
# CODE CALLBACK
# =========================================================

async def code_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle design-code selection."""

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("code:"):
        return

    parts = data.split(":")

    if len(parts) < 3:
        return

    code_family = parts[1]
    structure_type = parts[2]

    project_id = (
        parts[3]
        if len(parts) > 3
        else context.user_data.get(
            "current_project_id"
        )
    )

    if code_family not in CODE_FAMILIES:
        await query.edit_message_text(
            "❌ آیین‌نامه انتخاب‌شده پشتیبانی نمی‌شود."
        )
        return

    if structure_type not in STRUCTURE_TYPES:
        await query.edit_message_text(
            "❌ نوع سازه نامعتبر است."
        )
        return

    context.user_data["code_family"] = code_family
    context.user_data["structure_type"] = structure_type

    if project_id:
        context.user_data["current_project_id"] = project_id

    await query.edit_message_text(
        f"{CODE_FAMILIES[code_family]}\n\n"
        f"{STRUCTURE_TYPES[structure_type]}\n\n"
        "📐 <b>انتخاب عضو سازه‌ای</b>\n\n"
        "عضوی را که می‌خواهید محاسبه کنید انتخاب کنید.",
        reply_markup=get_member_keyboard(
            structure_type,
            code_family,
            project_id,
        ),
        parse_mode="HTML",
    )


# =========================================================
# MEMBER CALLBACK
# =========================================================

async def member_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle structural-member selection."""

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("member:"):
        return

    parts = data.split(":")

    if len(parts) < 4:
        return

    member_type = parts[1]
    structure_type = parts[2]
    code_family = parts[3]

    project_id = (
        parts[4]
        if len(parts) > 4
        else context.user_data.get(
            "current_project_id"
        )
    )

    context.user_data["member_type"] = member_type
    context.user_data["structure_type"] = structure_type
    context.user_data["code_family"] = code_family

    if project_id:
        context.user_data["current_project_id"] = project_id

    member_name = MEMBERS.get(
        member_type,
        "عضو سازه‌ای",
    )

    # -----------------------------------------------------
    # ROUTING PLACEHOLDER
    # -----------------------------------------------------

    handler_messages = {
        "foundation": (
            "🧱 <b>فونداسیون</b>\n\n"
            "نوع فونداسیون را انتخاب کنید."
        ),
        "column": (
            "🏛 <b>ستون</b>\n\n"
            "نوع ستون و هندسه مقطع را انتخاب کنید."
        ),
        "beam": (
            "📏 <b>تیر</b>\n\n"
            "نوع تیر و مشخصات مقطع را انتخاب کنید."
        ),
        "slab": (
            "▰ <b>دال / سقف</b>\n\n"
            "نوع سقف را انتخاب کنید."
        ),
        "wall": (
            "🧱 <b>دیوار سازه‌ای</b>\n\n"
            "مشخصات دیوار را وارد کنید."
        ),
        "stair": (
            "🪜 <b>راه‌پله</b>\n\n"
            "نوع و مشخصات راه‌پله را انتخاب کنید."
        ),
    }

    message = handler_messages.get(
        member_type,
        f"📐 <b>{member_name}</b>\n\n"
        "ماژول این عضو در حال اتصال است.",
    )

    await query.edit_message_text(
        f"{message}\n\n"
        f"📚 آیین‌نامه: {CODE_FAMILIES.get(code_family, code_family)}\n"
        f"🏗 نوع سازه: {STRUCTURE_TYPES.get(structure_type, structure_type)}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ انتخاب عضو دیگر",
                        callback_data=(
                            f"code:{code_family}:"
                            f"{structure_type}"
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
                        "🏠 منوی اصلی",
                        callback_data="navigation:main",
                    )
                ],
            ]
        ),
        parse_mode="HTML",
    )


# =========================================================
# HANDLER EXPORTS
# =========================================================

__all__ = [
    "STRUCTURE_TYPES",
    "CODE_FAMILIES",
    "MEMBERS",
    "get_calculation_menu_keyboard",
    "get_code_keyboard",
    "get_member_keyboard",
    "calculations_callback",
    "code_callback",
    "member_callback",
]
