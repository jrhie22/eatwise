"""PCOS metabolic phenotype scoring from survey answers."""

from __future__ import annotations

from typing import Any

PHENOTYPE_LABELS = {
    "A": "Type A — Insulin Resistant",
    "B": "Type B — Adrenal / Stress",
    "C": "Type C — Inflammatory",
    "D": "Type D — Post-Pill",
}


def get_phenotype(data: dict[str, Any]) -> str:
    """
    Categorize user into A, B, C, or D from survey fields.

    Type A: insulin resistance pattern (BMI, cravings, central weight).
    Type B: stress/cortisol pattern (stress, leaner BMI, sleep).
    Type C: inflammatory pattern (acne, GI, joints).
    Type D: recent discontinuation of hormonal birth control.
    """
    scores = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0}

    bmi = float(data["bmi"])
    stress = int(data["stress_level"])  # 1–5
    energy = int(data["energy_level"])  # 1–5
    cycle = data["cycle_regularity"]
    acne = data["acne_severity"]
    hair_thin = data["hair_thinning"]

    sugar = data.get("sugar_cravings", "Moderate")
    weight_pattern = data.get("weight_pattern", "Evenly distributed")
    sleep_trouble = data.get("sleep_trouble", "Sometimes")
    digestive = data.get("digestive_issues", "No")
    joint = data.get("joint_pain", "No")
    post_pill = data.get("post_pill", "No")

    # --- Type D (post-pill): strong prior when recent stop ---
    if post_pill == "Yes, within the last 1–2 years":
        scores["D"] += 5.0
    elif post_pill == "Yes, more than 2 years ago":
        scores["D"] += 1.5

    # --- Type A (insulin resistant) ---
    if bmi >= 27:
        scores["A"] += 3.0
    elif bmi >= 25:
        scores["A"] += 2.0
    elif bmi >= 23:
        scores["A"] += 0.5

    if sugar == "High (especially under stress)":
        scores["A"] += 2.5
    elif sugar == "Moderate":
        scores["A"] += 1.0

    if weight_pattern == "Mostly around my midsection":
        scores["A"] += 2.5
    elif weight_pattern == "Upper body / midsection":
        scores["A"] += 1.5

    if cycle in ("Very irregular (>40 days or unpredictable)", "Absent for 3+ months"):
        scores["A"] += 1.0

    # --- Type B (adrenal / stress) ---
    if bmi < 25:
        scores["B"] += 1.5
    if stress >= 4:
        scores["B"] += 2.5
    elif stress == 3:
        scores["B"] += 1.0

    if sleep_trouble == "Often / I wake wired or tired":
        scores["B"] += 2.5
    elif sleep_trouble == "Sometimes":
        scores["B"] += 1.0

    if energy <= 2:
        scores["B"] += 1.5

    # --- Type C (inflammatory) ---
    if acne in ("Moderate", "Severe / cystic"):
        scores["C"] += 2.5
    elif acne == "Mild":
        scores["C"] += 0.5

    if digestive == "Yes, often":
        scores["C"] += 2.5
    elif digestive == "Sometimes":
        scores["C"] += 1.0

    if joint == "Yes":
        scores["C"] += 2.0

    if hair_thin == "Yes":
        scores["C"] += 0.5

    # Cross-hints: high stress can worsen inflammation
    if stress >= 4 and scores["C"] > 0:
        scores["C"] += 0.5

    # If D is high but another type is higher, still allow D to win if very clear post-pill
    best = max(scores, key=lambda k: scores[k])
    ordered = sorted(scores.items(), key=lambda x: -x[1])
    if ordered[0][1] == ordered[1][1] and scores["D"] >= 4:
        return "D"
    return best


