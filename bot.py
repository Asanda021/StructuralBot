import logging, os, threading, tempfile, math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram.error import BadRequest
from app.db import Database
from app.engine import estimate_members, calculate_slab, rebar_summary, grid_rebar, multi_face_grid_rebar, repeated_bar_rebar, format_estimate
from app.exporter import create_excel, create_pdf
from app.keyboards import main_menu, back_home, section_menu, type_menu, review_menu, report_menu, calc_mode_menu, persistent_menu

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

# Quick-entry values are convenience only; they are never used silently.
READY={
 "تعداد":1, "تعداد ستون":1, "تعداد تیر":1,
 "طول":1.2, "عرض":1.2, "ضخامت":0.5, "ارتفاع":3.0,
 "عرض ستون":0.3, "عمق ستون":0.3, "عرض تیر":0.3, "ارتفاع تیر":0.5,
 "فاصله تیرچه":50, "قطر حرارتی":8, "فاصله حرارتی":25,
 "قطر شبکه پایین":16, "فاصله شبکه پایین":20,
 "قطر شبکه بالا":0, "فاصله شبکه بالا":0,
 "قطر سنجاقی":10, "فاصله سنجاقی":25,
 "قطر خاموت":10, "فاصله خاموت":20,
 "فاصله خاموت عادی":20, "فاصله خاموت بحرانی":10,
 "قطر میلگرد طولی":16, "تعداد میلگرد طولی هر ستون":8, "تعداد میلگرد طولی هر تیر":4, "تعداد میلگرد پایینی هر تیر":4, "قطر میلگرد پایینی":16, "تعداد میلگرد بالایی هر تیر":2, "قطر میلگرد بالایی":16,
 "قطر میلگرد تقویتی":16, "قطر کمرکش":12, "تعداد وجه مسلح":2,
 "طول هر خاموت":1.0, "طول هر سنجاقی":0.8,
 "طول هر میلگرد تقویتی":2.0, "طول هر کمرکش":1.0,
 "تعداد میلگرد تقویتی هر تیر":2, "تعداد سنجاقی هر تیر":2, "تعداد میلگرد کمرکش":2,
 "ضریب بتن":0.18, "طول یونولیت":1.0, "عرض یونولیت":0.5,
}

def ready_value(section,typ,label):
    if label=="ضریب بتن":
        if "دوبل" in typ: return 0.23
        if "تک" in typ: return 0.18
    return READY.get(label)

