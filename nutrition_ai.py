"""Mistral text + vision extraction → structured dict."""
import base64
import json
import os
import re

from mistralai import Mistral

_JSON = re.compile(r"```(?:json)?\s*([\s\S]*?)```")


def _client() -> Mistral:
    return Mistral(api_key=os.environ["MISTRAL_API_KEY"])


def _parse(content: str) -> dict:
    t = content.strip()
    m = _JSON.search(t)
    if m:
        t = m.group(1).strip()
    return json.loads(t)


def analyze_text(dish_name: str) -> dict:
    p = f"""Extract nutrition for: "{dish_name}"
Return ONLY JSON keys: ingredients (list of strings), macros {{calories, protein_g,
carbs_g, sugar_g, fat_g, caffeine_mg, sodium_mg}}, hidden_flags (list, insulin/processed)."""
    r = _client().chat.complete(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": p}],
    )
    return _parse(r.choices[0].message.content or "{}")


def analyze_image(image_bytes: bytes, mime: str = "image/jpeg") -> dict:
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    url = f"data:{mime};base64,{b64}"
    p = """Read this food label. Return ONLY JSON keys: ingredients (list),
macros {calories, protein_g, carbs_g, sugar_g, fat_g, caffeine_mg, sodium_mg},
hidden_flags (list, insulin-spiking or processed additives)."""
    r = _client().chat.complete(
        model="pixtral-12b-2409",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": url}},
            {"type": "text", "text": p},
        ]}],
    )
    return _parse(r.choices[0].message.content or "{}")
