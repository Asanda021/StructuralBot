"""Foundation quantity takeoff layer."""
import math

def _num(value, name="value", allow_zero=True):
    try: x=float(value)
    except (TypeError,ValueError): raise ValueError(f"{name} must be numeric")
    if x<0 or (not allow_zero and x==0): raise ValueError(f"{name} must be positive")
    return x

def _ceil_count(length, spacing_m):
    if spacing_m<=0: raise ValueError("spacing must be positive")
    return max(1, math.ceil(length/spacing_m)+1)

def _grid(L,W,d,spacing_cm,repeat=1,stock=12.0,top=False):
    L=_num(L,"length",False); W=_num(W,"width",False); d=_num(d,"diameter",False); s=_num(spacing_cm,"spacing",False)/100
    nx=_ceil_count(W,s); ny=_ceil_count(L,s); repeat=max(1,int(math.ceil(_num(repeat,"repeat"))))
    pieces=([L]*nx+[W]*ny)*repeat; length=sum(pieces); weight=d*d/162*length
    bars=math.ceil(length/stock) if length else 0; buy=bars*stock
    return {"diameter_mm":d,"spacing_cm":spacing_cm,"bars_each_direction":[nx*repeat,ny*repeat],
            "cut_lengths_m":pieces,"count_bars":len(pieces),"length_m":length,"weight_kg":weight,
            "stock_length_m":stock,"branches":bars,"procurement_length_m":buy,
            "procurement_weight_kg":d*d/162*buy,"top_bar":bool(top)}

def _repeated(count,length,d,stock=12.0):
    n=int(math.ceil(_num(count,"count"))); L=_num(length,"length",False); d=_num(d,"diameter",False)
    total=n*L; bars=math.ceil(total/stock) if total else 0; buy=bars*stock
    return {"diameter_mm":d,"count_bars":n,"cut_lengths_m":[L]*n,"length_m":total,
            "weight_kg":d*d/162*total,"stock_length_m":stock,"branches":bars,
            "procurement_length_m":buy,"procurement_weight_kg":d*d/162*buy}

def _formwork(L,W,T,mode):
    return 2*(L+W)*T if str(mode).lower() in ("all","کامل","1","true") else 0.0

def _add(result,section,name,value,unit,note=""):
    result["quantities"].append({"section":section,"name":name,"value":round(float(value),6),"unit":unit,"note":note})

def _blinding(result,n,L,W,t):
    t=_num(t,"blinding_thickness"); area=n*L*W; vol=area*t
    result["blinding"]={"area_m2":area,"thickness_m":t,"volume_m3":vol}
    if vol: _add(result,"زیرسازی","بتن مگر",vol,"m³"); _add(result,"زیرسازی","مساحت مگر",area,"m²")

def _earthwork(result,n,L,W,T,ws,depth,backfill,replacement):
    ws=_num(ws,"working_space"); depth=_num(depth,"excavation_depth")
    eL,eW=L+2*ws,W+2*ws; exc=n*eL*eW*depth
    blind=result["blinding"].get("volume_m3",0.0); concrete=result["concrete"]["volume_m3"]
    calc=max(0.0,exc-blind-concrete)
    bf=calc if backfill is None else _num(backfill,"backfill")
    rep=_num(replacement,"replacement_soil")
    result["earthwork"]={"excavation_length_m":eL,"excavation_width_m":eW,"excavation_depth_m":depth,
                         "working_space_m":ws,"excavation_volume_m3":exc,
                         "backfill_volume_m3":bf,"replacement_soil_volume_m3":rep}
    _add(result,"عملیات خاکی","خاکبرداری فونداسیون",exc,"m³")
    _add(result,"عملیات خاکی","خاکریزی اطراف فونداسیون",bf,"m³")
    if rep: _add(result,"عملیات خاکی","خاک جانشین",rep,"m³")

def _accessories(result,chairs,spacers,anchors):
    for name,value,unit in (("خرک",chairs,"عدد"),("اسپیسر / فاصله‌نگهدار",spacers,"عدد"),("انکربولت",anchors,"عدد")):
        value=_num(value,name)
        if value: result["accessories"].append({"name":name,"value":value,"unit":unit}); _add(result,"متعلقات",name,value,unit)

