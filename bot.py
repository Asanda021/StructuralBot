import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    ContextTypes, MessageHandler, filters,
)

from app.db import Database
from app.engine import (
    foundation_calc, column_calc, beam_calc, slab_calc,
    concrete_for_dimensions, rebar_equivalent, bbs_cutlist,
)
from app.keyboards import main_menu, calc_menu, rebar_menu, back_menu

TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DATABASE_PATH", "/tmp/structuralbot.db")
PORT = int(os.getenv("PORT", "10000"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | StructuralBot | %(levelname)s | %(message)s",
)
log = logging.getLogger("StructuralBot")
db = Database(DB_PATH)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            body = b"StructuralBot OK"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_):
        pass


def health_server():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler)
    log.info("Health server listening on port %s", PORT)
    server.serve_forever()


def clean_number(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def parse_numbers(text, count):
    values = [float(x.strip()) for x in text.replace("،", ",").split(",")]
    if len(values) != count or any(v <= 0 for v in values):
        raise ValueError
    return values


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.first_name or "")
    context.user_data.clear()
    await update.message.reply_text(
        "🏗 <b>StructuralBot</b>\n\n"
        "نسخه سبک محاسبات و برآورد سازه آماده است.\n"
        "از منوی زیر شروع کن.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.callback_query:
        q = update.callback_query
        await q.edit_message_text("🏠 <b>منوی اصلی</b>", parse_mode="HTML", reply_markup=main_menu())
    else:
        await update.message.reply_text("🏠 منوی اصلی", reply_markup=main_menu())


def result_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ویرایش ورودی‌ها", callback_data="edit_last")],
        [InlineKeyboardButton("🔁 محاسبه مجدد", callback_data="recalc_last"),
         InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")],
    ])


def wizard_keyboard(options, custom_label="✏️ ورود دستی"):
    rows = []
    row = []
    for label, value in options:
        row.append(InlineKeyboardButton(label, callback_data=f"wizval|{value}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(custom_label, callback_data="wizcustom")])
    rows.append([InlineKeyboardButton("❌ لغو", callback_data="home")])
    return InlineKeyboardMarkup(rows)


def wizard_prompt(title, labels, index, options=None, manual=False):
    label = labels[index]
    text = (
        f"📐 <b>{title}</b>\\n\\n"
        f"مرحله {index + 1} از {len(labels)}\\n"
        f"<b>{label}</b> را انتخاب کن.\\n\\n"
        "برای سرعت، یکی از گزینه‌ها را بزن؛ یا «ورود دستی» را انتخاب کن و فقط همین مقدار را تایپ کن."
    )
    markup = wizard_keyboard(options or []) if not manual else InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ برگشت", callback_data=f"wizback|{max(index-1,0)}")],
        [InlineKeyboardButton("❌ لغو", callback_data="home")],
    ])
    return text, markup


def begin_wizard(context, kind):
    specs = {
        "foundation": ("پی", ["عرض پی (m)", "طول پی (m)", "ضخامت پی (m)"]),
        "column": ("ستون", ["عرض ستون (m)", "عمق ستون (m)", "ارتفاع ستون (m)"]),
        "beam": ("تیر", ["عرض تیر (m)", "ارتفاع تیر (m)", "طول تیر (m)"]),
        "slab": ("سقف", ["ضخامت سقف (m)", "طول سقف (m)", "عرض سقف (m)"]),
        "quantity": ("برآورد بتن", ["بعد اول (m)", "بعد دوم (m)", "بعد سوم (m)"]),
        "rebar_eq": ("معادل‌سازی میلگرد", ["قطر اول (mm)", "قطر دوم (mm)"]),
        "bbs": ("BBS / Cut List", ["قطر میلگرد (mm)", "تعداد میلگرد", "طول هر قطعه (m)"]),
    }
    title, labels = specs[kind]
    context.user_data.clear()
    context.user_data.update({"wizard": kind, "wizard_index": 0, "wizard_values": []})
    return title, labels


