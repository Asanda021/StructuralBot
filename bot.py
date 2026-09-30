import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from app.db import Database
from app.engine import estimate_building, format_estimate
from app.keyboards import main_menu, cancel_menu, back_home, report_menu, review_menu

TOKEN = os.getenv("BOT" + "_TOKEN")
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


def n(v):
    return f"{float(v):,.2f}".rstrip("0").rstrip(".")


FIELDS = [
    ("floors", "تعداد طبقات", "طبقه"),
    ("area", "زیربنای هر طبقه", "m²"),
    ("foundation_count", "تعداد پی", "عدد"),
    ("footing_w", "عرض پی", "m"),
    ("footing_l", "طول پی", "m"),
    ("footing_t", "ضخامت پی", "m"),
    ("columns_per_floor", "تعداد ستون در هر طبقه", "عدد"),
    ("column_w", "عرض ستون", "m"),
    ("column_d", "عمق ستون", "m"),
    ("floor_h", "ارتفاع طبقه", "m"),
    ("beam_length_per_floor", "طول کل تیرها در هر طبقه", "m"),
    ("beam_w", "عرض تیر", "m"),
    ("beam_h", "ارتفاع تیر", "m"),
    ("slab_t", "ضخامت سقف", "m"),
    ("stair_area_per_floor", "مساحت راه‌پله در هر طبقه", "m²"),
    ("stair_t", "ضخامت راه‌پله", "m"),
]

OPTIONS = {
    "floors": ["2", "3", "4", "5", "6", "8", "10"],
    "area": ["80", "100", "120", "150", "200", "250"],
    "foundation_count": ["4", "6", "8", "10", "12", "16"],
    "footing_w": ["1", "1.2", "1.5", "1.8", "2"],
    "footing_l": ["1", "1.2", "1.5", "1.8", "2"],
    "footing_t": ["0.4", "0.5", "0.6", "0.7"],
    "columns_per_floor": ["6", "8", "10", "12", "16", "20"],
    "column_w": ["0.3", "0.35", "0.4", "0.45", "0.5"],
    "column_d": ["0.3", "0.35", "0.4", "0.45", "0.5"],
    "floor_h": ["2.8", "3", "3.2", "3.5", "4"],
    "beam_length_per_floor": ["40", "60", "80", "100", "120", "150"],
    "beam_w": ["0.25", "0.3", "0.35", "0.4"],
    "beam_h": ["0.4", "0.45", "0.5", "0.6"],
    "slab_t": ["0.12", "0.15", "0.18", "0.2", "0.25"],
    "stair_area_per_floor": ["6", "8", "10", "12", "15"],
    "stair_t": ["0.12", "0.15", "0.18", "0.2"],
}


