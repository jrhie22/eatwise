"""OpenAI GPT-4o-mini vision for ingredient label analysis."""

from __future__ import annotations

import base64
import os
from typing import Any

from openai import OpenAI

from phenotype_engine import PHENOTYPE_LABELS


def _client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=key)


def analyze_label_image(
    image_bytes: bytes,
    mime_type: str,
    phenotype_key: str,
) -> str:
    """
    Send label image to GPT-4o-mini (vision) and return markdown-style analysis text.
    """
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"
    pheno_name = PHENOTYPE_LABELS.get(phenotype_key, phenotype_key)

    prompt = f"""You are a clinical nutrition assistant helping a woman with PCOS who has been categorized for educational purposes as: {pheno_name}.

Analyze the ingredient list in this food label image. If the image is not readable or not a food label, say so briefly.

Cover:
1. Hidden added sugars and high-glycemic additives (e.g., maltodextrin, dextrose, corn syrup solids, fruit juice concentrate used as sweetener).
2. Industrial seed oils (e.g., soybean, canola, corn oil) if present.
3. Ingredients that may act as endocrine disruptors or are controversial in PCOS communities (e.g., certain preservatives, artificial colors, BPA concern only if packaging visible — be factual).

End with a single clear rating on its own line exactly in this format:
Rating: Safe | Caution | Avoid

Keep the tone supportive and non-alarmist; this is not a diagnosis."""

    client = _client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url, "detail": "high"},
                    },
                ],
            }
        ],
        max_tokens=1200,
    )
    text = response.choices[0].message.content
    return (text or "").strip()
