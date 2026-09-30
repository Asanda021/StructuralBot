from collections import defaultdict
import math

def _num(v):
    value=float(v)
    if value < 0: raise ValueError("مقدار نمی‌تواند منفی باشد")
    return value

def rebar_weight(diameter_mm, length_m):
    d=_num(diameter_mm); l=_num(length_m)
    return d*d/162.0*l

REBAR_GRADE_FY_MPA = {
    "A1": 240.0, "A2": 300.0, "A3": 400.0, "A4": 500.0,
    "S240": 240.0, "S300": 300.0, "S400": 400.0, "S500": 500.0,
}

def _grade_number(value, default):
    text=str(value or "").upper().replace(" ", "")
    for key, fy in REBAR_GRADE_FY_MPA.items():
        if key in text:
            return fy
    return float(default)

def _concrete_strength_mpa(value, default=25.0):
    text=str(value or "").upper().replace(" ", "")
    if text.startswith("C"):
        try:
            return float(text[1:])
        except ValueError:
            pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)

def development_length_tension(diameter_mm, concrete_grade="C25", rebar_grade="A3",
                               top_bar=False, cb_over_db=1.0, ktr_over_db=0.0):
    """Automatic tension development length using the Mبحث 9 Chapter 21 framework.

    The exact value depends on concrete cover/spacing, transverse reinforcement,
    bar position and steel grade. When those drawing details are not available,
    the engine uses a conservative internal cb/db fallback and Ktr=0.
    """
    d=_num(diameter_mm)
    fc=_concrete_strength_mpa(concrete_grade)
    fy=_grade_number(rebar_grade, 400.0)
    if fc <= 0 or fy <= 0:
        raise ValueError("مقاومت بتن/میلگرد برای محاسبه طول مهاری نامعتبر است")
    psi_t=1.3 if top_bar else 1.0
    psi_e=1.0
    psi_s=0.8 if d <= 20.0 else 1.0
    psi_g=1.0
    ratio=max(0.1, min(float(cb_over_db)+float(ktr_over_db), 2.5))
    ld_mm=(fy*psi_t*psi_e*psi_s*psi_g)/(1.1*math.sqrt(fc)*ratio)*d
    ld_mm=max(ld_mm, 300.0, 12.0*d)
    return {
        "ld_m":ld_mm/1000.0, "ld_mm":ld_mm, "diameter_mm":d,
        "concrete_grade":str(concrete_grade or "C25"),
        "rebar_grade":str(rebar_grade or "A3"),
        "psi_t":psi_t, "psi_s":psi_s, "psi_e":psi_e, "psi_g":psi_g,
        "cb_over_db_used":ratio, "ktr_over_db_used":float(ktr_over_db),
        "basis":"مبحث ۹، فصل ۹-۲۱؛ طول مهاری کششی",
    }

def lap_splice_length_tension(diameter_mm, concrete_grade="C25", rebar_grade="A3",
                              top_bar=False, splice_class="B", cb_over_db=1.0):
    """Automatic tensile lap length; Type B is the default when the drawing
    only says that a long bar must be spliced."""
    ld=development_length_tension(
        diameter_mm, concrete_grade, rebar_grade, top_bar,
        cb_over_db=cb_over_db, ktr_over_db=0.0
    )
    factor=1.0 if str(splice_class).upper()=="A" else 1.3
    lap_mm=max(300.0, factor*ld["ld_mm"])
    return {**ld, "lap_m":lap_mm/1000.0, "lap_mm":lap_mm,
            "splice_class":"A" if factor==1.0 else "B",
            "basis":"مبحث ۹، بند ۹-۲۱-۴؛ وصله پوششی کششی"}

