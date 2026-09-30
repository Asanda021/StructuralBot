import logging, os, threading, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from app.db import Database
from app.engine import estimate_items, format_estimate, calculate_rebar_weight
from app.exporter import create_excel, create_pdf
from app.keyboards import main_menu, back_home, section_menu, item_menu, report_menu, review_menu

TOKEN=os.getenv("BOT"+" _TOKEN".replace(" ",""))
DB_PATH=os.getenv("DATABASE_PATH","/tmp/structuralbot.db")
PORT=int(os.getenv("PORT","10000"))
logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),format="%(asctime)s | StructuralBot | %(levelname)s | %(message)s")
log=logging.getLogger("StructuralBot"); db=Database(DB_PATH)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/","/health"):
            body=b"StructuralBot OK"; self.send_response(200); self.send_header("Content-Type","text/plain; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
        else: self.send_response(404); self.end_headers()
    def log_message(self,*_): pass
def health_server(): ThreadingHTTPServer(("0.0.0.0",PORT),HealthHandler).serve_forever()

UNIT_MAP={"یونولیت":"عدد","تیرچه":"m","بولت":"عدد","صفحه مدفون":"عدد","وصله/کوپلر":"عدد",
          "بتن سقف":"m³","بتن ستون":"m³","بتن تیر":"m³","بتن دیوار":"m³","بتن پله":"m³","بتن مگر":"m³",
          "پی منفرد":"m³","پی نواری":"m³","پی گسترده":"m³","پی مرکب":"m³",
          "قالب پی":"m²","قالب ستون":"m²","قالب تیر":"m²","قالب سقف":"m²","قالب دیوار":"m²","قالب پله":"m²"}
def unit_for(name): return UNIT_MAP.get(name,"kg" if ("میلگرد" in name or name in {"خاموت ستون","خاموت تیر","سنجاقی ستون","سنجاقی","اتکا","ژوئن","کلاف میانی","میلگرد سفارشی","میلگرد اصلی پله","میلگرد حرارتی","میلگرد منفی"}) else "عدد")

def fmt(v): return f"{float(v):,.3f}".rstrip("0").rstrip(".")

def start(update,context):
    async def run():
        u=update.effective_user; db.ensure_user(u.id,u.first_name or ""); context.user_data.clear()
        await update.message.reply_text("🏗 <b>StructuralBot</b>\n\n<b>متره جامع ساختمان بتنی</b>\nاز روی نقشه، اجزای سازه و مصالح را ثبت کن و در پایان جدول جامع، Excel و PDF بگیر.",parse_mode="HTML",reply_markup=main_menu())
    return run()
start= start(update=None,context=None) if False else None

async def start_cmd(update,context):
    u=update.effective_user; db.ensure_user(u.id,u.first_name or ""); context.user_data.clear()
    await update.message.reply_text("🏗 <b>StructuralBot</b>\n\n<b>متره جامع ساختمان بتنی</b>\nاز روی نقشه، اجزای سازه و مصالح را ثبت کن و در پایان جدول جامع، Excel و PDF بگیر.",parse_mode="HTML",reply_markup=main_menu())

def reset_takeoff(context,name=None):
    context.user_data.clear(); context.user_data.update({"project_name":name or "پروژه بدون نام","items":[]})

def mode_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("✏️ ورود مقدار نهایی",callback_data="mode|direct")],
                                 [InlineKeyboardButton("📐 محاسبه از ابعاد",callback_data="mode|geometry")],
                                 [InlineKeyboardButton("🔩 محاسبه وزن میلگرد",callback_data="mode|rebar")],
                                 [InlineKeyboardButton("⬅️ انتخاب آیتم دیگر",callback_data="choose_section")]])

