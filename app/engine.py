import math

def _positive(*xs):
    if any(x <= 0 for x in xs):
        raise ValueError("values must be positive")

def foundation_calc(width, length, thickness):
    _positive(width, length, thickness)
    v = width * length * thickness
    return {"حجم بتن (m³)": v, "سطح تقریبی قالب (m²)": 2*(width+length)*thickness + width*length}

def column_calc(width, depth, height):
    _positive(width, depth, height)
    return {"حجم بتن (m³)": width*depth*height, "سطح جانبی تقریبی (m²)": 2*(width+depth)*height}

def beam_calc(width, height, length):
    _positive(width, height, length)
    return {"حجم بتن (m³)": width*height*length, "سطح جانبی تقریبی (m²)": 2*(width+height)*length}

def slab_calc(thickness, length, width):
    _positive(thickness, length, width)
    return {"حجم بتن (m³)": thickness*length*width, "مساحت سقف (m²)": length*width}

def concrete_for_dimensions(a, b, c):
    _positive(a, b, c)
    v = a*b*c
    return {"حجم بتن (m³)": v, "بتن با 5٪ پرت (m³)": v*1.05}

def rebar_equivalent(d1, d2):
    _positive(d1, d2)
    a1 = math.pi*d1**2/4
    a2 = math.pi*d2**2/4
    return {
        f"سطح مقطع Φ{d1:g} (mm²)": a1,
        f"سطح مقطع Φ{d2:g} (mm²)": a2,
        f"تعداد Φ{d2:g} معادل 1×Φ{d1:g}": a1/a2,
    }

def bbs_cutlist(diameter, count, length):
    _positive(diameter, count, length)
    pieces = math.ceil(length / 12)
    total_length = count * length
    kg_per_m = diameter**2 / 162
    total_weight = total_length * kg_per_m
    return {
        "تعداد میلگرد": count,
        "طول هر میلگرد (m)": length,
        "تعداد قطعه 12 متری موردنیاز": pieces * count,
        "طول کل (m)": total_length,
        "وزن تقریبی (kg)": total_weight,
    }
