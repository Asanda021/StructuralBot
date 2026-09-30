from collections import defaultdict

def _num(v):
    value = float(v)
    if value < 0: raise ValueError("مقدار نمی‌تواند منفی باشد")
    return value

def calculate_rebar_weight(diameter_mm, length_m, count=1):
    d, length, count = _num(diameter_mm), _num(length_m), _num(count)
    return (d*d/162.0) * length * count

def estimate_items(items):
    rows=[]; totals=defaultdict(float)
    for i, raw in enumerate(items,1):
        q=_num(raw.get("quantity",0)); unit=raw.get("unit","عدد"); section=raw.get("section","سایر"); name=raw.get("name","آیتم بدون نام")
        row={"row":i,"section":section,"name":name,"type":raw.get("type","custom"),"quantity":round(q,4),"unit":unit,"note":raw.get("note","")}
        rows.append(row); totals[unit]+=q
    return {"version":"takeoff-2.0","method":"item_based_takeoff","items":rows,"totals_by_unit":dict(totals),"item_count":len(rows),"assumptions":["هر ردیف بر اساس اطلاعات واردشده از نقشه ثبت شده است.","آرماتور می‌تواند مستقیم بر حسب kg یا از قطر، طول و تعداد محاسبه شود.","این سیستم متره است و جایگزین طراحی سازه، نقشه آرماتوربندی یا کنترل مهندسی نیست."]}

def estimate_building(data):
    required=["floors","area","foundation_count","footing_w","footing_l","footing_t","columns_per_floor","column_w","column_d","floor_h","beam_length_per_floor","beam_w","beam_h","slab_t","stair_area_per_floor","stair_t"]
    if any(float(data[k])<=0 for k in required): raise ValueError("همه مقادیر باید بزرگ‌تر از صفر باشند")
    floors=int(data["floors"]); fc=int(data["foundation_count"]); cp=int(data["columns_per_floor"])
    concrete={"فونداسیون":fc*data["footing_w"]*data["footing_l"]*data["footing_t"],"ستون":floors*cp*data["column_w"]*data["column_d"]*data["floor_h"],"تیر":floors*data["beam_length_per_floor"]*data["beam_w"]*data["beam_h"],"سقف":floors*data["area"]*data["slab_t"],"راه‌پله":floors*data["stair_area_per_floor"]*data["stair_t"]}
    formwork={"فونداسیون":fc*2*(data["footing_w"]+data["footing_l"])*data["footing_t"],"ستون":floors*cp*2*(data["column_w"]+data["column_d"])*data["floor_h"],"تیر":floors*data["beam_length_per_floor"]*2*(data["beam_w"]+data["beam_h"]),"سقف":floors*data["area"],"راه‌پله":floors*data["stair_area_per_floor"]*2}
    rates={"فونداسیون":110.0,"ستون":140.0,"تیر":130.0,"سقف":80.0,"راه‌پله":100.0}; rates.update(data.get("rebar_rates",{})); rebar={k:concrete[k]*rates[k] for k in concrete}
    c,f,r=sum(concrete.values()),sum(formwork.values()),sum(rebar.values())
    return {"version":"legacy-1.0","method":"preliminary_quantities","floors":floors,"area_per_floor":data["area"],"concrete":concrete,"formwork":formwork,"rebar":rebar,"totals":{"concrete_net":c,"formwork_net":f,"rebar_net":r},"waste_pct":{"concrete":5.0,"rebar":3.0},"procurement":{"concrete":c*1.05,"rebar":r*1.03},"rebar_rates_kg_m3":rates}

def format_estimate(result):
    if result.get("method")=="item_based_takeoff":
        lines=["📋 <b>گزارش جامع متره ساختمان بتنی</b>","",f"تعداد ردیف‌ها: <b>{result['item_count']}</b>","", "<pre>ردیف | بخش | آیتم | مقدار | واحد</pre>"]
        for r in result["items"]: lines.append(f"{r['row']} | {r['section']} | {r['name']} | {r['quantity']:,.3f} | {r['unit']}")
        lines += ["","<b>جمع‌بندی</b>"]+[f"• {u}: <b>{v:,.3f}</b>" for u,v in result["totals_by_unit"].items()]+["","⚠️ مقادیر بر اساس داده‌های واردشده از نقشه تهیه شده‌اند؛ کنترل با نقشه‌های مصوب و مدارک آرماتوربندی ضروری است."]
        return "\n".join(lines)
    lines=["📊 <b>گزارش برآورد مقادیر ساختمان بتنی</b>",""]
    for title,key,unit in [("🧱 بتن","concrete","m³"),("🪵 قالب","formwork","m²"),("🔩 میلگرد","rebar","kg")]:
        lines.append(f"<b>{title}</b>"); lines += [f"• {n}: {v:,.2f} {unit}" for n,v in result[key].items()]; lines.append("")
    return "\n".join(lines)
