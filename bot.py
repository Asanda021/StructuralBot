import logging, os, threading, tempfile, math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram.error import BadRequest
from app.db import Database
from app.engine import estimate_members, calculate_slab, rebar_summary, grid_rebar, format_estimate
from app.exporter import create_excel, create_pdf
from app.keyboards import main_menu, back_home, section_menu, type_menu, review_menu, report_menu

TOKEN=os.getenv("BOT_TOKEN")
DB_PATH=os.getenv("DATABASE_PATH","/tmp/structuralbot.db")
PORT=int(os.getenv("PORT","10000"))
logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),format="%(asctime)s | StructuralBot | %(levelname)s | %(message)s")
log=logging.getLogger("StructuralBot"); db=Database(DB_PATH)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body=b"StructuralBot OK" if self.path in ("/","/health") else b"Not found"
        self.send_response(200 if self.path in ("/","/health") else 404)
        self.send_header("Content-Type","text/plain"); self.end_headers(); self.wfile.write(body)
    def log_message(self,*_): pass
def health_server(): ThreadingHTTPServer(("0.0.0.0",PORT),HealthHandler).serve_forever()

def fmt(v):
    return f"{float(v):,.3f}".rstrip("0").rstrip(".")

def presets_for(section,typ):
    if section=="ستون" and "×" in typ:
        w,d=[float(x)/100 for x in typ.split("×")]
        return {"width":w,"depth":d}
    return {}

def schema(section,typ):
    if section=="سقف":
        if typ.startswith("تیرچه"):
            return [("طول سقف","m"),("عرض سقف","m"),("فاصله تیرچه","cm"),("طول تیرچه","m"),
                    ("قطر حرارتی","mm"),("فاصله حرارتی","cm")]
        return [("طول سقف","m"),("عرض سقف","m"),("ضخامت/ارتفاع مؤثر سقف","m"),
                ("قطر حرارتی","mm"),("فاصله حرارتی","cm")]
    if section=="فونداسیون":
        return [("تعداد","عدد"),("طول","m"),("عرض","m"),("ضخامت","m"),
                ("قطر میلگرد اصلی","mm"),("فاصله میلگرد اصلی","cm")]
    if section=="ستون":
        return [("تعداد ستون","عدد"),("عرض ستون","m"),("عمق ستون","m"),("ارتفاع","m"),
                ("تعداد میلگرد طولی هر ستون","عدد"),("قطر میلگرد طولی","mm"),
                ("قطر خاموت","mm"),("فاصله خاموت","cm")]
    if section=="تیر":
        return [("تعداد تیر","عدد"),("طول","m"),("عرض","m"),("ارتفاع","m"),
                ("تعداد میلگرد طولی هر تیر","عدد"),("قطر میلگرد طولی","mm"),
                ("قطر خاموت","mm"),("فاصله خاموت","cm")]
    if section=="دیوار":
        return [("طول دیوار","m"),("ارتفاع","m"),("ضخامت","m"),
                ("قطر قائم","mm"),("فاصله قائم","cm"),("قطر افقی","mm"),("فاصله افقی","cm")]
    if section=="پله":
        return [("مساحت","m²"),("ضخامت","m"),("قطر میلگرد اصلی","mm"),("فاصله اصلی","cm"),
                ("قطر حرارتی","mm"),("فاصله حرارتی","cm")]
    return [("مقدار/حجم بتن","m³"),("وزن میلگرد","kg")]

def ask_text(name,fields):
    label,unit=fields[0]
    return f"✏️ <b>{name}</b>\n\n<b>{label}</b> ({unit})\nعدد را وارد کن.\n\n۰ = در صورت نداشتن این جزء"

