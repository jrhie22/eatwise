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


def _init_session() -> None:
    defaults: dict[str, Any] = {
        "wizard_step": 0,
        "survey_complete": False,
        "survey": {},
        "phenotype_key": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


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

    st.title("EatWise")
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


if __name__ == "__main__":
    main()