def wizard_options(kind, index):
    common = {
        "foundation": [
            [("0.30", "0.30"), ("0.40", "0.40"), ("0.50", "0.50")],
            [("1.00", "1.00"), ("1.50", "1.50"), ("2.00", "2.00")],
            [("0.30", "0.30"), ("0.40", "0.40"), ("0.50", "0.50")],
        ],
        "column": [
            [("0.30", "0.30"), ("0.40", "0.40"), ("0.50", "0.50")],
            [("0.30", "0.30"), ("0.40", "0.40"), ("0.50", "0.50")],
            [("3.00", "3.00"), ("3.50", "3.50"), ("4.00", "4.00")],
        ],
        "beam": [
            [("0.25", "0.25"), ("0.30", "0.30"), ("0.40", "0.40")],
            [("0.40", "0.40"), ("0.50", "0.50"), ("0.60", "0.60")],
            [("4.00", "4.00"), ("5.00", "5.00"), ("6.00", "6.00")],
        ],
        "slab": [
            [("0.12", "0.12"), ("0.15", "0.15"), ("0.20", "0.20")],
            [("4.00", "4.00"), ("5.00", "5.00"), ("6.00", "6.00")],
            [("3.00", "3.00"), ("4.00", "4.00"), ("5.00", "5.00")],
        ],
        "quantity": [
            [("0.15", "0.15"), ("0.20", "0.20"), ("0.30", "0.30")],
            [("4.00", "4.00"), ("5.00", "5.00"), ("6.00", "6.00")],
            [("3.00", "3.00"), ("4.00", "4.00"), ("5.00", "5.00")],
        ],
        "rebar_eq": [
            [("12", "12"), ("14", "14"), ("16", "16"), ("18", "18"), ("20", "20"), ("22", "22"), ("25", "25"), ("28", "28"), ("32", "32")],
            [("12", "12"), ("14", "14"), ("16", "16"), ("18", "18"), ("20", "20"), ("22", "22"), ("25", "25"), ("28", "28"), ("32", "32")],
        ],
        "bbs": [
            [("12", "12"), ("14", "14"), ("16", "16"), ("18", "18"), ("20", "20"), ("22", "22"), ("25", "25"), ("28", "28"), ("32", "32")],
            [("5", "5"), ("10", "10"), ("15", "15"), ("20", "20"), ("25", "25"), ("30", "30")],
            [("3", "3"), ("4", "4"), ("5", "5"), ("6", "6"), ("8", "8"), ("10", "10"), ("12", "12")],
        ],
    }
    return common[kind][index]


def wizard_labels(kind):
    return {
        "foundation": ["عرض پی (m)", "طول پی (m)", "ضخامت پی (m)"],
        "column": ["عرض ستون (m)", "عمق ستون (m)", "ارتفاع ستون (m)"],
        "beam": ["عرض تیر (m)", "ارتفاع تیر (m)", "طول تیر (m)"],
        "slab": ["ضخامت سقف (m)", "طول سقف (m)", "عرض سقف (m)"],
        "quantity": ["بعد اول (m)", "بعد دوم (m)", "بعد سوم (m)"],
        "rebar_eq": ["قطر اول (mm)", "قطر دوم (mm)"],
        "bbs": ["قطر میلگرد (mm)", "تعداد میلگرد", "طول هر قطعه (m)"],
    }[kind]


def wizard_title(kind):
    return {
        "foundation": "پی",
        "column": "ستون",
        "beam": "تیر",
        "slab": "سقف",
        "quantity": "برآورد بتن",
        "rebar_eq": "معادل‌سازی میلگرد",
        "bbs": "BBS / Cut List",
    }[kind]