def phenotype_content(key: str) -> dict[str, str]:
    """Copy for dashboard and PDF."""
    content = {
        "A": {
            "root_cause": (
                "Your symptom pattern often aligns with **insulin resistance** and "
                "elevated insulin driving ovarian androgen output. Blood sugar swings can "
                "worsen cravings, abdominal weight, and cycle irregularity — distinct from "
                "only \"hormone imbalance\" alone."
            ),
            "protocols": (
                "- **Myo-inositol (often 2–4 g/day, split doses):** studied for insulin "
                "signaling and ovulation support in PCOS.\n"
                "- **Vitamin D** if low (confirm with testing): common gap in PCOS.\n"
                "- **Omega-3 (EPA/DHA):** metabolic and inflammatory support.\n"
                "- Discuss **metformin** or inositol trials with your clinician if "
                "appropriate."
            ),
            "nutrition_movement": (
                "**Nutrition:** Protein-forward meals, fiber-rich plants, minimize liquid "
                "sugars and ultra-processed carbs; consider lower glycemic load pattern "
                "you can sustain.\n\n"
                "**Movement:** Strength training + daily walking; avoid \"all or nothing\" "
                "cardio that spikes hunger and stress."
            ),
        },
        "B": {
            "root_cause": (
                "Your answers suggest a **stress–cortisol** axis may be central: sleep "
                "fragmentation, feeling wired-but-tired, and energy crashes can interact "
                "with PCOS even when BMI is lower."
            ),
            "protocols": (
                "- **Magnesium (glycinate or citrate):** sleep and nervous system support; "
                "dose with clinician.\n"
                "- **Adaptogen discussion (e.g., ashwagandha):** evidence mixed; avoid if "
                "pregnant and review interactions.\n"
                "- **B-vitamin complex** if diet is tight or stress is high (personalize).\n"
                "- Salivary cortisol / morning cortisol labs only if your clinician agrees."
            ),
            "nutrition_movement": (
                "**Nutrition:** Regular meals, adequate calories, limit fasting extremes; "
                "reduce stimulants if sleep is fragile; prioritize minerals (leafy greens, "
                "nuts, seeds).\n\n"
                "**Movement:** Slow, heavy strength work; walking; avoid overtraining; "
                "breathwork or HRV-friendly recovery."
            ),
        },
        "C": {
            "root_cause": (
                "**Inflammation and gut–immune crosstalk** may be amplifying androgenic "
                "skin signs and systemic symptoms. Skin, digestion, and joints often "
                "move together when immune tone is elevated."
            ),
            "protocols": (
                "- **Zinc:** skin and immune support; monitor copper balance long-term.\n"
                "- **Omega-3:** anti-inflammatory baseline.\n"
                "- **Curcumin / turmeric** (bioavailable forms): discuss if on blood "
                "thinners.\n"
                "- Consider **celiac screening** or GI workup with your clinician if "
                "digestive symptoms persist."
            ),
            "nutrition_movement": (
                "**Nutrition:** Anti-inflammatory pattern: colorful plants, olive oil, "
                "fermented foods if tolerated; trial structured elimination only with "
                "guidance.\n\n"
                "**Movement:** Moderate, consistent activity; mobility work; avoid "
                "punishing routines that raise cortisol further."
            ),
        },
        "D": {
            "root_cause": (
                "After stopping **combined hormonal contraception**, androgen and cycle "
                "symptoms can **rebound** while the hypothalamic–pituitary–ovarian axis "
                "recalibrates. This is a distinct window that benefits from metabolic "
                "support, not only suppression."
            ),
            "protocols": (
                "- **Myo-inositol** and **chromium** (evidence variable): discuss dosing.\n"
                "- **B vitamins** if post-pill nutrient concerns.\n"
                "- **Liver-supportive basics:** sleep, protein, fiber — labs if symptoms "
                "persist.\n"
                "- Timeline expectations: many need 3–12 months for stabilization; track "
                "cycles objectively."
            ),
            "nutrition_movement": (
                "**Nutrition:** Stabilize blood sugar early; emphasize whole-food protein; "
                "avoid aggressive restriction during rebound.\n\n"
                "**Movement:** Gentle strength progression + walking; protect sleep as a "
                "non-negotiable recovery lever."
            ),
        },
    }
    return content[key]
