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
    total_len=nW*L+nL*W
    r=rebar_summary(diameter_mm,total_len,stock_length_m)
    r.update({"count_bars":nW+nL,"bars_each_direction":[nW,nL]})
    return r

SLAB_TYPES={
 "تیرچه تک":{"concrete_coeff":0.18,"joist_factor":1},
 "تیرچه دوبل":{"concrete_coeff":0.23,"joist_factor":2},
 "وافل":{"concrete_coeff":None,"joist_factor":0},
 "دال بتنی":{"concrete_coeff":None,"joist_factor":0},
 "دال تخت":{"concrete_coeff":None,"joist_factor":0},
}

def calculate_slab(data):
    area=_num(data["length"])*_num(data["width"])
    typ=data["slab_type"]; coeff=data.get("concrete_coeff")
    if coeff is None: coeff=_num(data.get("thickness",0))
    concrete=area*float(coeff)
    result={"area_m2":area,"concrete_m3":concrete,"concrete_coeff":float(coeff)}
    if typ.startswith("تیرچه"):
        spacing=_num(data.get("joist_spacing_cm",50))/100
        n=math.ceil(_num(data["width"])/spacing)+1
        joist_len=_num(data.get("joist_length_m",data["length"]))
        joist_count=n
        result["joist_count"]=joist_count
        result["joist_total_length_m"]=joist_count*joist_len
        block_len=_num(data.get("block_length_m",1.0))
        blocks_per_line=math.ceil(joist_len/block_len) if block_len else 0
        result["foam_blocks"]=max(0,joist_count-1)*blocks_per_line
    if data.get("thermal_dia") and data.get("thermal_spacing_cm"):
        result["thermal"]=grid_rebar(data["length"],data["width"],data["thermal_dia"],data["thermal_spacing_cm"])
    if data.get("negative_dia") and data.get("negative_spacing_cm"):
        # negative bars are normally strip/detail dependent; this is a configurable takeoff rule.
        result["negative"]=grid_rebar(data["length"],data.get("negative_strip_width_m",1.0),
                                       data["negative_dia"],data["negative_spacing_cm"])
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
    return {"version":"takeoff-3.0","method":"drawing_driven_member_takeoff",
            "members":members,"items":rows,"totals_by_unit":dict(totals),
            "item_count":len(rows),"member_count":len(members),
            "assumptions":["اعداد تیپ فقط پیش‌فرض قابل ویرایش هستند.","مقادیر اجرایی و خرید میلگرد جداگانه نمایش داده می‌شوند.",
                           "ضرایب بتن سقف بر اساس سیستم انتخاب‌شده ثبت می‌شوند.",
                           "این ابزار متره است و جایگزین طراحی یا کنترل نقشه مصوب نیست."]}

def estimate_items(items):
    # Backward-compatible adapter
    members=[{"section":x.get("section","سایر"),"member":x.get("name",""),"type":x.get("type",""),
              "quantity":1,"components":[{"name":x.get("name","آیتم"),"value":x.get("quantity",0),
              "unit":x.get("unit","عدد"),"note":x.get("note","")}]} for x in items]
    return estimate_members(members)

def estimate_building(data):
    # Legacy compatibility
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
