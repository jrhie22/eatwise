"""Mistral: three grounded general-advice bullets for the PDF from survey + EatWise doc text."""
from __future__ import annotations

import json
import os
import re
from typing import Any

from phenotype_engine import phenotype_content

_JSON = re.compile(r"```(?:json)?\s*([\s\S]*?)```")


def _strip_md(s: str) -> str:
    return str(s).replace("**", "")


def _parse_json(text: str) -> dict[str, Any]:
    t = (text or "").strip()
    m = _JSON.search(t)
    if m:
        t = m.group(1).strip()
    return json.loads(t)


def _build_eatwise_doc_for_prompt(
    survey: dict[str, Any],
    phenotype_key: str,
    phenotype_label: str,
) -> str:
    """Same narrative blocks that appear in the medical PDF, so the model stays on-document."""
    pc = phenotype_content(phenotype_key)
    survey_lines = [
        f"Cycle regularity: {survey.get('cycle_regularity', '')}",
        f"Acne severity: {survey.get('acne_severity', '')}",
        f"Hair thinning: {survey.get('hair_thinning', '')}",
        f"BMI: {survey.get('bmi', '')}",
        f"Stress level (1-5): {survey.get('stress_level', '')}",
        f"Energy level (1-5): {survey.get('energy_level', '')}",
        f"Sugar cravings: {survey.get('sugar_cravings', '')}",
        f"Weight pattern: {survey.get('weight_pattern', '')}",
        f"Sleep difficulty: {survey.get('sleep_trouble', '')}",
        f"Digestive issues: {survey.get('digestive_issues', '')}",
        f"Joint pain: {survey.get('joint_pain', '')}",
        f"Recent hormonal birth control discontinuation: {survey.get('post_pill', '')}",
    ]
    return "\n".join(
        [
            f"Metabolic phenotype: {phenotype_label} (code {phenotype_key})",
            "",
            "Patient-reported snapshot (PDF labels):",
            "\n".join(survey_lines),
            "",
            "Full survey JSON (detail):",
            json.dumps(survey, indent=2, default=str),
            "",
            "--- EatWise educational text from the PDF (stay consistent with this) ---",
            "",
            "Root cause (patient education):",
            _strip_md(pc["root_cause"]),
            "",
            "Lifestyle and supplement topics for discussion:",
            _strip_md(pc["protocols"]),
            "",
            "Nutrition & movement emphasis:",
            _strip_md(pc["nutrition_movement"]),
        ]
    )


def fetch_survey_insights(
    survey: dict[str, Any],
    phenotype_key: str,
    phenotype_label: str,
) -> dict[str, Any]:
    """Returns ``general_advice``: exactly 3 strings grounded in the EatWise PDF document. Raises if no API key or API/parse fails."""
    doc = _build_eatwise_doc_for_prompt(survey, phenotype_key, phenotype_label)
    prompt = f"""You are a clinical nutrition educator (not diagnosing). Read ONLY the EatWise patient summary below.

Write exactly 3 short bullet points of practical GENERAL advice the patient can discuss with her clinician. Each bullet must align with the document below — do not contradict it, do not invent a diagnosis, and do not introduce brand-new medical claims that are absent from this framing.

EatWise summary:
---
{doc}
---

Return ONLY valid JSON in this exact shape:
{{"general_advice": ["first bullet", "second bullet", "third bullet"]}}

Plain strings inside the array, no markdown."""

    if os.environ.get("MISTRAL_API_KEY", "").strip():
        api_key = os.environ["MISTRAL_API_KEY"]
        try:
            from mistralai.client import Mistral  # mistralai v2.x
        except ImportError:
            from mistralai import Mistral  # mistralai v0.x / v1.x

        client = Mistral(api_key=api_key)
        chat_response = client.chat.complete(
            model="mistral-medium-2508",
            messages=[{"role": "user", "content": prompt}],
        )
        raw_txt = (chat_response.choices[0].message.content or "").strip()
        return _normalize_general_advice(_parse_json(raw_txt))

    raise RuntimeError("Set MISTRAL_API_KEY for AI PDF add-on.")


def _normalize_general_advice(raw: dict[str, Any]) -> dict[str, Any]:
    def _lst(x: Any, nmax: int) -> list[str]:
        if x is None:
            return []
        if isinstance(x, str):
            return [_strip_one(x)][:nmax]
        if isinstance(x, list):
            return [_strip_one(str(i)) for i in x if str(i).strip()][:nmax]
        return []

    def _strip_one(s: str) -> str:
        return s.strip().replace("\n", " ")[:500]

    ga = _lst(raw.get("general_advice"), 10)
    if len(ga) < 3 and raw.get("must_know"):
        ga = _lst(raw.get("must_know"), 10)
    while len(ga) < 3:
        ga.append("Discuss how to personalize these themes with your clinician.")
    return {"general_advice": ga[:3]}
