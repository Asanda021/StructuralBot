import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    ContextTypes, MessageHandler, filters,
)

from app.db import Database
from app.engine import (
    foundation_calc, column_calc, beam_calc, slab_calc,
    concrete_for_dimensions, rebar_equivalent,
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


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data or ""
    await q.answer()
    log.info("button=%s user=%s", data, update.effective_user.id)

    if data == "home":
        await home(update, context)
        return

    if data == "calc":
        context.user_data.clear()
        await q.edit_message_text("📐 نوع محاسبه را انتخاب کن:", reply_markup=calc_menu())
        return

    if data in {"foundation", "column", "beam", "slab"}:
        context.user_data["step"] = data
        names = {
            "foundation": "پی",
            "column": "ستون",
            "beam": "تیر",
            "slab": "سقف",
        }
        examples = {
            "foundation": "0.60, 2.00, 0.40",
            "column": "0.40, 0.40, 3.00",
            "beam": "0.30, 0.50, 5.00",
            "slab": "0.15, 5.00, 4.00",
        }
        await q.edit_message_text(
            f"📐 <b>{names[data]}</b>\n\n"
            f"سه مقدار را با کاما بفرست:\n<code>{examples[data]}</code>\n\n"
            "همه ابعاد بر حسب متر هستند.",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    if data == "rebar":
        context.user_data.clear()
        await q.edit_message_text("🔩 ابزارهای میلگرد:", reply_markup=rebar_menu())
        return

    if data == "rebar_eq":
        context.user_data["step"] = "rebar_eq"
        await q.edit_message_text(
            "🔄 <b>معادل‌سازی میلگرد</b>\\n\\nدو قطر را با کاما بفرست.\\nمثال: <code>16, 20</code>",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    if data == "bbs":
        context.user_data["step"] = "bbs"
        await q.edit_message_text(
            "📋 <b>BBS / Cut List</b>\\n\\nقطر، تعداد و طول هر قطعه را با کاما بفرست.\\nمثال: <code>16, 20, 8.5</code>",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    if data == "codes":
        await q.edit_message_text(
            "📚 <b>کدهای طراحی</b>\\n\\nنسخه سبک فعلی ورودی کد را جدا نگه می‌دارد.\\nدر فاز بعد کدهای ایران و سایر کشورها به‌صورت Adapter اضافه می‌شوند.",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    if data == "quantity":
        context.user_data["step"] = "quantity"
        await q.edit_message_text(
            "🧮 <b>برآورد بتن</b>\n\n"
            "ضخامت/بعد اول، بعد دوم، بعد سوم را با کاما بفرست.\n"
            "مثال: <code>0.30, 5, 4</code>",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    if data == "rebar":
        context.user_data["step"] = "rebar"
        await q.edit_message_text(
            "🔩 <b>معادل‌سازی میلگرد</b>\n\n"
            "دو قطر را با کاما بفرست.\n"
            "مثال: <code>16, 20</code>",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    if data == "projects":
        projects = db.projects(update.effective_user.id)
        lines = "\n".join(f"• {p[1]}" for p in projects) if projects else "هنوز پروژه‌ای ثبت نشده."
        context.user_data["step"] = "project"
        await q.edit_message_text(
            "🏗 <b>پروژه‌های من</b>\n\n" + lines +
            "\n\nنام پروژه جدید را بفرست تا ذخیره شود.",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    if data == "reports":
        last = db.last_calc(update.effective_user.id)
        if last:
            text = f"📊 <b>{last[0]}</b>\n\n{last[1]}"
        else:
            text = "📊 هنوز محاسبه‌ای ذخیره نشده."
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=back_menu())
        return

    if data == "account":
        await q.edit_message_text(
            "👤 <b>حساب کاربری</b>\n\nنسخه پایه فعال است.\n"
            "ساختار حساب، اعتبار و پرداخت برای توسعه بعدی جدا نگه داشته شده.",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    if data == "settings":
        await q.edit_message_text(
            "⚙️ <b>تنظیمات</b>\n\nواحد فعلی: متر / کیلوگرم\nزبان: فارسی",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    if data == "ai":
        await q.edit_message_text(
            "🤖 <b>دستیار هوشمند</b>\n\n"
            "فعلاً موتور محاسبات مستقل است. اتصال AI در مرحله بعد به‌عنوان لایه کمکی اضافه می‌شود.",
            parse_mode="HTML", reply_markup=back_menu(),
        )
        return

    await q.edit_message_text("این گزینه هنوز فعال نشده.", reply_markup=back_menu())


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")
    text = (update.message.text or "").strip()
    uid = update.effective_user.id

    if step == "project":
        db.ensure_user(uid, update.effective_user.first_name or "")
        db.add_project(uid, text)
        context.user_data.clear()
        await update.message.reply_text(f"✅ پروژه «{text}» ذخیره شد.", reply_markup=main_menu())
        return

    if step not in {"foundation", "column", "beam", "slab", "quantity", "rebar_eq", "bbs"}:
        await update.message.reply_text("از منوی زیر یک گزینه انتخاب کن.", reply_markup=main_menu())
        return

    try:
        count = 2 if step == "rebar_eq" else 3
        values = parse_numbers(text, count)
        if step == "foundation":
            title, result = "پی", foundation_calc(*values)
        elif step == "column":
            title, result = "ستون", column_calc(*values)
        elif step == "beam":
            title, result = "تیر", beam_calc(*values)
        elif step == "slab":
            title, result = "سقف", slab_calc(*values)
        elif step == "quantity":
            title, result = "برآورد بتن", concrete_for_dimensions(*values)
        else:
            title, result = "معادل‌سازی میلگرد", rebar_equivalent(*values)
    except (ValueError, TypeError):
        example = "16, 20" if step == "rebar_eq" else ("16, 20, 8.5" if step == "bbs" else "0.30, 5, 4")
        await update.message.reply_text(f"❌ ورودی نامعتبر است. مثال: {example}")
        return

    lines = "\n".join(f"• {k}: {clean_number(v)}" for k, v in result.items())
    db.ensure_user(uid, update.effective_user.first_name or "")
    db.save_calc(uid, title, lines)
    context.user_data.clear()
    await update.message.reply_text(
        f"✅ <b>{title}</b>\n\n{lines}\n\n"
        "⚠️ این خروجی برای برآورد اولیه است و جایگزین طراحی نهایی مهندس محاسب نیست.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, BadRequest) and "Message is not modified" in str(context.error):
        return
    log.exception("Unhandled update", exc_info=context.error)


def build_app():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    app.add_error_handler(error_handler)
    return app


def main():
    db.init()
    threading.Thread(target=health_server, daemon=True).start()
    app = build_app()
    log.info("StructuralBot Lite starting")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=0.0,
        timeout=10,
    )


if __name__ == "__main__":
    main()