def automatic_cut_lengths(length_m, diameter_mm, stock_length_m=12.0,
                          concrete_grade="C25", rebar_grade="A3",
                          top_bar=False, cb_over_db=1.0):
    """Split a long drawing bar into stock-length pieces with automatic code lap."""
    L=_num(length_m); d=_num(diameter_mm); stock=_num(stock_length_m)
    if L <= stock + 1e-9:
        return {"cut_lengths_m":[L],"splice_count":0,"lap_m":0.0,"development":None}
    lap=lap_splice_length_tension(
        d, concrete_grade, rebar_grade, top_bar, splice_class="B",
        cb_over_db=cb_over_db
    )
    lap_m=lap["lap_m"]
    if lap_m >= stock:
        raise ValueError("طول وصله محاسبه‌شده برای شاخه استاندارد مناسب نیست")
    pieces=max(2, math.ceil((L-lap_m)/(stock-lap_m)))
    advance=stock-lap_m
    last=L-(pieces-1)*advance
    while last > stock + 1e-9:
        pieces += 1
        last=L-(pieces-1)*advance
    if last <= 0:
        raise ValueError("تقسیم خودکار طول میلگرد نامعتبر است")
    cuts=[stock]*(pieces-1)+[last]
    return {"cut_lengths_m":cuts,"splice_count":pieces-1,"lap_m":lap_m,"development":lap}

def rebar_summary(diameter_mm, total_length_m, stock_length_m=12.0, waste_percent=0.0):
    d=_num(diameter_mm); total=_num(total_length_m); stock=_num(stock_length_m)
    waste_pct=_num(waste_percent)
    waste_length=total*waste_pct/100.0
    required_length=total+waste_length
    branches=math.ceil(required_length/stock) if required_length else 0
    procurement_length=branches*stock
    return {"diameter_mm":d,"length_m":total,"weight_kg":rebar_weight(d,total),
            "stock_length_m":stock,"branches":branches,
            "waste_percent":waste_pct,"waste_length_m":waste_length,
            "procurement_length_m":procurement_length,
            "procurement_weight_kg":rebar_weight(d,procurement_length)}

def grid_rebar(area_l, area_w, diameter_mm, spacing_cm, stock_length_m=12.0):
    L=_num(area_l); W=_num(area_w); s=_num(spacing_cm)/100
    if s<=0: raise ValueError("فاصله میلگرد باید بزرگ‌تر از صفر باشد")
    nW=math.ceil(W/s)+1
    nL=math.ceil(L/s)+1
    len_x=nW*L; len_y=nL*W
    r=rebar_summary(diameter_mm,len_x+len_y,stock_length_m)
    r.update({"count_bars":nW+nL,"bars_each_direction":[nW,nL],
              "length_each_direction_m":[len_x,len_y],
              "cut_lengths_m":[L]*nW+[W]*nL})
    return r

def multi_face_grid_rebar(area_l, area_w, diameter_mm, spacing_cm, faces=2, stock_length_m=12.0):
    """Two-sided wall/mesh grid takeoff. Faces are explicit drawing inputs."""
    f=max(1,math.ceil(_num(faces)))
    base=grid_rebar(area_l,area_w,diameter_mm,spacing_cm,stock_length_m)
    total_len=base["length_m"]*f
    r=rebar_summary(diameter_mm,total_len,stock_length_m)
    r.update({
        "count_bars":base["count_bars"]*f,
        "faces":f,
        "bars_each_direction":[base["bars_each_direction"][0]*f,base["bars_each_direction"][1]*f],
        "length_each_direction_m":[base["length_each_direction_m"][0]*f,base["length_each_direction_m"][1]*f],
        "cut_lengths_m":base.get("cut_lengths_m",[])*f,
    })
    return r

def line_rebar(length_m, spacing_cm, diameter_mm, stock_length_m=12.0):
    L=_num(length_m); s=_num(spacing_cm)/100
    if s<=0: raise ValueError("فاصله میلگرد باید بزرگ‌تر از صفر باشد")
    count=math.ceil(L/s)+1
    return {"count_bars":count,"cut_lengths_m":[L]*count,
            **rebar_summary(diameter_mm,count*L,stock_length_m)}

def adjusted_bar_length(straight_m, bend_m=0.0, hook_m=0.0, lap_m=0.0):
    return _num(straight_m)+_num(bend_m)+_num(hook_m)+_num(lap_m)

