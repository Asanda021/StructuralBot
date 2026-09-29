"""
StructuralBot - Account Handler

User account, profile, usage and subscription information.

This module is intentionally presentation-focused.
Persistent billing/subscription logic belongs to billing/.
"""

from __future__ import annotations

from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes


# ---------------------------------------------------------
# DEFAULT ACCOUNT DATA
# ---------------------------------------------------------

DEFAULT_ACCOUNT = {
    "credits": 0,
    "plan": "free",
    "calculations_count": 0,
    "reports_count": 0,
    "projects_count": 0,
}


PLAN_NAMES = {
    "free": "رایگان",
    "basic": "Basic",
    "professional": "Professional",
    "business": "Business",
}


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def get_account_data(
    context: ContextTypes.DEFAULT_TYPE,
) -> dict[str, Any]:
    account = context.user_data.get("account")

    if not isinstance(account, dict):
        account = DEFAULT_ACCOUNT.copy()
        context.user_data["account"] = account

    for key, value in DEFAULT_ACCOUNT.items():
        account.setdefault(key, value)

    return account


def get_user_display_name(
    update: Update,
) -> str:
    user = update.effective_user

    if user is None:
        return "کاربر"

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return "کاربر"


def get_plan_name(
    plan: str,
) -> str:
    return PLAN_NAMES.get(
        plan,
        plan,
    )


# ---------------------------------------------------------
# KEYBOARDS
# ---------------------------------------------------------

def account_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👤 پروفایل",
                    callback_data="account:profile",
                ),
                InlineKeyboardButton(
                    "📊 وضعیت استفاده",
                    callback_data="account:usage",
                ),
            ],
            [
                InlineKeyboardButton(
                    "💳 اشتراک و اعتبار",
                    callback_data="account:subscription",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📋 پروژه‌های من",
                    callback_data="account:projects",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚙️ تنظیمات حساب",
                    callback_data="account:settings",
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


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📊 وضعیت استفاده",
                    callback_data="account:usage",
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 اشتراک",
                    callback_data="account:subscription",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 حساب کاربری",
                    callback_data="account:menu",
                )
            ],
        ]
    )


def subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💳 مشاهده پلن‌ها",
                    callback_data="account:plans",
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ افزایش اعتبار",
                    callback_data="account:credits",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 حساب کاربری",
                    callback_data="account:menu",
                )
            ],
        ]
    )


# ---------------------------------------------------------
# MAIN ACCOUNT MENU
# ---------------------------------------------------------

async def show_account_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    account = get_account_data(context)

    plan = get_plan_name(
        str(account.get("plan", "free"))
    )

    credits = account.get("credits", 0)

    text = (
        "👤 <b>حساب کاربری</b>\n\n"
        f"نام: <b>{get_user_display_name(update)}</b>\n"
        f"پلن: <b>{plan}</b>\n"
        f"اعتبار: <b>{credits}</b>\n\n"
        "از منوی زیر بخش موردنظر را انتخاب کنید."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=account_menu_keyboard(),
        )


# ---------------------------------------------------------
# PROFILE
# ---------------------------------------------------------

async def show_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    account = get_account_data(context)
    user = update.effective_user

    if user is None:
        user_id = "-"
        username = "-"
    else:
        user_id = user.id
        username = (
            f"@{user.username}"
            if user.username
            else "ثبت نشده"
        )

    text = (
        "👤 <b>پروفایل کاربر</b>\n\n"
        f"نام: <b>{get_user_display_name(update)}</b>\n"
        f"Username: <b>{username}</b>\n"
        f"Telegram ID: <code>{user_id}</code>\n\n"
        f"پلن: <b>{get_plan_name(str(account['plan']))}</b>\n"
        f"اعتبار: <b>{account['credits']}</b>"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=profile_keyboard(),
    )


# ---------------------------------------------------------
# USAGE
# ---------------------------------------------------------

async def show_usage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    account = get_account_data(context)

    text = (
        "📊 <b>وضعیت استفاده</b>\n\n"
        f"🧮 تعداد محاسبات: "
        f"<b>{account.get('calculations_count', 0)}</b>\n"
        f"📄 تعداد گزارش‌ها: "
        f"<b>{account.get('reports_count', 0)}</b>\n"
        f"🏗 تعداد پروژه‌ها: "
        f"<b>{account.get('projects_count', 0)}</b>\n"
        f"💳 اعتبار باقی‌مانده: "
        f"<b>{account.get('credits', 0)}</b>\n\n"
        "در نسخه نهایی این اطلاعات از Database و "
        "سیستم اشتراک خوانده خواهد شد."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "💳 اشتراک",
                        callback_data="account:subscription",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 حساب کاربری",
                        callback_data="account:menu",
                    )
                ],
            ]
        ),
    )


# ---------------------------------------------------------
# SUBSCRIPTION
# ---------------------------------------------------------

