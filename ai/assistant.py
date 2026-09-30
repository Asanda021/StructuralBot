import os
import json
import httpx

API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

LANGUAGE_NAMES = {"fa":"Persian","en":"English","ar":"Arabic","zh":"Chinese"}

def enabled():
    return bool(os.getenv("OPENAI_API_KEY"))

def _extract_text(data):
    if isinstance(data, dict) and data.get("output_text"):
        return str(data["output_text"]).strip()
    parts=[]
    for item in data.get("output",[]) if isinstance(data,dict) else []:
        for content in item.get("content",[]) if isinstance(item,dict) else []:
            if content.get("type")=="output_text" and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts).strip()

async def explain_takeoff(result, language="fa"):
    """Optional background AI explanation. It never performs structural design or changes quantities."""
    if not enabled():
        return None
    lang=LANGUAGE_NAMES.get(language,"Persian")
    compact={
        "concrete_total_m3": result.get("concrete_total_m3",0),
        "item_count": result.get("item_count",0),
        "member_count": result.get("member_count",0),
        "rebar_by_diameter": result.get("rebar_by_diameter",{}),
        "qa": result.get("qa",{}),
    }
    prompt=(
        f"Write a concise professional construction quantity-takeoff explanation in {lang}. "
        "Explain what was measured, important QA warnings, and what the engineer should verify. "
        "Do not invent dimensions, reinforcement, design decisions, standards, or quantities. "
        "This is quantity takeoff, not structural design.\n\n"
        + json.dumps(compact, ensure_ascii=False)
    )
    headers={"Authorization":f"Bearer {os.environ['OPENAI_API_KEY']}","Content-Type":"application/json"}
    payload={"model":DEFAULT_MODEL,"input":prompt,"store":False}
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            r=await client.post(API_URL,headers=headers,json=payload)
            r.raise_for_status()
            return _extract_text(r.json()) or None
    except Exception:
        return None