async def show_wizard_step(target, context, index=None, manual=False):
    kind = context.user_data["wizard"]
    if index is not None:
        context.user_data["wizard_index"] = index
    index = context.user_data["wizard_index"]
    labels = wizard_labels(kind)
    text, markup = wizard_prompt(
        wizard_title(kind), labels, index,
        wizard_options(kind, index) if not manual else None,
        manual=manual,
    )
    if hasattr(target, "edit_message_text"):
        await target.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await target.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def finish_wizard(update, context):
    kind = context.user_data["wizard"]
    values = context.user_data["wizard_values"]
    uid = update.effective_user.id
    if kind == "foundation":
        title, result = "پی", foundation_calc(*values)
    elif kind == "column":
        title, result = "ستون", column_calc(*values)
    elif kind == "beam":
        title, result = "تیر", beam_calc(*values)
    elif kind == "slab":
        title, result = "سقف", slab_calc(*values)
    elif kind == "quantity":
        title, result = "برآورد بتن", concrete_for_dimensions(*values)
    elif kind == "rebar_eq":
        title, result = "معادل‌سازی میلگرد", rebar_equivalent(*values)
    else:
        title, result = "BBS / Cut List", bbs_cutlist(*values)

    lines = "\\n".join(f"• {k}: {clean_number(v)}" for k, v in result.items())
    db.ensure_user(uid, update.effective_user.first_name or "")
    db.save_calc(uid, title, lines)
    context.user_data.clear()
    context.user_data["last_calc_kind"] = kind
    context.user_data["last_calc_values"] = values
    await update.effective_message.reply_text(
        f"✅ <b>{title}</b>\\n\\n{lines}\\n\\n"
        "⚠️ این خروجی برای برآورد اولیه است و جایگزین طراحی نهایی مهندس محاسب نیست.",
        parse_mode="HTML",
        reply_markup=result_keyboard(),
    )


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data or ""
    await q.answer()
    log.info("button=%s user=%s", data, update.effective_user.id)

    if data == "home":
        await home(update, context)
        return

    if data == "recalc_last":
        kind = context.user_data.get("last_calc_kind")
        values = context.user_data.get("last_calc_values")
        if not kind or not values:
            await q.edit_message_text("⚠️ محاسبه قبلی در این نشست موجود نیست.", reply_markup=main_menu())
            return
        context.user_data.update({"wizard": kind, "wizard_values": list(values), "wizard_index": 0})
        await finish_wizard(update, context)
        return

    if data == "edit_last":
        kind = context.user_data.get("last_calc_kind")
        values = context.user_data.get("last_calc_values")
        if not kind or not values:
            await q.edit_message_text("⚠️ محاسبه قبلی در این نشست موجود نیست.", reply_markup=main_menu())
            return
        context.user_data.update({"wizard": kind, "wizard_values": list(values), "wizard_index": 0, "editing": True})
        rows = []
        for i, label in enumerate(wizard_labels(kind)):
            rows.append([InlineKeyboardButton(f"✏️ {label}: {clean_number(values[i])}", callback_data=f"edit_field|{i}")])
        rows.append([InlineKeyboardButton("✅ تأیید و محاسبه", callback_data="confirm_edit")])
        rows.append([InlineKeyboardButton("❌ لغو ویرایش", callback_data="cancel_edit")])
        await q.edit_message_text("✏️ <b>ویرایش ورودی‌ها</b>\\n\\nموردی را که می‌خواهی تغییر کند انتخاب کن:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return

    if data.startswith("edit_field|"):
        idx = int(data.split("|", 1)[1])
        kind = context.user_data.get("wizard")
        if not kind:
            await q.edit_message_text("جلسه ویرایش منقضی شده.", reply_markup=main_menu())
            return
        context.user_data["wizard_index"] = idx
        context.user_data["manual"] = True
        label = wizard_labels(kind)[idx]
        await q.edit_message_text(
            f"✏️ <b>{label}</b>\\n\\nمقدار جدید را تایپ کن.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ لغو ویرایش", callback_data="cancel_edit")]])
        )
        return

    if data == "confirm_edit":
        await finish_wizard(update, context)
        return

    if data == "cancel_edit":
        kind = context.user_data.get("last_calc_kind")
        values = context.user_data.get("last_calc_values")
        context.user_data.clear()
        if kind and values:
            context.user_data["last_calc_kind"] = kind
            context.user_data["last_calc_values"] = values
        await q.edit_message_text("ویرایش لغو شد.", reply_markup=result_keyboard())
        return

    if data.startswith("wizval|"):
        if "wizard" not in context.user_data:
            await q.edit_message_text("این مرحله منقضی شده. دوباره از منو شروع کن.", reply_markup=main_menu())
            return
        try:
            value = float(data.split("|", 1)[1])
            context.user_data["wizard_values"].append(value)
        except (ValueError, KeyError):
            await q.edit_message_text("ورودی نامعتبر است.", reply_markup=main_menu())
            return

        index = context.user_data["wizard_index"] + 1
        if index >= len(wizard_labels(context.user_data["wizard"])):
            await finish_wizard(update, context)
        else:
            context.user_data["wizard_index"] = index
            await show_wizard_step(q, context)
        return

    if data == "wizcustom":
        if "wizard" not in context.user_data:
            await q.edit_message_text("این مرحله منقضی شده. دوباره از منو شروع کن.", reply_markup=main_menu())
            return
        index = context.user_data["wizard_index"]
        label = wizard_labels(context.user_data["wizard"])[index]
        await q.edit_message_text(
            f"✏️ <b>{label}</b>\\n\\n"
            "فقط همین مقدار را تایپ کن.\\n"
            "مثال: <code>0.35</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ لغو", callback_data="home")]
            ]),
        )
        context.user_data["manual"] = True
        return

    if data.startswith("wizback|"):
        if "wizard" in context.user_data:
            idx = int(data.split("|", 1)[1])
            context.user_data["wizard_index"] = idx
            if len(context.user_data["wizard_values"]) > idx:
                context.user_data["wizard_values"] = context.user_data["wizard_values"][:idx]
            await show_wizard_step(q, context)
        return

    if data == "calc":
        context.user_data.clear()
        await q.edit_message_text("📐 نوع محاسبه را انتخاب کن:", reply_markup=calc_menu())
        return

    if data in {"foundation", "column", "beam", "slab"}:
        title, labels = begin_wizard(context, data)
        await show_wizard_step(q, context)
        return

    if data == "quantity":
        begin_wizard(context, "quantity")
        await show_wizard_step(q, context)
        return

    if data == "rebar":
        context.user_data.clear()
        await q.edit_message_text("🔩 ابزارهای میلگرد:", reply_markup=rebar_menu())
        return

    if data == "rebar_eq":
        begin_wizard(context, "rebar_eq")
        await show_wizard_step(q, context)
        return

    if data == "bbs":
        begin_wizard(context, "bbs")
        await show_wizard_step(q, context)
        return

    if data == "codes":
        await q.edit_message_text(
            "📚 <b>کدهای طراحی</b>\\n\\n"
            "نسخه سبک فعلی ورودی کد را جدا نگه می‌دارد.\\n"
            "در فاز بعد کدهای ایران و سایر کشورها به‌صورت Adapter اضافه می‌شوند.",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    if data == "projects":
        projects = db.projects(update.effective_user.id)
        lines = "\\n".join(f"• {p[1]}" for p in projects) if projects else "هنوز پروژه‌ای ثبت نشده."
        context.user_data["step"] = "project"
        await q.edit_message_text(
            "🏗 <b>پروژه‌های من</b>\\n\\n" + lines +
            "\\n\\nنام پروژه جدید را بفرست تا ذخیره شود.",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    if data == "reports":
        last = db.last_calc(update.effective_user.id)
        if last:
            text = f"📊 <b>{last[0]}</b>\\n\\n{last[1]}"
        else:
            text = "📊 هنوز محاسبه‌ای ذخیره نشده."
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=back_menu())
        return

    if data == "account":
        await q.edit_message_text(
            "👤 <b>حساب کاربری</b>\\n\\nنسخه پایه فعال است.\\n"
            "ساختار حساب، اعتبار و پرداخت برای توسعه بعدی جدا نگه داشته شده.",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    if data == "settings":
        await q.edit_message_text(
            "⚙️ <b>تنظیمات</b>\\n\\nواحد فعلی: متر / کیلوگرم\\nزبان: فارسی",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    if data == "ai":
        await q.edit_message_text(
            "🤖 <b>دستیار هوشمند</b>\\n\\n"
            "فعلاً موتور محاسبات مستقل است. اتصال AI در مرحله بعد به‌عنوان لایه کمکی اضافه می‌شود.",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    await q.edit_message_text("این گزینه هنوز فعال نشده.", reply_markup=back_menu())


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("wizard"):
        kind = context.user_data["wizard"]
        if not context.user_data.get("manual"):
            await update.message.reply_text(
                "از دکمه‌های همین مرحله استفاده کن؛ اگر می‌خواهی عدد را خودت وارد کنی، «✏️ ورود دستی» را بزن.",
                reply_markup=wizard_keyboard(wizard_options(kind, context.user_data["wizard_index"])),
            )
            return
        text = (update.message.text or "").strip().replace("،", ".")
        try:
            value = float(text)
            if value <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ فقط یک عدد مثبت وارد کن. مثال: <code>0.35</code>", parse_mode="HTML")
            return
        if context.user_data.get("editing"):
            idx = context.user_data["wizard_index"]
            context.user_data["wizard_values"][idx] = value
            context.user_data["manual"] = False
            context.user_data["editing"] = False
            rows = []
            for i, label in enumerate(wizard_labels(kind)):
                rows.append([InlineKeyboardButton(f"✏️ {label}: {clean_number(context.user_data['wizard_values'][i])}", callback_data=f"edit_field|{i}")])
            rows.append([InlineKeyboardButton("✅ تأیید و محاسبه", callback_data="confirm_edit")])
            rows.append([InlineKeyboardButton("❌ لغو ویرایش", callback_data="cancel_edit")])
            await update.message.reply_text("✏️ مقدار اصلاح شد. مورد دیگری را هم می‌توانی ویرایش کنی:", reply_markup=InlineKeyboardMarkup(rows))
            return
        context.user_data["wizard_values"].append(value)
        context.user_data["manual"] = False
        index = context.user_data["wizard_index"] + 1
        if index >= len(wizard_labels(kind)):
            await finish_wizard(update, context)
        else:
            context.user_data["wizard_index"] = index
            await show_wizard_step(update.message, context)
        return

    step = context.user_data.get("step")
    text = (update.message.text or "").strip()
    uid = update.effective_user.id

    if step == "project":
        db.ensure_user(uid, update.effective_user.first_name or "")
        db.add_project(uid, text)
        context.user_data.clear()
        await update.message.reply_text(f"✅ پروژه «{text}» ذخیره شد.", reply_markup=main_menu())
        return

    await update.message.reply_text("از منوی زیر یک گزینه انتخاب کن.", reply_markup=main_menu())



async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, BadRequest) and "Message is not modified" in str(context.error):
        return
    log.error("Unhandled bot error: %s", context.error, exc_info=context.error)


def build_app():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    app.add_error_handler(error_handler)
    return app


def main():
    log.info("Starting StructuralBot")
    db.init()
    threading.Thread(target=health_server, daemon=True).start()
    app = build_app()
    log.info("Telegram application starting")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("FATAL STARTUP ERROR")
        raise