def calc_member(section,typ,v):
    p=presets_for(section,typ)
    if section=="سقف":
        if typ.startswith("تیرچه"):
            data={"slab_type":typ,"length":v[0],"width":v[1],"joist_spacing_cm":v[2],"joist_length_m":v[3],
                  "thermal_dia":v[4] or None,"thermal_spacing_cm":v[5] or None}
        else:
            data={"slab_type":typ,"length":v[0],"width":v[1],"thickness":v[2],
                  "thermal_dia":v[3] or None,"thermal_spacing_cm":v[4] or None}
        r=calculate_slab(data); comps=[
          {"name":"بتن سقف","value":r["concrete_m3"],"unit":"m³","note":f"مساحت × ضریب/ضخامت = {r['concrete_coeff']:.3f}"},
          {"name":"مساحت سقف","value":r["area_m2"],"unit":"m²"}]
        if "joist_count" in r:
            comps += [{"name":"تعداد تیرچه","value":r["joist_count"],"unit":"عدد","note":f"طول کل {r['joist_total_length_m']:.2f} m"},
                      {"name":"یونولیت","value":r["foam_blocks"],"unit":"عدد","note":"برآورد بر اساس طول تیرچه و بلوک پیش‌فرض 33cm"}]
        if "thermal" in r:
            t=r["thermal"]; comps += [{"name":"شبکه حرارتی - طول","value":t["length_m"],"unit":"m"},
                                      {"name":"شبکه حرارتی - وزن","value":t["weight_kg"],"unit":"kg", "note":f"Φ{t['diameter_mm']:.0f} | {t['branches']} شاخه 12m"},
                                      {"name":"شبکه حرارتی - شاخه خرید","value":t["branches"],"unit":"شاخه"}]
        return comps
    if section=="فونداسیون":
        n,L,W,T,d,s=v; concrete=n*L*W*T; comps=[{"name":"بتن","value":concrete,"unit":"m³"}]
        if d and s:
            r=grid_rebar(L,W,d,s); comps += [{"name":"میلگرد اصلی - وزن","value":n*r["weight_kg"],"unit":"kg","note":f"Φ{d:g} @ {s:g}cm"},
              {"name":"میلگرد اصلی - شاخه خرید","value":n*r["branches"],"unit":"شاخه"}]
        return comps
    if section in ("ستون","تیر"):
        n,a,b,c,bars,d,sd,ss=v
        concrete=n*a*b*c
        length=n*bars*c; r=rebar_summary(d,length) if d and length else {"weight_kg":0,"branches":0}
        stirrups=max(1,math.ceil(c/(ss/100))+1) if ss else 0
        slen=stirrups*(2*(a+b)*0.9)*n
        sr=rebar_summary(sd,slen) if sd and slen else {"weight_kg":0,"branches":0}
        return [{"name":"بتن","value":concrete,"unit":"m³"},
          {"name":"میلگرد طولی - وزن","value":r["weight_kg"],"unit":"kg","note":f"Φ{d:g} | {bars:g} عدد در هر عضو"},
          {"name":"میلگرد طولی - شاخه خرید","value":r["branches"],"unit":"شاخه"},
          {"name":"خاموت - وزن","value":sr["weight_kg"],"unit":"kg","note":f"Φ{sd:g} @ {ss:g}cm"},
          {"name":"خاموت - شاخه خرید","value":sr["branches"],"unit":"شاخه"}]
    if section=="دیوار":
        L,H,T,vd,vs,hd,hs=v; concrete=L*H*T
        comps=[{"name":"بتن","value":concrete,"unit":"m³"}]
        if vd and vs:
            r=grid_rebar(H,L,vd,vs); comps += [{"name":"میلگرد قائم - وزن","value":r["weight_kg"],"unit":"kg"},{"name":"میلگرد قائم - شاخه خرید","value":r["branches"],"unit":"شاخه"}]
        if hd and hs:
            r=grid_rebar(L,H,hd,hs); comps += [{"name":"میلگرد افقی - وزن","value":r["weight_kg"],"unit":"kg"},{"name":"میلگرد افقی - شاخه خرید","value":r["branches"],"unit":"شاخه"}]
        return comps
    if section=="پله":
        area,t,d,s,td,ts=v; comps=[{"name":"بتن پله","value":area*t,"unit":"m³"}]
        if d and s:
            r=grid_rebar(area**0.5,area**0.5,d,s); comps += [{"name":"میلگرد اصلی - وزن","value":r["weight_kg"],"unit":"kg"},{"name":"میلگرد اصلی - شاخه خرید","value":r["branches"],"unit":"شاخه"}]
        if td and ts:
            r=grid_rebar(area**0.5,area**0.5,td,ts); comps += [{"name":"میلگرد حرارتی - وزن","value":r["weight_kg"],"unit":"kg"},{"name":"میلگرد حرارتی - شاخه خرید","value":r["branches"],"unit":"شاخه"}]
        return comps
    return [{"name":"بتن","value":v[0],"unit":"m³"},{"name":"میلگرد","value":v[1],"unit":"kg"}]

