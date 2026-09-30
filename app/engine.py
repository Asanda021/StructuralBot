from collections import defaultdict
import math

def _num(v):
    value=float(v)
    if value < 0: raise ValueError("مقدار نمی‌تواند منفی باشد")
    return value

def rebar_weight(diameter_mm, length_m):
    d=_num(diameter_mm); l=_num(length_m)
    return d*d/162.0*l

def rebar_summary(diameter_mm, total_length_m, stock_length_m=12.0):
    d=_num(diameter_mm); total=_num(total_length_m); stock=_num(stock_length_m)
    branches=math.ceil(total/stock) if total else 0
    return {"diameter_mm":d,"length_m":total,"weight_kg":rebar_weight(d,total),
            "stock_length_m":stock,"branches":branches,
            "procurement_weight_kg":rebar_weight(d,branches*stock)}

def grid_rebar(area_l, area_w, diameter_mm, spacing_cm, stock_length_m=12.0):
    L=_num(area_l); W=_num(area_w); s=_num(spacing_cm)/100
    if s<=0: raise ValueError("فاصله میلگرد باید بزرگ‌تر از صفر باشد")
    nW=math.ceil(W/s)+1
    nL=math.ceil(L/s)+1
    len_x=nW*L; len_y=nL*W
    r=rebar_summary(diameter_mm,len_x+len_y,stock_length_m)
    r.update({"count_bars":nW+nL,"bars_each_direction":[nW,nL],
              "length_each_direction_m":[len_x,len_y]})
    return r

def line_rebar(length_m, spacing_cm, diameter_mm, stock_length_m=12.0):
    L=_num(length_m); s=_num(spacing_cm)/100
    if s<=0: raise ValueError("فاصله میلگرد باید بزرگ‌تر از صفر باشد")
    count=math.ceil(L/s)+1
    return {"count_bars":count, **rebar_summary(diameter_mm,count*L,stock_length_m)}

def repeated_bar_rebar(count, length_each_m, diameter_mm, stock_length_m=12.0):
    n=math.ceil(_num(count)); L=_num(length_each_m)
    return {"count_bars":n, "length_each_m":L, **rebar_summary(diameter_mm,n*L,stock_length_m)}

SLAB_TYPES={
 "تیرچه تک":{"concrete_coeff":0.18,"joist_factor":1,"block_kind":"یونولیتی"},
 "تیرچه دوبل":{"concrete_coeff":0.23,"joist_factor":2,"block_kind":"یونولیتی"},
 "تیرچه یونولیتی تک":{"concrete_coeff":0.18,"joist_factor":1,"block_kind":"یونولیتی"},
 "تیرچه یونولیتی دوبل":{"concrete_coeff":0.23,"joist_factor":2,"block_kind":"یونولیتی"},
 "تیرچه بلوک سفالی تک":{"concrete_coeff":0.18,"joist_factor":1,"block_kind":"سفالی"},
 "تیرچه بلوک سفالی دوبل":{"concrete_coeff":0.23,"joist_factor":2,"block_kind":"سفالی"},
 "وافل":{"concrete_coeff":None,"joist_factor":0,"block_kind":None},
 "دال بتنی":{"concrete_coeff":None,"joist_factor":0,"block_kind":None},
 "دال تخت":{"concrete_coeff":None,"joist_factor":0,"block_kind":None},
}

def calculate_slab(data):
    L=_num(data["length"]); W=_num(data["width"]); area=L*W
    typ=data["slab_type"]; meta=SLAB_TYPES.get(typ,{})
    coeff=data.get("concrete_coeff")
    if coeff is None: coeff=meta.get("concrete_coeff")
    if coeff is None: coeff=_num(data.get("thickness",0))
    if coeff<=0: raise ValueError("ضریب بتن یا ضخامت سقف باید وارد شود")
    concrete=area*float(coeff)
    result={"area_m2":area,"concrete_m3":concrete,"concrete_coeff":float(coeff)}
    if meta.get("joist_factor"):
        spacing=_num(data.get("joist_spacing_cm",50))/100
        n=max(1,math.ceil(W/spacing)+1)
        joist_len=_num(data.get("joist_length_m",L))
        factor=meta["joist_factor"]
        joist_count=n*factor
        result["joist_count"]=joist_count
        result["joist_lines"]=n
        result["joist_total_length_m"]=joist_count*joist_len
        block_len=_num(data.get("block_length_m",1.0))
        block_width=_num(data.get("block_width_m",spacing))
        blocks_per_line=math.ceil(joist_len/block_len) if block_len else 0
        gaps=max(0,math.ceil(W/block_width)-1)
        result["block_count"]=gaps*blocks_per_line
        result["block_length_m"]=block_len
        result["block_width_m"]=block_width
        result["block_kind"]=meta.get("block_kind")
        # Optional tie beams / kلاف میانی
        tie_count=_num(data.get("tie_count",0))
        tie_len=_num(data.get("tie_length_m",0))
        if tie_count and tie_len:
            td=_num(data.get("tie_dia",0))
            if td: result["tie_beam_rebar"]=repeated_bar_rebar(tie_count,tie_len,td)
            result["tie_count"]=tie_count
            result["tie_length_total_m"]=tie_count*tie_len
        # Optional negative reinforcement over supports: user supplies actual strip length/count.
        neg_count=_num(data.get("negative_count",0)); neg_len=_num(data.get("negative_length_m",0))
        neg_dia=_num(data.get("negative_dia",0))
        if neg_count and neg_len and neg_dia:
            result["negative"]=repeated_bar_rebar(neg_count,neg_len,neg_dia)
        # Optional اتکا/ادکا: exact piece count and cut length come from drawing/detail.
        otka_count=_num(data.get("otka_count",0)); otka_len=_num(data.get("otka_length_m",0)); otka_dia=_num(data.get("otka_dia",0))
        if otka_count and otka_len and otka_dia:
            result["otka"]=repeated_bar_rebar(otka_count,otka_len,otka_dia)
        # Optional کلاف عرضی/ژوئن
        joan_count=_num(data.get("joan_count",0)); joan_len=_num(data.get("joan_length_m",0)); joan_dia=_num(data.get("joan_dia",0))
        if joan_count and joan_len and joan_dia:
            result["joan"]=repeated_bar_rebar(joan_count,joan_len,joan_dia)
    if data.get("thermal_dia") and data.get("thermal_spacing_cm"):
        result["thermal"]=grid_rebar(L,W,data["thermal_dia"],data["thermal_spacing_cm"])
    return result

