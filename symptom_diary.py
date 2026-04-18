"""
symptom_diary.py
Daily symptom logging for PCOS — stores entries in Streamlit session state,
renders the daily log form, history view, and AI-powered summary.
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any

import streamlit as st

# ── Symptom schema ────────────────────────────────────────────────────────────

SYMPTOMS: list[dict] = [
    {
        "key": "cycle_regularity",
        "label": "Cycle Regularity",
        "icon": "🔄",
        "type": "select",
        "options": ["Regular", "Slightly off", "Irregular", "Absent / skipped"],
    },
    {
        "key": "acne_severity",
        "label": "Acne Severity",
        "icon": "🔴",
        "type": "select",
        "options": ["None", "Mild", "Moderate", "Severe / cystic"],
    },
    {
        "key": "hair_thinning",
        "label": "Hair Thinning noticed today",
        "icon": "💇",
        "type": "checkbox",
    },
    {
        "key": "energy_levels",
        "label": "Energy Levels",
        "icon": "⚡",
        "type": "slider",
        "min": 1,
        "max": 5,
        "default": 3,
        "low_label": "Exhausted",
        "high_label": "Energized",
    },
    {
        "key": "stress_levels",
        "label": "Stress Levels",
        "icon": "😤",
        "type": "slider",
        "min": 1,
        "max": 5,
        "default": 3,
        "low_label": "Calm",
        "high_label": "Very stressed",
    },
    {
        "key": "sugar_cravings",
        "label": "Sugar Cravings",
        "icon": "🍬",
        "type": "select",
        "options": ["None", "Mild", "Moderate", "Strong / hard to resist"],
    },
    {
        "key": "sleep_difficulty",
        "label": "Sleep Quality",
        "icon": "😴",
        "type": "select",
        "options": ["Slept well", "Some difficulty", "Woke up often", "Barely slept"],
    },
    {
        "key": "bloating",
        "label": "Bloating",
        "icon": "🫧",
        "type": "checkbox",
    },
    {
        "key": "inflammation",
        "label": "Inflammation / Puffiness",
        "icon": "🔥",
        "type": "checkbox",
    },
    {
        "key": "joint_pain",
        "label": "Joint Pain",
        "icon": "🦴",
        "type": "checkbox",
    },
]

# ── Session state ─────────────────────────────────────────────────────────────

def _init() -> None:
    if "diary_entries" not in st.session_state:
        st.session_state.diary_entries: dict[str, dict] = {}
    if "diary_summary" not in st.session_state:
        st.session_state.diary_summary: str = ""
    if "diary_summary_loading" not in st.session_state:
        st.session_state.diary_summary_loading = False


def _today() -> str:
    return date.today().isoformat()


def _all_entries() -> list[tuple[str, dict]]:
    return sorted(st.session_state.diary_entries.items(), reverse=True)


# ── AI summary ────────────────────────────────────────────────────────────────

def _build_summary_prompt(entries: list[tuple[str, dict]], phenotype_key: str | None) -> str:
    phenotype_line = f"Her PCOS phenotype is: {phenotype_key}." if phenotype_key else ""
    lines = [
        "You are a metabolic health assistant supporting a woman with PCOS.",
        phenotype_line,
        "Below are her symptom diary entries (newest first). Each entry includes symptoms logged that day and foods consumed.",
        "Write a concise, warm, and clinically grounded summary that:",
        "1. Identifies the top 2-3 symptom patterns or trends across her logs.",
        "2. Notes any food-symptom correlations you observe.",
        "3. Gives 2-3 specific, actionable recommendations based on her patterns.",
        "4. Reminds her this is a companion tool, not a diagnosis.",
        "Keep the tone supportive and clear. Use plain language, no jargon.",
        "",
        "=== DIARY ENTRIES ===",
    ]
    for date_str, entry in entries:
        lines.append(f"\nDate: {date_str}")
        for s in SYMPTOMS:
            val = entry.get(s["key"])
            if val is not None:
                lines.append(f"  {s['label']}: {val}")
        foods = entry.get("foods_consumed", "").strip()
        if foods:
            lines.append(f"  Foods consumed: {foods}")
    return "\n".join(lines)


def _generate_summary(phenotype_key: str | None) -> None:
    entries = _all_entries()
    if not entries:
        st.session_state.diary_summary = "No entries logged yet."
        return

    prompt = _build_summary_prompt(entries, phenotype_key)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        st.session_state.diary_summary = message.content[0].text
    except Exception as e:
        # Fallback: rule-based summary if API unavailable
        st.session_state.diary_summary = _rule_based_summary(entries)


def _rule_based_summary(entries: list[tuple[str, dict]]) -> str:
    """Simple pattern summary when AI is unavailable."""
    n = len(entries)
    if n == 0:
        return "No entries to summarize yet."

    # Count checkbox symptoms
    checkbox_keys = ["hair_thinning", "bloating", "inflammation", "joint_pain"]
    counts: dict[str, int] = {k: 0 for k in checkbox_keys}
    energy_vals, stress_vals = [], []
    all_foods: list[str] = []

    for _, entry in entries:
        for k in checkbox_keys:
            if entry.get(k):
                counts[k] += 1
        if entry.get("energy_levels"):
            energy_vals.append(int(entry["energy_levels"]))
        if entry.get("stress_levels"):
            stress_vals.append(int(entry["stress_levels"]))
        if entry.get("foods_consumed", "").strip():
            all_foods.append(entry["foods_consumed"].strip())

    lines = [f"**Summary across {n} logged day(s):**\n"]

    for k, cnt in counts.items():
        if cnt > 0:
            label = next(s["label"] for s in SYMPTOMS if s["key"] == k)
            lines.append(f"- **{label}** reported on {cnt} of {n} days.")

    if energy_vals:
        avg_e = sum(energy_vals) / len(energy_vals)
        lines.append(f"- Average **energy level**: {avg_e:.1f} / 5.")
    if stress_vals:
        avg_s = sum(stress_vals) / len(stress_vals)
        lines.append(f"- Average **stress level**: {avg_s:.1f} / 5.")
    if all_foods:
        lines.append(f"\n**Foods logged across entries:** {'; '.join(all_foods[:5])}")

    lines.append(
        "\n_For a deeper AI-powered analysis, add an Anthropic API key to your `.env` file._"
    )
    return "\n".join(lines)


# ── Symptom log form ──────────────────────────────────────────────────────────

def _render_log_form() -> None:
    today = _today()
    existing = st.session_state.diary_entries.get(today, {})

    st.markdown(f"#### 📅 Today — {today}")
    if existing:
        st.success("✅ You've already logged today. You can update your entry below.")

    entry: dict[str, Any] = {}

    # ── Symptoms grid ─────────────────────────────────────────────────────────
    st.markdown("##### Symptoms")

    # Render in 2-column layout
    col_left, col_right = st.columns(2)
    cols = [col_left, col_right]

    for i, symptom in enumerate(SYMPTOMS):
        col = cols[i % 2]
        key = symptom["key"]
        label = f"{symptom['icon']} {symptom['label']}"

        with col:
            with st.container():
                if symptom["type"] == "checkbox":
                    default_val = existing.get(key, False)
                    entry[key] = st.checkbox(label, value=default_val, key=f"diary_{key}")

                elif symptom["type"] == "select":
                    options = symptom["options"]
                    default_val = existing.get(key, options[0])
                    idx = options.index(default_val) if default_val in options else 0
                    entry[key] = st.selectbox(label, options, index=idx, key=f"diary_{key}")

                elif symptom["type"] == "slider":
                    default_val = existing.get(key, symptom["default"])
                    val = st.slider(
                        label,
                        min_value=symptom["min"],
                        max_value=symptom["max"],
                        value=int(default_val),
                        key=f"diary_{key}",
                    )
                    st.caption(f"1 = {symptom['low_label']} · 5 = {symptom['high_label']}")
                    entry[key] = val

    # ── Foods consumed ────────────────────────────────────────────────────────
    st.markdown("##### 🍽️ Foods consumed today")
    st.caption("List the main foods you ate — be as specific or general as you like.")
    entry["foods_consumed"] = st.text_area(
        "Foods",
        value=existing.get("foods_consumed", ""),
        placeholder="e.g. oatmeal with berries, lentil soup, grilled salmon, apple...",
        height=100,
        key="diary_foods",
        label_visibility="collapsed",
    )

    # ── Notes ─────────────────────────────────────────────────────────────────
    entry["notes"] = st.text_area(
        "📝 Additional notes (optional)",
        value=existing.get("notes", ""),
        placeholder="Anything else worth noting — mood, medications, exercise...",
        height=80,
        key="diary_notes",
    )

    st.markdown("")
    if st.button("💾 Save today's log", type="primary", key="diary_save"):
        st.session_state.diary_entries[today] = entry
        st.session_state.diary_summary = ""  # invalidate old summary
        st.success("✅ Entry saved!")
        st.rerun()


# ── History view ──────────────────────────────────────────────────────────────

def _render_history() -> None:
    entries = _all_entries()
    if not entries:
        st.info("No entries yet. Log your first day using the **Log Today** tab.")
        return

    st.markdown(f"#### 📋 All entries ({len(entries)} days logged)")

    for date_str, entry in entries:
        with st.expander(f"📅 {date_str}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                for s in SYMPTOMS[:5]:
                    val = entry.get(s["key"])
                    if val is not None:
                        st.markdown(f"**{s['icon']} {s['label']}:** {val}")
            with col2:
                for s in SYMPTOMS[5:]:
                    val = entry.get(s["key"])
                    if val is not None:
                        st.markdown(f"**{s['icon']} {s['label']}:** {val}")

            foods = entry.get("foods_consumed", "").strip()
            if foods:
                st.markdown(f"**🍽️ Foods:** {foods}")
            notes = entry.get("notes", "").strip()
            if notes:
                st.markdown(f"**📝 Notes:** {notes}")


# ── Summary view ──────────────────────────────────────────────────────────────

def _render_summary(phenotype_key: str | None) -> None:
    entries = _all_entries()
    n = len(entries)

    if n == 0:
        st.info("Log at least one day before generating a summary.")
        return

    st.markdown(f"#### 🧠 Pattern Summary — {n} day(s) logged")
    st.caption(
        "This summary identifies trends across your diary entries and gives "
        "actionable guidance based on your phenotype. It is not a diagnosis."
    )

    if st.button("✨ Generate summary", type="primary", key="diary_gen_summary"):
        with st.spinner("Analyzing your patterns..."):
            _generate_summary(phenotype_key)

    if st.session_state.diary_summary:
        st.divider()
        st.markdown(st.session_state.diary_summary)


# ── Public entry point ────────────────────────────────────────────────────────

def render_symptom_diary() -> None:
    _init()

    phenotype_key = st.session_state.get("phenotype_key", None)

    st.markdown("### 📓 Symptom Diary")
    st.caption(
        "Log your symptoms daily to track patterns over time. "
        "The more consistently you log, the more useful the pattern summary becomes."
    )

    if phenotype_key:
        from phenotype_engine import PHENOTYPE_LABELS
        label = PHENOTYPE_LABELS.get(phenotype_key, phenotype_key)
        st.markdown(
            f'<div style="display:inline-block;background:#FFD1DC;color:#fff;'
            f'padding:0.3rem 0.8rem;border-radius:999px;font-size:0.85rem;'
            f'font-weight:600;margin-bottom:1rem">Logging for: {label}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info(
            "💡 Complete the **Phenotype survey** in the app to personalize your pattern summary."
        )

    tab_log, tab_history, tab_summary = st.tabs(["📅 Log Today", "📋 History", "🧠 Summary"])

    with tab_log:
        _render_log_form()

    with tab_history:
        _render_history()

    with tab_summary:
        _render_summary(phenotype_key)