"""Yelp Fusion search + PCOS-oriented filtering."""
import os
from typing import Any

import requests

_GOOD = {
    "insulin_resistant": ("salad", "seafood", "soup", "poke", "fish"),
    "adrenal": ("tea", "juice", "vegan", "organic", "salad"),
    "post_pill": ("farm", "organic", "salad", "mediterranean", "vegetarian"),
    "lean_inflammatory": ("mediterranean", "salad", "gluten_free", "seafood", "persian"),
}
_BAD = ("fast food", "hotdog", "burgers", "fried chicken", "donut", "pizza")


def _pack(b: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": b.get("name"),
        "url": b.get("url"),
        "rating": b.get("rating"),
        "price": b.get("price"),
        "categories": [c.get("title") for c in (b.get("categories") or [])[:3]],
    }


def find_places(zip_code: str, budget_tier: int, phenotype: str) -> list[dict[str, Any]]:
    key = os.environ.get("YELP_API_KEY", "")
    if not key:
        return []
    h = {"Authorization": f"Bearer {key}"}
    q = {"location": zip_code, "categories": "restaurants", "limit": 30, "sort_by": "rating"}
    if 1 <= budget_tier <= 4:
        q["price"] = ",".join(str(i) for i in range(1, budget_tier + 1))
    r = requests.get(
        "https://api.yelp.com/v3/businesses/search", headers=h, params=q, timeout=20
    )
    r.raise_for_status()
    biz = r.json().get("businesses") or []
    good = _GOOD.get(phenotype, _GOOD["insulin_resistant"])
    out: list[dict[str, Any]] = []

    def consider(block_bad: bool, need_good: bool) -> None:
        for b in biz:
            cats = " ".join(c.get("title", "").lower() for c in b.get("categories") or [])
            name = (b.get("name") or "").lower()
            blob = f"{cats} {name}"
            if block_bad and any(x in blob for x in _BAD):
                continue
            if need_good and not any(g in blob for g in good):
                continue
            out.append(_pack(b))

    consider(True, True)
    if not out:
        consider(True, False)
    return out[:12]
