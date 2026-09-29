"""
StructuralBot - Reports Handler

Telegram handler for project and calculation reports.

The report layer is presentation-only.
Engineering calculations remain in core/ and codes/.
"""

from __future__ import annotations

from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes


# ---------------------------------------------------------
# REPORT TYPES
# ---------------------------------------------------------

REPORT_TYPES = {
    "project": "گزارش پروژه",
    "calculation": "گزارش محاسبات",
    "rebar": "گزارش میلگرد",
    "bbs": "گزارش BBS",
    "cutlist": "گزارش Cut List",
    "quantities": "گزارش مصالح",
}


REPORT_FORMATS = {
    "telegram": "Telegram",
    "pdf": "PDF",
    "excel": "Excel",
}


# ---------------------------------------------------------
# KEYBOARDS
# ---------------------------------------------------------

def reports_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🏗 گزارش پروژه",
                    callback_data="report:project",
                ),
                InlineKeyboardButton(
                    "📐 گزارش محاسبات",
                    callback_data="report:calculation",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔩 گزارش میلگرد",
                    callback_data="report:rebar",
                ),
                InlineKeyboardButton(
                    "📋 گزارش BBS",
                    callback_data="report:bbs",
                ),
            ],
            [
                InlineKeyboardButton(
                    "✂️ گزارش Cut List",
                    callback_data="report:cutlist",
                ),
                InlineKeyboardButton(
                    "🧮 گزارش مصالح",
                    callback_data="report:quantities",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚙️ تنظیمات گزارش",
                    callback_data="report:settings",
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


def format_keyboard(
    report_type: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📱 نمایش در تلگرام",
                    callback_data=f"report_format:telegram:{report_type}",
                )
            ],
            [
                InlineKeyboardButton(
                    "📄 خروجی PDF",
                    callback_data=f"report_format:pdf:{report_type}",
                ),
                InlineKeyboardButton(
                    "📊 خروجی Excel",
                    callback_data=f"report_format:excel:{report_type}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔙 انتخاب گزارش",
                    callback_data="report:menu",
                )
            ],
        ]
    )


def report_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📏 واحدها",
                    callback_data="report_setting:units",
                ),
                InlineKeyboardButton(
                    "🔢 اعداد",
                    callback_data="report_setting:numbers",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📑 جزئیات",
                    callback_data="report_setting:details",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="report:menu",
                )
            ],
        ]
    )


# ---------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------

async def show_reports_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "📊 <b>گزارش‌ها</b>\n\n"
        "نوع گزارش موردنظر را انتخاب کنید.\n\n"
        "گزارش‌ها در معماری نهایی از یک منبع داده مشترک "
        "استفاده می‌کنند تا خروجی Telegram، PDF و Excel "
        "با یکدیگر اختلاف نداشته باشند."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=reports_menu_keyboard(),
        )


# ---------------------------------------------------------
# REPORT SELECTION
# ---------------------------------------------------------

async def show_report_type(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    report_type: str,
) -> None:
    title = REPORT_TYPES.get(report_type)

    if title is None:
        await update.callback_query.edit_message_text(
            "❌ نوع گزارش نامعتبر است.",
            reply_markup=reports_menu_keyboard(),
        )
        return

    context.user_data["selected_report_type"] = report_type

    text = (
        f"📊 <b>{title}</b>\n\n"
        "فرمت خروجی را انتخاب کنید:"
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=format_keyboard(report_type),
    )


# ---------------------------------------------------------
# TELEGRAM REPORT
# ---------------------------------------------------------

def build_telegram_report(
    report_type: str,
    context: ContextTypes.DEFAULT_TYPE,
) -> str:
    title = REPORT_TYPES.get(
        report_type,
        "گزارش",
    )

    project = context.user_data.get(
        "current_project"
    )

    project_name = "پروژه جاری"

    if project is not None:
        project_name = getattr(
            project,
            "name",
            None,
        ) or project_name

    lines = [
        f"📊 <b>{title}</b>",
        "",
        f"🏗 پروژه: <b>{project_name}</b>",
        "",
    ]

    if report_type == "project":
        lines.extend(
            [
                "این گزارش شامل اطلاعات کلی پروژه،",
                "اعضا، طبقات، محاسبات و خروجی‌های مرتبط خواهد بود.",
            ]
        )

    elif report_type == "calculation":
        lines.extend(
            [
                "این گزارش شامل نتایج محاسبات عضو،",
                "کنترل‌ها، فرضیات و وضعیت بررسی‌ها خواهد بود.",
            ]
        )

    elif report_type == "rebar":
        lines.extend(
            [
                "این گزارش شامل مشخصات آرماتور،",
                "قطرها، تعداد، طول و وزن میلگردها خواهد بود.",
            ]
        )

    elif report_type == "bbs":
        lines.extend(
            [
                "این گزارش شامل Bar Bending Schedule،",
                "شکل میلگرد، ابعاد، تعداد و طول قطعات خواهد بود.",
            ]
        )

    elif report_type == "cutlist":
        lines.extend(
            [
                "این گزارش شامل برنامه برش میلگرد،",
                "شاخه‌های مصرفی، پرت و باقی‌مانده‌ها خواهد بود.",
            ]
        )

    elif report_type == "quantities":
        lines.extend(
            [
                "این گزارش شامل Quantity Takeoff",
                "و جمع مصالح پروژه خواهد بود.",
            ]
        )

    lines.extend(
        [
            "",
            "⚠️ این صفحه فعلاً ساختار گزارش را نمایش می‌دهد.",
            "تولید نهایی گزارش باید از داده واقعی موتور محاسبات انجام شود.",
        ]
    )

    return "\n".join(lines)


