"""Telegram UI for selecting a project's country and design-code pack."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from codes.catalog import CODE_PACKS, by_country, get_code_pack, is_implemented

try:
    from database import update_project_code
except ImportError:
    update_project_code = None


def _project_id(context: ContextTypes.DEFAULT_TYPE):
    return context.user_data.get("current_project_id")


def _country_keyboard():
    countries = sorted({p.country for p in CODE_PACKS})
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(c, callback_data=f"codecountry:{c}")]
         for c in countries] +
        [[InlineKeyboardButton("⬅️ بازگشت", callback_data="project:list")]]
    )


async def show_code_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q:
        await q.answer()
        await q.edit_message_text(
            "📚 <b>کشور و آیین‌نامه پروژه</b>\n\n"
            "ابتدا کشور/نظام مقرراتی را انتخاب کنید.",
            reply_markup=_country_keyboard(),
            parse_mode="HTML",
        )


async def code_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    await q.answer()
    data = q.data or ""

    if data == "codes:list":
        await show_code_countries(update, context)
        return

    if data.startswith("codecountry:"):
        country = data.split(":", 1)[1]
        packs = by_country(country)
        keyboard = []
        for p in packs:
            status = "✅" if p.status == "IMPLEMENTED" else "🟡"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {p.title} [{p.edition}]",
                    callback_data=f"codeset:{p.code_id}",
                )
            ])
        keyboard.append([InlineKeyboardButton("⬅️ کشورها", callback_data="codes:list")])
        await q.edit_message_text(
            f"📚 <b>{country}</b>\n\n"
            "🟢 = موتور قطعی موجود\n"
            "🟡 = کاتالوگ ثبت شده؛ قبل از استفاده محاسباتی باید Adapter و تست عددی تکمیل شود.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    if data.startswith("codeset:"):
        code_id = data.split(":", 1)[1]
        pack = get_code_pack(code_id)
        project_id = _project_id(context)
        if not pack or not project_id:
            await q.edit_message_text("❌ پروژه یا آیین‌نامه پیدا نشد.")
            return

        if update_project_code is None:
            await q.edit_message_text("❌ سرویس ذخیره آیین‌نامه در دسترس نیست.")
            return

        update_project_code(project_id, pack.code_id, pack.edition)
        context.user_data["current_code_id"] = pack.code_id
        context.user_data["current_code_edition"] = pack.edition

        if is_implemented(pack.code_id):
            msg = "✅ آیین‌نامه انتخاب شد و Adapter محاسباتی آن در دسترس است."
        else:
            msg = (
                "🟡 آیین‌نامه ثبت و به پروژه متصل شد، اما Adapter محاسباتی "
                "این مجموعه هنوز فعال نیست؛ ربات اجازه نمی‌دهد نتیجه را "
                "به‌عنوان طراحی آیین‌نامه‌ای قطعی اعلام کند."
            )

        await q.edit_message_text(
            f"📚 <b>{pack.title}</b>\n"
            f"ویرایش: {pack.edition}\n"
            f"کشور: {pack.country}\n\n{msg}",
            parse_mode="HTML",
        )


__all__ = ["show_code_countries", "code_callback"]