async def show_subscription(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    account = get_account_data(context)

    plan = get_plan_name(
        str(account.get("plan", "free"))
    )

    text = (
        "💳 <b>اشتراک و اعتبار</b>\n\n"
        f"پلن فعلی: <b>{plan}</b>\n"
        f"اعتبار: <b>{account.get('credits', 0)}</b>\n\n"
        "StructuralBot برای مدل تجاری آینده می‌تواند "
        "پلن‌های مختلف، اعتبار مصرفی، خروجی‌های پولی "
        "و حساب‌های سازمانی داشته باشد.\n\n"
        "پرداخت و فعال‌سازی واقعی در لایه billing "
        "پیاده‌سازی خواهد شد."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=subscription_keyboard(),
    )


# ---------------------------------------------------------
# PLANS
# ---------------------------------------------------------

async def show_plans(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "💳 <b>پلن‌های StructuralBot</b>\n\n"
        "🆓 <b>Free</b>\n"
        "برای استفاده پایه و آشنایی با سیستم.\n\n"
        "🔹 <b>Basic</b>\n"
        "برای استفاده شخصی و پروژه‌های محدود.\n\n"
        "🔹 <b>Professional</b>\n"
        "برای استفاده حرفه‌ای، گزارش‌ها و قابلیت‌های بیشتر.\n\n"
        "🔹 <b>Business</b>\n"
        "برای تیم‌ها، شرکت‌ها و استفاده سازمانی.\n\n"
        "⚙️ جزئیات قیمت‌گذاری، محدودیت‌ها و پرداخت "
        "در billing تعریف خواهند شد."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➕ افزایش اعتبار",
                        callback_data="account:credits",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 اشتراک",
                        callback_data="account:subscription",
                    )
                ],
            ]
        ),
    )


# ---------------------------------------------------------
# CREDITS
# ---------------------------------------------------------

async def show_credits(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    account = get_account_data(context)

    text = (
        "➕ <b>اعتبار</b>\n\n"
        f"اعتبار فعلی شما: <b>{account.get('credits', 0)}</b>\n\n"
        "در مدل نهایی، اعتبار می‌تواند برای مواردی مانند:\n"
        "• محاسبات پیشرفته\n"
        "• تولید PDF / Excel\n"
        "• قابلیت‌های AI\n"
        "• امکانات حرفه‌ای\n"
        "مصرف شود.\n\n"
        "اتصال به درگاه پرداخت بعداً در billing انجام می‌شود."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "💳 پلن‌ها",
                        callback_data="account:plans",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 اشتراک",
                        callback_data="account:subscription",
                    )
                ],
            ]
        ),
    )


# ---------------------------------------------------------
# PROJECTS
# ---------------------------------------------------------

async def show_account_projects(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    projects = context.user_data.get(
        "projects",
        [],
    )

    if not isinstance(projects, list):
        projects = []

    if projects:
        lines = [
            "📋 <b>پروژه‌های من</b>",
            "",
        ]

        for index, project in enumerate(
            projects[:20],
            start=1,
        ):
            if isinstance(project, dict):
                name = project.get(
                    "name",
                    f"پروژه {index}",
                )
            else:
                name = getattr(
                    project,
                    "name",
                    f"پروژه {index}",
                )

            lines.append(
                f"{index}. {name}"
            )

        text = "\n".join(lines)

    else:
        text = (
            "📋 <b>پروژه‌های من</b>\n\n"
            "در این نشست پروژه‌ای ثبت نشده است.\n\n"
            "مدیریت دائمی پروژه‌ها از طریق Database "
            "انجام خواهد شد."
        )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🏗 مدیریت پروژه‌ها",
                        callback_data="menu:projects",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 حساب کاربری",
                        callback_data="account:menu",
                    )
                ],
            ]
        ),
    )


# ---------------------------------------------------------
# ACCOUNT SETTINGS
# ---------------------------------------------------------

async def show_account_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "⚙️ <b>تنظیمات حساب</b>\n\n"
        "تنظیمات اصلی حساب در بخش Settings مدیریت می‌شوند.\n\n"
        "موارد قابل مدیریت:\n"
        "• زبان\n"
        "• سیستم واحد\n"
        "• تنظیمات اعلان‌ها\n"
        "• تنظیمات گزارش\n"
        "• تنظیمات AI"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⚙️ تنظیمات اصلی",
                        callback_data="menu:settings",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 حساب کاربری",
                        callback_data="account:menu",
                    )
                ],
            ]
        ),
    )


# ---------------------------------------------------------
# CALLBACK ROUTER
# ---------------------------------------------------------

async def account_callback(
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

    if data == "account:menu":
        await show_account_menu(
            update,
            context,
        )
        return

    # -----------------------------------------------------
    # PROFILE
    # -----------------------------------------------------

    if data == "account:profile":
        await show_profile(
            update,
            context,
        )
        return

    # -----------------------------------------------------
    # USAGE
    # -----------------------------------------------------

    if data == "account:usage":
        await show_usage(
            update,
            context,
        )
        return

    # -----------------------------------------------------
    # SUBSCRIPTION
    # -----------------------------------------------------

    if data == "account:subscription":
        await show_subscription(
            update,
            context,
        )
        return

    if data == "account:plans":
        await show_plans(
            update,
            context,
        )
        return

    if data == "account:credits":
        await show_credits(
            update,
            context,
        )
        return

    # -----------------------------------------------------
    # PROJECTS
    # -----------------------------------------------------

    if data == "account:projects":
        await show_account_projects(
            update,
            context,
        )
        return

    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    if data == "account:settings":
        await show_account_settings(
            update,
            context,
        )
        return


# ---------------------------------------------------------
# HANDLER FACTORY
# ---------------------------------------------------------

def get_account_callback_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(
        account_callback,
        pattern=r"^account(?:[:_]|$)",
    )


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

__all__ = [
    "DEFAULT_ACCOUNT",
    "PLAN_NAMES",
    "show_account_menu",
    "show_profile",
    "show_usage",
    "show_subscription",
    "show_plans",
    "show_credits",
    "show_account_projects",
    "show_account_settings",
    "account_callback",
    "get_account_callback_handler",
]