def schema(section,typ):
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
                    ("تعداد میلگرد طولی","عدد"),("قطر میلگرد طولی","mm"),
                    ("قطر خاموت","mm"),("فاصله خاموت","cm"),("طول هر خاموت","m"),
                    ("قطر سنجاقی","mm"),("فاصله سنجاقی","cm"),("طول هر سنجاقی","m")]
        return [("تعداد","عدد"),("طول","m"),("عرض","m"),("ضخامت","m"),
                ("قطر شبکه پایین","mm"),("فاصله شبکه پایین","cm"),
                ("قطر شبکه بالا","mm"),("فاصله شبکه بالا","cm"),
                ("قطر سنجاقی","mm"),("فاصله سنجاقی","cm"),("طول هر سنجاقی","m"),
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

def input_keyboard(rv=None, unit=""):
    """Professional persistent keyboard shown above Telegram's typing area during numeric entry."""
    rows=[]
    if rv is not None:
        rows.append([KeyboardButton(f"⚡ مقدار آماده: {rv} {unit}")])
    rows.append([KeyboardButton("⬅️ مرحله قبل"), KeyboardButton("📋 ورودی‌ها")])
    rows.append([KeyboardButton("❌ لغو عضو"), KeyboardButton("🏠 منو")])
    rows.append([KeyboardButton("🔄 شروع مجدد")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False, is_persistent=True,
                               input_field_placeholder="عدد را وارد کنید یا از منوی پایین انتخاب کنید")

def field_menu(rv=None, unit=""):
    rows=[]
    if rv is not None:
        rows.append([InlineKeyboardButton(f"⚡ مقدار آماده: {rv} {unit}",callback_data=f"ready|{rv}")])
    rows.append([
        InlineKeyboardButton("⬅️ مرحله قبل",callback_data="back_field"),
        InlineKeyboardButton("📋 ورودی‌ها",callback_data="show_inputs")
    ])
    rows.append([
        InlineKeyboardButton("❌ لغو عضو",callback_data="cancel_member"),
        InlineKeyboardButton("🏠 منو",callback_data="home")
    ])
    rows.append([InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")])
    return InlineKeyboardMarkup(rows)

def ask_text(name,fields,section,typ):
    label,unit=fields[0]
    rv=ready_value(section,typ,label)
    ready=f"\n⚡ مقدار آماده: <b>{rv}</b> {unit} (قابل ویرایش)" if rv is not None else ""
    return f"✏️ <b>{name}</b>\n\n<b>{label}</b> ({unit}){ready}\nعدد را وارد کن.\n\n⚠️ اعداد آماده فقط میانبر ورود هستند؛ مقدار نهایی را با نقشه کنترل کن."

def rcomps(title,r,note=""):
    n=int(r.get("count_bars",0)); branches=r.get("branches",0)
    dia=f"Φ{r['diameter_mm']:g}"
    return [
      {"name":f"{title} - تعداد قطعه","value":n,"unit":"عدد","note":note,"category":"میلگرد","diameter_mm":r["diameter_mm"]},
      {"name":f"{title} - طول اجرا","value":r["length_m"],"unit":"m","note":dia,"category":"میلگرد","diameter_mm":r["diameter_mm"]},
      {"name":f"{title} - وزن اجرا","value":r["weight_kg"],"unit":"kg","note":dia,"category":"میلگرد","diameter_mm":r["diameter_mm"]},
      {"name":f"{title} - شاخه خرید","value":branches,"unit":"شاخه","note":f"{dia} | شاخه {r['stock_length_m']:g}m | وزن خرید {r['procurement_weight_kg']:.2f}kg","category":"میلگرد","diameter_mm":r["diameter_mm"],"procurement_weight_kg":r["procurement_weight_kg"]},
      {"name":f"{title} - طول خرید","value":r.get("procurement_length_m",r["length_m"]),"unit":"m","note":f"{dia} | پرت {r.get('waste_percent',0):g}%","category":"میلگرد","diameter_mm":r["diameter_mm"]}
    ]

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
            n,L,W,H,bars,d,sd,ss,slen,pd,ps,plen=v
            comps=[{"name":"بتن شناژ","value":n*L*W*H,"unit":"m³"}]
            if bars and d: comps += rcomps("میلگرد طولی",repeated_bar_rebar(n*bars,L,d))
            if sd and ss and slen:
                cnt=n*(math.ceil(L/(ss/100))+1); comps += rcomps("خاموت شناژ",repeated_bar_rebar(cnt,slen,sd))
            if pd and ps and plen:
                cnt=n*(math.ceil(L/(ps/100))+1); comps += rcomps("سنجاقی شناژ",repeated_bar_rebar(cnt,plen,pd))
            return comps
        n,L,W,T,bd,bs,td,ts,pd,ps,plen,en,elen,ed=v
        comps=[{"name":"بتن فونداسیون","value":n*L*W*T,"unit":"m³"},{"name":"مساحت فونداسیون","value":n*L*W,"unit":"m²"}]
        if bd and bs: comps += rcomps("شبکه پایین دو جهت",grid_rebar(L,W,bd,bs))
        if td and ts: comps += rcomps("شبکه بالا دو جهت",grid_rebar(L,W,td,ts))
        if pd and ps and plen:
            cnt=n*(math.ceil(L/(ps/100))+1)*(math.ceil(W/(ps/100))+1)
            comps += rcomps("سنجاقی پی",repeated_bar_rebar(cnt,plen,pd),f"محاسبه از شبکه {ps:g}cm؛ طول هر سنجاقی از دیتیل")
        if en and elen and ed: comps += rcomps("میلگرد انتظار",repeated_bar_rebar(n*en,elen,ed))
        return comps

    if section=="ستون":
        n,a,b,h,bars,d,sd,ss,slen,pin,plen,pd=v
        comps=[{"name":"بتن ستون","value":n*a*b*h,"unit":"m³"},{"name":"مساحت مقطع","value":a*b,"unit":"m²"}]
        if bars and d: comps += rcomps("میلگرد طولی",repeated_bar_rebar(n*bars,h,d),f"{bars:g} عدد در هر ستون")
        if sd and ss and slen:
            cnt=n*(math.ceil(h/(ss/100))+1); comps += rcomps("خاموت",repeated_bar_rebar(cnt,slen,sd))
        if pin and plen and pd:
            levels=max(1,math.ceil(h/(ss/100))+1) if ss else pin
            comps += rcomps("سنجاقی ستون",repeated_bar_rebar(n*levels*pin,plen,pd))
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
            if total: comps += rcomps("خاموت",repeated_bar_rebar(total,slen,sd),f"عادی {c_normal} | بحرانی دو طرف {c_critical}")
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
        n,area,t,d,s,td,ts=v; side=math.sqrt(area)
        comps=[{"name":"بتن پله","value":n*area*t,"unit":"m³"},{"name":"مساحت پله","value":n*area,"unit":"m²"}]
        if d and s: comps += rcomps("میلگرد اصلی",grid_rebar(side,side,d,s))
        if td and ts: comps += rcomps("میلگرد حرارتی دو جهت",grid_rebar(side,side,td,ts))
        return comps
    return [{"name":"بتن","value":v[0],"unit":"m³"},{"name":"میلگرد","value":v[1],"unit":"kg"}]

def show_member_types(q,section):
    return q.edit_message_text(f"🏗 <b>{section}</b>\n\nنوع عضو را از تیپ‌های آماده انتخاب کن یا سفارشی را بزن.",parse_mode="HTML",reply_markup=type_menu(section))

async def start_cmd(update,context):
    db.ensure_user(update.effective_user.id,update.effective_user.first_name or "")
    context.user_data.clear()
    await update.message.reply_text("🏗 <b>StructuralBot</b>\n\n<b>متره جامع از روی نقشه</b>\nبرای ورود به حالت محاسبه، دکمه زیر را بزن.",parse_mode="HTML",reply_markup=calc_mode_menu())

def reset(context,name):
    context.user_data.clear(); context.user_data.update({"project_name":name,"members":[],"history":[]})

async def review(q,context):
    ms=context.user_data.get("members",[])
    qa=quality_check_members(ms)
    lines=["🔎 <b>بازبینی کامل متره</b>","",f"پروژه: <b>{context.user_data.get('project_name')}</b>"]
    lines += ["",f"کنترل خودکار: <b>{'بدون هشدار' if qa['ok'] else str(len(qa['warnings']))+' هشدار'}</b>"]
    for w in qa.get('warnings',[])[:12]:
        lines.append(f"⚠️ {w}")
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
    if data=="calc_mode":
        context.user_data["calculation_mode"]=True
        await q.edit_message_text("🧮 <b>حالت محاسبه فعال شد</b>\n\nحالا پروژه جدید را شروع کن یا یک پروژه را ادامه بده.",parse_mode="HTML",reply_markup=main_menu()); return
    if data=="restart":
        context.user_data.clear()
        await q.edit_message_text("🔄 <b>شروع مجدد</b>\n\nتمام اطلاعات موقت این مرحله پاک شد. برای شروع دوباره، حالت محاسبه را فعال کن.",parse_mode="HTML",reply_markup=calc_mode_menu()); return
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
        context.user_data.update({"current_section":section,"current_type":typ,"current_values":[],"current_queue":schema(section,typ),"current_history":[],"current_edit":None,"current_preset":presets_for(section,typ)})
        await ask_next(q,context); return
    if data.startswith("edit|"):
        idx=int(data.split("|")[1]); m=context.user_data["members"][idx]
        context.user_data.update({"current_section":m["section"],"current_type":m["type"],"current_values":m.get("raw",[]),
                                  "current_history":[],
                                  "current_queue":schema(m["section"],m["type"]),"current_edit":idx,"current_preset":presets_for(m["section"],m["type"])})
        await ask_next(q,context); return
    if data.startswith("delete|"):
        idx=int(data.split("|")[1]); context.user_data["members"].pop(idx); await review(q,context); return
    if data=="edit_members":
        rows=[]
        for i,m in enumerate(context.user_data.get("members",[])):
            rows.append([InlineKeyboardButton(f"✏️ {i+1}. {m['member']}",callback_data=f"edit|{i}"),InlineKeyboardButton("❌",callback_data=f"delete|{i}")])
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
    if data.startswith("ready|"):
        value=float(data.split("|",1)[1])
        queue=context.user_data.get("current_queue",[])
        if queue:
            context.user_data.setdefault("current_history",[]).append(queue[0])
            context.user_data["current_values"].append(value); queue.pop(0)
        await ask_next(q,context); return
    if data in ("pricing","settings","help"):
        msg={"pricing":"💰 قیمت‌گذاری در مرحله بعد روی همین اقلام و واحدها سوار می‌شود.",
             "settings":"⚙️ طول شاخه پیش‌فرض میلگرد ۱۲ متر است.",
             "help":"❓ تیپ‌ها و اعداد آماده فقط برای ورود سریع‌اند؛ مقدار نهایی باید با نقشه و دیتیل پروژه تطبیق داشته باشد."}[data]
        await q.edit_message_text(msg,reply_markup=back_home()); return

async def ask_next(q,context):
    queue=context.user_data.get("current_queue",[])
    if not queue:
        await finish_member(q,context); return
    label,unit=queue[0]
    if context.user_data.get("current_preset") and label in ("عرض ستون","عمق ستون","عرض تیر","ارتفاع تیر"):
        p=context.user_data["current_preset"]; key={"عرض ستون":"width","عمق ستون":"depth","عرض تیر":"beam_width","ارتفاع تیر":"beam_height"}[label]
        context.user_data["current_values"].append(p[key]); context.user_data["current_queue"].pop(0); await ask_next(q,context); return
    rv=ready_value(context.user_data["current_section"],context.user_data["current_type"],label)
    extra=[InlineKeyboardButton(f"⚡ استفاده از مقدار آماده: {rv} {unit}",callback_data=f"ready|{rv}")] if rv is not None else None
    await q.edit_message_text(ask_text(context.user_data["current_type"],queue,context.user_data["current_section"],context.user_data["current_type"]),parse_mode="HTML",reply_markup=field_menu(rv,unit))

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
    await q.message.reply_text("⌨️ ورود اطلاعات این عضو تمام شد.", reply_markup=ReplyKeyboardRemove())
    await q.edit_message_text(f"✅ <b>{m['member']}</b> محاسبه شد.\n\nبتن، میلگرد، طول، وزن، شاخه و اجزای وابسته در همین مرحله ثبت شدند.",parse_mode="HTML",
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ عضو بعدی",callback_data="choose_section")],
                                                                   [InlineKeyboardButton("🔎 بازبینی",callback_data="finish_takeoff")],
                                                                   [InlineKeyboardButton("🏠 منوی اصلی",callback_data="home")]]))

async def message(update,context):
    text=(update.message.text or "").strip().replace("،",".")
    if context.user_data.get("awaiting_project_name"):
        if not text or len(text)>120: await update.message.reply_text("❌ نام پروژه نامعتبر است."); return
        reset(context,text); await update.message.reply_text(f"🏗 پروژه «{text}» ساخته شد.",reply_markup=section_menu()); return
    # Professional actions from the keyboard attached to Telegram's typing area.
    if text.startswith("⚡ مقدار آماده:"):
        queue=context.user_data.get("current_queue",[])
        if queue:
            rv=ready_value(context.user_data.get("current_section",""),context.user_data.get("current_type",""),queue[0][0])
            if rv is not None:
                context.user_data.setdefault("current_history",[]).append(queue[0])
                context.user_data["current_values"].append(rv)
                context.user_data["current_queue"].pop(0)
                await ask_next_message(update,context)
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
                ready_value(context.user_data.get("current_section",""),context.user_data.get("current_type",""),queue[0][0]) if queue else None,
                queue[0][1] if queue else ""))
        return
    if text=="❌ لغو عضو":
        for k in ("current_section","current_type","current_values","current_queue","current_history","current_edit","current_preset"):
            context.user_data.pop(k,None)
        await update.message.reply_text("❌ <b>ورود این عضو لغو شد.</b>",parse_mode="HTML",reply_markup=section_menu())
        return
    if text=="🏠 منو":
        context.user_data.clear()
        await update.message.reply_text("🏠 <b>منوی اصلی</b>",parse_mode="HTML",reply_markup=main_menu())
        return
    if text=="🔄 شروع مجدد":
        context.user_data.clear()
        await update.message.reply_text("🔄 <b>شروع مجدد</b>\n\nحالت محاسبه را دوباره فعال کن.",parse_mode="HTML",reply_markup=calc_mode_menu())
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
        rv=ready_value(context.user_data["current_section"],context.user_data["current_type"],label)
        ready=f"\n⚡ مقدار آماده: {rv} {unit}" if rv is not None else ""
        buttons=[]
        if rv is not None:
            buttons.append([InlineKeyboardButton(f"⚡ استفاده از مقدار آماده: {rv} {unit}",callback_data=f"ready|{rv}")])
        buttons.append([InlineKeyboardButton("⬅️ اصلاح مرحله قبل",callback_data="back_field")])
        buttons.append([InlineKeyboardButton("🏠 منو",callback_data="home"),InlineKeyboardButton("🔄 شروع مجدد",callback_data="restart")])
        await update.message.reply_text(f"⏳ ثبت شد.\n\nمرحله بعد: <b>{label}</b> ({unit}){ready}",parse_mode="HTML",reply_markup=input_keyboard(rv,unit))
    else:
        class Q:
            async def edit_message_text(self,*a,**kw): await update.message.reply_text(*a,**kw)
        await finish_member(Q(),context)

async def error_handler(update,context):
    if isinstance(context.error,BadRequest) and "Message is not modified" in str(context.error): return
    log.error("Unhandled bot error: %s",context.error,exc_info=context.error)

def main():
    if not TOKEN: raise RuntimeError("BOT_TOKEN environment variable is not set")
    db.init(); threading.Thread(target=health_server,daemon=True).start()
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start_cmd)); app.add_handler(CallbackQueryHandler(callback)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,message)); app.add_error_handler(error_handler)
    log.info("Starting StructuralBot - drawing-driven takeoff v4")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
