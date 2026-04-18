"""Rule-based PCOS scoring; no ML."""
import json
from pathlib import Path

with (Path(__file__).parent / "flags.json").open() as _f:
    RULES = json.load(_f)


def score_food(phenotype: str, data: dict) -> dict:
    r = RULES.get(phenotype) or next(iter(RULES.values()))
    ings = " ".join(data.get("ingredients") or []).lower()
    hf = " ".join(data.get("hidden_flags") or []).lower()
    blob = f"{ings} {hf}"
    m = data.get("macros") or {}
    pts, flagged = 0, []
    sg = float(m.get("sugar_g") or 0)
    if sg > float(r.get("sugar_g", 12)):
        pts += 28
        flagged.append(f"sugar ~{sg}g (threshold {r['sugar_g']}g)")
    caf = float(m.get("caffeine_mg") or 0)
    if caf > float(r.get("caffeine_mg", 80)):
        pts += 22
        flagged.append(f"caffeine ~{caf}mg")
    na = float(m.get("sodium_mg") or 0)
    if na > float(r.get("sodium_mg", 800)):
        pts += 20
        flagged.append(f"sodium ~{na}mg")
    for kw, w in r.get("keywords", {}).items():
        if kw in blob:
            pts += min(30, int(w))
            if kw not in flagged:
                flagged.append(kw)
    for oil in r.get("oils", []):
        if oil in blob:
            pts += 20
            flagged.append(oil)
    if phenotype == "adrenal" and any(x in blob for x in ("alcohol", "ethanol", "wine", "beer")):
        pts += 24
        flagged.append("alcohol")
    if phenotype == "post_pill" and sum(
        1 for d in ("cream", "whey", "casein", "milk solid") if d in blob
    ) >= 2:
        pts += 18
        flagged.append("dairy-heavy")
    pts = min(100, pts)
    if pts <= 35:
        v, why = "safe", "Few PCOS triggers for your type in this item."
    elif pts <= 69:
        v, why = "caution", "Some ingredients or macros may worsen your PCOS pattern."
    else:
        v, why = "avoid", "Multiple strong triggers for your PCOS type—consider skipping."
    out = {
        "score": pts,
        "verdict": v,
        "reason": why,
        "flagged_ingredients": flagged,
        "swap": r.get("swap") if v == "avoid" else None,
    }
    return out
