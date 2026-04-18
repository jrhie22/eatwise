"""Doctor advocacy PDF via fpdf2 (import as fpdf)."""

from __future__ import annotations

from datetime import date
from typing import Any

from fpdf import FPDF

from phenotype_engine import PHENOTYPE_LABELS, phenotype_content


def _pdf_text(s: str) -> str:
    """Core fonts are Latin-1; normalize common Unicode punctuation."""
    return (
        s.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )


class _EatWisePDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def _pdf_bullet_block(pdf: FPDF, title: str, items: list[str]) -> None:
    if not items:
        return
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 8, _pdf_text(title), ln=True)
    pdf.set_font("Helvetica", "", 10)
    for it in items:
        pdf.multi_cell(0, 5, _pdf_text(f"- {it}"))
        pdf.set_x(pdf.l_margin)


def build_medical_summary_pdf(
    survey: dict[str, Any],
    phenotype_key: str,
    *,
    insights: dict[str, Any] | None = None,
) -> bytes:
    """Generate PDF bytes for clinician handoff. Optional ``insights`` with ``general_advice`` (3 bullets) from Mistral."""
    label = PHENOTYPE_LABELS[phenotype_key]
    pc = phenotype_content(phenotype_key)

    pdf = _EatWisePDF()
    pdf.alias_nb_pages()
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Title band
    pdf.set_fill_color(255, 209, 220)
    pdf.set_draw_color(230, 180, 190)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_y(10)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 8, "EatWise - Metabolic PCOS Summary", ln=True, align="C")
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "For clinical discussion (not a diagnosis)", ln=True, align="C")

    pdf.set_xy(pdf.l_margin, 36)
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Patient-reported snapshot", ln=True)
    pdf.set_font("Helvetica", "", 10)

    lines = [
        f"Date: {date.today().isoformat()}",
        f"Metabolic phenotype (app-derived): {label}",
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
    for line in lines:
        pdf.multi_cell(0, 5, _pdf_text(str(line)))
        pdf.set_x(pdf.l_margin)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Framing: root cause hypothesis (patient education)", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _pdf_text(_strip_md(pc["root_cause"])))
    pdf.set_x(pdf.l_margin)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Lifestyle and supplement topics for discussion", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _pdf_text(_strip_md(pc["protocols"])))
    pdf.set_x(pdf.l_margin)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Nutrition & movement emphasis", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _pdf_text(_strip_md(pc["nutrition_movement"])))
    pdf.set_x(pdf.l_margin)

    advice = list(insights.get("general_advice") or insights.get("must_know") or [])[:3] if insights else []
    if advice:
        pdf.add_page()
        pdf.set_y(pdf.t_margin)
        pdf.set_text_color(40, 40, 40)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "General advice (for discussion)", ln=True)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(
            0,
            4,
            _pdf_text(
                "Three bullets grounded in your EatWise summary (survey + PDF framing), "
                "via Mistral. Not a diagnosis; confirm with your clinician."
            ),
        )
        pdf.set_x(pdf.l_margin)
        pdf.set_text_color(40, 40, 40)
        _pdf_bullet_block(pdf, "Key points", advice)

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(
        0,
        4,
        _pdf_text(
            "Disclaimer: EatWise is an educational tool. It does not replace medical advice, "
            "diagnosis, or treatment. The patient is seeking metabolic-first strategies as an "
            "alternative or complement to hormonal suppression when clinically appropriate."
        ),
    )

    raw = pdf.output(dest="S")
    return bytes(raw)


def _strip_md(text: str) -> str:
    return text.replace("**", "")
