def positive(*values):
    if any(float(v) <= 0 for v in values):
        raise ValueError("همه مقادیر باید بزرگ‌تر از صفر باشند")


DEFAULT_REBAR_RATES = {
    "فونداسیون": 110.0,
    "ستون": 140.0,
    "تیر": 130.0,
    "سقف": 80.0,
    "راه‌پله": 100.0,
}


def estimate_building(data):
    required = [
        "floors", "area", "foundation_count",
        "footing_w", "footing_l", "footing_t",
        "columns_per_floor", "column_w", "column_d", "floor_h",
        "beam_length_per_floor", "beam_w", "beam_h",
        "slab_t", "stair_area_per_floor", "stair_t",
    ]
    positive(*(data[k] for k in required))

    for key in ("floors", "foundation_count", "columns_per_floor"):
        value = float(data[key])
        if not value.is_integer():
            raise ValueError(f"{key} must be an integer")
    floors = int(data["floors"])
    data["foundation_count"] = int(data["foundation_count"])
    data["columns_per_floor"] = int(data["columns_per_floor"])
    area = data["area"]

    concrete = {
        "فونداسیون": data["foundation_count"] * data["footing_w"] * data["footing_l"] * data["footing_t"],
        "ستون": floors * data["columns_per_floor"] * data["column_w"] * data["column_d"] * data["floor_h"],
        "تیر": floors * data["beam_length_per_floor"] * data["beam_w"] * data["beam_h"],
        "سقف": floors * area * data["slab_t"],
        "راه‌پله": floors * data["stair_area_per_floor"] * data["stair_t"],
    }

    formwork = {
        "فونداسیون": data["foundation_count"] * 2 * (data["footing_w"] + data["footing_l"]) * data["footing_t"],
        "ستون": floors * data["columns_per_floor"] * 2 * (data["column_w"] + data["column_d"]) * data["floor_h"],
        "تیر": floors * data["beam_length_per_floor"] * 2 * (data["beam_w"] + data["beam_h"]),
        "سقف": floors * area,
        "راه‌پله": floors * data["stair_area_per_floor"] * 2,
    }

    rates = dict(DEFAULT_REBAR_RATES)
    rates.update(data.get("rebar_rates", {}))
    rebar = {k: concrete[k] * rates[k] for k in concrete}

    totals = {
        "concrete_net": sum(concrete.values()),
        "formwork_net": sum(formwork.values()),
        "rebar_net": sum(rebar.values()),
    }

    waste = {
        "concrete": float(data.get("concrete_waste_pct", 5.0)),
        "rebar": float(data.get("rebar_waste_pct", 3.0)),
    }

    procurement = {
        "concrete": totals["concrete_net"] * (1 + waste["concrete"] / 100),
        "rebar": totals["rebar_net"] * (1 + waste["rebar"] / 100),
    }

    return {
        "version": "takeoff-1.0",
        "method": "preliminary_quantities",
        "floors": floors,
        "area_per_floor": area,
        "concrete": concrete,
        "formwork": formwork,
        "rebar": rebar,
        "totals": totals,
        "waste_pct": waste,
        "procurement": procurement,
        "rebar_rates_kg_m3": rates,
        "assumptions": [
            "مقادیر بتن، قالب و میلگرد بر اساس هندسه و ضرایب برآوردی واردشده محاسبه شده‌اند.",
            "میلگرد جایگزین نقشه آرماتور، BBS یا لیستوفر اجرایی نیست.",
            "مقادیر خرید بتن و میلگرد شامل پرت تعریف‌شده در تنظیمات برآورد هستند.",
            "راه‌پله در این نسخه به‌صورت مساحت × ضخامت مدل شده است.",
        ],
    }


def format_estimate(result):
    lines = [
        "📊 <b>متره و برآورد اولیه ساختمان بتنی</b>",
        "",
        f"🏢 تعداد طبقات: {result['floors']:g}",
        f"📐 زیربنای هر طبقه: {result['area_per_floor']:,.2f} m²",
        "",
        "🧱 <b>بتن خالص</b>",
    ]
    for k, v in result["concrete"].items():
        lines.append(f"• {k}: {v:,.2f} m³")
    lines.append(f"• جمع بتن خالص: {result['totals']['concrete_net']:,.2f} m³")
    lines.append(f"• بتن موردنیاز با {result['waste_pct']['concrete']:g}% پرت: {result['procurement']['concrete']:,.2f} m³")

    lines += ["", "🪵 <b>قالب‌بندی</b>"]
    for k, v in result["formwork"].items():
        lines.append(f"• {k}: {v:,.2f} m²")
    lines.append(f"• جمع قالب‌بندی: {result['totals']['formwork_net']:,.2f} m²")

    lines += ["", "🔩 <b>میلگرد ـ برآورد وزنی</b>"]
    for k, v in result["rebar"].items():
        lines.append(f"• {k}: {v:,.0f} kg")
    lines.append(f"• جمع خالص میلگرد: {result['totals']['rebar_net']:,.0f} kg")
    lines.append(f"• میلگرد خرید با {result['waste_pct']['rebar']:g}% پرت: {result['procurement']['rebar']:,.0f} kg")

    lines += [
        "",
        "⚠️ <b>مبنای محاسبه</b>",
        "این خروجی «متره و برآورد اولیه» است. وزن میلگرد با ضرایب kg/m³ برآورد شده و برای خرید یا اجرا باید با نقشه‌های سازه و BBS کنترل شود.",
    ]
    return "\n".join(lines)
