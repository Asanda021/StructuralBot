import logging, os, threading, tempfile, math, html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram.error import BadRequest
from app.db import Database
from app.engine import estimate_members, calculate_slab, rebar_summary, grid_rebar, multi_face_grid_rebar, repeated_bar_rebar, format_estimate
from app.exporter import create_excel, create_pdf
from ai.assistant import explain_takeoff
from app.keyboards import main_menu, back_home, section_menu, type_menu, review_menu, report_menu, calc_mode_menu, persistent_menu, walls_menu, takeoff_menu, settings_menu, units_menu, standards_menu, concrete_settings_menu, rebar_settings_menu, rebar_equivalency_menu, rebar_equiv_source_menu, rebar_equiv_target_menu, language_menu

TOKEN=os.getenv("BOT_TOKEN")
DB_PATH=os.getenv("DATABASE_PATH","/tmp/structuralbot.db")
PORT=int(os.getenv("PORT","10000"))
logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),format="%(asctime)s | StructuralBot | %(levelname)s | %(message)s")
log=logging.getLogger("StructuralBot"); db=Database(DB_PATH)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            body = b"StructuralBot OK"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()
    def log_message(self, *_): pass
def health_server():
    ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()


def fmt(v):
    return f"{float(v):,.3f}".rstrip("0").rstrip(".")

def presets_for(section,typ):
    if "×" in typ and section in ("ستون","تیر"):
        w,d=[float(x)/100 for x in typ.split("×")]
        if section=="ستون": return {"width":w,"depth":d}
        return {"beam_width":w,"beam_height":d}
    return {}

# Ready values: broad engineering shortcuts to minimize typing.
# These are editable input presets only; they never replace drawing/detail information.
READY_OPTIONS = {
 "تعداد":[1,2,3,4,5,6,8,10,12,16,20],
 "تعداد ستون":[1,2,3,4,6,8,10,12,16,20],
 "تعداد تیر":[1,2,3,4,6,8,10,12,16,20],
 "تعداد دیوار":[1,2,3,4,5,6,8,10],
 "تعداد بازشو":[0,1,2,3,4,5],
 "طول":[1.0,1.2,1.5,1.8,2.0,2.2,2.5,2.8,3.0,3.2,3.5,4.0,4.5,5.0,6.0],
 "عرض":[1.0,1.2,1.5,1.8,2.0,2.2,2.5,2.8,3.0,3.5,4.0,4.5,5.0,6.0],
 "طول سقف":[3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,12.0,15.0],
 "عرض سقف":[3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,12.0],
 "طول دیوار":[2.0,3.0,4.0,5.0,6.0,8.0,10.0],
 "ضخامت":[0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.60],
 "ضخامت مگر":[0.08,0.10,0.12,0.15],
 "ضخامت/ارتفاع مؤثر سقف":[0.15,0.20,0.25,0.30,0.35],
 "ضخامت کل سقف":[0.20,0.25,0.30,0.35,0.40],
 "ضخامت لایه رویه/تاپینگ":[0.04,0.05,0.06,0.07,0.08],
 "ضخامت دیوار":[0.15,0.20,0.25,0.30,0.35,0.40],
 "عرض ستون":[0.30,0.35,0.40,0.45,0.50,0.60],
 "عمق ستون":[0.30,0.35,0.40,0.45,0.50,0.60],
 "ارتفاع":[2.5,2.7,2.8,3.0,3.2,3.5,4.0],
 "عرض تیر":[0.25,0.30,0.35,0.40,0.45,0.50],
 "ارتفاع تیر":[0.40,0.45,0.50,0.55,0.60,0.70,0.80],
 "فاصله تیرچه":[40,45,50,55,60],
 "فاصله ماژول":[5,10,15,20,25,30],
 "فاصله حرارتی":[10,12.5,15,17.5,20,22.5,25,27.5,30,35,40,45],
 "فاصله قائم":[10,12.5,15,17.5,20,22.5,25,30],
 "فاصله افقی":[10,12.5,15,17.5,20,22.5,25,30],
 "فاصله شبکه پایین":[10,12.5,15,17.5,20,22.5,25,30],
 "فاصله شبکه بالا":[10,12.5,15,17.5,20,22.5,25,30],
 "فاصله خاموت":[10,12.5,15,17.5,20,22.5,25,30],
 "فاصله خاموت عادی":[10,12.5,15,17.5,20,22.5,25,30],
 "فاصله خاموت بحرانی":[8,10,12.5,15,17.5,20],
 "فاصله سنجاقی":[10,15,20,25,30],
 "قطر حرارتی":[6,8,10,12],
 "قطر میلگرد شبکه پایین":[10,12,14,16,18,20],
 "قطر میلگرد شبکه بالا":[10,12,14,16,18,20],
 "قطر قائم":[10,12,14,16,18,20],
 "قطر افقی":[8,10,12,14,16],
 "قطر میلگرد طولی":[12,14,16,18,20,22,25,28,32],
 "قطر میلگرد پایینی":[12,14,16,18,20,22,25,28,32],
 "قطر میلگرد بالایی":[10,12,14,16,18,20,22,25,28,32],
 "قطر میلگرد تقویتی":[12,14,16,18,20,22,25,28,32],
 "قطر خاموت":[8,10,12],
 "قطر سنجاقی":[8,10,12],
 "قطر کلاف/ژوئن":[8,10,12,14,16],
 "قطر سنجاقی ژوئن":[8,10],
 "قطر میلگرد منفی":[10,12,14,16,18,20],
 "قطر اتکا/ادکا":[10,12,14,16,18],
 "قطر کمرکش":[10,12,14,16],
 "تعداد میلگرد طولی هر ستون":[4,6,8,10,12,14,16],
 "تعداد میلگرد طولی هر شناژ":[4,6,8,10],
 "تعداد میلگرد پایینی هر تیر":[2,3,4,5,6,8],
 "تعداد میلگرد بالایی هر تیر":[2,3,4,5,6],
 "تعداد میلگرد تقویتی هر تیر":[1,2,3,4,5,6],
 "تعداد سنجاقی هر تیر":[1,2,3,4,6,8],
 "تعداد میلگرد کمرکش":[1,2,3,4,6,8],
 "تعداد وجه مسلح":[1,2],
 "تعداد میلگرد انتظار":[0,2,4,6,8,10,12,16],
 "تعداد کلاف میانی/ژوئن":[0,1,2,3,4,5,6],
 "تعداد سنجاقی ژوئن":[0,2,4,6,8,10,12],
 "تعداد میلگرد منفی":[0,2,4,6,8,10,12,16,20],
 "تعداد اتکا/ادکا":[0,2,4,6,8,10,12,16,20],
 "ضریب بتن":[0.18,0.23],
 "طول یونولیت":[1.0,1.2,1.5,2.0],
 "عرض یونولیت":[0.40,0.50,0.60],
 "طول یونولیت/بلوک":[1.0,1.2,1.5,2.0],
 "عرض یونولیت/بلوک":[0.40,0.50,0.60],
 "طول ماژول خالی":[0.50,0.60,0.70,0.80],
 "عرض ماژول خالی":[0.50,0.60,0.70,0.80],
 "ارتفاع ماژول خالی":[0.15,0.20,0.25,0.30],
 "طول بازشو":[0.60,0.80,1.0,1.2,1.5,2.0],
 "عرض بازشو":[0.60,0.80,1.0,1.2,1.5,2.0],
 "مساحت":[2.0,3.0,4.0,5.0,6.0,8.0,10.0,12.0],
 "ضخامت مگر":[0.08,0.10,0.12,0.15],
 "طول هر خاموت":[0.80,1.00,1.20,1.40,1.60,1.80,2.00],
 "طول هر سنجاقی":[0.50,0.60,0.80,1.00,1.20],
 "طول هر سنجاقی ژوئن":[0.30,0.40,0.50,0.60,0.80],
 "طول هر کلاف/ژوئن":[2.0,3.0,4.0,5.0,6.0],
 "طول هر میلگرد تقویتی":[1.5,2.0,2.5,3.0,4.0],
 "طول هر میلگرد منفی":[1.0,1.5,2.0,2.5,3.0],
 "طول هر اتکا/ادکا":[0.50,0.60,0.80,1.00,1.20],
 "طول هر انتظار":[0.80,1.00,1.20,1.50,2.00],
 "طول هر کمرکش":[1.0,1.5,2.0,2.5,3.0],
}

# Explicit foundation presets: every standard foundation input has selectable shortcuts.
FOUNDATION_READY = {
 "تعداد":[1,2,3,4,6,8,10,12,16,20],
 "طول":[1.0,1.2,1.5,1.8,2.0,2.5,3.0,4.0,5.0,6.0],
 "عرض":[1.0,1.2,1.5,1.8,2.0,2.5,3.0,4.0,5.0,6.0],
 "ضخامت":[0.30,0.35,0.40,0.45,0.50,0.55,0.60,0.70,0.80],
 "ضخامت مگر":[0.08,0.10,0.12,0.15],
 "قطر میلگرد شبکه پایین":[10,12,14,16,18,20,22],
 "فاصله میلگرد شبکه پایین":[10,12.5,15,17.5,20,25,30],
 "قطر میلگرد شبکه بالا":[10,12,14,16,18,20,22],
 "فاصله میلگرد شبکه بالا":[10,12.5,15,17.5,20,25,30],
 "تعداد میلگرد انتظار":[0,2,4,6,8,10,12,16,20],
 "طول هر انتظار":[0.50,0.80,1.00,1.20,1.50,2.00],
 "قطر میلگرد انتظار":[10,12,14,16,18,20],
 "تعداد میلگرد طولی هر شناژ":[4,6,8,10,12],
 "قطر میلگرد طولی":[12,14,16,18,20,22,25,28,32],
 "قطر خاموت":[8,10,12],
 "فاصله خاموت":[10,12.5,15,20,25,30],
 "طول هر خاموت":[0.80,1.00,1.20,1.40,1.60,1.80,2.00],
}

# Exact common isolated-footing presets requested for fast drawing entry.
FOOTING_PRESETS = {
 "پی منفرد":[(1.5,1.5,0.50),(1.8,1.8,0.50),(2.0,2.0,0.50)]
}

