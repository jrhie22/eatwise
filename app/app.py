def _render_symptom_diary_page() -> None:
    st.subheader("Symptom Diary")
    st.info("This is a placeholder for the Symptom Diary feature. You can add your daily symptoms, notes, or other relevant information here in the future.")



import hashlib
import json
import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from label_vision import analyze_label_image
from medical_pdf import build_medical_summary_pdf
from phenotype_engine import PHENOTYPE_LABELS, get_phenotype, phenotype_content
from recipe_store import RECIPE_STEP_SCHEMA, recent_recipes, save_recipe

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


def _init_session() -> None:
    defaults: dict[str, Any] = {
        "wizard_step": 0,
        "survey_complete": False,
        "survey": {},
        "phenotype_key": None,
        "eatwise_view": "landing",
        "auth_user": None,
        "auth_mode": "signin",  # or "signup"
    }


def _render_landing() -> None:
    # Only show nav bar, EatWise, and main content. Removed extra hero/header section above nav.
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
    if st.button("Check In", type="primary", key="landing_discover"):
        if not st.session_state.get("auth_user"):
            st.session_state.eatwise_view = "auth"
            st.rerun()
        else:
            st.session_state.eatwise_view = "platform"
            st.rerun()

def _render_auth_page() -> None:
    # Session state is initialized in main()
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'signin'
    mode = st.radio("Choose authentication mode", ["Sign In", "Sign Up"], index=0 if st.session_state.auth_mode == "signin" else 1, horizontal=True, key="auth_mode_radio")
    st.session_state.auth_mode = "signin" if mode == "Sign In" else "signup"
    mode_key = st.session_state.auth_mode
    email = st.text_input("Email", key=f"auth_email_{mode_key}")
    password = st.text_input("Password", type="password", key=f"auth_password_{mode_key}")
    if st.session_state.auth_mode == "signup":
        password2 = st.text_input("Confirm Password", type="password", key=f"auth_password2_{mode_key}")
    else:
        password2 = None
    if st.button("Continue", key=f"auth_continue_{mode_key}", type="primary"):
        if not email or not password or (st.session_state.auth_mode == "signup" and password != password2):
            st.error("Please fill all fields and make sure passwords match.")
        else:
            st.session_state.auth_user = {"email": email}
            st.session_state.eatwise_view = "platform"
            st.rerun()
    if 'auth_user' not in st.session_state:
        st.session_state.auth_user = None
    if st.session_state.auth_user:
        st.success(f"Signed in as {st.session_state.auth_user['email']}")
        if st.button("Sign out", key="auth_signout"):
            st.session_state.auth_user = None
            st.session_state.eatwise_view = "landing"
            st.rerun()
    st.divider()


# Ensure about page is defined at the top level
def _render_about_page() -> None:
    st.markdown("# EatWise")
    st.subheader("About")
    st.markdown("""
EatWise is the first AI phenotyping platform for PCOS. Our mission is to empower women with PCOS to understand their metabolic phenotype and receive personalized, evidence-based recommendations for nutrition, movement, and lifestyle.

**Features:**
- Diagnostic onboarding survey to determine your metabolic phenotype
- Personalized dashboard and recommendations
- Food label scanner with AI-powered analysis
- Symptom diary and recipe management
- Exportable medical summary PDF for clinician visits

EatWise is not a substitute for medical advice. Always consult your healthcare provider for diagnosis and treatment.
    """)


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
                st.session_state.pop("_survey_insights_cache", None)
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
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 0
    step = st.session_state.wizard_step
    total = 4
    st.progress((step + 1) / total, text=f"Step {step + 1} of {total}")

    if step == 0:
        st.subheader("General Information")
        name = st.text_input("Full Name", key="w_name")
        age = st.number_input("Age", min_value=0, max_value=120, value=30, key="w_age")
        country = st.text_input("Country", key="w_country")
        ethnicity = st.text_input("Ethnicity", key="w_ethnicity")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Next", type="primary"):
                st.session_state._draft = {
                    "name": name,
                    "age": age,
                    "country": country,
                    "ethnicity": ethnicity,
                }
                st.session_state.wizard_step = 1
                st.rerun()
        return

    if step == 1:
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
            if st.button("Back"):
                st.session_state.wizard_step = 0
                st.rerun()
        with c2:
            if st.button("Next", type="primary"):
                d = dict(st.session_state.get("_draft", {}))
                d.update({
                    "cycle_regularity": cycle,
                    "acne_severity": acne,
                    "hair_thinning": hair,
                })
                st.session_state._draft = d
                st.session_state.wizard_step = 2
                st.rerun()
        return

    # The rest of the steps increment by 1 (was step 1/2, now 2/3)
    if step == 2:
        st.subheader("Body composition & daily load")
        bmi = st.number_input("BMI", min_value=15.0, max_value=60.0, value=26.0, step=0.1, key="w_bmi")
        stress = st.slider("Stress levels (1 = low, 5 = high)", 1, 5, 3, key="w_stress")
        energy = st.slider("Energy levels (1 = low, 5 = high)", 1, 5, 3, key="w_energy")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back"):
                st.session_state.wizard_step = 1
                st.rerun()
        with c2:
            if st.button("Next", type="primary"):
                d = dict(st.session_state.get("_draft", {}))
                d.update({
                    "bmi": bmi,
                    "stress_level": stress,
                    "energy_level": energy,
                })
                st.session_state._draft = d
                st.session_state.wizard_step = 3
                st.rerun()
        return

    if step == 3:
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
                st.session_state.wizard_step = 2
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
                d.update({
                    "sugar_cravings": sugar,
                    "weight_pattern": weight_pattern,
                    "sleep_trouble": sleep_trouble,
                    "digestive_issues": digestive,
                    "joint_pain": joint,
                    "post_pill": pill_map[post_pill],
                })
                st.session_state.survey = d
                st.session_state.phenotype_key = get_phenotype(d)
                st.session_state.survey_complete = True
                st.session_state.wizard_step = 0
                if "_draft" in st.session_state:
                    del st.session_state._draft
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