def value_keyboard(key):
    rows = []
    row = []
    for value in OPTIONS.get(key, []):
        row.append(InlineKeyboardButton(value, callback_data=f"pv|{value}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("✏️ ورود دستی", callback_data="manual")])
    rows.append([InlineKeyboardButton("❌ لغو", callback_data="home")])
    return InlineKeyboardMarkup(rows)


def prompt_for(key, index):
    _, label, unit = next(x for x in FIELDS if x[0] == key)
    progress = "█" * (index + 1) + "░" * (len(FIELDS) - index - 1)
    text = (
        f"🏗 <b>برآورد مقادیر ساختمان بتنی</b>\n\n"
        f"گام {index + 1} از {len(FIELDS)}  |  <code>{progress}</code>\n"
        f"<b>{label}</b> ({unit}) را انتخاب کن.\n\n"
        "⚡ برای سرعت از کلیدهای آماده استفاده کن؛ در صورت نیاز «ورود دستی» را بزن."
    )
    return text, value_keyboard(key)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.first_name or "")
    context.user_data.clear()
    await update.message.reply_text(
        "🏗 <b>StructuralBot</b>\n\n"
        "برآورد مقادیر و مصالح ساختمان بتنی\n"
        "محاسبات طراحی سازه در این نسخه ارائه نمی‌شود.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🏠 <b>منوی اصلی</b>", parse_mode="HTML", reply_markup=main_menu()
        )
    else:
        await update.message.reply_text("🏠 منوی اصلی", reply_markup=main_menu())


def begin_project(context, project_name):
    context.user_data.clear()
    context.user_data.update({
        "takeoff": True,
        "takeoff_index": 0,
        "takeoff_values": {},
        "manual": False,
        "project_name": project_name[:120],
    })


async def show_step(target, context):
    index = context.user_data["takeoff_index"]
    key = FIELDS[index][0]
    text, markup = prompt_for(key, index)
    if hasattr(target, "edit_message_text"):
        await target.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await target.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def finish_project(update, context):
    data = dict(context.user_data["takeoff_values"])
    result = estimate_building(data)
    report = format_estimate(result)
    uid = update.effective_user.id
    db.ensure_user(uid, update.effective_user.first_name or "")
    project_id = context.user_data.get("project_id")
    if not project_id:
        project_id = db.add_project(uid, context.user_data.get("project_name", "پروژه بدون نام"))
    db.save_estimate(uid, project_id, data, result, report)
    project_name = context.user_data.get("project_name", "پروژه")
    context.user_data.clear()
    context.user_data["last_estimate"] = result
    context.user_data["last_report"] = report
    context.user_data["last_project_id"] = project_id
    context.user_data["last_project_name"] = project_name
    await update.effective_message.reply_text(
        "✅ <b>برآورد مقادیر اولیه پروژه آماده شد</b>\n\n" + report,
        parse_mode="HTML",
        reply_markup=report_menu(),
    )


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data or ""
    await q.answer()
    log.info("button=%s user=%s", data, update.effective_user.id)

    if data == "home":
        await home(update, context)
        return

    if data == "new_project":
        context.user_data.clear()
        context.user_data["awaiting_project_name"] = True
        await q.edit_message_text(
            "🏗 <b>پروژه جدید</b>\n\nنام پروژه را بفرست.",
            parse_mode="HTML", reply_markup=cancel_menu()
        )
        return

    if data.startswith("edit_saved|"):
        idx = int(data.split("|", 1)[1])
        context.user_data["editing_index"] = idx
        context.user_data["manual"] = True
        _, label, unit = FIELDS[idx]
        await q.edit_message_text(
            f"✏️ <b>{label}</b> ({unit})\n\nمقدار جدید را بفرست.",
            parse_mode="HTML", reply_markup=cancel_menu()
        )
        return

    if data == "review_saved":
        await show_review(q, context)
        return

    if data == "edit_current":
        context.user_data["editing_saved"] = True
        rows = []
        for i, (key, label, unit) in enumerate(FIELDS):
            rows.append([InlineKeyboardButton(
                f"✏️ {label}: {n(context.user_data['takeoff_values'].get(key, 0))} {unit}",
                callback_data=f"edit_saved|{i}"
            )])
        rows.append([InlineKeyboardButton("🔎 بازبینی دوباره", callback_data="review_saved")])
        rows.append([InlineKeyboardButton("❌ لغو", callback_data="home")])
        await q.edit_message_text(
            "✏️ <b>ویرایش اطلاعات</b>\n\nبخش موردنظر را انتخاب کن.",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows)
        )
        return

    if data == "previous_step":
        if context.user_data.get("takeoff"):
            idx = max(0, context.user_data.get("takeoff_index", len(FIELDS)) - 1)
            context.user_data["takeoff_index"] = idx
            context.user_data["manual"] = False
            await show_step(q, context)
        else:
            await q.edit_message_text("جلسه برآورد منقضی شده.", reply_markup=main_menu())
        return

    if data.startswith("pv|"):
        if not context.user_data.get("takeoff"):
            await q.edit_message_text("جلسه متره منقضی شده.", reply_markup=main_menu())
            return
        key = FIELDS[context.user_data["takeoff_index"]][0]
        try:
            value = float(data.split("|", 1)[1])
            if value <= 0:
                raise ValueError
        except ValueError:
            await q.edit_message_text("ورودی نامعتبر است.", reply_markup=main_menu())
            return
        context.user_data["takeoff_values"][key] = value
        context.user_data["takeoff_index"] += 1
        if context.user_data["takeoff_index"] >= len(FIELDS):
            await show_review(q, context)
        else:
            await show_step(q, context)
        return

    if data == "manual":
        if not context.user_data.get("takeoff"):
            await q.edit_message_text("جلسه متره منقضی شده.", reply_markup=main_menu())
            return
        context.user_data["manual"] = True
        key = FIELDS[context.user_data["takeoff_index"]][0]
        _, label, unit = FIELDS[context.user_data["takeoff_index"]]
        await q.edit_message_text(
            f"✏️ <b>{label}</b> ({unit})\n\nفقط همین مقدار را بفرست.\nمثال: <code>3.2</code>",
            parse_mode="HTML",
            reply_markup=cancel_menu(),
        )
        return

    if data == "confirm_project":
        await finish_project(update, context)
        return

    if data == "edit_project":
        last = db.last_estimate(update.effective_user.id)
        if not last:
            await q.edit_message_text("هنوز پروژه‌ای برای ویرایش ذخیره نشده.", reply_markup=main_menu())
            return
        context.user_data.clear()
        context.user_data.update({
            "takeoff": True,
            "editing_saved": True,
            "manual": False,
            "takeoff_index": 0,
            "takeoff_values": dict(last["inputs"]),
            "project_id": last["project_id"],
            "project_name": last["project_name"],
        })
        rows = []
        for i, (key, label, unit) in enumerate(FIELDS):
            rows.append([InlineKeyboardButton(
                f"✏️ {label}: {n(last['inputs'].get(key, 0))} {unit}",
                callback_data=f"edit_saved|{i}"
            )])
        rows.append([InlineKeyboardButton("🔎 بررسی و محاسبه", callback_data="review_saved")])
        rows.append([InlineKeyboardButton("❌ لغو", callback_data="home")])
        await q.edit_message_text(
            f"✏️ <b>ویرایش پروژه: {last['project_name']}</b>\n\nیک آیتم را انتخاب کن.",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows)
        )
        return

    if data == "recalc_project":
        last = db.last_estimate(update.effective_user.id)
        if not last:
            await q.edit_message_text("هنوز برآوردی ذخیره نشده.", reply_markup=main_menu())
            return
        await q.edit_message_text(
            format_estimate(last["result"]),
            parse_mode="HTML", reply_markup=report_menu()
        )
        return

    if data == "projects":
        projects = db.projects(update.effective_user.id)
        if projects:
            body = "\n".join(f"• {p[1]}" for p in projects)
        else:
            body = "هنوز پروژه‌ای ثبت نشده."
        await q.edit_message_text(
            "📂 <b>پروژه‌های من</b>\n\n" + body,
            parse_mode="HTML",
            reply_markup=back_home(),
        )
        return

    if data in {"takeoff_concrete", "takeoff_rebar", "takeoff_formwork"}:
        last = db.last_estimate(update.effective_user.id)
        if not last:
            await q.edit_message_text(
                "ابتدا یک پروژه بساز تا مقادیر آن در این بخش نمایش داده شود.",
                reply_markup=main_menu(),
            )
            return
        result = last["result"]
        title = {
            "takeoff_concrete": "🧱 جدول مقادیر بتن",
            "takeoff_rebar": "🔩 جدول برآورد میلگرد",
            "takeoff_formwork": "🪵 جدول مقادیر قالب‌بندی",
        }[data]
        source = {
            "takeoff_concrete": result["concrete"],
            "takeoff_rebar": result["rebar"],
            "takeoff_formwork": result["formwork"],
        }[data]
        unit = {"takeoff_concrete": "m³", "takeoff_rebar": "kg", "takeoff_formwork": "m²"}[data]
        lines = [f"<b>{title}</b>", f"📁 پروژه: {last['project_name']}", "", "<pre>آیتم                 مقدار</pre>"]
        for name, value in source.items():
            lines.append(f"• {name}: <b>{value:,.2f}</b> {unit}")
        await q.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=back_home())
        return

    if data == "reports":
        last = db.last_calc(update.effective_user.id)
        text = f"📊 <b>آخرین گزارش</b>\n\n{last[1]}" if last else "📊 هنوز گزارشی ثبت نشده."
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=back_home())
        return

    if data == "pricing":
        await q.edit_message_text(
            "💰 <b>برآورد ریالی</b>\n\n"
            "مرحله بعدی: تعریف قیمت واحد بتن، میلگرد، قالب و سایر اقلام و محاسبه مبلغ کل پروژه.",
            parse_mode="HTML", reply_markup=back_home(),
        )
        return

    if data == "exports":
        await q.edit_message_text(
            "📄 <b>خروجی</b>\n\n"
            "PDF و Excel در مرحله گزارش حرفه‌ای پروژه اضافه می‌شوند.",
            parse_mode="HTML", reply_markup=back_home(),
        )
        return

    if data == "settings":
        await q.edit_message_text(
            "⚙️ <b>تنظیمات</b>\n\nواحد طول: متر\nمساحت: مترمربع\nحجم: مترمکعب\nوزن: کیلوگرم",
            parse_mode="HTML", reply_markup=back_home(),
        )
        return

    if data == "help":
        await q.edit_message_text(
            "❓ <b>راهنما</b>\n\n"
            "این ربات برای متره و برآورد اولیه ساختمان بتنی طراحی شده است.\n"
            "مقادیر میلگرد در این نسخه با ضرایب برآوردی kg/m³ محاسبه می‌شوند؛ برای لیستوفر اجرایی باید اطلاعات آرماتوربندی پروژه وارد شود.",
            parse_mode="HTML", reply_markup=back_home(),
        )
        return

    await q.edit_message_text("این گزینه در این نسخه تعریف نشده است.", reply_markup=back_home())