def estimate_members(members):
    rows=[]; totals=defaultdict(float)
    for i,m in enumerate(members,1):
        base={"row":i,"section":m.get("section","سایر"),"member":m.get("member",""),
              "type":m.get("type",""),"quantity":m.get("quantity",1)}
        for c in m.get("components",[]):
            row={**base,"name":c["name"],"value":round(float(c["value"]),4),"unit":c["unit"],
                 "note":c.get("note","")}
            rows.append(row); totals[c["unit"]]+=float(c["value"])
    return {"version":"takeoff-4.0","method":"drawing_driven_member_takeoff",
            "members":members,"items":rows,"totals_by_unit":dict(totals),
            "item_count":len(rows),"member_count":len(members),
            "assumptions":["تیپ‌ها و اعداد آماده فقط میانبر ورود هستند و باید با نقشه تطبیق داده شوند.",
                           "مقادیر میلگرد اجرایی، طول، وزن و شاخه خرید جداگانه ثبت می‌شوند.",
                           "شاخه استاندارد پیش‌فرض ۱۲ متر است.",
                           "قطعات خم‌دار مانند سنجاقی، اتکا و ژوئن فقط با طول/تعداد واقعی دیتیل محاسبه می‌شوند؛ ضریب مخفی اعمال نمی‌شود.",
                           "این ابزار متره است و جایگزین طراحی یا کنترل نقشه مصوب نیست."]}

def estimate_items(items):
    members=[{"section":x.get("section","سایر"),"member":x.get("name",""),"type":x.get("type",""),
              "quantity":1,"components":[{"name":x.get("name","آیتم"),"value":x.get("quantity",0),
              "unit":x.get("unit","عدد"),"note":x.get("note","")}]} for x in items]
    return estimate_members(members)

def estimate_building(data):
    required=["floors","area","foundation_count","footing_w","footing_l","footing_t","columns_per_floor",
              "column_w","column_d","floor_h","beam_length_per_floor","beam_w","beam_h","slab_t",
              "stair_area_per_floor","stair_t"]
    if any(float(data[k])<=0 for k in required): raise ValueError("همه مقادیر باید بزرگ‌تر از صفر باشند")
    floors=int(data["floors"]); fc=int(data["foundation_count"]); cp=int(data["columns_per_floor"])
    concrete={"فونداسیون":fc*data["footing_w"]*data["footing_l"]*data["footing_t"],
              "ستون":floors*cp*data["column_w"]*data["column_d"]*data["floor_h"],
              "تیر":floors*data["beam_length_per_floor"]*data["beam_w"]*data["beam_h"],
              "سقف":floors*data["area"]*data["slab_t"],
              "راه‌پله":floors*data["stair_area_per_floor"]*data["stair_t"]}
    formwork={"فونداسیون":fc*2*(data["footing_w"]+data["footing_l"])*data["footing_t"],
              "ستون":floors*cp*2*(data["column_w"]+data["column_d"])*data["floor_h"],
              "تیر":floors*data["beam_length_per_floor"]*2*(data["beam_w"]+data["beam_h"]),
              "سقف":floors*data["area"],"راه‌پله":floors*data["stair_area_per_floor"]*2}
    rates={"فونداسیون":110.0,"ستون":140.0,"تیر":130.0,"سقف":80.0,"راه‌پله":100.0}; rates.update(data.get("rebar_rates",{}))
    rebar={k:concrete[k]*rates[k] for k in concrete}
    c=sum(concrete.values()); f=sum(formwork.values()); r=sum(rebar.values())
    return {"version":"legacy-1.0","method":"preliminary_quantities","floors":floors,"area_per_floor":data["area"],
            "concrete":concrete,"formwork":formwork,"rebar":rebar,"totals":{"concrete_net":c,"formwork_net":f,"rebar_net":r}}

def format_estimate(result):
    lines=["📋 <b>گزارش جامع متره ساختمان بتنی</b>","",
           f"اعضای متره‌شده: <b>{result.get('member_count',0)}</b>",
           f"ردیف‌های مصالح: <b>{result.get('item_count',0)}</b>",""]
    for m in result.get("members",[]):
        lines.append(f"🏗 <b>{m.get('member','')}</b> | {m.get('section','')} | {m.get('type','')}")
        for c in m.get("components",[]):
            extra=f" — {c.get('note','')}" if c.get("note") else ""
            lines.append(f"• {c['name']}: <b>{c['value']:,.2f}</b> {c['unit']}{extra}")
    lines += ["","<b>جمع‌بندی</b>"]
    for u,v in result.get("totals_by_unit",{}).items(): lines.append(f"• {u}: <b>{v:,.2f}</b>")
    lines += ["","⚠️ کنترل نهایی با نقشه‌های مصوب و دیتیل‌های اجرایی ضروری است."]
    return "\n".join(lines)
