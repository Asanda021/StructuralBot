"""
StructuralBot - AI Assistant Handler

Telegram interface for the future engineering AI assistant.

Important:
- This module does NOT perform structural design by itself.
- AI must use validated project/calculation data.
- Final engineering checks remain under the selected design code.
"""

from __future__ import annotations

from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes


# ---------------------------------------------------------
# AI MODES
# ---------------------------------------------------------

AI_MODES = {
    "assistant": "دستیار مهندسی",
    "explain": "توضیح محاسبات",
    "review": "بازبینی نتیجه",
    "project": "تحلیل پروژه",
    "report": "کمک در گزارش",
}


# ---------------------------------------------------------
# KEYBOARDS
# ---------------------------------------------------------

def ai_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🤖 دستیار مهندسی",
                    callback_data="ai:assistant",
                )
            ],
            [
                InlineKeyboardButton(
                    "📐 توضیح محاسبات",
                    callback_data="ai:explain",
                ),
                InlineKeyboardButton(
                    "🔎 بازبینی نتیجه",
                    callback_data="ai:review",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🏗 تحلیل پروژه",
                    callback_data="ai:project",
                ),
                InlineKeyboardButton(
                    "📊 کمک در گزارش",
                    callback_data="ai:report",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚠️ حدود استفاده",
                    callback_data="ai:limits",
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


def ai_chat_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 شروع گفت‌وگوی جدید",
                    callback_data="ai:new",
                )
            ],
            [
                InlineKeyboardButton(
                    "📐 توضیح محاسبات",
                    callback_data="ai:explain",
                ),
                InlineKeyboardButton(
                    "🔎 بازبینی",
                    callback_data="ai:review",
                ),
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
# SESSION HELPERS
# ---------------------------------------------------------

def clear_ai_session(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    context.user_data.pop("ai_mode", None)
    context.user_data.pop("ai_waiting_message", None)


def get_current_project(
    context: ContextTypes.DEFAULT_TYPE,
) -> Any:
    return context.user_data.get("current_project")


def get_ai_context(
    context: ContextTypes.DEFAULT_TYPE,
) -> dict[str, Any]:
    """
    Return a small structured context for the future AI service.

    This deliberately avoids sending arbitrary user_data to an
    external AI provider.
    """

    project = get_current_project(context)

    result: dict[str, Any] = {
        "project_exists": project is not None,
        "project_name": None,
        "language": context.user_data.get("language"),
        "unit_system": context.user_data.get("unit_system"),
        "design_code": context.user_data.get("design_code"),
        "structure_type": context.user_data.get("structure_type"),
    }

    if project is not None:
        result["project_name"] = getattr(
            project,
            "name",
            None,
        )

    return result


# ---------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------

async def show_ai_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    clear_ai_session(context)

    text = (
        "🤖 <b>دستیار هوشمند مهندسی</b>\n\n"
        "دستیار هوشمند StructuralBot برای کمک در کارهای "
        "مهندسی، توضیح نتایج و بررسی داده‌های پروژه طراحی می‌شود.\n\n"
        "قابلیت‌های هدف:\n"
        "• توضیح نتایج محاسبات\n"
        "• پاسخ به پرسش‌های فنی\n"
        "• بررسی ورودی‌ها و خطاهای احتمالی\n"
        "• کمک در تفسیر گزارش‌ها\n"
        "• تحلیل ساختار داده‌های پروژه\n"
        "• راهنمای استفاده از ربات\n\n"
        "⚠️ خروجی AI نباید بدون کنترل مهندسی و مقررات "
        "به‌عنوان تأیید نهایی طراحی استفاده شود."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=ai_menu_keyboard(),
        )


# ---------------------------------------------------------
# AI MODES
# ---------------------------------------------------------

async def show_ai_mode(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    mode: str,
) -> None:
    if mode not in AI_MODES:
        await update.callback_query.edit_message_text(
            "❌ حالت دستیار نامعتبر است.",
            reply_markup=ai_menu_keyboard(),
        )
        return

    context.user_data["ai_mode"] = mode
    context.user_data["ai_waiting_message"] = True

    mode_texts = {
        "assistant": (
            "سؤال فنی یا اجرایی خود را بنویسید."
        ),
        "explain": (
            "نتیجه یا بخش محاسباتی موردنظر را مشخص کنید "
            "تا توضیح داده شود."
        ),
        "review": (
            "اطلاعات یا نتیجه محاسبه‌ای که می‌خواهید بررسی شود "
            "را ارسال کنید."
        ),
        "project": (
            "سؤال خود درباره پروژه جاری را ارسال کنید."
        ),
        "report": (
            "بگویید در تهیه یا تفسیر کدام گزارش به کمک نیاز دارید."
        ),
    }

    description = mode_texts.get(
        mode,
        "درخواست خود را ارسال کنید.",
    )

    text = (
        f"🤖 <b>{AI_MODES[mode]}</b>\n\n"
        f"{description}\n\n"
        "نمونه:\n"
        "<code>چرا مقدار آرماتور این تیر زیاد شده؟</code>\n\n"
        "برای بازگشت از دکمه زیر استفاده کنید."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="ai:menu",
                    )
                ]
            ]
        ),
    )