COMPOUND_PRESETS = {
    "ستون": {"30×30":[0.30,0.30],"35×35":[0.35,0.35],"40×40":[0.40,0.40],"40×50":[0.40,0.50],"50×50":[0.50,0.50]},
    "تیر": {"30×50":[0.30,0.50],"30×60":[0.30,0.60],"35×60":[0.35,0.60],"40×70":[0.40,0.70]},
}
def compound_options(section, typ, label):
    if section in ("ستون","تیر") and typ in COMPOUND_PRESETS.get(section,{}) and label in ("عرض ستون","عرض تیر"):
        return [(typ, COMPOUND_PRESETS[section][typ])]
    if section=="فونداسیون" and typ=="پی منفرد" and label=="طول":
        return [("1.50×1.50×0.50",[1.50,1.50,0.50]),("1.80×1.80×0.50",[1.80,1.80,0.50]),("2.00×2.00×0.50",[2.00,2.00,0.50])]
    return []
def apply_compound_preset(context, values):
    queue=context.user_data.get("current_queue",[])
    for value in values:
        if not queue: break
        context.user_data.setdefault("current_history",[]).append(queue.pop(0))
        context.user_data.setdefault("current_values",[]).append(value)
    return len(values)
def ready_options(section,typ,label):
    # Foundation fields always expose engineering shortcut buttons; manual entry remains available.
    if section=="فونداسیون":
        if typ=="پی منفرد" and label in ("طول","عرض","ضخامت"):
            vals=FOOTING_PRESETS[typ]
            idx={"طول":0,"عرض":1,"ضخامت":2}[label]
            return list(dict.fromkeys(x[idx] for x in vals))
        if label in FOUNDATION_READY:
            return FOUNDATION_READY[label]
    if label=="ضریب بتن":
        if "دوبل" in typ: return [0.23]
        if "تک" in typ: return [0.18]
    return READY_OPTIONS.get(label, [])

def ready_value(section,typ,label):
    vals=ready_options(section,typ,label)
    return vals[0] if vals else None

def schema(section,typ):
    # Foundation has no pin/snagakhi input in this takeoff model.
    if section=="فونداسیون" and typ!="بتن مگر":
        pass
    if section=="سقف":
        if typ.startswith("تیرچه"):
            return [
              ("طول سقف","m"),("عرض سقف","m"),("فاصله تیرچه","cm"),("طول تیرچه","m"),
              ("قطر حرارتی","mm"),("فاصله حرارتی","cm"),
              ("طول یونولیت/بلوک","m"),("عرض یونولیت/بلوک","m"),
              ("تعداد کلاف میانی/ژوئن","عدد"),("طول هر کلاف/ژوئن","m"),("قطر کلاف/ژوئن","mm"),
              ("تعداد سنجاقی ژوئن","عدد"),("طول هر سنجاقی ژوئن","m"),("قطر سنجاقی ژوئن","mm"),
              ("تعداد میلگرد منفی","عدد"),("طول هر میلگرد منفی","m"),("قطر میلگرد منفی","mm"),
              ("تعداد اتکا/ادکا","عدد"),("طول هر اتکا/ادکا","m"),("قطر اتکا/ادکا","mm"),
              ("تعداد بازشو","عدد"),("طول بازشو","m"),("عرض بازشو","m")
            ]
        if typ in ("وافل","یوبوت"):
            return [
              ("طول سقف","m"),("عرض سقف","m"),("ضخامت کل سقف","m"),("ضخامت لایه رویه/تاپینگ","m"),
              ("طول ماژول خالی","m"),("عرض ماژول خالی","m"),("ارتفاع ماژول خالی","m"),
              ("فاصله ماژول","cm"),("قطر حرارتی","mm"),("فاصله حرارتی","cm"),
              ("تعداد بازشو","عدد"),("طول بازشو","m"),("عرض بازشو","m")
            ]
        return [("طول سقف","m"),("عرض سقف","m"),("ضخامت/ارتفاع مؤثر سقف","m"),
                ("قطر حرارتی","mm"),("فاصله حرارتی","cm"),
                ("تعداد بازشو","عدد"),("طول بازشو","m"),("عرض بازشو","m")]
    if section=="فونداسیون":
        if typ=="بتن مگر":
            return [("تعداد","عدد"),("طول","m"),("عرض","m"),("ضخامت مگر","m")]
        if typ=="شناژ":
            return [("تعداد","عدد"),("طول","m"),("عرض","m"),("ارتفاع","m"),
                    ("تعداد میلگرد طولی هر شناژ","عدد"),("قطر میلگرد طولی","mm"),
                    ("قطر خاموت","mm"),("فاصله خاموت","cm"),("طول هر خاموت","m"),
                    ("تعداد میلگرد انتظار","عدد"),("طول هر انتظار","m"),("قطر میلگرد انتظار","mm")]
        return [("تعداد","عدد"),("طول","m"),("عرض","m"),("ضخامت","m"),
                ("قطر میلگرد شبکه پایین","mm"),("فاصله میلگرد شبکه پایین","cm"),
                ("قطر میلگرد شبکه بالا","mm"),("فاصله میلگرد شبکه بالا","cm"),
                ("تعداد میلگرد انتظار","عدد"),("طول هر انتظار","m"),("قطر میلگرد انتظار","mm")]
    if section=="ستون":
        return [("تعداد ستون","عدد"),("عرض ستون","m"),("عمق ستون","m"),("ارتفاع","m"),
                ("تعداد میلگرد طولی هر ستون","عدد"),("قطر میلگرد طولی","mm"),
                ("قطر خاموت","mm"),("فاصله خاموت","cm"),("طول هر خاموت","m"),
                ("تعداد سنجاقی در هر تراز","عدد"),("طول هر سنجاقی","m"),("قطر سنجاقی","mm")]
    if section=="تیر":
        return [("تعداد تیر","عدد"),("طول","m"),("عرض تیر","m"),("ارتفاع تیر","m"),
                ("تعداد میلگرد پایینی هر تیر","عدد"),("قطر میلگرد پایینی","mm"),
                ("تعداد میلگرد بالایی هر تیر","عدد"),("قطر میلگرد بالایی","mm"),
                ("قطر خاموت","mm"),("فاصله خاموت عادی","cm"),("فاصله خاموت بحرانی","cm"),
                ("طول ناحیه بحرانی هر طرف","m"),("طول هر خاموت","m"),
                ("تعداد میلگرد تقویتی هر تیر","عدد"),("طول هر میلگرد تقویتی","m"),("قطر میلگرد تقویتی","mm"),
                ("تعداد سنجاقی هر تیر","عدد"),("طول هر سنجاقی","m"),("قطر سنجاقی","mm"),
                ("تعداد میلگرد کمرکش","عدد"),("طول هر کمرکش","m"),("قطر کمرکش","mm")]
    if section=="دیوار":
        return [("تعداد دیوار","عدد"),("طول دیوار","m"),("ارتفاع","m"),("ضخامت","m"),
                ("تعداد وجه مسلح","عدد"),("قطر قائم","mm"),("فاصله قائم","cm"),("قطر افقی","mm"),("فاصله افقی","cm"),
                ("قطر تقویتی","mm"),("تعداد تقویتی","عدد"),("طول هر تقویتی","m")]
    if section=="پله":
        return [("تعداد","عدد"),("مساحت","m²"),("ضخامت","m"),("قطر میلگرد اصلی","mm"),("فاصله اصلی","cm"),
                ("قطر حرارتی","mm"),("فاصله حرارتی","cm")]
    return [("مقدار/حجم بتن","m³"),("وزن میلگرد","kg")]

def progress_text(context):
    schema_all=schema(context.user_data.get("current_section",""),context.user_data.get("current_type",""))
    queue=context.user_data.get("current_queue",[])
    completed=max(0,len(schema_all)-len(queue)); total=len(schema_all)
    current=min(total,completed+1) if total else 0
    filled=context.user_data.get("current_values",[])
    summary=[f"{label}: {fmt(filled[i])} {unit}" for i,(label,unit) in enumerate(schema_all) if i<len(filled) and filled[i] is not None]
    bar="🟩"*min(current-1,8)+"⬜"*max(0,min(total-current,8))
    return current,total,bar,summary[-4:]