GEOMETRY={
 "پی منفرد":[("تعداد پی","عدد"),("عرض پی","m"),("طول پی","m"),("ضخامت پی","m")],
 "پی مرکب":[("تعداد پی","عدد"),("عرض","m"),("طول","m"),("ضخامت","m")],
 "بتن ستون":[("تعداد","عدد"),("عرض ستون","m"),("عمق ستون","m"),("ارتفاع","m")],
 "بتن تیر":[("تعداد","عدد"),("طول","m"),("عرض تیر","m"),("ارتفاع تیر","m")],
 "بتن سقف":[("مساحت","m²"),("ضخامت","m")],
 "بتن دیوار":[("طول","m"),("ارتفاع","m"),("ضخامت","m")],
 "بتن پله":[("مساحت","m²"),("ضخامت","m")],
}
def formula_value(name,vals):
    if name in ("پی منفرد","پی مرکب"): return vals[0]*vals[1]*vals[2]*vals[3]
    if name=="بتن ستون": return vals[0]*vals[1]*vals[2]*vals[3]
    if name=="بتن تیر": return vals[0]*vals[1]*vals[2]*vals[3]
    if name in ("بتن سقف","بتن پله"): return vals[0]*vals[1]
    if name=="بتن دیوار": return vals[0]*vals[1]*vals[2]
    raise ValueError("فرمول این آیتم هنوز تعریف نشده است")

async def show_sections(q): await q.edit_message_text("📚 <b>انتخاب بخش سازه</b>\n\nبخشی را که از روی نقشه می‌خواهی متره کنی انتخاب کن.",parse_mode="HTML",reply_markup=section_menu())

async def finish_takeoff(update,context):
    if not context.user_data.get("items"):
        await update.callback_query.edit_message_text("هنوز هیچ آیتمی ثبت نشده است.",reply_markup=section_menu()); return
    await show_review(update.callback_query,context)

async def show_review(target,context):
    items=context.user_data.get("items",[])
    lines=["🔎 <b>بازبینی متره</b>","",f"پروژه: <b>{context.user_data.get('project_name')}</b>",f"تعداد ردیف: <b>{len(items)}</b>",""]
    for i,x in enumerate(items,1): lines.append(f"{i}. {x['section']} | {x['name']} | <b>{fmt(x['quantity'])}</b> {x['unit']}")
    lines += ["","➕ برای اضافه‌کردن آیتم، ویرایش را بزن. سپس ثبت نهایی کن."]
    await target.edit_message_text("\n".join(lines),parse_mode="HTML",reply_markup=review_menu())

async def finish_and_save(update,context):
    items=context.user_data.get("items",[])
    if not items: return
    result=estimate_items(items); report=format_estimate(result); uid=update.effective_user.id
    pid=context.user_data.get("project_id") or db.add_project(uid,context.user_data.get("project_name","پروژه"))
    db.save_estimate(uid,pid,{"items":items},result,report)
    context.user_data["last_result"]=result; context.user_data["last_report"]=report; context.user_data["last_project_id"]=pid
    await update.effective_message.reply_text("✅ <b>متره نهایی ثبت شد</b>\n\n"+report,parse_mode="HTML",reply_markup=report_menu())