def show_member_types(q,section):
    return q.edit_message_text(f"🏗 <b>{section}</b>\n\nنوع عضو را از تیپ‌های آماده انتخاب کن یا سفارشی را بزن.",parse_mode="HTML",reply_markup=type_menu(section))

async def start_cmd(update,context):
    db.ensure_user(update.effective_user.id,update.effective_user.first_name or "")
    context.user_data.clear()
    await update.message.reply_text("🏗 <b>StructuralBot</b>\n\n<b>متره جامع از روی نقشه</b>\nاطلاعات خام نقشه را بگیر؛ ربات مقدار بتن، میلگرد، شاخه، تیرچه و یونولیت را محاسبه می‌کند.",parse_mode="HTML",reply_markup=main_menu())

def reset(context,name):
    context.user_data.clear(); context.user_data.update({"project_name":name,"members":[],"history":[]})

async def review(q,context):
    ms=context.user_data.get("members",[])
    lines=["🔎 <b>بازبینی کامل متره</b>","",f"پروژه: <b>{context.user_data.get('project_name')}</b>"]
    for i,m in enumerate(ms,1):
        lines.append(f"\n<b>{i}. {m['member']}</b> | {m['section']} | {m['type']}")
        for c in m["components"]: lines.append(f"• {c['name']}: {fmt(c['value'])} {c['unit']}")
    if not ms: lines.append("\nهنوز عضوی ثبت نشده.")
    await q.edit_message_text("\n".join(lines),parse_mode="HTML",reply_markup=review_menu())

async def save_final(update,context):
    ms=context.user_data.get("members",[])
    if not ms: await update.callback_query.edit_message_text("هیچ عضوی ثبت نشده.",reply_markup=section_menu()); return
    result=estimate_members(ms); uid=update.effective_user.id
    pid=context.user_data.get("project_id") or db.add_project(uid,context.user_data.get("project_name","پروژه"))
    db.save_estimate(uid,pid,{"members":ms},result,format_estimate(result))
    context.user_data["last_result"]=result
    await update.effective_message.reply_text("✅ <b>متره نهایی ثبت شد</b>\n\n"+format_estimate(result),parse_mode="HTML",reply_markup=report_menu())