async def show_review(target, context):
    values = context.user_data["takeoff_values"]
    groups = [
        ("🏗 مشخصات پروژه", FIELDS[0:3]),
        ("🧱 فونداسیون", FIELDS[3:6]),
        ("🏢 ستون‌ها", FIELDS[6:10]),
        ("📏 تیرها", FIELDS[10:13]),
        ("⬜ سقف", FIELDS[13:14]),
        ("🪜 راه‌پله", FIELDS[14:16]),
    ]
    lines = ["🔎 <b>بازبینی نهایی اطلاعات</b>", "", "قبل از محاسبه، مقادیر زیر را کنترل کن:"]
    for title, fields in groups:
        lines.append("")
        lines.append(f"<b>{title}</b>")
        for key, label, unit in fields:
            lines.append(f"• {label}: <b>{n(values[key])}</b> {unit}")
    lines += ["", "⚠️ هنوز محاسبه نهایی انجام نشده است."]
    if hasattr(target, "edit_message_text"):
        await target.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=review_menu())
    else:
        await target.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=review_menu())


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if context.user_data.get("awaiting_project_name"):
        if not text or len(text) > 120:
            await update.message.reply_text("❌ نام پروژه باید بین ۱ تا ۱۲۰ کاراکتر باشد.")
            return
        begin_project(context, text)
        await show_step(update.message, context)
        return

    if context.user_data.get("editing_saved") and context.user_data.get("manual"):
        try:
            value = float(text.replace("،", "."))
            if value <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ فقط یک عدد مثبت وارد کن.")
            return
        idx = context.user_data["editing_index"]
        context.user_data["takeoff_values"][FIELDS[idx][0]] = value
        context.user_data["manual"] = False
        await show_review(update.message, context)
        return

    if context.user_data.get("takeoff"):
        if not context.user_data.get("manual"):
            await update.message.reply_text(
                "از گزینه‌های همین مرحله استفاده کن یا «✏️ ورود دستی» را بزن.",
                reply_markup=main_menu(),
            )
            return
        text = (update.message.text or "").strip().replace("،", ".")
        try:
            value = float(text)
            if value <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ فقط یک عدد مثبت وارد کن. مثال: <code>3.2</code>", parse_mode="HTML")
            return
        key = FIELDS[context.user_data["takeoff_index"]][0]
        context.user_data["takeoff_values"][key] = value
        context.user_data["manual"] = False
        context.user_data["takeoff_index"] += 1
        if context.user_data["takeoff_index"] >= len(FIELDS):
            await show_review(update.message, context)
        else:
            await show_step(update.message, context)
        return

    await update.message.reply_text("از منوی زیر انتخاب کن.", reply_markup=main_menu())


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
    log.info("Starting StructuralBot - Concrete Quantity Takeoff")
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