def input_keyboard(values=None, unit="", compound=None):
    rows=[]
    source=[(str(v),None) for v in values] if not compound else compound
    row=[]
    for title,_ in source:
        row.append(KeyboardButton(f"⚡ {title}" + (f" {unit}" if not compound else "")))
        if len(row)==4: rows.append(row); row=[]
    if row: rows.append(row)
    rows.append([KeyboardButton("✏️ ورود دستی")])
    rows.append([KeyboardButton("⬅️ مرحله قبل"), KeyboardButton("📋 ورودی‌ها")])
    rows.append([KeyboardButton("❌ لغو عضو"), KeyboardButton("🏠 منو")])
    rows.append([KeyboardButton("🔄 شروع مجدد")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False, is_persistent=True,
                               input_field_placeholder="مقدار آماده را انتخاب کن یا ورود دستی بزن")

def field_menu(values=None, unit="", compound=None):
    rows=[]; source=compound if compound else [(str(v),None) for v in (values or [])]
    row=[]
    for title,_ in source:
        row.append(InlineKeyboardButton(f"⚡ {title}" + (f" {unit}" if not compound else ""),callback_data=f"preset|{title}" if compound else f"ready|{title}"))
        if len(row)==4: rows.append(row); row=[]
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("✏️ ورود دستی",callback_data="manual")])
    rows.append([InlineKeyboardButton("⬅️ مرحله قبل",callback_data="back_field"),InlineKeyboardButton("📋 ورودی‌ها",callback_data="show_inputs")])
    rows.append([InlineKeyboardButton("❌ لغو عضو",callback_data="cancel_member"),InlineKeyboardButton("🏠 منو",callback_data="home")])
    rows.append([InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")])
    return InlineKeyboardMarkup(rows)

def ask_text(name,fields,section,typ,values=None,compound=None,context=None):
    label,unit=fields[0]
    current,total,bar,summary=progress_text(context) if context else (1,len(fields),"",[])
    if compound: ready="\n\n⚡ <b>ابعاد آماده:</b> "+" | ".join(x[0] for x in compound)
    elif values: ready=f"\n\n⚡ <b>مقادیر آماده:</b> {' | '.join(str(v) for v in values)} {unit}"
    else: ready=""
    filled="\n📋 <b>ثبت‌شده:</b> "+" | ".join(summary) if summary else ""
    return f"🏗 <b>{name}</b>\n\n<b>مرحله {current} از {total}</b>  {bar}\n\n🎯 <b>{label}</b> ({unit}){ready}{filled}\n\nیکی از گزینه‌های آماده را بزن یا «✏️ ورود دستی» را انتخاب کن.\n⚠️ گزینه‌های آماده فقط میانبر ورود هستند؛ مقدار نهایی باید با نقشه کنترل شود."

def rcomps(title,r,note=""):
    n=int(r.get("count_bars",0)); branches=r.get("branches",0)
    dia=f"Φ{r['diameter_mm']:g}"
    return [
      {"name":f"{title} - تعداد قطعه","value":n,"unit":"عدد","note":note,"category":"میلگرد","diameter_mm":r["diameter_mm"]},
      {"name":f"{title} - طول اجرا","value":r["length_m"],"unit":"m","note":dia,"category":"میلگرد","diameter_mm":r["diameter_mm"],"cut_lengths_m":r.get("cut_lengths_m",[])},
      {"name":f"{title} - وزن اجرا","value":r["weight_kg"],"unit":"kg","note":dia,"category":"میلگرد","diameter_mm":r["diameter_mm"]},
      {"name":f"{title} - شاخه خرید","value":branches,"unit":"شاخه","note":f"{dia} | شاخه {r['stock_length_m']:g}m | وزن خرید {r['procurement_weight_kg']:.2f}kg","category":"میلگرد","diameter_mm":r["diameter_mm"],"procurement_weight_kg":r["procurement_weight_kg"]},
      {"name":f"{title} - طول خرید","value":r.get("procurement_length_m",r["length_m"]),"unit":"m","note":f"{dia} | پرت {r.get('waste_percent',0):g}%","category":"میلگرد","diameter_mm":r["diameter_mm"]}
    ]

def repeated_grid_for_foundation(n,L,W,dia,spacing):
    """Repeat a drawing-defined two-way foundation mesh for each footing/unit."""
    r=grid_rebar(L,W,dia,spacing)
    count=max(1,int(math.ceil(float(n))))
    r["count_bars"]*=count
    r["length_m"]*=count
    r["weight_kg"]*=count
    r["procurement_length_m"]*=count
    r["waste_length_m"]*=count
    r["branches"]=math.ceil(r["procurement_length_m"]/r["stock_length_m"]) if r["procurement_length_m"] else 0
    r["procurement_length_m"]=r["branches"]*r["stock_length_m"]
    r["procurement_weight_kg"]=r["diameter_mm"]**2/162*r["procurement_length_m"]
    r["cut_lengths_m"]=r.get("cut_lengths_m",[])*count
    return r

def calc_member(section,typ,v):
    p=presets_for(section,typ)
    if section=="سقف":
        if typ.startswith("تیرچه"):
            data={"slab_type":typ,"length":v[0],"width":v[1],"joist_spacing_cm":v[2],"joist_length_m":v[3],
                  "thermal_dia":v[4] or None,"thermal_spacing_cm":v[5] or None,
                  "block_length_m":v[6] or 1.0,"block_width_m":v[7] or 0.5,
                  "joan_count":v[8],"joan_length_m":v[9],"joan_dia":v[10],
                  "negative_count":v[14],"negative_length_m":v[15],"negative_dia":v[16],
                  "otka_count":v[17],"otka_length_m":v[18],"otka_dia":v[19],
                  "openings":[{"length":v[21],"width":v[22],"count":v[20]}] if v[20] and v[21] and v[22] else []}
            r=calculate_slab(data)
            comps=[{"name":"بتن سقف","value":r["concrete_m3"],"unit":"m³","note":f"مساحت خالص × ضریب {r['concrete_coeff']:.3f}"},
                   {"name":"مساحت سقف","value":r["area_m2"],"unit":"m²"},{"name":"مساحت بازشو","value":r["opening_area_m2"],"unit":"m²"},
                   {"name":"تعداد تیرچه","value":r["joist_count"],"unit":"عدد","note":f"{r['joist_lines']} خط تیرچه × ضریب سیستم"},
                   {"name":"طول کل تیرچه","value":r["joist_total_length_m"],"unit":"m"},
                   {"name":"بلوک/یونولیت","value":r["block_count"],"unit":"عدد","note":f"{r['block_kind']} | {r['block_length_m']}×{r['block_width_m']}m"}]
            if "thermal" in r: comps += rcomps("شبکه حرارتی دو جهت",r["thermal"],f"X={r['thermal']['bars_each_direction'][0]} | Y={r['thermal']['bars_each_direction'][1]}")
            if r.get("tie_beam_rebar"): comps += rcomps("کلاف/ژوئن",r["tie_beam_rebar"])
            if r.get("negative"): comps += rcomps("میلگرد منفی",r["negative"])
            if r.get("otka"): comps += rcomps("اتکا/ادکا",r["otka"])
            if v[8] and v[9]: comps.append({"name":"تعداد کلاف/ژوئن","value":v[8],"unit":"عدد","note":f"طول هرکدام {v[9]}m"})
            if v[11] and v[12] and v[13]: comps += rcomps("سنجاقی ژوئن",repeated_bar_rebar(v[11],v[12],v[13]))
            return comps
        if typ in ("وافل","یوبوت"):
            L,W,T,top,ml,mw,mh,spacing,td,ts,oc,ol,ow=v
            area=L*W
            pitch_x=ml+spacing/100
            pitch_y=mw+spacing/100
            nx=max(1,math.ceil(L/pitch_x)) if pitch_x>0 else 0
            ny=max(1,math.ceil(W/pitch_y)) if pitch_y>0 else 0
            modules=nx*ny
            void_volume=modules*ml*mw*mh
            opening_area=oc*ol*ow if oc and ol and ow else 0
            concrete=max(0,area*T-void_volume-opening_area*T)
            comps=[{"name":"بتن سقف","value":concrete,"unit":"m³","note":f"حجم خالص {typ} پس از کسر فضای خالی ماژول و بازشو"},
                   {"name":"مساحت سقف","value":area,"unit":"m²"},{"name":"تعداد ماژول خالی","value":modules,"unit":"عدد"},
                   {"name":"حجم فضای خالی","value":void_volume,"unit":"m³"},{"name":"مساحت بازشو","value":opening_area,"unit":"m²"}]
            if td and ts: comps += rcomps("شبکه حرارتی دو جهت",grid_rebar(L,W,td,ts),f"{typ} | X/Y")
            return comps
        L,W,T,td,ts,oc,ol,ow=v
        openings=[{"length":ol,"width":ow,"count":oc}] if oc and ol and ow else []
        r=calculate_slab({"slab_type":typ,"length":L,"width":W,"thickness":T,"thermal_dia":td or None,"thermal_spacing_cm":ts or None,"openings":openings})
        comps=[{"name":"بتن سقف","value":r["concrete_m3"],"unit":"m³","note":f"مساحت خالص × ضخامت {r['concrete_coeff']:.3f}m"},{"name":"مساحت سقف","value":r["area_m2"],"unit":"m²"},{"name":"مساحت بازشو","value":r["opening_area_m2"],"unit":"m²"}]
        if "thermal" in r: comps += rcomps("شبکه حرارتی دو جهت",r["thermal"],f"X={r['thermal']['bars_each_direction'][0]} | Y={r['thermal']['bars_each_direction'][1]}")
        return comps

    if section=="فونداسیون":
        if typ=="بتن مگر":
            n,L,W,T=v; return [{"name":"بتن مگر","value":n*L*W*T,"unit":"m³"},{"name":"مساحت مگر","value":n*L*W,"unit":"m²"}]
        if typ=="شناژ":
            n,L,W,H,bars,d,sd,ss,slen,en,elen,ed=v
            comps=[{"name":"بتن شناژ","value":n*L*W*H,"unit":"m³"}]
            if bars and d: comps += rcomps("میلگرد طولی",repeated_bar_rebar(n*bars,L,d))
            if sd and ss and slen:
                cnt=n*(math.ceil(L/(ss/100))+1)
                comps += rcomps("خاموت شناژ",repeated_bar_rebar(cnt,slen,sd),f"تعداد خاموت از طول و فاصله نقشه؛ طول قطعه از دیتیل")
            if en and elen and ed:
                comps += rcomps("میلگرد انتظار شناژ",repeated_bar_rebar(n*en,elen,ed))
            return comps
        n,L,W,T,bd,bs,td,ts,en,elen,ed=v
        comps=[{"name":"بتن فونداسیون","value":n*L*W*T,"unit":"m³"},{"name":"مساحت فونداسیون","value":n*L*W,"unit":"m²"}]
        if bd and bs:
            comps += rcomps("میلگرد شبکه پایین - دو جهت",repeated_grid_for_foundation(n,L,W,bd,bs))
        if td and ts:
            comps += rcomps("میلگرد شبکه بالا - دو جهت",repeated_grid_for_foundation(n,L,W,td,ts))
        if en and elen and ed:
            comps += rcomps("میلگرد انتظار",repeated_bar_rebar(n*en,elen,ed))
        return comps

    if section=="ستون":
        n,a,b,h,bars,d,sd,ss,slen,pin,plen,pd=v
        comps=[{"name":"بتن ستون","value":n*a*b*h,"unit":"m³"},{"name":"مساحت مقطع","value":a*b,"unit":"m²"}]
        if bars and d: comps += rcomps("میلگرد طولی",repeated_bar_rebar(n*bars,h,d),f"{bars:g} عدد در هر ستون")
        if sd and ss and slen:
            cnt=n*(math.ceil(h/(ss/100))+1); comps += rcomps("خاموت",repeated_bar_rebar(cnt,slen,sd))
        if pin and plen and pd:
            # Number of crossties at each stirrup level is an explicit drawing/detail input.
            levels=max(1,math.ceil(h/(ss/100))+1) if ss else 1
            comps += rcomps("سنجاقی ستون",repeated_bar_rebar(n*levels*pin,plen,pd),
                            f"{pin:g} عدد در هر تراز × {levels:g} تراز")
        return comps

    if section=="تیر":
        # v20 = legacy single longitudinal-bar line; v22 = separate bottom/top bars.
        if len(v)==20:
            n,L,a,h,bars,d,sd,ss,cs,clen,slen,rcount,rlen,rd,pin,plen,pd,kcount,klen,kd=v
            top_bars=0; top_d=0
        else:
            n,L,a,h,bars,d,top_bars,top_d,sd,ss,cs,clen,slen,rcount,rlen,rd,pin,plen,pd,kcount,klen,kd=v
        comps=[{"name":"بتن تیر","value":n*L*a*h,"unit":"m³"},{"name":"طول تیر","value":n*L,"unit":"m"}]
        if bars and d: comps += rcomps("میلگرد پایینی تیر",repeated_bar_rebar(n*bars,L,d),f"{bars:g} عدد در هر تیر")
        if top_bars and top_d: comps += rcomps("میلگرد بالایی تیر",repeated_bar_rebar(n*top_bars,L,top_d),f"{top_bars:g} عدد در هر تیر")
        if sd and slen:
            normal=max(0,L-2*clen)
            c_normal=(math.ceil(normal/(ss/100))+1) if ss and normal>0 else 0
            c_critical=(2*(math.ceil(clen/(cs/100))+1)) if cs and clen>0 else 0
            total=n*(c_normal+c_critical)
            if total:
                comps += rcomps("خاموت",repeated_bar_rebar(total,slen,sd),
                                f"عادی {c_normal} | بحرانی دو طرف {c_critical} | طول قطعه از دیتیل نقشه")
        if rcount and rlen and rd: comps += rcomps("میلگرد تقویتی",repeated_bar_rebar(n*rcount,rlen,rd))
        if pin and plen and pd: comps += rcomps("سنجاقی تیر",repeated_bar_rebar(n*pin,plen,pd))
        if kcount and klen and kd: comps += rcomps("کمرکش تیر",repeated_bar_rebar(n*kcount,klen,kd))
        return comps

    if section=="دیوار":
        # v11 = legacy single-face format; v12 = current two-face format.
        if len(v)==11:
            n,L,H,T,vd,vs,hd,hs,rd,rc,rl=v
            faces=1
        else:
            n,L,H,T,faces,vd,vs,hd,hs,rd,rc,rl=v
        comps=[{"name":"بتن دیوار","value":n*L*H*T,"unit":"m³"},
               {"name":"مساحت یک وجه دیوار","value":n*L*H,"unit":"m²"},
               {"name":"تعداد وجه مسلح","value":faces,"unit":"وجه"}]
        if vd and vs:
            r=multi_face_grid_rebar(H,L,vd,vs,faces)
            r["count_bars"]*=n
            r["length_m"]*=n; r["weight_kg"]*=n; r["branches"]=math.ceil(r["procurement_length_m"]*n/r["stock_length_m"])
            r["procurement_length_m"]=r["branches"]*r["stock_length_m"]
            r["procurement_weight_kg"]=r["diameter_mm"]**2/162*r["procurement_length_m"]
            r["cut_lengths_m"]=r.get("cut_lengths_m",[])*n
            comps += rcomps("میلگرد قائم دو وجه",r,f"{faces:g} وجه × {n:g} دیوار")
        if hd and hs:
            r=multi_face_grid_rebar(L,H,hd,hs,faces)
            r["count_bars"]*=n
            r["length_m"]*=n; r["weight_kg"]*=n; r["branches"]=math.ceil(r["procurement_length_m"]*n/r["stock_length_m"])
            r["procurement_length_m"]=r["branches"]*r["stock_length_m"]
            r["procurement_weight_kg"]=r["diameter_mm"]**2/162*r["procurement_length_m"]
            r["cut_lengths_m"]=r.get("cut_lengths_m",[])*n
            comps += rcomps("میلگرد افقی دو وجه",r,f"{faces:g} وجه × {n:g} دیوار")
        if rd and rc and rl: comps += rcomps("میلگرد تقویتی",repeated_bar_rebar(n*rc,rl,rd))
        return comps

    if section=="پله":
        n,area,t,d,s,td,ts=v
        # Area is intentionally supplied from the drawing; no square-root geometry is
        # invented for the reinforcement cut lengths.
        comps=[{"name":"بتن پله","value":n*area*t,"unit":"m³"},
               {"name":"مساحت پله","value":n*area,"unit":"m²"}]
        if d and s:
            # This is an area-based mesh takeoff. For inclined flights or non-square plans,
            # exact bar lengths must come from the stair detail rather than inferred geometry.
            comps.append({"name":"میلگرد اصلی - قطر","value":d,"unit":"mm",
                           "note":"طول و تعداد قطعات اصلی پله باید از دیتیل اجرایی تعیین شود."})
            comps.append({"name":"میلگرد اصلی - فاصله","value":s,"unit":"cm"})
        if td and ts:
            comps.append({"name":"میلگرد حرارتی - قطر","value":td,"unit":"mm"})
            comps.append({"name":"میلگرد حرارتی - فاصله","value":ts,"unit":"cm"})
        return comps
    return [{"name":"بتن","value":v[0],"unit":"m³"},{"name":"میلگرد","value":v[1],"unit":"kg"}]

def show_member_types(q,section):
    return q.edit_message_text(f"🏗 <b>{section}</b>\n\nنوع عضو را از تیپ‌های آماده انتخاب کن یا سفارشی را بزن.",parse_mode="HTML",reply_markup=type_menu(section))

LANGUAGE_STANDARD = {
    "fa": "iran",
    "en": "aci",
    "ar": "aci",
    "zh": "china",
}
LANGUAGE_NAMES = {"fa":"فارسی","ar":"العربية","en":"English","zh":"中文"}
STANDARD_NAMES = {
    "iran":"مقررات ملی ایران",
    "aci":"ACI 318",
    "ec2":"Eurocode 2",
    "china":"China — GB/T 50010-2010(2024) + GB/T 50011-2010(2024)",
}

async def start_cmd(update,context):
    uid=update.effective_user.id
    db.ensure_user(uid,update.effective_user.first_name or "")
    settings=db.settings(uid)
    context.user_data.clear()
    context.user_data["language"]=settings.get("language","fa")
    await update.message.reply_text(
        "🌐 <b>زبان / Language / اللغة / 语言</b>\n\n"
        "زبان رابط کاربری را انتخاب کن. آیین‌نامه مرجع به‌صورت خودکار بر اساس زبان فعال می‌شود و بعداً از تنظیمات قابل تغییر است.",
        parse_mode="HTML",
        reply_markup=language_menu(initial=True)
    )
def reset(context,name):
    context.user_data.clear(); context.user_data.update({"project_name":name,"members":[],"history":[]})

async def review(q,context):
    ms=context.user_data.get("members",[])
    qa=quality_check_members(ms)
    lines=["🔎 <b>بازبینی کامل پروژه</b>","",f"🏗 پروژه: <b>{html.escape(str(context.user_data.get('project_name','پروژه')))}</b>",
           f"👷 تعداد اعضا: <b>{len(ms)}</b>",
           f"🧱 حجم بتن: <b>{fmt(estimate_members(ms).get('concrete_total_m3',0))} m³</b>" if ms else "🧱 حجم بتن: <b>0 m³</b>",
           "",f"🛡 کنترل خودکار: <b>{'بدون هشدار' if qa['ok'] else str(len(qa['warnings']))+' هشدار'}</b>"]
    for w in qa.get('warnings',[])[:8]:
        lines.append(f"⚠️ {html.escape(str(w))}")
    if ms:
        lines.append("")
        lines.append("📋 <b>اعضای پروژه</b>")
        for i,m in enumerate(ms,1):
            comp_count=len(m.get("components",[]))
            lines.append(f"{i}. <b>{html.escape(str(m.get('member','عضو')))}</b> — {comp_count} قلم متره")
    else:
        lines.append("\nهنوز عضوی ثبت نشده.")
    lines.append("")
    lines.append("برای اصلاح، حذف یا کپی هر عضو از «اصلاح/حذف» استفاده کن.")
    await q.edit_message_text("\n".join(lines),parse_mode="HTML",reply_markup=review_menu())

def _copyable_report(result, project_name):
    lines=[
        "STRUCTURALBOT — گزارش متره و برآورد",
        f"پروژه: {project_name}",
        "",
        f"تعداد اعضا: {result.get('member_count',0)}",
        f"حجم کل بتن: {result.get('concrete_total_m3',0):,.3f} m³",
        "",
        "جمع کل میلگرد — تفکیک نوع"
    ]
    groups={}
    for m in result.get("members",[]):
        for c in m.get("components",[]):
            if c.get("category")!="میلگرد": continue
            name=str(c.get("name","")); dia=c.get("diameter_mm")
            if dia is None: continue
            base=name.split(" - ")[0]
            g=groups.setdefault((base,float(dia)),{"pieces":0,"length":0.0,"weight":0.0,"branches":0,"buy_weight":0.0,"buy_length":0.0})
            if name.endswith(" - تعداد قطعه"): g["pieces"]+=int(c.get("value",0))
            elif name.endswith(" - طول اجرا"): g["length"]+=float(c.get("value",0))
            elif name.endswith(" - وزن اجرا"): g["weight"]+=float(c.get("value",0))
            elif name.endswith(" - شاخه خرید"):
                g["branches"]+=int(c.get("value",0)); g["buy_weight"]+=float(c.get("procurement_weight_kg",0))
            elif name.endswith(" - طول خرید"): g["buy_length"]+=float(c.get("value",0))
    if groups:
        for (base,dia),g in groups.items():
            lines += [
                "",
                f"نوع میلگرد: {base}",
                f"قطر: Φ{dia:g}",
                f"تعداد قطعه: {g['pieces']}",
                f"طول اجرا: {g['length']:.2f} m",
                f"وزن اجرا: {g['weight']:.2f} kg",
                f"شاخه خرید: {g['branches']}",
                f"طول خرید: {g['buy_length']:.2f} m",
                f"وزن خرید: {g['buy_weight']:.2f} kg",
            ]
    else:
        lines.append("میلگردی ثبت نشده است.")
    lines += ["","خلاصه خرید بر اساس قطر"]
    for dia,d in result.get("rebar_by_diameter",{}).items():
        lines.append(f"Φ{dia}: {d.get('branches',0)} شاخه | {d.get('procurement_weight_kg',0):.2f} kg خرید | {d.get('weight_kg',0):.2f} kg اجرا")
    lines += ["","کنترل کیفیت: "+("بدون هشدار" if result.get("qa",{}).get("ok") else f"{len(result.get('qa',{}).get('warnings',[]))} هشدار")]
    for w in result.get("qa",{}).get("warnings",[])[:12]:
        lines.append("هشدار: "+str(w))
    if result.get("ai_explanation"):
        lines += ["","توضیح هوشمند:",str(result["ai_explanation"])]
    return "\n".join(lines)

async def save_final(update,context):
    ms=context.user_data.get("members",[])
    if not ms: await update.callback_query.edit_message_text("هیچ عضوی ثبت نشده.",reply_markup=section_menu()); return
    result=estimate_members(ms); uid=update.effective_user.id
    result["report_mode"]=db.settings(uid).get("calc_mode","detailed")
    result["project_settings"]=db.settings(uid)
    if result["project_settings"].get("standard")=="china":
        result["project_settings"]["china_codes"]=["GB/T 50010-2010(2024)","GB/T 50011-2010(2024)"]
    pid=context.user_data.get("project_id") or db.add_project(uid,context.user_data.get("project_name","پروژه"))
    db.save_estimate(uid,pid,{"members":ms},result,format_estimate(result))
    context.user_data["last_result"]=result

    async def _background_ai():
        explanation=await explain_takeoff(result, db.settings(uid).get("language","fa"))
        if explanation:
            result["ai_explanation"]=explanation
            db.update_latest_estimate_result(uid,pid,result)
            context.user_data["last_result"]=result

    # AI runs behind the takeoff flow; it never changes quantities or design data.
    context.application.create_task(_background_ai(), update=update)
    await update.effective_message.reply_text(
        "✅ <b>متره نهایی ثبت شد</b>\n\n"+format_estimate(result)+
        "\n\n🧠 توضیحات هوشمند در پس‌زمینه در حال آماده‌سازی است.",
        parse_mode="HTML",reply_markup=report_menu()
    )

async def callback(update,context):
    q=update.callback_query; data=q.data or ""; await q.answer()
    if data=="home":
        context.user_data.clear()
        await q.edit_message_text("🏠 <b>منوی اصلی</b>",parse_mode="HTML",reply_markup=main_menu())
        await q.message.reply_text("",reply_markup=ReplyKeyboardRemove())
        return
    if data=="calc_mode":
        await q.edit_message_text("🧮 <b>شروع برآورد</b>\n\nبرای ورود به موارد برآوردی، دکمه زیر را بزن.",parse_mode="HTML",reply_markup=calc_mode_menu())
        return
    if data=="start_estimate":
        if not context.user_data.get("project_name"):
            context.user_data["project_name"]="برآورد جدید"
            context.user_data.setdefault("members",[])
        await q.edit_message_text("📚 <b>موارد برآوردی</b>\n\nعضو سازه‌ای موردنظر را انتخاب کن.",parse_mode="HTML",reply_markup=section_menu())
        return
    if data=="settings":
        s=db.settings(update.effective_user.id)
        msg=(f"⚙️ <b>تنظیمات متره</b>\\n\\n"
             f"زبان: <b>{s.get('language','fa')}</b>\\n"
             f"واحد: <b>{s.get('unit_system','metric')}</b>\\n"
             f"حالت متره: <b>{s.get('calc_mode','detailed')}</b>\\n"
             f"بتن: <b>{s.get('concrete_grade','C25')}</b>\\n"
             f"میلگرد: <b>{s.get('rebar_grade','A3')}</b>\\n"
             f"مرجع: <b>{s.get('standard','iran')}</b>\\n"
             f"شاخه خرید: <b>{s.get('stock_length_m',12):g}m</b>\\n\\n"
             "این گزینه‌ها فقط مشخصات پروژه/گزارش هستند و هیچ طراحی سازه‌ای را خودکار نمی‌کنند.")
        await q.edit_message_text(msg,parse_mode="HTML",reply_markup=settings_menu()); return
    if data=="account":
        await q.edit_message_text("👤 <b>حساب کاربری</b>\\n\\nپروژه‌های ذخیره‌شده و آخرین متره‌های شما از این بخش مدیریت می‌شوند.",parse_mode="HTML",reply_markup=back_home()); return
    if data=="takeoff_menu":
        await q.edit_message_text("📦 <b>انتخاب نوع متره</b>",parse_mode="HTML",reply_markup=takeoff_menu()); return
    if data.startswith("takeoff|"):
        kind=data.split("|",1)[1]
        titles={"concrete":"🧱 بتن","rebar":"🔩 میلگرد","formwork":"🪵 قالب‌بندی","materials":"🧱 مصالح"}
        if kind=="rebar":
            await q.edit_message_text("🔩 <b>میلگرد</b>\\n\\nمتره میلگرد از روی دیتیل نقشه انجام می‌شود. برای معادل‌سازی قطرها از گزینه زیر استفاده کن.",parse_mode="HTML",reply_markup=rebar_equivalency_menu()); return
        if kind=="concrete":
            await q.edit_message_text("🧱 <b>بتن</b>\\n\\nهندسه اعضا یک‌بار از روی نقشه وارد می‌شود و حجم بتن در همان عضو محاسبه می‌گردد.",parse_mode="HTML",reply_markup=section_menu()); return
        if kind=="formwork":
            await q.edit_message_text("🪵 <b>قالب‌بندی</b>\\n\\nساختار منوی قالب‌بندی فعال شد؛ مقادیر باید از هندسه واقعی عضو و دیتیل اجرایی پروژه استخراج شوند.",parse_mode="HTML",reply_markup=section_menu()); return
        await q.edit_message_text("🧱 <b>مصالح</b>\\n\\nمصالح متره‌شده شامل بتن، میلگرد، تیرچه/یونولیت و اجزای اجرایی در گزارش جامع جمع می‌شوند.",parse_mode="HTML",reply_markup=report_menu()); return
    if data=="units":
        await q.edit_message_text("📏 <b>سیستم واحد</b>",parse_mode="HTML",reply_markup=units_menu()); return
    if data.startswith("unit|"):
        val=data.split("|",1)[1]
        db.set_settings(update.effective_user.id,unit_system=val)
        await q.edit_message_text(f"✅ سیستم واحد روی <b>{val}</b> ذخیره شد.",parse_mode="HTML",reply_markup=settings_menu()); return
    if data=="standards":
        await q.edit_message_text("📐 <b>مرجع گزارش</b>\\n\\nاین انتخاب فقط به‌عنوان مشخصات/مرجع گزارش ذخیره می‌شود؛ StructuralBot در این پروژه طراحی سازه انجام نمی‌دهد.",parse_mode="HTML",reply_markup=standards_menu()); return
    if data.startswith("standard|"):
        val=data.split("|",1)[1]
        db.set_settings(update.effective_user.id,standard=val)
        names={"iran":"مقررات ملی ایران","aci":"ACI 318","ec2":"Eurocode 2","china":"China GB/T 50010-2010(2024) + GB/T 50011-2010(2024)"}
        await q.edit_message_text(f"✅ مرجع گزارش: <b>{names.get(val,val)}</b>\\n\\nبرای حالت چین، استاندارد بتن GB/T 50010-2010(2024) در گزارش ثبت می‌شود و استاندارد لرزه‌ای GB/T 50011-2010(2024) نیز به‌عنوان مرجع پروژه درج می‌گردد. این انتخاب طراحی خودکار انجام نمی‌دهد.",parse_mode="HTML",reply_markup=settings_menu()); return
    if data=="concrete_settings":
        await q.edit_message_text("🏗 <b>رده بتن</b>",parse_mode="HTML",reply_markup=concrete_settings_menu()); return
    if data.startswith("concrete_grade|"):
        val=data.split("|",1)[1]
        db.set_settings(update.effective_user.id,concrete_grade=val)
        await q.edit_message_text(f"✅ رده بتن <b>{val}</b> ذخیره شد.",parse_mode="HTML",reply_markup=settings_menu()); return
    if data=="rebar_settings":
        await q.edit_message_text("🔩 <b>گرید میلگرد</b>",parse_mode="HTML",reply_markup=rebar_settings_menu()); return
    if data.startswith("rebar_grade|"):
        val=data.split("|",1)[1]
        db.set_settings(update.effective_user.id,rebar_grade=val)
        await q.edit_message_text(f"✅ گرید میلگرد <b>{val}</b> ذخیره شد.",parse_mode="HTML",reply_markup=settings_menu()); return
    if data=="stock_length":
        db.set_settings(update.effective_user.id,stock_length_m=12.0)
        await q.edit_message_text("📏 طول شاخه استاندارد خرید فعلاً <b>۱۲ متر</b> است.",parse_mode="HTML",reply_markup=settings_menu()); return
    if data=="building_info":
        await q.edit_message_text("🏢 <b>اطلاعات ساختمان</b>\\n\\nنام پروژه، تعداد طبقات و مشخصات کلی پروژه در جریان «پروژه جدید» ثبت می‌شوند. هندسه هر عضو نیز مرحله‌به‌مرحله از نقشه گرفته می‌شود.",parse_mode="HTML",reply_markup=back_home()); return
    if data=="pricing":
        await q.edit_message_text("💰 <b>برآورد ریالی</b>\\n\\nمنوی آن در ساختار محصول قرار گرفت، اما نرخ‌گذاری تا پایدار شدن متره و گزارش‌های مصالح به‌صورت خودکار عددسازی نمی‌کند.",parse_mode="HTML",reply_markup=back_home()); return
    if data=="rebar_equiv":
        await q.edit_message_text(
            "🔁 <b>معادل‌سازی میلگرد</b>\n\n"
            "روند طبق ساختار تعریف‌شده:\n"
            "۱️⃣ تعداد میلگرد فعلی\n"
            "۲️⃣ قطر میلگرد فعلی\n"
            "۳️⃣ فقط قطر میلگرد جایگزین\n"
            "۴️⃣ محاسبه تعداد میلگرد جایگزین",
            parse_mode="HTML", reply_markup=rebar_equivalency_menu()
        ); return
    if data.startswith("eqcountstart|"):
        count=int(data.split("|",1)[1])
        context.user_data["rebar_equiv_count"]=count
        await q.edit_message_text(
            f"🔁 <b>تعداد فعلی: {count} عدد</b>\n\nحالا قطر میلگرد فعلی را انتخاب کن.",
            parse_mode="HTML", reply_markup=rebar_equiv_source_menu(count)
        ); return
    if data.startswith("eqsrc|"):
        _,a,b=data.split("|")
        count=int(a); source=int(b)
        context.user_data["rebar_equiv_count"]=count
        context.user_data["rebar_equiv_source"]=source
        await q.edit_message_text(
            f"🔁 <b>میلگرد فعلی: {count}Φ{source}</b>\n\nحالا فقط <b>قطر میلگرد جایگزین</b> را انتخاب کن.",
            parse_mode="HTML", reply_markup=rebar_equiv_target_menu(count,source)
        ); return
    if data.startswith("eqdst|"):
        _,a,b,c=data.split("|")
        count=int(a); source=int(b); target=int(c)
        area_old=count*math.pi*source*source/4.0
        area_new_one=math.pi*target*target/4.0
        new_count=math.ceil(area_old/area_new_one)
        area_new=new_count*area_new_one
        increase=(area_new/area_old-1.0)*100.0 if area_old else 0.0
        await q.edit_message_text(
            "🔁 <b>نتیجه معادل‌سازی میلگرد</b>\n\n"
            f"میلگرد فعلی: <b>{count}Φ{source}</b>\n"
            f"سطح مقطع فعلی: <b>{area_old:.2f} mm²</b>\n\n"
            f"میلگرد جایگزین: <b>{new_count}Φ{target}</b>\n"
            f"سطح مقطع جایگزین: <b>{area_new:.2f} mm²</b>\n"
            f"افزایش سطح مقطع: <b>{increase:.2f}%</b>\n\n"
            "تعداد جایگزین رو به بالا گرد شده تا سطح مقطع فولاد کمتر از مقدار فعلی نشود.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 معادل‌سازی جدید",callback_data="rebar_equiv")],
                [InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]
            ])
        ); return
    if data=="language":
        await q.edit_message_text("🌐 <b>انتخاب زبان رابط کاربری</b>",parse_mode="HTML",reply_markup=language_menu()); return
    if data.startswith("lang|"):
        lang=data.split("|",1)[1]
        standard=LANGUAGE_STANDARD.get(lang,"iran")
        db.set_settings(update.effective_user.id,language=lang,standard=standard)
        context.user_data["language"]=lang
        context.user_data["standard"]=standard
        await q.edit_message_text(
            f"✅ <b>{LANGUAGE_NAMES.get(lang,lang)}</b> فعال شد.\n\n"
            f"📐 مرجع پیش‌فرض: <b>{STANDARD_NAMES.get(standard,standard)}</b>\n"
            "این مرجع در پس‌زمینه برای گزارش و کنترل پروژه ثبت شد و از ⚙️ تنظیمات قابل تغییر است.",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        await q.message.reply_text("",reply_markup=ReplyKeyboardRemove())
        return
    if data=="restart":
        context.user_data.clear()
        await q.edit_message_text("🔄 <b>شروع مجدد</b>\n\nابتدا زبان را انتخاب کن.",parse_mode="HTML",reply_markup=language_menu(initial=True)); return
    if data=="new_project":
        context.user_data.clear()
        context.user_data["project_name"]="پروژه جدید"
        context.user_data["members"]=[]
        await q.edit_message_text("🏗 <b>پروژه جدید</b>\n\nحالا اعضای سازه را از روی نقشه اضافه کن.",parse_mode="HTML",reply_markup=section_menu()); return
    if data=="start_estimate":
        context.user_data.clear()
        context.user_data["project_name"]="پروژه جدید"
        context.user_data["members"]=[]
        await q.edit_message_text("🧮 <b>شروع برآورد جدید</b>\n\nاز روی نقشه، بخش موردنظر را انتخاب کن.",parse_mode="HTML",reply_markup=section_menu()); return
    if data=="continue_project":
        uid=update.effective_user.id
        saved=db.last_estimate(uid)
        if not saved:
            await q.edit_message_text("📂 <b>برآورد ذخیره‌شده‌ای پیدا نشد.</b>\n\nابتدا یک برآورد جدید شروع کن.",parse_mode="HTML",reply_markup=main_menu()); return
        inputs=saved.get("inputs") or {}
        members=inputs.get("members",[]) if isinstance(inputs,dict) else []
        context.user_data.clear()
        context.user_data["project_id"]=saved["project_id"]
        context.user_data["project_name"]=saved["project_name"]
        context.user_data["members"]=members
        context.user_data["last_result"]=saved.get("result") or None
        await q.edit_message_text(
            f"📂 <b>ادامه برآورد</b>\n\n"
            f"🏗 پروژه: <b>{saved['project_name']}</b>\n"
            f"👷 تعداد اعضای ذخیره‌شده: <b>{len(members)}</b>\n\n"
            "می‌توانی عضو جدید اضافه کنی یا اعضای پروژه را از بازبینی اصلاح کنی.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ افزودن عضو",callback_data="choose_section")],
                [InlineKeyboardButton("🔎 بازبینی پروژه",callback_data="finish_takeoff")],
                [InlineKeyboardButton("📋 جدول جامع",callback_data="table")],
                [InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]
            ])
        ); return
    if data=="choose_section":
        if not context.user_data.get("project_name"):
            context.user_data["project_name"]="پروژه جدید"
        context.user_data.setdefault("members",[])
        await q.edit_message_text("📚 <b>انتخاب عضو</b>\n\nبخش موردنظر را انتخاب کن.",parse_mode="HTML",reply_markup=section_menu()); return
    if data=="walls_menu":
        await q.edit_message_text("🧱 <b>دیوارها</b>\n\nنوع دیوار را انتخاب کن:",parse_mode="HTML",reply_markup=walls_menu()); return
    if data.startswith("sec|"):
        await show_member_types(q,data.split("|",1)[1]); return
    if data.startswith("member|"):
        _,section,typ=data.split("|",2)
        sc=schema(section,typ)
        preset_values=list(COMPOUND_PRESETS.get(section,{}).get(typ,[]))
        if section=="فونداسیون" and typ=="پی منفرد":
            preset_values=[]
        context.user_data.update({"current_section":section,"current_type":typ,"current_values":preset_values,
                                  "current_queue":sc[len(preset_values):],"current_history":[],"current_edit":None,"current_preset":presets_for(section,typ)})
        await ask_next(q,context); return
    if data.startswith("edit|"):
        idx=int(data.split("|")[1]); m=context.user_data["members"][idx]
        raw=list(m.get("raw",[])); sc=schema(m["section"],m["type"])
        preset_count=len(COMPOUND_PRESETS.get(m["section"],{}).get(m["type"],[]))
        context.user_data.update({"current_section":m["section"],"current_type":m["type"],"current_values":raw[:preset_count],
                                  "current_history":[],"current_queue":sc[preset_count:],"current_edit":idx,"current_preset":presets_for(m["section"],m["type"])})
        await ask_next(q,context); return
    if data.startswith("delete|"):
        idx=int(data.split("|")[1]); context.user_data["members"].pop(idx); await review(q,context); return
    if data.startswith("copy|"):
        idx=int(data.split("|")[1]); src=context.user_data.get("members",[])[idx]
        import copy
        newm=copy.deepcopy(src)
        newm["member"]=newm.get("member","عضو")+" - کپی"
        context.user_data["members"].insert(idx+1,newm)
        await review(q,context); return
    if data=="edit_members":
        rows=[]
        for i,m in enumerate(context.user_data.get("members",[])):
            rows.append([InlineKeyboardButton(f"✏️ {i+1}. {m['member']}",callback_data=f"edit|{i}"),InlineKeyboardButton("📑",callback_data=f"copy|{i}"),InlineKeyboardButton("❌",callback_data=f"delete|{i}")])
        rows.append([InlineKeyboardButton("⬅️ بازبینی",callback_data="finish_takeoff")])
        await q.edit_message_text("✏️ <b>اصلاح یا حذف عضو</b>",parse_mode="HTML",reply_markup=InlineKeyboardMarkup(rows)); return
    if data=="member_calculate":
        idx=context.user_data.get("current_member_index"); ms=context.user_data.get("members",[])
        if idx is None or idx<0 or idx>=len(ms):
            await q.edit_message_text("❌ عضو جاری پیدا نشد.",reply_markup=section_menu()); return
        m=ms[idx]; result=estimate_members([m])
        concrete=result.get("concrete_total_m3",0)

        groups={}
        for comp in m.get("components",[]):
            if comp.get("category")!="میلگرد": continue
            name=str(comp.get("name",""))
            dia=comp.get("diameter_mm")
            if dia is None: continue
            base=name.split(" - ")[0]
            g=groups.setdefault((base,float(dia)),{
                "pieces":0,"length":0.0,"weight":0.0,"branches":0,
                "buy_weight":0.0,"buy_length":0.0,"stock":12.0,"cut_lengths":[]
            })
            if name.endswith(" - تعداد قطعه"):
                g["pieces"]+=int(comp.get("value",0))
            elif name.endswith(" - طول اجرا"):
                g["length"]+=float(comp.get("value",0))
                g["cut_lengths"] += [float(x) for x in comp.get("cut_lengths_m",[]) if x is not None]
            elif name.endswith(" - وزن اجرا"):
                g["weight"]+=float(comp.get("value",0))
            elif name.endswith(" - شاخه خرید"):
                g["branches"]+=int(comp.get("value",0))
                g["buy_weight"]+=float(comp.get("procurement_weight_kg",0))
                note=str(comp.get("note",""))
                if "شاخه " in note and "m" in note:
                    try: g["stock"]=float(note.split("شاخه ",1)[1].split("m",1)[0])
                    except Exception: pass
            elif name.endswith(" - طول خرید"):
                g["buy_length"]+=float(comp.get("value",0))

        tw=tb=tl=tp=buy_weight=buy_length=waste=0.0
        blocks=[]
        for n,(key,g) in enumerate(groups.items(),1):
            base,dia=key
            length_each=(g["length"]/g["pieces"]) if g["pieces"] else 0
            if g["cut_lengths"]:
                unique=sorted(set(round(x,3) for x in g["cut_lengths"]))
                if len(unique)==1: length_each=unique[0]
            if not g["buy_length"] and g["branches"]:
                g["buy_length"]=g["branches"]*g["stock"]
            g["waste"]=max(0.0,g["buy_length"]-g["length"])
            blocks += [
                f"<b>{n}. {base}</b>",
                f"قطر: <b>Φ{dia:g}</b>",
                f"تعداد قطعه: <b>{g['pieces']} عدد</b>",
                f"طول هر قطعه: <b>{length_each:.2f} m</b>",
                f"طول کل اجرا: <b>{g['length']:.2f} m</b>",
                f"شاخه خرید: <b>{g['branches']} × {g['stock']:g}m</b>",
                f"طول خرید: <b>{g['buy_length']:.2f} m</b>",
                f"پرت خرید: <b>{g['waste']:.2f} m</b>",
                f"وزن اجرا: <b>{g['weight']:.2f} kg</b>",
                f"وزن خرید: <b>{g['buy_weight']:.2f} kg</b>",
                "────────────────"
            ]
            tp+=g["pieces"]; tb+=g["branches"]; tl+=g["length"]; tw+=g["weight"]
            buy_weight+=g["buy_weight"]; buy_length+=g["buy_length"]; waste+=g["waste"]

        other=[]
        for comp in m.get("components",[]):
            if comp.get("category")=="میلگرد": continue
            name=str(comp.get("name",""))
            # Concrete and area are already shown in the member summary.
            if name in ("بتن فونداسیون","بتن پله","بتن","مساحت فونداسیون","مساحت پله"):
                continue
            other.append(f"• {name}: <b>{fmt(comp['value'])}</b> {comp['unit']}")

        lines=[
            "🧮 <b>محاسبات نهایی عضو</b>","",
            f"🏷 <b>عضو:</b> {m['member']}",
            f"🧱 <b>حجم بتن:</b> {fmt(concrete)} m³",
        ]
        for comp in m.get("components",[]):
            if comp.get("category")!="میلگرد" and comp.get("name") in ("مساحت فونداسیون","مساحت پله"):
                lines.append(f"📐 <b>مساحت:</b> {fmt(comp['value'])} {comp['unit']}")
                break
        lines += ["","🔩 <b>جزئیات میلگرد</b>"]
        if blocks: lines += blocks[:-1]
        else: lines.append("میلگردی برای این عضو ثبت نشده است.")
        lines += [
            "",
            "════════════════════════",
            "📊 <b>جمع میلگرد عضو</b>","",
            f"تعداد کل قطعات: <b>{int(tp)} عدد</b>",
            f"طول کل اجرا: <b>{tl:.2f} m</b>",
            f"وزن کل اجرا: <b>{tw:.2f} kg</b>",
            "",
            f"شاخه خرید: <b>{int(tb)} شاخه</b>",
            f"طول کل خرید: <b>{buy_length:.2f} m</b>",
            f"پرت خرید: <b>{waste:.2f} m</b>",
            f"وزن کل خرید: <b>{buy_weight:.2f} kg</b>",
        ]
        if other:
            lines += ["","📦 <b>سایر اقلام متره</b>",*other]

        await q.edit_message_text("\n".join(lines),parse_mode="HTML",reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 کپی نتیجه عضو",callback_data="copy_member_output")],
            [InlineKeyboardButton("✅ تأیید نهایی عضو",callback_data="member_confirm")],
            [InlineKeyboardButton("✏️ اصلاح عضو",callback_data="member_edit")],
            [InlineKeyboardButton("🔎 بازبینی پروژه",callback_data="finish_takeoff")],
            [InlineKeyboardButton("➕ عضو بعدی",callback_data="choose_section")]
        ])); return
    if data=="member_confirm":
        idx=context.user_data.get("current_member_index"); ms=context.user_data.get("members",[])
        if idx is None or idx<0 or idx>=len(ms):
            await q.edit_message_text("❌ عضو جاری پیدا نشد.",reply_markup=section_menu()); return
        m=ms[idx]
        await q.edit_message_text(f"✅ <b>{m['member']}</b> با موفقیت تأیید نهایی شد.\n\nاین عضو در متره پروژه ثبت شد و آماده ورود به عضو بعدی یا بازبینی کامل پروژه است.",parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ عضو بعدی",callback_data="choose_section")],
                [InlineKeyboardButton("🔎 بازبینی پروژه",callback_data="finish_takeoff")],
                [InlineKeyboardButton("✏️ اصلاح عضو",callback_data="member_edit")],
                [InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]
            ])); return
    if data=="member_edit":
        idx=context.user_data.get("current_member_index"); ms=context.user_data.get("members",[])
        if idx is None or idx<0 or idx>=len(ms):
            await q.edit_message_text("❌ عضو جاری پیدا نشد.",reply_markup=section_menu()); return
        m=ms[idx]; raw=list(m.get("raw",[])); sc=schema(m["section"],m["type"])
        preset_count=len(COMPOUND_PRESETS.get(m["section"],{}).get(m["type"],[]))
        context.user_data.update({"current_section":m["section"],"current_type":m["type"],"current_values":raw[:preset_count],
                                  "current_queue":sc[preset_count:],"current_history":[],"current_edit":idx,
                                  "current_preset":presets_for(m["section"],m["type"])})
        await ask_next(q,context); return
    if data=="finish_takeoff": await review(q,context); return
    if data=="confirm_project":
        ms=context.user_data.get("members",[])
        qa=quality_check_members(ms)
        result=estimate_members(ms) if ms else {"concrete_total_m3":0,"rebar_by_diameter":{}}
        concrete=result.get("concrete_total_m3",0)
        rebar=sum(float(x.get("weight_kg",0)) for x in result.get("rebar_by_diameter",{}).values())
        warnings=len(qa.get("warnings",[]))
        await q.edit_message_text(
            "🔐 <b>تأیید نهایی پروژه</b>\\n\\n"
            f"پروژه: <b>{context.user_data.get('project_name','-')}</b>\\n"
            f"تعداد اعضا: <b>{len(ms)}</b>\\n"
            f"بتن: <b>{fmt(concrete)} m³</b>\\n"
            f"وزن میلگرد اجرا: <b>{fmt(rebar)} kg</b>\\n"
            f"هشدار کنترل: <b>{warnings}</b>\\n\\n"
            "بعد از ذخیره نهایی، گزارش پروژه به‌عنوان آخرین متره ثبت می‌شود.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💾 تأیید و ذخیره نهایی",callback_data="final_save")],
                [InlineKeyboardButton("✏️ اصلاح",callback_data="edit_members")],
                [InlineKeyboardButton("⬅️ بازگشت به بازبینی",callback_data="finish_takeoff")]
            ])
        )
        return
    if data=="final_save":
        await save_final(update,context); return
    if data=="back":
        await q.edit_message_text("📚 <b>بخش سازه</b>",parse_mode="HTML",reply_markup=section_menu()); return
    if data=="table":
        r=context.user_data.get("last_result")
        if not r and context.user_data.get("members"):
            r=estimate_members(context.user_data["members"])
            context.user_data["last_result"]=r
        if not r:
            last=db.last_estimate(update.effective_user.id)
            r=last["result"] if last else None
        extra=(f"\n\n🧠 <b>توضیح هوشمند</b>\n{r.get('ai_explanation')}" if r and r.get("ai_explanation") else "")
        await q.edit_message_text((format_estimate(r)+extra) if r else "هنوز عضوی برای جدول جامع ثبت نشده است.",parse_mode="HTML",reply_markup=report_menu() if r else main_menu()); return
    if data=="reports":
        r=context.user_data.get("last_result")
        if not r and context.user_data.get("members"):
            r=estimate_members(context.user_data["members"])
            context.user_data["last_result"]=r
        if not r:
            last=db.last_estimate(update.effective_user.id)
            r=last["result"] if last else None
        extra=(f"\n\n🧠 <b>توضیح هوشمند</b>\n{r.get('ai_explanation')}" if r and r.get("ai_explanation") else "")
        await q.edit_message_text((format_estimate(r)+extra) if r else "هنوز گزارشی ثبت نشده است.",parse_mode="HTML",reply_markup=report_menu() if r else main_menu()); return
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
    if data=="show_inputs":
        queue=context.user_data.get("current_queue",[])
        values=context.user_data.get("current_values",[])
        history=context.user_data.get("current_history",[])
        lines=["📋 <b>وضعیت ورود اطلاعات</b>","",f"عضو: <b>{context.user_data.get('current_type','')}</b>"]
        if history:
            for i,(label,unit) in enumerate(history):
                lines.append(f"✅ {label}: <b>{fmt(values[i])}</b> {unit}")
        if queue:
            label,unit=queue[0]
            lines += ["",f"⏳ مرحله فعلی: <b>{label}</b> ({unit})"]
        await q.edit_message_text("\n".join(lines),parse_mode="HTML",reply_markup=field_menu(ready_value(context.user_data.get("current_section",""),context.user_data.get("current_type",""),queue[0][0]) if queue else None,queue[0][1] if queue else ""))
        return
    if data=="cancel_member":
        for k in ("current_section","current_type","current_values","current_queue","current_history","current_edit","current_preset"):
            context.user_data.pop(k,None)
        await q.edit_message_text("❌ <b>ورود این عضو لغو شد.</b>\n\nمی‌توانی عضو دیگری را انتخاب کنی.",parse_mode="HTML",reply_markup=section_menu())
        return
    if data=="back_field":
        values=context.user_data.get("current_values",[])
        history=context.user_data.get("current_history",[])
        queue=context.user_data.get("current_queue",[])
        if values and history:
            values.pop()
            queue.insert(0, history.pop())
            await ask_next(q,context)
        else:
            await q.edit_message_text("📚 <b>بخش سازه</b>",parse_mode="HTML",reply_markup=section_menu())
        return
    if data=="manual":
        queue=context.user_data.get("current_queue",[])
        if queue:
            await q.edit_message_text(f"✏️ <b>{queue[0][0]}</b> ({queue[0][1]})\n\nمقدار دلخواه را با عدد وارد کن.",parse_mode="HTML",reply_markup=field_menu([],queue[0][1]))
        return
    if data.startswith("preset|"):
        title=data.split("|",1)[1]; queue=context.user_data.get("current_queue",[])
        if queue:
            section=context.user_data.get("current_section",""); typ=context.user_data.get("current_type","")
            opts=compound_options(section,typ,queue[0][0])
            match=next((vals for name,vals in opts if name==title),None)
            if match is not None:
                apply_compound_preset(context,match)
                await ask_next(q,context)
        return
    if data.startswith("ready|"):
        value=float(data.split("|",1)[1]); queue=context.user_data.get("current_queue",[])
        if queue:
            context.user_data.setdefault("current_history",[]).append(queue[0])
            context.user_data["current_values"].append(value); queue.pop(0)
        await ask_next(q,context); return
    if data=="project_inputs":
        ms=context.user_data.get("members",[])
        lines=["📋 <b>ورودی‌های پروژه</b>",""]
        for i,m in enumerate(ms,1):
            lines.append(f"{i}. <b>{m.get('member','عضو')}</b>")
            for j,(label,unit) in enumerate(schema(m["section"],m["type"])):
                if j < len(m.get("raw",[])): lines.append(f"• {label}: {fmt(m['raw'][j])} {unit}")
        await q.edit_message_text("\n".join(lines) if ms else "هنوز ورودی‌ای ثبت نشده.",parse_mode="HTML",reply_markup=back_home()); return
    if data in ("settings","help"):
        mode=db.settings(update.effective_user.id).get("calc_mode","detailed")
        msg={"settings":f"⚙️ <b>تنظیمات متره</b>\n\nحالت فعلی: <b>{mode}</b>\nطول شاخه پیش‌فرض میلگرد: <b>۱۲ متر</b>\n\nتیپ‌های آماده فقط میانبر هستند و مقدار نهایی باید با نقشه کنترل شود.",
             "help":"❓ StructuralBot متره ساختمان بتنی را عضو‌به‌عضو انجام می‌دهد؛ هندسه یک‌بار وارد می‌شود و خروجی بتن، میلگرد، شاخه خرید، پرت و Cut List در گزارش جامع جمع می‌شود."}[data]
        await q.edit_message_text(msg,reply_markup=back_home()); return