def repeated_bar_rebar(count, length_each_m, diameter_mm, stock_length_m=12.0,
                       bend_m=0.0, hook_m=0.0, lap_m=0.0, waste_percent=0.0,
                       concrete_grade="C25", rebar_grade="A3", top_bar=False):
    n=math.ceil(_num(count)); L=_num(length_each_m)
    # Legacy parameters remain for compatibility with old saved projects.
    # Normal bot input no longer asks the user to enter bend/hook/lap lengths.
    cut_each=adjusted_bar_length(L,bend_m,hook_m,lap_m)
    plan=automatic_cut_lengths(
        cut_each, diameter_mm, stock_length_m,
        concrete_grade=concrete_grade, rebar_grade=rebar_grade, top_bar=top_bar
    )
    return {"count_bars":n,"length_each_m":L,"cut_length_each_m":cut_each,
            "cut_lengths_m":plan["cut_lengths_m"]*n,
            "bend_m":_num(bend_m),"hook_m":_num(hook_m),
            "lap_m":plan["lap_m"] if plan["splice_count"] else _num(lap_m),
            "splice_count":plan["splice_count"]*n,
            "development":plan["development"],
            **rebar_summary(diameter_mm,sum(plan["cut_lengths_m"])*n,stock_length_m,waste_percent)}