async def callback(update,context):
    q=update.callback_query; data=q.data or ""; await q.answer()
    if data=="home":
        context.user_data.clear(); await q.edit_message_text("🏠 <b>منوی اصلی</b>",parse_mode="HTML",reply_markup=main_menu()); return
    if data=="new_project":
        context.user_data.clear(); context.user_data["awaiting_project_name"]=True
        await q.edit_message_text("🏗 نام پروژه را بفرست.",reply_markup=back_home()); return
    if data in ("continue_project","choose_section"):
        if not context.user_data.get("project_name"):
            await q.edit_message_text("ابتدا «پروژه جدید» را بزن.",reply_markup=main_menu()); return
        await q.edit_message_text("📚 <b>بخش سازه</b>\n\nاز روی نقشه، بخش موردنظر را انتخاب کن.",parse_mode="HTML",reply_markup=section_menu()); return
    if data.startswith("sec|"):
        await show_member_types(q,data.split("|",1)[1]); return
    if data.startswith("member|"):
        _,section,typ=data.split("|",2)
        context.user_data.update({"current_section":section,"current_type":typ,"current_values":[],"current_queue":schema(section,typ),"current_edit":None})
        p=presets_for(section,typ)
        if p:
            context.user_data["current_preset"]=p
        await ask_next(q,context); return
    if data.startswith("edit|"):
        idx=int(data.split("|")[1]); m=context.user_data["members"][idx]
        context.user_data.update({"current_section":m["section"],"current_type":m["type"],"current_values":m.get("raw",[]),
                                  "current_queue":schema(m["section"],m["type"]),"current_edit":idx})
        await ask_next(q,context); return
    if data.startswith("delete|"):
        idx=int(data.split("|")[1]); context.user_data["members"].pop(idx); await review(q,context); return
    if data=="edit_members":
        rows=[]
        for i,m in enumerate(context.user_data.get("members",[])):
            rows.append([InlineKeyboardButton(f"✏️ {i+1}. {m['member']}",callback_data=f"edit|{i}"),
                         InlineKeyboardButton("❌",callback_data=f"delete|{i}")])
        rows.append([InlineKeyboardButton("⬅️ بازبینی",callback_data="finish_takeoff")])
        await q.edit_message_text("✏️ <b>اصلاح یا حذف عضو</b>",parse_mode="HTML",reply_markup=InlineKeyboardMarkup(rows)); return
    if data=="finish_takeoff": await review(q,context); return
    if data=="confirm_project": await save_final(update,context); return
    if data=="back":
        await q.edit_message_text("📚 <b>بخش سازه</b>",parse_mode="HTML",reply_markup=section_menu()); return
    if data=="table":
        r=context.user_data.get("last_result") or (db.last_estimate(update.effective_user.id) or {}).get("result")
        await q.edit_message_text(format_estimate(r) if r else "هنوز گزارشی ثبت نشده.",parse_mode="HTML",reply_markup=report_menu() if r else main_menu()); return
    if data=="reports":
        last=db.last_estimate(update.effective_user.id)
        await q.edit_message_text(format_estimate(last["result"]) if last else "هنوز گزارشی ثبت نشده.",parse_mode="HTML",reply_markup=report_menu() if last else main_menu()); return
    if data=="projects":
        ps=db.projects(update.effective_user.id); rows=[[InlineKeyboardButton(p[1],callback_data=f"open|{p[0]}")] for p in ps]
        rows.append([InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")])
        await q.edit_message_text("📂 <b>پروژه‌های من</b>",parse_mode="HTML",reply_markup=InlineKeyboardMarkup(rows)); return
    if data.startswith("open|"):
        p=db.project_estimate(update.effective_user.id,int(data.split("|")[1]))
        if not p: await q.edit_message_text("پروژه پیدا نشد.",reply_markup=main_menu()); return
        ins=p["inputs"]; ms=ins.get("members",[])
        context.user_data.update({"project_name":p["project_name"],"project_id":p["project_id"],"members":ms,"last_result":p["result"]})
        await review(q,context); return
    if data=="exports":
        last=db.last_estimate(update.effective_user.id)
        if not last: await q.edit_message_text("هنوز گزارشی برای خروجی نیست.",reply_markup=main_menu()); return
        with tempfile.TemporaryDirectory() as d:
            x=create_excel(last["result"],last["project_name"],os.path.join(d,"StructuralBot_Takeoff.xlsx"))
            p=create_pdf(last["result"],last["project_name"],os.path.join(d,"StructuralBot_Takeoff.pdf"))
            await update.effective_message.reply_document(open(x,"rb"),caption="📊 Excel - متره جامع")
            await update.effective_message.reply_document(open(p,"rb"),caption="📄 PDF - متره جامع")
        return
    if data in ("pricing","settings","help"):
        msg={"pricing":"💰 قیمت‌گذاری در مرحله بعد روی همین اقلام و واحدها سوار می‌شود.",
             "settings":"⚙️ طول شاخه پیش‌فرض میلگرد ۱۲ متر است و بعداً از تنظیمات قابل تغییر می‌شود.",
             "help":"❓ از روی نقشه بخش و تیپ را انتخاب کن. ربات اطلاعات هندسی و مشخصات آرماتور را می‌گیرد و مقدار بتن، میلگرد، وزن و تعداد شاخه را محاسبه می‌کند."}[data]
        await q.edit_message_text(msg,reply_markup=back_home()); return

async def ask_next(q,context):
    queue=context.user_data.get("current_queue",[])
    if not queue:
        await finish_member(q,context); return
    label,unit=queue[0]
    # apply column presets automatically and skip dimensions
    if context.user_data.get("current_preset") and label in ("عرض ستون","عمق ستون"):
        p=context.user_data["current_preset"]; key="width" if label=="عرض ستون" else "depth"
        context.user_data["current_values"].append(p[key]); context.user_data["current_queue"].pop(0); await ask_next(q,context); return
    await q.edit_message_text(ask_text(context.user_data["current_type"],queue),parse_mode="HTML",reply_markup=back_home())

async def finish_member(q,context):
    section=context.user_data["current_section"]; typ=context.user_data["current_type"]; vals=context.user_data["current_values"]
    try: comps=calc_member(section,typ,vals)
    except Exception as e:
        await q.edit_message_text(f"❌ خطا در محاسبه: {e}",reply_markup=back_home()); return
    idx=context.user_data.get("current_edit")
    m={"section":section,"member":f"{section} {typ}","type":typ,"quantity":1,"components":comps,"raw":vals}
    if idx is None: context.user_data.setdefault("members",[]).append(m)
    else: context.user_data["members"][idx]=m
    context.user_data["current_edit"]=None
    await q.edit_message_text(f"✅ <b>{m['member']}</b> محاسبه شد.\n\nاجزای بتن و آرماتور در همین مرحله ثبت شدند.",parse_mode="HTML",
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ عضو بعدی",callback_data="choose_section")],
                                                                   [InlineKeyboardButton("🔎 بازبینی",callback_data="finish_takeoff")],
                                                                   [InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]]))