async def ask_next(q,context):
    queue=context.user_data.get("current_queue",[])
    if not queue:
        await finish_member(q,context); return
    label,unit=queue[0]; section=context.user_data["current_section"]; typ=context.user_data["current_type"]
    options=ready_options(section,typ,label); compounds=compound_options(section,typ,label)
    await q.edit_message_text(ask_text(typ,queue,section,typ,options,compounds,context),parse_mode="HTML",reply_markup=field_menu(options,unit,compounds))

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

    # Persist the draft immediately so "ادامه برآورد" can restore it even
    # if the user leaves Telegram before finalizing the whole project.
    uid=q.from_user.id
    pid=context.user_data.get("project_id")
    if not pid:
        pid=db.add_project(uid,context.user_data.get("project_name","پروژه جدید"))
        context.user_data["project_id"]=pid
    try:
        draft=estimate_members(context.user_data.get("members",[]))
        db.save_draft(uid,pid,{"members":context.user_data.get("members",[])},draft)
        context.user_data["last_result"]=draft
    except Exception as e:
        log.warning("draft save failed: %s",e)
    context.user_data["current_member_index"]=len(context.user_data.get("members",[]))-1 if idx is None else idx
    await q.edit_message_text(
        f"✅ <b>{m['member']}</b> محاسبه شد.\n\nحالا نتیجه این عضو را نهایی کن یا در صورت نیاز اصلاحش کن.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🧮 محاسبه نهایی عضو",callback_data="member_calculate")],
            [InlineKeyboardButton("✏️ اصلاح عضو",callback_data="member_edit")],
            [InlineKeyboardButton("🔎 بازبینی پروژه",callback_data="finish_takeoff")],
            [InlineKeyboardButton("➕ عضو بعدی",callback_data="choose_section")],
            [InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]
        ])
    )