SLAB_TYPES={
 "تیرچه تک":{"concrete_coeff":0.18,"joist_factor":1,"block_kind":"یونولیتی"},
 "تیرچه دوبل":{"concrete_coeff":0.23,"joist_factor":2,"block_kind":"یونولیتی"},
 "تیرچه یونولیتی تک":{"concrete_coeff":0.18,"joist_factor":1,"block_kind":"یونولیتی"},
 "تیرچه یونولیتی دوبل":{"concrete_coeff":0.23,"joist_factor":2,"block_kind":"یونولیتی"},
 "تیرچه بلوک سفالی تک":{"concrete_coeff":0.18,"joist_factor":1,"block_kind":"سفالی"},
 "تیرچه بلوک سفالی دوبل":{"concrete_coeff":0.23,"joist_factor":2,"block_kind":"سفالی"},
 "وافل":{"concrete_coeff":None,"joist_factor":0,"block_kind":None},
 "یوبوت":{"concrete_coeff":None,"joist_factor":0,"block_kind":"یوبوت"},
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
    openings=data.get("openings") or []
    opening_area=sum(_num(op.get("length",0))*_num(op.get("width",0))*_num(op.get("count",1)) for op in openings)
    opening_area=min(opening_area,area)
    net_area=max(0.0,area-opening_area)
    concrete=net_area*float(coeff)
    result={"area_m2":area,"opening_area_m2":opening_area,"net_area_m2":net_area,
            "concrete_m3":concrete,"concrete_coeff":float(coeff),"slab_type":typ}
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

def cut_list_by_diameter(members, stock_length_m=12.0):
    """Create a procurement-oriented cut list from explicit bar pieces.
    Uses a first-fit decreasing bin pack; it never invents bar lengths.
    """
    stock=_num(stock_length_m)
    pieces=defaultdict(list)
    for m in members:
        for c in m.get("components",[]):
            if c.get("category")!="میلگرد" or c.get("unit")!="m":
                continue
            name=str(c.get("name",""))
            if "طول اجرا" not in name:
                continue
            dia=c.get("diameter_mm")
            if dia is None:
                continue
            # Prefer explicit piece length metadata; otherwise use the component total
            # as one piece. Callers can provide cut_lengths_m for true cutting data.
            cuts=c.get("cut_lengths_m")
            if cuts:
                pieces[float(dia)].extend(_num(x) for x in cuts)
            else:
                pieces[float(dia)].append(_num(c["value"]))
    result={}
    for dia, lengths in sorted(pieces.items()):
        bins=[]
        for length in sorted(lengths, reverse=True):
            if length>stock:
                bins.append({"pieces":[length],"used_m":length,"waste_m":0.0,"oversize":True})
                continue
            placed=False
            for b in bins:
                if b["used_m"]+length<=stock+1e-9:
                    b["pieces"].append(length); b["used_m"]+=length
                    b["waste_m"]=stock-b["used_m"]; placed=True; break
            if not placed:
                bins.append({"pieces":[length],"used_m":length,"waste_m":stock-length,"oversize":False})
        result[str(dia)]={
            "diameter_mm":dia,"stock_length_m":stock,
            "pieces_count":len(lengths),"stock_bars":len(bins),
            "used_length_m":sum(b["used_m"] for b in bins),
            "waste_length_m":sum(b["waste_m"] for b in bins),
            "bars":bins
        }
    return result

def validate_takeoff_geometry(members):
    """Validate drawing-derived geometry without inventing missing values."""
    warnings=[]
    for i,m in enumerate(members,1):
        label=f"{i}. {m.get('member',m.get('type','عضو'))}"
        for comp in m.get("components",[]):
            if comp.get("category")=="میلگرد" and comp.get("unit")=="m" and "طول اجرا" in str(comp.get("name","")):
                cuts=comp.get("cut_lengths_m") or []
                for cut in cuts:
                    if float(cut) > 12.0 + 1e-9:
                        warnings.append(f"{label}: قطعه میلگرد {float(cut):g}m از شاخه ۱۲m بزرگ‌تر است؛ وصله/تفکیک قطعه لازم است.")
            if comp.get("unit") in ("m","m²","m³","kg","عدد","شاخه"):
                try:
                    if float(comp.get("value",0)) < 0:
                        warnings.append(f"{label}: مقدار منفی در {comp.get('name','آیتم')}.")
                except (TypeError, ValueError):
                    warnings.append(f"{label}: مقدار نامعتبر در {comp.get('name','آیتم')}.")
    return warnings

def quality_check_members(members):
    """Pre-export QA: flags missing or ambiguous takeoff inputs without inventing values."""
    warnings=[]
    for i,m in enumerate(members,1):
        label=f"{i}. {m.get('member',m.get('type','عضو'))}"
        comps=m.get("components",[])
        if not comps:
            warnings.append(f"{label}: هیچ آیتم محاسباتی ثبت نشده.")
        if not any(c.get("unit")=="m³" and "بتن" in str(c.get("name","")) for c in comps):
            warnings.append(f"{label}: حجم بتن ثبت نشده یا قابل تشخیص نیست.")
        if m.get("section") not in ("سایر","آرماتور") and not any(c.get("category")=="میلگرد" for c in comps):
            warnings.append(f"{label}: دیتیل میلگرد در ورودی ثبت نشده؛ نقشه را کنترل کن.")
        for c in comps:
            if c.get("unit") in ("m³","m","kg","عدد","شاخه") and float(c.get("value",0)) < 0:
                warnings.append(f"{label}: مقدار منفی در {c.get('name','آیتم')}.")
            if c.get("category")=="میلگرد" and c.get("unit")=="m" and "طول اجرا" in str(c.get("name","")):
                dia=c.get("diameter_mm")
                if dia is None or float(dia)<=0:
                    warnings.append(f"{label}: قطر میلگرد برای {c.get('name','میلگرد')} مشخص نیست.")
    warnings.extend(validate_takeoff_geometry(members))
    warnings=list(dict.fromkeys(warnings))
    return {"ok":not warnings,"warnings":warnings,"checked_members":len(members)}

def estimate_members(members):
    rows=[]; totals=defaultdict(float)
    for i,m in enumerate(members,1):
        base={"row":i,"section":m.get("section","سایر"),"member":m.get("member",""),
              "type":m.get("type",""),"quantity":m.get("quantity",1)}
        for c in m.get("components",[]):
            row={**base,"name":c["name"],"value":round(float(c["value"]),4),"unit":c["unit"],
                 "note":c.get("note","")}
            rows.append(row); totals[c["unit"]]+=float(c["value"])
    rebar_by_diameter=defaultdict(lambda: {"weight_kg":0.0,"length_m":0.0,"procurement_weight_kg":0.0,"procurement_length_m":0.0,"branches":0})
    concrete_total=0.0
    for m in members:
        for c in m.get("components",[]):
            if c.get("category")=="میلگرد":
                dia=c.get("diameter_mm")
                if dia is not None:
                    key=float(dia)
                    if c.get("unit")=="kg":
                        rebar_by_diameter[key]["weight_kg"] += float(c["value"])
                    elif c.get("unit")=="m":
                        if "طول اجرا" in str(c.get("name","")):
                            rebar_by_diameter[key]["length_m"] += float(c["value"])
                        else:
                            rebar_by_diameter[key]["procurement_length_m"] += float(c["value"])
                    elif c.get("unit")=="شاخه":
                        rebar_by_diameter[key]["branches"] += int(float(c["value"]))
                        rebar_by_diameter[key]["procurement_weight_kg"] += float(c.get("procurement_weight_kg",0))
            if c.get("unit")=="m³" and "بتن" in str(c.get("name","")):
                concrete_total += float(c["value"])
    return {"version":"takeoff-5.0","method":"drawing_driven_member_takeoff","cut_list":cut_list_by_diameter(members),
            "qa":quality_check_members(members),
            "members":members,"items":rows,"totals_by_unit":dict(totals),
            "rebar_by_diameter":{str(k):v for k,v in sorted(rebar_by_diameter.items())},
            "concrete_total_m3":concrete_total,
            "item_count":len(rows),"member_count":len(members),
            "assumptions":["تیپ‌ها و اعداد آماده فقط میانبر ورود هستند و باید با نقشه تطبیق داده شوند.",
                           "مقادیر میلگرد اجرایی، طول، وزن و شاخه خرید جداگانه ثبت می‌شوند.",
                           "شاخه استاندارد پیش‌فرض ۱۲ متر است.",
                           "برای بازشوهای سقف، حجم بتن از مساحت خالص کسر می‌شود؛ آرماتور اطراف بازشو باید از دیتیل نقشه وارد شود.",
                           "طول مهاری و وصله پوششی میلگردهای بلند به‌صورت خودکار بر اساس قواعد فصل ۹-۲۱ و قطر میلگرد محاسبه می‌شود؛ ورود دستی خم/قلاب/وصله از کاربر حذف شده است.",
                           "برای قطعات بلندتر از شاخه استاندارد، موتور قطعه‌بندی و وصله پوششی پیش‌فرض نوع B را در Cut List اعمال می‌کند؛ دیتیل خاص نقشه باید بر آن مقدم باشد.",
                           "در نبود جزئیات پوشش/فاصله، موتور از پارامتر داخلی محافظه‌کارانه برای طول مهاری استفاده می‌کند و آن را در متادیتای محاسبه ثبت می‌کند.",
                           "تعداد تیرچه، یونولیت/بلوک و شبکه حرارتی از ابعاد و فواصل ورودی محاسبه می‌شود؛ مقدار نهایی باید با پلان و دیتیل اجرایی تطبیق داده شود.",
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
    mode=result.get("report_mode","detailed")
    lines=["📋 <b>گزارش جامع متره ساختمان بتنی</b>","",
           f"حالت گزارش: <b>{mode}</b>","",
           f"اعضای متره‌شده: <b>{result.get('member_count',0)}</b>",
           f"ردیف‌های مصالح: <b>{result.get('item_count',0)}</b>",""]
    for m in result.get("members",[]):
        lines.append(f"🏗 <b>{m.get('member','')}</b> | {m.get('section','')} | {m.get('type','')}")
        for c in m.get("components",[]):
            extra=f" — {c.get('note','')}" if c.get("note") else ""
            lines.append(f"• {c['name']}: <b>{c['value']:,.2f}</b> {c['unit']}{extra}")
    lines += ["","<b>جمع‌بندی بتن</b>",f"• حجم کل بتن: <b>{result.get('concrete_total_m3',0):,.3f}</b> m³",
                "","<b>جمع‌بندی میلگرد بر اساس قطر</b>"]
    if mode != "quick":
        for dia,data in result.get("rebar_by_diameter",{}).items():
            lines.append(f"• Φ{float(dia):g}: <b>{data.get('weight_kg',0):,.2f}</b> kg | {data.get('branches',0)} شاخه 12m | وزن خرید {data.get('procurement_weight_kg',0):,.2f} kg")
    lines += ["","<b>جمع‌بندی واحدها</b>"]
    for u,v in result.get("totals_by_unit",{}).items(): lines.append(f"• {u}: <b>{v:,.2f}</b>")
    if mode == "procurement":
        lines += ["","<b>Cut List / خرید</b>"]
        for dia,data in result.get("cut_list",{}).items():
            lines.append(f"• Φ{float(dia):g}: {data.get('stock_bars',0)} شاخه | مصرف {data.get('used_length_m',0):,.2f}m | پرت برش {data.get('waste_length_m',0):,.2f}m")
    lines += ["","⚠️ کنترل نهایی با نقشه‌های مصوب و دیتیل‌های اجرایی ضروری است."]
    return "\n".join(lines)
