"""Bar Mark schedule for foundation reinforcement.

This layer does not guess structural reinforcement. It converts explicit
foundation reinforcement inputs/calculated grids into traceable Bar Marks.
"""
import re

def _code(label, index):
    text=re.sub(r"[^A-Za-z0-9]+","_",str(label or "").strip()).strip("_").upper()
    return f"F-{index:03d}" if not text else f"F-{index:03d}"

def build_foundation_bar_marks(reinforcement):
    marks=[]
    for i,r in enumerate(reinforcement or [],1):
        marks.append({
            "bar_mark":_code(r.get("name"),i),
            "name":r.get("name",""),
            "diameter_mm":r.get("diameter_mm"),
            "spacing_cm":r.get("spacing_cm"),
            "direction":r.get("direction"),
            "count":r.get("count_bars",0),
            "length_m":r.get("length_m",0.0),
            "cut_lengths_m":list(r.get("cut_lengths_m") or []),
            "weight_kg":r.get("weight_kg",0.0),
            "branches":r.get("branches",0),
            "procurement_length_m":r.get("procurement_length_m",0.0),
            "note":"Bar Mark تولیدشده از داده صریح متره؛ بدون حدس‌زدن دیتیل سازه‌ای.",
        })
    return marks

def build_foundation_schedule(result):
    return build_foundation_bar_marks(result.get("reinforcement",[]))