async def message(update,context):
    text=(update.message.text or "").strip().replace("،",".")
    if context.user_data.get("awaiting_project_name"):
        if not text or len(text)>120: await update.message.reply_text("❌ نام پروژه نامعتبر است."); return
        reset(context,text); await update.message.reply_text(f"🏗 پروژه «{text}» ساخته شد.",reply_markup=section_menu()); return
    # Professional actions from the keyboard attached to Telegram's typing area.
    if text=="✏️ ورود دستی":
        queue=context.user_data.get("current_queue",[])
        if queue:
            await update.message.reply_text(f"✏️ <b>مرحله {progress_text(context)[0]} از {progress_text(context)[1]}</b>\n🎯 {queue[0][0]} ({queue[0][1]})\nمقدار دلخواه را وارد کن.",parse_mode="HTML",reply_markup=input_keyboard([],queue[0][1],compound_options(context.user_data["current_section"],context.user_data["current_type"],queue[0][0])))
        return
    if text.startswith("⚡ "):
        title=text[2:].strip()
        queue=context.user_data.get("current_queue",[])
        if queue:
            section=context.user_data.get("current_section","")
            typ=context.user_data.get("current_type","")
            opts=compound_options(section,typ,queue[0][0])
            match=next((vals for name,vals in opts if name==title),None)
            if match is not None:
                apply_compound_preset(context,match)
                await ask_next_message(update,context)
                return
            raw=title.split()[0] if title else ""
            try: value=float(raw.replace("،","."))
            except ValueError: value=None
            if value is not None:
                context.user_data.setdefault("current_history",[]).append(queue[0])
                context.user_data["current_values"].append(value)
                queue.pop(0)
                await ask_next_message(update,context)
                return
    if text=="🧮 شروع برآورد":
        if not context.user_data.get("project_name"):
            context.user_data["project_name"]="برآورد جدید"
            context.user_data.setdefault("members",[])
        await update.message.reply_text("📚 <b>موارد برآوردی</b>\n\nعضو سازه‌ای موردنظر را انتخاب کن.",parse_mode="HTML",reply_markup=section_menu())
        return
    if text=="⬅️ مرحله قبل":
        values=context.user_data.get("current_values",[])
        history=context.user_data.get("current_history",[])
        queue=context.user_data.get("current_queue",[])
        if values and history:
            values.pop()
            queue.insert(0,history.pop())
            await ask_next_message(update,context)
        return
    if text=="📋 ورودی‌ها":
        queue=context.user_data.get("current_queue",[])
        values=context.user_data.get("current_values",[])
        history=context.user_data.get("current_history",[])
        lines=["📋 <b>وضعیت ورود اطلاعات</b>","",f"عضو: <b>{context.user_data.get('current_type','')}</b>"]
        for i,(label,unit) in enumerate(history):
            if i < len(values):
                lines.append(f"✅ {label}: <b>{fmt(values[i])}</b> {unit}")
        if queue:
            lines += ["",f"⏳ مرحله فعلی: <b>{queue[0][0]}</b> ({queue[0][1]})"]
        await update.message.reply_text("\n".join(lines),parse_mode="HTML",
            reply_markup=input_keyboard(
                ready_options(context.user_data.get("current_section",""),context.user_data.get("current_type",""),queue[0][0]) if queue else [],
                queue[0][1] if queue else ""))
        return
    if text=="❌ لغو عضو":
        for k in ("current_section","current_type","current_values","current_queue","current_history","current_edit","current_preset"):
            context.user_data.pop(k,None)
        await update.message.reply_text("❌ <b>ورود این عضو لغو شد.</b>",parse_mode="HTML",reply_markup=section_menu())
        return
    if text in ("🏠 خانه","🏠 منو"):
        context.user_data.clear()
        await update.message.reply_text("🏠 <b>منوی اصلی</b>",parse_mode="HTML",reply_markup=main_menu())
        await update.message.reply_text("منوی ثابت:",reply_markup=persistent_menu())
        return
    if text=="📂 پروژه‌ها":
        ps=db.projects(update.effective_user.id)
        rows=[[InlineKeyboardButton(p[1],callback_data=f"open|{p[0]}")] for p in ps]
        rows.append([InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")])
        await update.message.reply_text("📂 <b>پروژه‌های من</b>",parse_mode="HTML",reply_markup=InlineKeyboardMarkup(rows))
        return
        return

    queue=context.user_data.get("current_queue")
    if queue:
        try: value=float(text)
        except ValueError: await update.message.reply_text("❌ فقط عدد وارد کن."); return
        if value<0: await update.message.reply_text("❌ عدد منفی مجاز نیست."); return
        context.user_data.setdefault("current_history",[]).append(queue[0])
        context.user_data["current_values"].append(value); context.user_data["current_queue"].pop(0)
        await ask_next_message(update,context); return
    await update.message.reply_text("از منوی زیر انتخاب کن.",reply_markup=persistent_menu())

async def ask_next_message(update,context):
    if context.user_data.get("current_queue"):
        label,unit=context.user_data["current_queue"][0]
        options=ready_options(context.user_data["current_section"],context.user_data["current_type"],label)
        current,total,bar,_=progress_text(context)
        await update.message.reply_text(
            f"⏳ ثبت شد.\n\n<b>مرحله {current} از {total}</b>  {bar}\n🎯 <b>{label}</b> ({unit})\nاز گزینه‌های آماده انتخاب کن یا ورود دستی را بزن.",
            parse_mode="HTML",
            reply_markup=input_keyboard(options,unit,compound_options(context.user_data["current_section"],context.user_data["current_type"],label))
        )
    else:
        await finish_member_message(update,context)

async def finish_member_message(update,context):
    section=context.user_data["current_section"]; typ=context.user_data["current_type"]; vals=context.user_data["current_values"]
    try:
        comps=calc_member(section,typ,vals)
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در محاسبه: {e}")
        return
    idx=context.user_data.get("current_edit")
    m={"section":section,"member":f"{section} {typ}","type":typ,"quantity":1,"components":comps,"raw":vals}
    if idx is None:
        context.user_data.setdefault("members",[]).append(m)
    else:
        context.user_data["members"][idx]=m
    context.user_data["current_edit"]=None
    await update.message.reply_text(
        f"✅ <b>{m['member']}</b> محاسبه شد.\\n\\nبتن، میلگرد، وزن، شاخه خرید و اجزای وابسته ثبت شد.",
        parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ عضو بعدی",callback_data="choose_section")],
            [InlineKeyboardButton("🔎 بازبینی",callback_data="finish_takeoff")],
            [InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]
        ])
    )

async def error_handler(update,context):
    if isinstance(context.error,BadRequest) and "Message is not modified" in str(context.error): return
    log.error("Unhandled bot error: %s",context.error,exc_info=context.error)

def bot_worker():
    while True:
        try:
            app=Application.builder().token(TOKEN).build()
            app.add_handler(CommandHandler("start",start_cmd))
            app.add_handler(CallbackQueryHandler(callback))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,message))
            app.add_error_handler(error_handler)
            log.info("Starting StructuralBot - drawing-driven takeoff v5")
            app.run_polling(drop_pending_updates=True, stop_signals=None)
        except Exception as exc:
            log.error("Telegram worker stopped; retrying in 5s: %s",exc,exc_info=exc)
            import time
            time.sleep(5)

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")
    db.init()
    threading.Thread(target=bot_worker,daemon=True,name="telegram-worker").start()
    health_server()

if __name__=="__main__": main()
