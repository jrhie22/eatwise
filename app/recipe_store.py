"""Recipe ideas: local JSON file (no database)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
RECIPES_FILE = DATA_DIR / "recipes.json"

RECIPE_STEP_SCHEMA: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "prep_style",
        "Step 1 — Prep level",
        ("No-cook", "Minimal chop only", "Moderate prep", "Full prep / batch cook"),
    ),
    (
        "cook_method",
        "Step 2 — Heat / equipment",
        (
            "No heat (raw or chilled)",
            "Stovetop",
            "Oven",
            "Air fryer",
            "Pressure cooker / Instant Pot",
            "Blender only",
            "Other / mixed",
        ),
    ),
    (
        "active_time_band",
        "Step 3 — Active kitchen time",
        ("Under 15 minutes", "15–30 minutes", "30–60 minutes", "60+ minutes"),
    ),
    (
        "make_ahead",
        "Step 4 — Make-ahead fit",
        (
            "Best eaten same day",
            "Fine 1 day ahead",
            "3+ days or freezer friendly",
            "Not ideal made ahead",
        ),
    ),
)


def _read_rows() -> list[dict[str, Any]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not RECIPES_FILE.is_file():
        RECIPES_FILE.write_text("[]", encoding="utf-8")
    data = json.loads(RECIPES_FILE.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "recipes" in data:
        return list(data["recipes"])
    return list(data) if isinstance(data, list) else []


def _write_rows(rows: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = RECIPES_FILE.with_suffix(".tmp.json")
    tmp.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    tmp.replace(RECIPES_FILE)


def save_recipe(
    title: str,
    ingredients: str,
    steps: dict[str, str],
    goals_fit: str,
    *,
    low_gi: bool,
    anti_inflammatory: bool,
    fiber_grams: float,
    phenotype_key: str | None = None,
    display_name: str | None = None,
    status: str = "Submitted",
) -> None:
    rows = _read_rows()
    now = datetime.now(timezone.utc).isoformat()
    doc: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "title": title.strip(),
        "ingredients": ingredients.strip(),
        "steps": {k: (steps.get(k) or "").strip() for k, _, _ in RECIPE_STEP_SCHEMA},
        "goals_fit": (goals_fit or "").strip(),
        "pcos_rules": {
            "low_gi": bool(low_gi),
            "anti_inflammatory": bool(anti_inflammatory),
            "fiber_grams": float(fiber_grams),
        },
        "status": status,
        "phenotype_key": phenotype_key,
        "display_name": (display_name or "").strip() or None,
        "created_at": now,
    }
    rows.append(doc)
    _write_rows(rows)


def recent_recipes(limit: int = 30) -> list[dict[str, Any]]:
    rows = _read_rows()
    rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    out: list[dict[str, Any]] = []
    for d in rows[:limit]:
        pr = d.get("pcos_rules") or {}
        out.append(
            {
                "id": str(d.get("id", "")),
                "title": d.get("title", ""),
                "ingredients": d.get("ingredients", ""),
                "steps": d.get("steps") or {},
                "goals_fit": d.get("goals_fit", ""),
                "notes": d.get("notes", d.get("idea", "")),
                "pcos_rules": {
                    "low_gi": pr.get("low_gi"),
                    "anti_inflammatory": pr.get("anti_inflammatory"),
                    "fiber_grams": pr.get("fiber_grams"),
                },
                "status": d.get("status", ""),
                "phenotype_key": d.get("phenotype_key"),
                "display_name": d.get("display_name"),
                "created_at": d.get("created_at"),
            }
        )
    return out
