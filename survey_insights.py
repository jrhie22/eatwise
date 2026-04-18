"""Mistral: JSON bullets for the medical PDF from survey + phenotype."""
from __future__ import annotations

import json
import os
import re
from typing import Any

_JSON = re.compile(r"```(?:json)?\s*([\s\S]*?)```")


def _parse_json(text: str) -> dict[str, Any]:
    t = (text or "").strip()
    m = _JSON.search(t)
    if m:
        t = m.group(1).strip()
    return json.loads(t)


def fetch_survey_insights(
    survey: dict[str, Any],
    phenotype_key: str,
    phenotype_label: str,
) -> dict[str, Any]:
    """Returns must_know (3), avoid_ingredients, good_for_symptoms lists. Raises on API/parse errors."""
    body = json.dumps(survey, indent=2, default=str)
    prompt = f"""Clinical nutrition educator (not diagnosing). PCOS type: {phenotype_label} (code {phenotype_key}).
Survey JSON:
{body}

Return ONLY JSON with:
- must_know: array of exactly 3 short strings (key things this patient should understand)
- avoid_ingredients: array of 5-8 concrete ingredients or additive categories to limit
- good_for_symptoms: array of 5-8 foods or eating patterns that tend to support this profile

Plain strings, no markdown."""

    if os.environ.get("GEMINI_API_KEY", "").strip():
        import google.generativeai as genai

        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        r = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        raw_txt = (getattr(r, "text", None) or "").strip()
        if not raw_txt and getattr(r, "candidates", None):
            parts = getattr(r.candidates[0].content, "parts", None) or []
            raw_txt = "".join(getattr(p, "text", "") or "" for p in parts).strip()
        if not raw_txt:
            raise RuntimeError("Gemini returned no text (safety filter or empty response).")
        return _normalize_insights(_parse_json(raw_txt))

    if os.environ.get("MISTRAL_API_KEY", "").strip():
        from mistralai import Mistral

        cl = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
        r = cl.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
        )
        return _normalize_insights(_parse_json(r.choices[0].message.content or "{}"))

    raise RuntimeError("Set GEMINI_API_KEY or MISTRAL_API_KEY for AI PDF add-on.")


def _normalize_insights(raw: dict[str, Any]) -> dict[str, Any]:
    def _lst(x: Any, nmax: int) -> list[str]:
        if x is None:
            return []
        if isinstance(x, str):
            return [_strip_one(x)][:nmax]
        if isinstance(x, list):
            out = [_strip_one(str(i)) for i in x if str(i).strip()]
            return out[:nmax]
        return []

    def _strip_one(s: str) -> str:
        return s.strip().replace("\n", " ")[:500]

    mk = _lst(raw.get("must_know"), 10)
    while len(mk) < 3:
        mk.append("Discuss individualized nutrition targets with your clinician.")
    mk = mk[:3]
    return {
        "must_know": mk,
        "avoid_ingredients": _lst(raw.get("avoid_ingredients"), 12),
        "good_for_symptoms": _lst(raw.get("good_for_symptoms"), 12),
    }
