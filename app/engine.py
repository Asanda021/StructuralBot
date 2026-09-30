import math

def positive(*values):
    if any(float(v) <= 0 for v in values):
        raise ValueError("همه مقادیر باید بزرگ‌تر از صفر باشند")

def estimate_building(data):
    positive(
        data["floors"], data["area"], data["foundation_count"],
        data["footing_w"], data["footing_l"], data["footing_t"],
        data["columns_per_floor"], data["column_w"], data["column_d"], data["floor_h"],
        data["beam_length_per_floor"], data["beam_w"], data["beam_h"],
        data["slab_t"], data["stair_area_per_floor"], data["stair_t"]
    )

    floors = data["floors"]
    area = data["area"]

    footing_concrete = (
        data["foundation_count"] * data["footing_w"] *
        data["footing_l"] * data["footing_t"]
    )
    column_concrete = (
        floors * data["columns_per_floor"] * data["column_w"] *
        data["column_d"] * data["floor_h"]
    )
    beam_concrete = (
        floors * data["beam_length_per_floor"] *
        data["beam_w"] * data["beam_h"]
    )
    slab_concrete = floors * area * data["slab_t"]
    stair_concrete = floors * data["stair_area_per_floor"] * data["stair_t"]

    concrete = {
        "فونداسیون": footing_concrete,
        "ستون": column_concrete,
        "تیر": beam_concrete,
        "سقف": slab_concrete,
        "راه‌پله": stair_concrete,
    }
    total_concrete = sum(concrete.values())

    footing_form = data["foundation_count"] * (
        2 * (data["footing_w"] + data["footing_l"]) * data["footing_t"]
    )
    column_form = floors * data["columns_per_floor"] * (
        2 * (data["column_w"] + data["column_d"]) * data["floor_h"]
    )
    beam_form = floors * data["beam_length_per_floor"] * (
        2 * (data["beam_w"] + data["beam_h"])
    )
    slab_form = floors * area
    stair_form = floors * data["stair_area_per_floor"] * 2
    formwork = {
        "فونداسیون": footing_form,
        "ستون": column_form,
        "تیر": beam_form,
        "سقف": slab_form,
        "راه‌پله": stair_form,
    }
    total_formwork = sum(formwork.values())

    rates = data.get("rebar_rates", {
        "فونداسیون": 110,
        "ستون": 140,
        "تیر": 130,
        "سقف": 80,
        "راه‌پله": 100,
    })
    rebar = {k: concrete[k] * rates[k] for k in concrete}
    total_rebar = sum(rebar.values())

    return {
        "floors": floors,
        "area": area,
        "concrete": concrete,
        "total_concrete": total_concrete,
        "formwork": formwork,
        "total_formwork": total_formwork,
        "rebar": rebar,
        "total_rebar": total_rebar,
        "rebar_rates": rates,
    }

def format_estimate(result):
    lines = [
        "📊 خلاصه متره ساختمان بتنی",
        "",
        f"🏢 طبقات: {result['floors']:g}",
        f"📐 زیربنای هر طبقه: {result['area']:g} m²",
        "",
        "🧱 بتن:",
    ]
    for k, v in result["concrete"].items():
        lines.append(f"• {k}: {v:,.2f} m³")
    lines += [f"• جمع بتن: {result['total_concrete']:,.2f} m³", "", "🪵 قالب‌بندی:"]
    for k, v in result["formwork"].items():
        lines.append(f"• {k}: {v:,.2f} m²")
    lines += [f"• جمع قالب: {result['total_formwork']:,.2f} m²", "", "🔩 میلگرد:"]
    for k, v in result["rebar"].items():
        lines.append(f"• {k}: {v:,.0f} kg")
    lines += [
        f"• جمع میلگرد برآوردی: {result['total_rebar']:,.0f} kg",
        "",
        "⚠️ میلگرد در این نسخه بر اساس ضرایب برآوردی kg/m³ محاسبه می‌شود و جایگزین BBS یا لیستوفر اجرایی نیست.",
    ]
    return "\n".join(lines)