def _ai_insights_keys_configured() -> bool:
    return bool(os.environ.get("MISTRAL_API_KEY", "").strip())


def _ensure_survey_insights(
    survey: dict[str, Any],
    phenotype_key: str,
    phenotype_label: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Load or fetch survey LLM bullets. Uses session cache keyed by survey + phenotype.

    Returns ``(insights, error_message)``. ``error_message`` is set only when API keys
    are present but the request or parse failed. When keys are missing, returns
    ``(None, None)``.
    """
    sig = hashlib.sha256(
        json.dumps({"survey": survey, "key": phenotype_key}, sort_keys=True, default=str).encode()
    ).hexdigest()
    cache = st.session_state.get("_survey_insights_cache")
    if isinstance(cache, dict) and cache.get("sig") == sig:
        if cache.get("_fetch_failed"):
            return None, str(cache.get("_fetch_error") or "Request failed")
        return cache.get("insights"), None

    if not _ai_insights_keys_configured():
        return None, None

    from survey_insights import fetch_survey_insights

    try:
        insights = fetch_survey_insights(survey, phenotype_key, phenotype_label)
        st.session_state["_survey_insights_cache"] = {
            "sig": sig,
            "insights": insights,
            "_fetch_failed": False,
        }
        return insights, None
    except Exception as e:
        st.session_state["_survey_insights_cache"] = {
            "sig": sig,
            "insights": None,
            "_fetch_failed": True,
            "_fetch_error": str(e),
        }
        return None, str(e)


def _render_solution_page() -> None:
    st.subheader("Solution - Different ways you can explore")
    st.markdown(
        """
**1. Phenotype survey** — Answer our short questions about cycles, skin, stress, weight pattern, sleep, digestion, and recent birth control use. Answers map to a metabolic phenotype (Types A–D).

**2. Personalized dashboard** — Root-cause framing, nutrition and movement ideas, and discussion points for clinic visits — all filtered through your phenotype.

**3. Food label scanner** — Upload an ingredient label; we interpret it in the context of your phenotype (requires an OpenAI API key).

Export a **medical summary PDF** from the dashboard when you want something concrete to bring to an appointment.
        """
    )

    if 'survey_complete' not in st.session_state:
        st.session_state.survey_complete = False
    if not st.session_state.survey_complete:
        st.info(
            "Use **Discover Your Recommendations** on the home page to complete the survey. "
            "Then return here for AI nutrition highlights matched to your answers."
        )
        return

    key = st.session_state.phenotype_key
    survey = st.session_state.survey
    if not key or not survey:
        st.warning("Survey state is incomplete. Finish the phenotype survey from the home flow.")
        return

    label = PHENOTYPE_LABELS[key]
    st.divider()
    st.markdown(f"**Your phenotype:** {label}")

    if not _ai_insights_keys_configured():
        st.caption(
            "Add `MISTRAL_API_KEY` to `.env` to show three grounded advice bullets here (same output as the PDF add-on)."
        )
        return

    with st.spinner("Loading personalized nutrition highlights…"):
        insights, err = _ensure_survey_insights(survey, key, label)

    if err:
        st.warning(
            f"Could not load AI highlights ({err}). Check your API key and network, then refresh this page."
        )
        return

    if not insights:
        return

    bullets = list(insights.get("general_advice") or insights.get("must_know") or [])
    st.markdown("#### AI-Powered General advice (Based on your Initial Answers)")
    for item in bullets[:3]:
        st.markdown(f"- {item}")
    st.caption(
        "Three bullets from Mistral AI, grounded in the same text as your PDF. "
        "For discussion with your clinician, not a diagnosis."
    )


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
    insights: dict[str, Any] | None = None
    insight_err: str | None = None
    if _ai_insights_keys_configured():
        with st.spinner("Generating AI nutrition highlights for your PDF…"):
            insights, insight_err = _ensure_survey_insights(survey, key, label)
        if insight_err:
            st.warning(
                f"Could not add AI highlights to the PDF ({insight_err}). "
                "The export still includes your survey and phenotype content."
            )
    else:
        st.caption(
            "Optional: set `MISTRAL_API_KEY` in `.env` to append three grounded general-advice bullets to the PDF."
        )

    pdf_bytes = build_medical_summary_pdf(survey, key, insights=insights)
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
        st.session_state.pop("_survey_insights_cache", None)
        st.rerun()


def _render_scanner_sidebar() -> None:
    st.markdown("**Food label scanner**")
    _ensure_openai_key()
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    if 'survey_complete' not in st.session_state:
        st.session_state.survey_complete = False
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


def _render_recipes_tab() -> None:
    st.subheader("Recipes")
    st.caption("Ideas saved to local **`data/recipes.json`** (bundled examples + your adds). Not medical advice.")

    with st.form("recipe_form", clear_on_submit=True):
        name = st.text_input("Recipe name", max_chars=200, placeholder="e.g. PCOS flaxseed smoothie")
        ingredients = st.text_area(
            "Ingredients",
            height=120,
            placeholder="List main ingredients (one per line is fine).",
        )
        st.markdown("**Steps** (same choices for all users — easy to compare and filter later)")
        step_choices: dict[str, str] = {}
        for key, label, options in RECIPE_STEP_SCHEMA:
            step_choices[key] = st.selectbox(label, options, key=f"recipe_step_{key}")
        goals_fit = st.text_area(
            "How it fits your goals",
            height=100,
            placeholder="e.g. Keeps me full until lunch, aligns with my insulin-resistance lens…",
        )
        st.markdown("**PCOS-oriented flags** (`pcos_rules` in JSON)")
        c1, c2 = st.columns(2)
        with c1:
            low_gi = st.checkbox("Low glycemic emphasis", value=True)
        with c2:
            anti_inflam = st.checkbox("Anti-inflammatory emphasis", value=True)
        fiber = st.number_input("Fiber (grams, approximate per serving)", min_value=0.0, max_value=120.0, value=0.0, step=1.0)
        nick = st.text_input("Display name (optional)", max_chars=80)
        submitted = st.form_submit_button("Save recipe")

    if submitted:
        if not (name or "").strip():
            st.error("Please add a recipe name.")
        else:
            with st.spinner("Saving…"):
                try:
                    save_recipe(
                        name,
                        ingredients or "",
                        step_choices,
                        goals_fit or "",
                        low_gi=low_gi,
                        anti_inflammatory=anti_inflam,
                        fiber_grams=fiber,
                        phenotype_key=st.session_state.get("phenotype_key"),
                        display_name=nick,
                        status="Submitted",
                    )
                    st.success("Saved.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    st.divider()
    st.markdown("#### Recent recipes")
    try:
        with st.spinner("Loading…"):
            rows = recent_recipes(24)
        if not rows:
            st.info("No recipes in `data/recipes.json` yet—add one above.")
        else:
            for row in rows:
                who = row.get("display_name") or "Anonymous"
                ph = row.get("phenotype_key")
                extra = f" · lens `{ph}`" if ph else ""
                ts = row.get("created_at")
                if isinstance(ts, str) and ts:
                    ts_s = ts.replace("+00:00", "Z")[:19] + " UTC"
                elif hasattr(ts, "strftime"):
                    ts_s = ts.strftime("%Y-%m-%d %H:%M UTC")
                else:
                    ts_s = "—"
                pr = row.get("pcos_rules") or {}
                flags = (
                    f"low GI: {pr.get('low_gi')} · anti-inflammatory: {pr.get('anti_inflammatory')} · "
                    f"fiber ~{pr.get('fiber_grams')} g"
                )
                sd = row.get("steps") or {}
                with st.container(border=True):
                    st.markdown(
                        f"**{row['title']}** · `{row.get('status') or '—'}` · _{who}_{extra}_ · _{ts_s}_"
                    )
                    st.caption(flags)
                    if row.get("ingredients"):
                        st.markdown("**Ingredients**")
                        st.write(row["ingredients"])
                    if any(sd.get(k) for k, _, _ in RECIPE_STEP_SCHEMA):
                        st.markdown("**Steps (rule-based)**")
                        for key, label, _opts in RECIPE_STEP_SCHEMA:
                            v = sd.get(key)
                            if v:
                                st.write(f"- **{label}:** {v}")
                    if row.get("goals_fit"):
                        st.markdown("**How it fits your goals**")
                        st.write(row["goals_fit"])
                    if row.get("notes") and not row.get("ingredients"):
                        st.markdown("**Notes (legacy)**")
                        st.write(row["notes"])
    except Exception as e:
        st.error(f"Could not load recipes: {e}")


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
        _render_recipes_tab()
    elif view == "symptom_diary":
        _render_symptom_diary_page()
    elif view == "auth":
        _render_auth_page()
    elif view == "platform":
        if st.session_state.auth_user is None:
            st.session_state.eatwise_view = "auth"
            st.rerun()
        _render_platform_app()
    else:
        _render_platform_app()


if __name__ == "__main__":
    main()