async def callback(update,context):
    q=update.callback_query; data=q.data or ""; await q.answer()
    if data=="home":
        context.user_data.clear(); await q.edit_message_text("🏠 <b>منوی اصلی</b>",parse_mode="HTML",reply_markup=main_menu()); return
    if data=="new_project":
        context.user_data.clear(); context.user_data["awaiting_project_name"]=True
        await q.edit_message_text("🏗 <b>پروژه جدید</b>\n\nنام پروژه را بفرست.",parse_mode="HTML",reply_markup=back_home()); return
    if data in ("choose_section","continue_project"):
        if not context.user_data.get("items"):
            if not context.user_data.get("project_name"): await q.edit_message_text("ابتدا پروژه جدید بساز.",reply_markup=main_menu()); return
        await show_sections(q); return
    if data.startswith("sec|"):
        sec=data.split("|",1)[1]; context.user_data["section"]=sec
        await q.edit_message_text(f"📚 <b>{sec}</b>\n\nآیتم موردنظر را انتخاب کن.",parse_mode="HTML",reply_markup=item_menu(sec)); return
    if data.startswith("item|"):
        parts=data.split("|",2); name=parts[2]; context.user_data["current_item"]=name
        await q.edit_message_text(f"➕ <b>{name}</b>\n\nروش ورود مقدار را انتخاب کن.",parse_mode="HTML",reply_markup=mode_menu()); return
    if data.startswith("mode|"):
        mode=data.split("|",1)[1]; name=context.user_data.get("current_item"); context.user_data["input_mode"]=mode
        if mode=="direct":
            context.user_data["input_queue"]=[("مقدار",unit_for(name))]; context.user_data["input_values"]=[]
        elif mode=="geometry" and name in GEOMETRY:
            context.user_data["input_queue"]=GEOMETRY[name]; context.user_data["input_values"]=[]
        elif mode=="rebar":
            context.user_data["input_queue"]=[("قطر میلگرد","mm"),("طول هر قطعه","m"),("تعداد","عدد")]; context.user_data["input_values"]=[]
        else:
            context.user_data["input_queue"]=[("مقدار",unit_for(name))]; context.user_data["input_values"]=[]
        context.user_data["manual_input"]=True; await ask_next(update,context); return
    if data=="finish_takeoff": await finish_takeoff(update,context); return
    if data=="confirm_project":
        await finish_and_save(update,context); return
    if data=="table":
        result=context.user_data.get("last_result") or (db.last_estimate(update.effective_user.id) or {}).get("result")
        if not result: await q.edit_message_text("هنوز متره‌ای ثبت نشده.",reply_markup=main_menu()); return
        await q.edit_message_text(format_estimate(result),parse_mode="HTML",reply_markup=report_menu()); return
    if data=="reports":
        last=db.last_estimate(update.effective_user.id)
        await q.edit_message_text(format_estimate(last["result"]) if last else "📊 هنوز گزارشی ثبت نشده.",parse_mode="HTML",reply_markup=report_menu() if last else main_menu()); return
    if data=="projects":
        ps=db.projects(update.effective_user.id)
        rows=[[InlineKeyboardButton(p[1],callback_data=f"open|{p[0]}")] for p in ps]
        rows.append([InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")])
        await q.edit_message_text("📂 <b>پروژه‌های من</b>\n\nیک پروژه را انتخاب کن.",parse_mode="HTML",reply_markup=InlineKeyboardMarkup(rows) if ps else back_home()); return
    if data.startswith("open|"):
        p=db.project_estimate(update.effective_user.id,int(data.split("|")[1]))
        if not p: await q.edit_message_text("پروژه پیدا نشد.",reply_markup=main_menu()); return
        context.user_data.clear(); context.user_data.update({"project_name":p["project_name"],"project_id":p["project_id"],"items":p["inputs"].get("items",[]),"last_result":p["result"]})
        await q.edit_message_text(format_estimate(p["result"]),parse_mode="HTML",reply_markup=report_menu()); return
    if data=="exports":
        last=db.last_estimate(update.effective_user.id)
        if not last: await q.edit_message_text("هنوز گزارشی برای خروجی وجود ندارد.",reply_markup=main_menu()); return
        with tempfile.TemporaryDirectory() as d:
            x=create_excel(last["result"],last["project_name"],os.path.join(d,"StructuralBot_Takeoff.xlsx"))
            p=create_pdf(last["result"],last["project_name"],os.path.join(d,"StructuralBot_Takeoff.pdf"))
            await update.effective_message.reply_document(open(x,"rb"),caption="📊 Excel - جدول جامع متره")
            await update.effective_message.reply_document(open(p,"rb"),caption="📄 PDF - گزارش جامع متره")
        return
    if data=="pricing":
        await q.edit_message_text("💰 <b>قیمت‌گذاری</b>\n\nهسته متره آماده است. مرحله بعد می‌توانیم قیمت واحد هر آیتم را به همین جدول وصل کنیم.",parse_mode="HTML",reply_markup=back_home()); return
    if data=="settings":
        await q.edit_message_text("⚙️ <b>تنظیمات</b>\n\nواحدها در سطح هر آیتم تعیین می‌شوند و برای آیتم سفارشی قابل انتخاب خواهند بود.",parse_mode="HTML",reply_markup=back_home()); return
    if data=="help":
        await q.edit_message_text("❓ <b>راهنما</b>\n\nاز روی نقشه بخش را انتخاب کن، آیتم را بزن و مقدار نهایی یا ابعاد را وارد کن. برای آرماتور می‌توانی قطر، طول و تعداد را بدهی. در پایان یک جدول جامع از همه اقلام پروژه دریافت می‌کنی.",parse_mode="HTML",reply_markup=back_home()); return
    await q.edit_message_text("این گزینه تعریف نشده است.",reply_markup=main_menu())

async def ask_next(update,context):
    q=context.user_data.get("input_queue",[])
    if not q:
        await add_current_item(update,context); return
    label,unit=q[0]
    await update.callback_query.edit_message_text(f"✏️ <b>{label}</b> ({unit})\n\nفقط عدد را بفرست. مثال: <code>3.2</code>",parse_mode="HTML",reply_markup=back_home())

async def add_current_item(update,context):
    name=context.user_data["current_item"]; sec=context.user_data["section"]; vals=context.user_data["input_values"]; mode=context.user_data["input_mode"]
    if mode=="geometry":
        quantity=formula_value(name,vals); note="محاسبه‌شده از ابعاد واردشده"
        unit="m³"
    elif mode=="rebar":
        quantity=calculate_rebar_weight(vals[0],vals[1],vals[2]); note=f"قطر {vals[0]}mm × طول {vals[1]}m × تعداد {vals[2]}"
        unit="kg"
    else:
        quantity=vals[0]; note="ورود مستقیم از نقشه"; unit=unit_for(name)
    context.user_data.setdefault("items",[]).append({"section":sec,"name":name,"quantity":quantity,"unit":unit,"note":note,"type":mode})
    context.user_data.pop("manual_input",None); context.user_data.pop("input_queue",None); context.user_data.pop("input_values",None)
    await update.effective_message.reply_text(f"✅ ثبت شد: <b>{name}</b> — {fmt(quantity)} {unit}",parse_mode="HTML",reply_markup=section_menu())

async def message(update,context):
    text=(update.message.text or "").strip().replace("،",".")
    if context.user_data.get("awaiting_project_name"):
        if not text or len(text)>120: await update.message.reply_text("❌ نام پروژه نامعتبر است."); return
        reset_takeoff(context,text); await update.message.reply_text(f"🏗 پروژه «{text}» ساخته شد.\n\nحالا بخش سازه را انتخاب کن.",reply_markup=section_menu()); return
    if context.user_data.get("manual_input"):
        try: value=float(text)
        except ValueError: await update.message.reply_text("❌ فقط عدد وارد کن."); return
        if value<=0: await update.message.reply_text("❌ عدد باید بزرگ‌تر از صفر باشد."); return
        context.user_data["input_values"].append(value); context.user_data["input_queue"].pop(0)
        if context.user_data["input_queue"]: await update.message.reply_text(f"⏳ ثبت شد.\n\nمرحله بعد: <b>{context.user_data['input_queue'][0][0]}</b> ({context.user_data['input_queue'][0][1]})",parse_mode="HTML",reply_markup=back_home())
        else: await add_current_item(update,context)
        return
    await update.message.reply_text("از منوی زیر انتخاب کن.",reply_markup=main_menu())

async def error_handler(update,context):
    if isinstance(context.error,BadRequest) and "Message is not modified" in str(context.error): return
    log.error("Unhandled bot error: %s",context.error,exc_info=context.error)

def build_app():
    if not TOKEN: raise RuntimeError("BOT_TOKEN environment variable is not set")
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start_cmd)); app.add_handler(CallbackQueryHandler(callback)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,message)); app.add_error_handler(error_handler); return app

def main():
    log.info("Starting StructuralBot - Concrete Quantity Takeoff v2"); db.init(); threading.Thread(target=health_server,daemon=True).start(); build_app().run_polling(drop_pending_updates=True)

if __name__=="__main__":
    try: main()
    except Exception: log.exception("FATAL STARTUP ERROR"); raise