async def show_telegram_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    report_type: str,
) -> None:
    text = build_telegram_report(
        report_type,
        context,
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📄 PDF",
                        callback_data=f"report_format:pdf:{report_type}",
                    ),
                    InlineKeyboardButton(
                        "📊 Excel",
                        callback_data=f"report_format:excel:{report_type}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔄 گزارش دیگر",
                        callback_data="report:menu",
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
# PDF / EXCEL
# ---------------------------------------------------------

async def show_export_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    report_type: str,
    export_format: str,
) -> None:
    title = REPORT_TYPES.get(
        report_type,
        "گزارش",
    )

    format_title = REPORT_FORMATS.get(
        export_format,
        export_format,
    )

    if export_format == "pdf":
        text = (
            f"📄 <b>{title} — PDF</b>\n\n"
            "ساختار خروجی PDF آماده اتصال به موتور گزارش‌گیری است.\n\n"
            "در نسخه نهایی:\n"
            "• مشخصات پروژه\n"
            "• اطلاعات عضو\n"
            "• فرضیات و ورودی‌ها\n"
            "• نتایج محاسبات\n"
            "• کنترل‌های طراحی\n"
            "• جدول میلگرد\n"
            "• BBS / Cut List\n"
            "• جمع مصالح\n"
            "در فایل قرار می‌گیرد."
        )

    elif export_format == "excel":
        text = (
            f"📊 <b>{title} — Excel</b>\n\n"
            "ساختار خروجی Excel آماده اتصال به موتور گزارش‌گیری است.\n\n"
            "در نسخه نهایی می‌توان شیت‌های جداگانه برای:\n"
            "• Project\n"
            "• Members\n"
            "• Calculations\n"
            "• Reinforcement\n"
            "• BBS\n"
            "• Cut List\n"
            "• Quantities\n"
            "ایجاد کرد."
        )

    else:
        text = (
            f"📊 <b>{title}</b>\n\n"
            f"فرمت انتخاب‌شده: {format_title}"
        )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت به گزارش",
                        callback_data=f"report:{report_type}",
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
# SETTINGS
# ---------------------------------------------------------

async def show_report_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    text = (
        "⚙️ <b>تنظیمات گزارش</b>\n\n"
        "تنظیمات قابل توسعه:\n"
        "• سیستم واحد\n"
        "• تعداد اعشار\n"
        "• نمایش فرضیات\n"
        "• نمایش جزئیات کنترل‌ها\n"
        "• نمایش وزن میلگرد\n"
        "• نمایش پرت Cut List\n"
        "• اطلاعات پروژه و کارفرما\n\n"
        "تنظیمات در نسخه نهایی در سطح کاربر و پروژه "
        "قابل ذخیره خواهند بود."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=report_settings_keyboard(),
    )


async def show_report_setting(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    setting: str,
) -> None:
    titles = {
        "units": "📏 واحدها",
        "numbers": "🔢 اعداد",
        "details": "📑 جزئیات",
    }

    title = titles.get(setting, "تنظیمات")

    text = (
        f"{title}\n\n"
        "این بخش برای اتصال به UserSettings و "
        "تنظیمات پروژه در نسخه بعدی آماده شده است."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔙 تنظیمات گزارش",
                        callback_data="report:settings",
                    )
                ]
            ]
        ),
    )


# ---------------------------------------------------------
# CALLBACK ROUTER
# ---------------------------------------------------------

async def reports_callback(
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

    if data == "report:menu":
        await show_reports_menu(
            update,
            context,
        )
        return

    # -----------------------------------------------------
    # REPORT TYPES
    # -----------------------------------------------------

    if data.startswith("report:"):
        report_type = data.split(":", 1)[1]

        if report_type == "menu":
            await show_reports_menu(
                update,
                context,
            )
            return

        if report_type == "settings":
            await show_report_settings(
                update,
                context,
            )
            return

        await show_report_type(
            update,
            context,
            report_type,
        )
        return

    # -----------------------------------------------------
    # REPORT FORMAT
    # -----------------------------------------------------

    if data.startswith("report_format:"):
        parts = data.split(":")

        if len(parts) != 3:
            await query.edit_message_text(
                "❌ درخواست گزارش نامعتبر است.",
                reply_markup=reports_menu_keyboard(),
            )
            return

        export_format = parts[1]
        report_type = parts[2]

        if export_format == "telegram":
            await show_telegram_report(
                update,
                context,
                report_type,
            )
            return

        await show_export_message(
            update,
            context,
            report_type,
            export_format,
        )
        return

    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    if data.startswith("report_setting:"):
        setting = data.split(":", 1)[1]

        await show_report_setting(
            update,
            context,
            setting,
        )
        return


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

def get_reports_callback_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(
        reports_callback,
        pattern=r"^report(?:[:_]|$)",
    )


__all__ = [
    "REPORT_TYPES",
    "REPORT_FORMATS",
    "show_reports_menu",
    "reports_callback",
    "get_reports_callback_handler",
]