def calculate_foundation_takeoff(data):
    kind=str(data.get("foundation_type",data.get("type","پی منفرد")))
    n=int(math.ceil(_num(data.get("count",1),"count"))); L=_num(data.get("length"),"length",False)
    W=_num(data.get("width"),"width",False); T=_num(data.get("thickness"),"thickness",False)
    stock=_num(data.get("stock_length_m",12),"stock_length_m",False)
    result={"version":"foundation-takeoff-1.0","foundation_type":kind,"count":n,
            "geometry":{"length_m":L,"width_m":W,"thickness_m":T},"earthwork":{},"blinding":{},
            "concrete":{},"formwork":{},"reinforcement":[],"accessories":[],"quantities":[],"warnings":[]}
    concrete=n*L*W*T; area=n*L*W; result["concrete"]={"volume_m3":concrete,"area_m2":area}
    _add(result,"بتن","بتن فونداسیون",concrete,"m³"); _add(result,"بتن","مساحت فونداسیون",area,"m²")
    _blinding(result,n,L,W,data.get("blinding_thickness",0))
    _earthwork(result,n,L,W,T,data.get("working_space_m",0),data.get("excavation_depth_m",T),
               data.get("backfill_volume_m3"),data.get("replacement_soil_m3",0))
    mode=data.get("formwork_mode","free"); fw=_formwork(L,W,T,mode)*n
    result["formwork"]={"contact_area_m2":fw,"mode":mode}
    if fw: _add(result,"قالب‌بندی","قالب‌بندی فونداسیون",fw,"m²","سطح تماس قالب با بتن؛ وجوه در تماس مستقیم با خاک قالب محسوب نشده‌اند.")
    bd,bs=data.get("bottom_dia_mm"),data.get("bottom_spacing_cm")
    if bd and bs:
        for direction in ("X","Y"):
            r=_grid(L,W,bd,bs,n,stock,False); r["direction"]=direction
            result["reinforcement"].append({"name":f"شبکه پایین - {direction}",**r})
            _add(result,"آرماتور",f"شبکه پایین - {direction}",r["weight_kg"],"kg",f"Φ{float(bd):g} @ {float(bs):g}cm")
    td,ts=data.get("top_dia_mm"),data.get("top_spacing_cm")
    if td and ts:
        for direction in ("X","Y"):
            r=_grid(L,W,td,ts,n,stock,True); r["direction"]=direction
            result["reinforcement"].append({"name":f"شبکه بالا - {direction}",**r})
            _add(result,"آرماتور",f"شبکه بالا - {direction}",r["weight_kg"],"kg",f"Φ{float(td):g} @ {float(ts):g}cm")
    if data.get("dowel_count") and data.get("dowel_length_m") and data.get("dowel_dia_mm"):
        r=_repeated(data["dowel_count"]*n,data["dowel_length_m"],data["dowel_dia_mm"],stock)
        result["reinforcement"].append({"name":"میلگرد انتظار",**r}); _add(result,"آرماتور","میلگرد انتظار",r["weight_kg"],"kg")
    if data.get("additional_count") and data.get("additional_length_m") and data.get("additional_dia_mm"):
        r=_repeated(data["additional_count"]*n,data["additional_length_m"],data["additional_dia_mm"],stock)
        result["reinforcement"].append({"name":"میلگرد تقویتی",**r}); _add(result,"آرماتور","میلگرد تقویتی",r["weight_kg"],"kg")
    _accessories(result,data.get("chair_count",0),data.get("spacer_count",0),data.get("anchor_bolt_count",0))
    result["totals"]={"earthwork_m3":result["earthwork"]["excavation_volume_m3"],"backfill_m3":result["earthwork"]["backfill_volume_m3"],
                      "blinding_m3":result["blinding"].get("volume_m3",0),"concrete_m3":concrete,"formwork_m2":fw,
                      "rebar_kg":sum(x.get("weight_kg",0) for x in result["reinforcement"])}
    return result

def foundation_bar_marks(result):
    from app.bar_marks import build_foundation_schedule
    return build_foundation_schedule(result)

def foundation_components(result):
    comps=[]
    for q in result["quantities"]:
        comps.append({"name":q["name"],"value":q["value"],"unit":q["unit"],"note":q.get("note",""),
                      "category":"میلگرد" if q["section"]=="آرماتور" else None})
    for r in result["reinforcement"]:
        comps += [
            {"name":f"{r['name']} - طول اجرا","value":r["length_m"],"unit":"m","category":"میلگرد","diameter_mm":r["diameter_mm"],"cut_lengths_m":r["cut_lengths_m"]},
            {"name":f"{r['name']} - وزن اجرا","value":r["weight_kg"],"unit":"kg","category":"میلگرد","diameter_mm":r["diameter_mm"]},
            {"name":f"{r['name']} - شاخه خرید","value":r["branches"],"unit":"شاخه","category":"میلگرد","diameter_mm":r["diameter_mm"],"procurement_weight_kg":r["procurement_weight_kg"]},
            {"name":f"{r['name']} - طول خرید","value":r["procurement_length_m"],"unit":"m","category":"میلگرد","diameter_mm":r["diameter_mm"]}]
    return comps
