"""
EatWise — metabolic-first PCOS support (Streamlit).
"""

from __future__ import annotations

import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from label_vision import analyze_label_image
from medical_pdf import build_medical_summary_pdf
from phenotype_engine import PHENOTYPE_LABELS, get_phenotype, phenotype_content

PRIMARY = "#FFD1DC"
BG = "#FFFFFF"
TEXT = "#2D2D2D"
FONT_STACK = "'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif"


def _inject_soft_clinical_css() -> None:
    st.markdown(
        f"""
        <style>
            html, body, [class*="css"]  {{
                font-family: {FONT_STACK};
            }}
            .stApp {{
                background-color: {BG};
                color: {TEXT};
            }}
            h1, h2, h3, h4 {{
                color: {TEXT} !important;
                font-weight: 600 !important;
            }}
            div[data-testid="stSidebar"] {{
                background-color: #FFFAFB;
                border-right: 1px solid #F5E0E6;
            }}
            .stButton > button {{
                background-color: {PRIMARY};
                color: #FFFFFF;
                border: none;
                font-weight: 600;
                border-radius: 8px;
                padding: 0.5rem 1rem;
            }}
            .stButton > button:hover {{
                background-color: #FFC2D0;
                color: #FFFFFF;
            }}
            div[data-testid="stTabs"] button[aria-selected="true"] {{
                color: {TEXT} !important;
                border-bottom-color: {PRIMARY} !important;
            }}
            .eatwise-card {{
                background: #FFFAFB;
                border: 1px solid #F5E0E6;
                border-radius: 12px;
                padding: 1.25rem 1.5rem;
                margin-bottom: 1rem;
            }}
            .eatwise-pill {{
                display: inline-block;
                background: {PRIMARY};
                color: #FFFFFF;
                padding: 0.35rem 0.85rem;
                border-radius: 999px;
                font-size: 0.85rem;
                font-weight: 600;
                margin-bottom: 0.75rem;
            }}
            .eatwise-hero {{
                background: linear-gradient(180deg, #FFF5F7 0%, #FFFFFF 55%);
                border: 1px solid #F5E0E6;
                border-radius: 16px;
                padding: 2rem 2.25rem;
                margin-bottom: 1.5rem;
            }}
            .eatwise-hero-tagline {{
                font-size: 0.95rem;
                font-weight: 600;
                letter-spacing: 0.02em;
                color: #C2185B;
                margin-bottom: 0.75rem;
            }}
            .eatwise-hero h2 {{
                margin-top: 0 !important;
                line-height: 1.25 !important;
            }}
            .eatwise-type-grid p {{
                margin: 0.35rem 0;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _ensure_openai_key() -> None:
    load_dotenv()
    try:
        k = st.secrets["OPENAI_API_KEY"]
        if k:
            os.environ["OPENAI_API_KEY"] = str(k)
    except (FileNotFoundError, KeyError):
        pass

def _ensure_anthropic_key() -> None:
    load_dotenv()
    try:
        k = st.secrets["ANTHROPIC_API_KEY"]
        if k:
            os.environ["ANTHROPIC_API_KEY"] = str(k)
    except (FileNotFoundError, KeyError):
        pass

def _init_session() -> None:
    defaults: dict[str, Any] = {
        "wizard_step": 0,
        "survey_complete": False,
        "survey": {},
        "phenotype_key": None,
        "eatwise_view": "landing",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _render_nav() -> None:
    current = st.session_state.get("eatwise_view", "landing")
    nav_items: list[tuple[str, str]] = [
        ("Home", "landing"),
        ("About", "about"),
        ("Solution", "solution"),
        ("Recipes", "recipes"),
        ("Symptom Diary", "symptom_diary"),
    ]
    c_logo, c1, c2, c3, c4, c5 = st.columns([1.35, 1, 1, 1, 1.15, 1.15], gap="small")
    with c_logo:
        st.markdown("### EatWise")
    for col, (label, key) in zip((c1, c2, c3, c4, c5), nav_items, strict=True):
        with col:
            active = current == key
            if st.button(
                label,
                key=f"nav_{key}",
                type="primary" if active else "secondary",
                use_container_width=True,
            ):
                if current != key:
                    st.session_state.eatwise_view = key
                    st.rerun()
    st.divider()


def _render_landing() -> None:
    st.markdown(
        """
        <div class="eatwise-hero">
            <div class="eatwise-hero-tagline">The first AI phenotyping platform for PCOS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
**1 in 10 women have PCOS.** Every doctor says the same thing. We don't.

Take our diagnostic survey at onboarding — it clusters each user into her metabolic phenotype. Every subsequent recommendation is filtered through this lens:

- **Type A: Insulin Resistant** — Weight, blood sugar, androgen spikes  
- **Type B: Adrenal** — Cortisol dysregulation, stress response  
- **Type C: Inflammatory** — Acne, gut health, systemic inflammation  
- **Type D: Post-Pill** — Hormonal rebound after stopping birth control pills  
        """
    )
    st.markdown("")
    if st.button("Discover Your Recommendations", type="primary", key="landing_discover"):
        st.session_state.eatwise_view = "platform"
        st.rerun()


def _render_about_page() -> None:
    st.subheader("About EatWise")
    st.markdown(
        """
EatWise is built for the majority of people with PCOS who are told the same generic advice — lose weight, go on the pill — without a clear picture of **which** metabolic drivers matter for *you*.

We use a structured onboarding survey to sort patterns into phenotypes, not labels. The goal is practical: recommendations you can discuss with your clinician and live with day to day.

EatWise is a **soft-clinical companion**. It does not diagnose or replace medical care.
        """
    )


def _render_solution_page() -> None:
    st.subheader("Solution")
    st.markdown(
        """
**1. Phenotype survey** — Short questions about cycles, skin, stress, weight pattern, sleep, digestion, and recent birth control use. Answers map to a metabolic phenotype (Types A–D).

**2. Personalized dashboard** — Root-cause framing, nutrition and movement ideas, and discussion points for clinic visits — all filtered through your phenotype.

**3. Food label scanner** — Upload an ingredient label; we interpret it in the context of your phenotype (requires an OpenAI API key).

Export a **medical summary PDF** when you want something concrete to bring to an appointment.
        """
    )


def _render_recipes_page() -> None:
    st.subheader("Recipes")
    st.info(
        "Phenotype-aligned meal ideas are on the roadmap. Until then, use **Your plan** "
        "after the survey for nutrition guidance tailored to your type."
    )
    st.caption("Recipes here will be filtered by your metabolic phenotype once enabled.")


def _render_symptom_diary_page() -> None:
    from symptom_diary import render_symptom_diary
    render_symptom_diary()


def _render_platform_app() -> None:
    st.caption("Metabolic health for PCOS — a soft-clinical companion, not a substitute for your clinician.")

    with st.sidebar:
        st.markdown("### Metabolic lens")
        _render_scanner_sidebar()

    tab_home, tab_dash, tab_scan = st.tabs(["Phenotype survey", "Dashboard", "Food label scanner"])

    with tab_home:
        if st.session_state.survey_complete:
            st.success("Survey complete. Open **Dashboard** for your plan, or **Food label scanner** to check products.")
            if st.button("Edit my answers (retake survey)"):
                st.session_state.survey_complete = False
                st.session_state.wizard_step = 0
                st.rerun()
        else:
            _render_survey_wizard()

    with tab_dash:
        if not st.session_state.survey_complete:
            st.info("Complete the **Phenotype survey** tab first.")
        else:
            _render_dashboard()

    with tab_scan:
        _ensure_openai_key()
        if not st.session_state.survey_complete:
            st.info("Complete the survey so we can analyze labels in the context of your phenotype.")
        elif not os.environ.get("OPENAI_API_KEY"):
            st.warning(
                "Set `OPENAI_API_KEY` in a `.env` file in this folder or in `.streamlit/secrets.toml`."
            )
        else:
            st.subheader("Upload a food ingredient label")
            st.caption("Uses GPT-4o-mini vision. Photos with clear ingredient lists work best.")
            f = st.file_uploader("Image", type=["png", "jpg", "jpeg", "webp"], key="main_upload")
            if f and st.button("Analyze with my phenotype", type="primary", key="main_analyze"):
                data = f.getvalue()
                mime = f.type or "image/jpeg"
                with st.spinner("Reading label..."):
                    try:
                        result = analyze_label_image(data, mime, st.session_state.phenotype_key)
                        st.markdown(result)
                        st.session_state["last_scan_result"] = result
                    except Exception as e:
                        st.error(str(e))


def _render_survey_wizard() -> None:
    step = st.session_state.wizard_step
    total = 3
    st.progress((step + 1) / total, text=f"Step {step + 1} of {total}")

    if step == 0:
        st.subheader("Cycle & skin")
        cycle = st.selectbox(
            "Cycle regularity",
            [
                "Mostly regular (26-35 days)",
                "Somewhat irregular",
                "Very irregular (>40 days or unpredictable)",
                "Absent for 3+ months",
            ],
            key="w_cycle",
        )
        acne = st.selectbox(
            "Acne severity",
            ["None / minimal", "Mild", "Moderate", "Severe / cystic"],
            key="w_acne",
        )
        hair = st.radio("Hair thinning", ["No", "Yes"], horizontal=True, key="w_hair")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Next", type="primary"):
                st.session_state._draft = {
                    "cycle_regularity": cycle,
                    "acne_severity": acne,
                    "hair_thinning": hair,
                }
                st.session_state.wizard_step = 1
                st.rerun()
        return

    if step == 1:
        st.subheader("Body composition & daily load")
        bmi = st.number_input("BMI", min_value=15.0, max_value=60.0, value=26.0, step=0.1, key="w_bmi")
        stress = st.slider("Stress levels (1 = low, 5 = high)", 1, 5, 3, key="w_stress")
        energy = st.slider("Energy levels (1 = low, 5 = high)", 1, 5, 3, key="w_energy")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back"):
                st.session_state.wizard_step = 0
                st.rerun()
        with c2:
            if st.button("Next", type="primary"):
                d = dict(st.session_state.get("_draft", {}))
                d.update(
                    {
                        "bmi": bmi,
                        "stress_level": stress,
                        "energy_level": energy,
                    }
                )
                st.session_state._draft = d
                st.session_state.wizard_step = 2
                st.rerun()
        return

    if step == 2:
        st.subheader("Metabolic pattern clues")
        sugar = st.selectbox(
            "Sugar cravings",
            ["Low", "Moderate", "High (especially under stress)"],
            key="w_sugar",
        )
        weight_pattern = st.selectbox(
            "Where weight tends to sit",
            [
                "Mostly around my midsection",
                "Upper body / midsection",
                "Evenly distributed",
                "Lower body",
            ],
            key="w_weight",
        )
        sleep_trouble = st.selectbox(
            "Sleep difficulty",
            ["Rarely", "Sometimes", "Often / I wake wired or tired"],
            key="w_sleep",
        )
        digestive = st.selectbox(
            "Digestive issues (bloating, IBS-type symptoms)",
            ["No", "Sometimes", "Yes, often"],
            key="w_gi",
        )
        joint = st.radio("Joint pain", ["No", "Yes"], horizontal=True, key="w_joint")
        post_pill = st.selectbox(
            "Hormonal birth control (recent stop)",
            [
                "No",
                "Yes, within the last 1-2 years",
                "Yes, more than 2 years ago",
            ],
            key="w_pill",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back"):
                st.session_state.wizard_step = 1
                st.rerun()
        with c2:
            if st.button("Finish & see my phenotype", type="primary"):
                d = dict(st.session_state.get("_draft", {}))
                # Normalize post_pill strings to match phenotype_engine
                pill_map = {
                    "No": "No",
                    "Yes, within the last 1-2 years": "Yes, within the last 1–2 years",
                    "Yes, more than 2 years ago": "Yes, more than 2 years ago",
                }
                d.update(
                    {
                        "sugar_cravings": sugar,
                        "weight_pattern": weight_pattern,
                        "sleep_trouble": sleep_trouble,
                        "digestive_issues": digestive,
                        "joint_pain": joint,
                        "post_pill": pill_map[post_pill],
                    }
                )
                st.session_state.survey = d
                st.session_state.phenotype_key = get_phenotype(d)
                st.session_state.survey_complete = True
                st.session_state.wizard_step = 0
                if "_draft" in st.session_state:
                    del st.session_state._draft
                st.rerun()


def _render_dashboard() -> None:
    key = st.session_state.phenotype_key
    survey = st.session_state.survey
    pc = phenotype_content(key)
    label = PHENOTYPE_LABELS[key]

    st.markdown(f'<div class="eatwise-pill">{label}</div>', unsafe_allow_html=True)
    st.markdown("### Personalized dashboard")

    with st.container():
        st.markdown("#### The root cause")
        st.markdown(pc["root_cause"])
    st.markdown("")

    with st.container():
        st.markdown("#### Beyond the Pill — discussion points")
        st.markdown(pc["protocols"])
    st.markdown("")

    with st.container():
        st.markdown("#### Nutrition & movement")
        st.markdown(pc["nutrition_movement"])

    st.divider()
    pdf_bytes = build_medical_summary_pdf(survey, key)
    st.download_button(
        "Export medical summary (PDF)",
        data=pdf_bytes,
        file_name="eatwise_metabolic_pcos_summary.pdf",
        mime="application/pdf",
        type="primary",
    )
    st.caption("Bring this PDF to visits when you want to discuss metabolic care beyond birth control.")

    if st.button("Retake phenotype survey", key="retake"):
        st.session_state.survey_complete = False
        st.session_state.survey = {}
        st.session_state.phenotype_key = None
        st.session_state.wizard_step = 0
        st.rerun()


def _render_scanner_sidebar() -> None:
    st.markdown("**Food label scanner**")
    _ensure_openai_key()
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    if not st.session_state.survey_complete:
        st.caption("Complete the survey to personalize the AI lens.")
        return
    if not has_key:
        st.warning("Add `OPENAI_API_KEY` to `.env` or Streamlit secrets to enable scanning.")
        return
    up = st.file_uploader("Ingredient label photo", type=["png", "jpg", "jpeg", "webp"], key="side_upload")
    if up and st.button("Analyze label", key="side_analyze"):
        data = up.getvalue()
        mime = up.type or "image/jpeg"
        with st.spinner("Analyzing label..."):
            try:
                out = analyze_label_image(data, mime, st.session_state.phenotype_key)
                st.session_state["last_scan_result"] = out
            except Exception as e:
                st.session_state["last_scan_result"] = f"Error: {e}"
    if st.session_state.get("last_scan_result"):
        st.markdown(st.session_state["last_scan_result"])


def main() -> None:
    st.set_page_config(
        page_title="EatWise",
        page_icon="🌸",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_soft_clinical_css()
    _ensure_openai_key()
    _init_session()

    _render_nav()

    view = st.session_state.get("eatwise_view", "landing")
    if view == "landing":
        _render_landing()
    elif view == "about":
        _render_about_page()
    elif view == "solution":
        _render_solution_page()
    elif view == "recipes":
        _render_recipes_page()
    elif view == "symptom_diary":
        _render_symptom_diary_page()
    else:
        _render_platform_app()


if __name__ == "__main__":
    main()