async def message(update,context):
    text=(update.message.text or "").strip().replace("،",".")
    if context.user_data.get("awaiting_project_name"):
        if not text or len(text)>120: await update.message.reply_text("❌ نام پروژه نامعتبر است."); return
        reset(context,text); await update.message.reply_text(f"🏗 پروژه «{text}» ساخته شد.",reply_markup=section_menu()); return
    queue=context.user_data.get("current_queue")
    if queue:
        try: value=float(text)
        except ValueError: await update.message.reply_text("❌ فقط عدد وارد کن."); return
        if value<0: await update.message.reply_text("❌ عدد منفی مجاز نیست."); return
        context.user_data["current_values"].append(value); context.user_data["current_queue"].pop(0)
        if context.user_data["current_queue"]:
            label,unit=context.user_data["current_queue"][0]
            await update.message.reply_text(f"⏳ ثبت شد.\n\nمرحله بعد: <b>{label}</b> ({unit})\n۰ = حذف این جزء",parse_mode="HTML",reply_markup=back_home())
        else:
            # continue using a message-only result path
            class Q:
                async def edit_message_text(self,*a,**kw): await update.message.reply_text(*a,**kw)
            await finish_member(Q(),context)
        return
    await update.message.reply_text("از منوی زیر انتخاب کن.",reply_markup=main_menu())

async def error_handler(update,context):
    if isinstance(context.error,BadRequest) and "Message is not modified" in str(context.error): return
    log.error("Unhandled bot error: %s",context.error,exc_info=context.error)

def main():
    if not TOKEN: raise RuntimeError("BOT_TOKEN environment variable is not set")
    db.init(); threading.Thread(target=health_server,daemon=True).start()
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start_cmd)); app.add_handler(CallbackQueryHandler(callback)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,message)); app.add_error_handler(error_handler)
    log.info("Starting StructuralBot - drawing-driven takeoff v3")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