# ---------------------------------------------------------
# LIMITS / SAFETY
# ---------------------------------------------------------

async def show_ai_limits(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "⚠️ <b>حدود استفاده از دستیار هوشمند</b>\n\n"
        "AI در StructuralBot باید نقش «دستیار» داشته باشد، "
        "نه جایگزین موتور محاسبات و مقررات طراحی.\n\n"
        "AI می‌تواند:\n"
        "• توضیح دهد\n"
        "• خلاصه کند\n"
        "• خطاهای ورودی را شناسایی کند\n"
        "• نتایج را تفسیر کند\n"
        "• پیشنهادهای بررسی ارائه دهد\n\n"
        "اما نتیجه نهایی طراحی باید از موتور محاسباتی "
        "و Design Code انتخاب‌شده عبور کند.\n\n"
        "همچنین AI نباید عدد مهندسی را بدون مشخص بودن "
        "واحد، عضو، مصالح، آیین‌نامه و شرایط مسئله "
        "به‌عنوان نتیجه قطعی ارائه کند."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🤖 دستیار",
                        callback_data="ai:assistant",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="ai:menu",
                    )
                ],
            ]
        ),
    )


# ---------------------------------------------------------
# NEW SESSION
# ---------------------------------------------------------

async def start_new_ai_session(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    clear_ai_session(context)

    text = (
        "🤖 <b>گفت‌وگوی جدید</b>\n\n"
        "حالت دستیار را انتخاب کنید:"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=ai_menu_keyboard(),
    )


# ---------------------------------------------------------
# AI RESPONSE PLACEHOLDER
# ---------------------------------------------------------

def build_placeholder_response(
    message: str,
    mode: str,
    context_data: dict[str, Any],
) -> str:
    """
    Temporary response until an AI provider/service is connected.

    The real implementation should call an AI service through a
    dedicated ai/service.py layer rather than putting provider
    logic inside this Telegram handler.
    """

    mode_title = AI_MODES.get(
        mode,
        AI_MODES["assistant"],
    )

    project_name = context_data.get(
        "project_name"
    )

    project_line = (
        f"پروژه جاری: {project_name}"
        if project_name
        else "پروژه جاری: انتخاب نشده"
    )

    return (
        "🤖 <b>StructuralBot AI</b>\n\n"
        f"حالت: {mode_title}\n"
        f"{project_line}\n\n"
        "پیام شما دریافت شد:\n"
        f"<i>{message[:500]}</i>\n\n"
        "🔧 موتور AI هنوز به این بخش متصل نشده است.\n\n"
        "در نسخه نهایی، پیام پس از ساخت Context مهندسی "
        "به سرویس AI ارسال می‌شود و پاسخ آن با اطلاعات "
        "پروژه، عضو، واحد و Design Code مرتبط خواهد شد.\n\n"
        "⚠️ پاسخ AI به‌تنهایی تأیید طراحی محسوب نمی‌شود."
    )


# ---------------------------------------------------------
# MESSAGE HANDLER
# ---------------------------------------------------------

async def ai_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if update.message is None:
        return

    if not context.user_data.get(
        "ai_waiting_message"
    ):
        return

    message = (update.message.text or "").strip()

    if not message:
        await update.message.reply_text(
            "❌ لطفاً پیام خود را وارد کنید."
        )
        return

    mode = context.user_data.get(
        "ai_mode",
        "assistant",
    )

    context_data = get_ai_context(context)

    response = build_placeholder_response(
        message=message,
        mode=mode,
        context_data=context_data,
    )

    context.user_data["ai_waiting_message"] = False

    await update.message.reply_text(
        response,
        parse_mode="HTML",
        reply_markup=ai_chat_keyboard(),
    )


# ---------------------------------------------------------
# CALLBACK ROUTER
# ---------------------------------------------------------

async def ai_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    # -----------------------------------------------------
    # MENU
    # -----------------------------------------------------

    if data == "ai:menu":
        await show_ai_menu(
            update,
            context,
        )
        return

    # -----------------------------------------------------
    # NEW
    # -----------------------------------------------------

    if data == "ai:new":
        await start_new_ai_session(
            update,
            context,
        )
        return

    # -----------------------------------------------------
    # LIMITS
    # -----------------------------------------------------

    if data == "ai:limits":
        await show_ai_limits(
            update,
            context,
        )
        return

    # -----------------------------------------------------
    # MODE
    # -----------------------------------------------------

    if data.startswith("ai:"):
        mode = data.split(":", 1)[1]

        if mode in AI_MODES:
            await show_ai_mode(
                update,
                context,
                mode,
            )
            return


# ---------------------------------------------------------
# HANDLER FACTORIES
# ---------------------------------------------------------

def get_ai_callback_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(
        ai_callback,
        pattern=r"^ai(?:[:_]|$)",
    )


def get_ai_message_handler():
    return ai_message


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

__all__ = [
    "AI_MODES",
    "show_ai_menu",
    "ai_callback",
    "ai_message",
    "get_ai_callback_handler",
    "get_ai_message_handler",
]
