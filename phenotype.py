"""Sidebar quiz → PCOS phenotype string in st.session_state."""
import streamlit as st

PHENOTYPES = [
    "insulin_resistant",
    "adrenal",
    "post_pill",
    "lean_inflammatory",
]
_QS = [
    (
        "After high-carb meals you feel:",
        [
            ("Crashy / hungry again fast", "insulin_resistant"),
            ("On edge or jittery", "adrenal"),
            ("Foggy or irregular cycles", "post_pill"),
            ("Bloated or inflamed", "lean_inflammatory"),
        ],
    ),
    (
        "Your main stress pattern is:",
        [
            ("Sugar cravings under stress", "insulin_resistant"),
            ("Burnout / sleep issues", "adrenal"),
            ("Hormone swings post-BC", "post_pill"),
            ("Skin/joint flare-ups", "lean_inflammatory"),
        ],
    ),
    (
        "Recent hormonal birth control?",
        [
            ("Not recently — focus on carbs/insulin", "insulin_resistant"),
            ("Not recently — stress/sleep is bigger", "adrenal"),
            ("Yes, stopped within 1–2 years", "post_pill"),
            ("Not recently — inflammation focus", "lean_inflammatory"),
        ],
    ),
    (
        "Weight / body comp:",
        [
            ("Gain around midsection", "insulin_resistant"),
            ("Cortisol / puffiness", "adrenal"),
            ("Unpredictable", "post_pill"),
            ("Lean but inflamed", "lean_inflammatory"),
        ],
    ),
    (
        "Foods that bother you most:",
        [
            ("Sugary drinks / desserts", "insulin_resistant"),
            ("Caffeine / salty snacks", "adrenal"),
            ("Dairy-heavy processed", "post_pill"),
            ("Gluten / fried / seed oils", "lean_inflammatory"),
        ],
    ),
]


def run_quiz() -> None:
    scores = {p: 0 for p in PHENOTYPES}
    for i, (q, opts) in enumerate(_QS):
        labels = [a[0] for a in opts]
        pick_label = st.radio(q, labels, key=f"pq_{i}", horizontal=False)
        pheno = next(o[1] for o in opts if o[0] == pick_label)
        scores[pheno] += 1
    top = max(scores, key=scores.get)
    st.session_state["phenotype"] = top
    st.caption(f"**Assigned:** {top.replace('_', ' ').title()}")
