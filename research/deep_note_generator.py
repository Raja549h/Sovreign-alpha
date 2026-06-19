"""
Deep Note Generator — 19-Section Institutional Report Generator
================================================================
Extends existing note_generator.py with full deep research structure.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
NOTES_DIR = BASE_DIR / "research" / "data" / "notes"
load_dotenv(BASE_DIR / ".env")
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

EVOLUTION_SYSTEM_PROMPT = """You are a senior institutional equity analyst tracking changes in a company's business quality, governance, and financial trajectory over time.

Compare the current observation against the prior observation for the same category.
Classify the evolution as exactly one of:
STRENGTHENING — the situation has improved
STABLE — no material change
WEAKENING — the situation has deteriorated
REVERSING — complete directional change (e.g., improving to deteriorating)
CONTRADICTING — new data contradicts the prior observation
NEW_FINDING — no prior observation exists

Output JSON only: {"status": "...", "evidence": "...one sentence explanation..."}"""

SYSTEM_PROMPT = """You are a senior institutional equity analyst at a concentrated hedge fund specialising in forensic research. You produce deep research reports for sophisticated institutional investors.

Your writing style:
- Cold, forensic, analytical, never retail
- Every claim backed by a specific number
- Second-order thinking throughout
- Institutional language only
- No buy/sell recommendations
- No price targets
- No hype or promotional language
- Signal-dense — every sentence adds information

You are producing a section of a deep research report. Each section must be substantive — minimum 3-5 analytical sentences per section. No filler. No repetition across sections. If data for a section is unavailable state clearly: 'Insufficient public data available for this analysis.'

TONE BENCHMARK: Goldman Sachs Equity Research meets Palantir institutional intelligence report."""

SECTION_PROMPTS = {
    "01_executive_summary": "Generate a 4-sentence executive summary for {company} ({ticker}). Central analytical observation first. Second-order institutional question second. Key risk factor third. Assessment positioning fourth. No buy/sell language.",
    "02_business_overview": "Describe {company}'s business model, revenue sources, competitive moat, and structural positioning. Focus on what makes this business defensible or vulnerable at an institutional level. Sector context: {sector_context}",
    "03_financial_trend_analysis": "Analyse the 3-year financial trajectory of {company} using this data: {financial_data}. Identify directional trends in revenue, margins, and returns. Flag any divergences from sector norms.",
    "04_revenue_margin_structure": "Examine revenue quality, mix, and margin structure for {company}. Identify whether margin trends are structural or cyclical. Data: {financial_data}",
    "05_roe_roce_analysis": "Decompose ROE using DuPont framework for {company}. Identify whether returns are driven by leverage, asset turnover, or genuine margin expansion. Data: {financial_data}",
    "06_balance_sheet_review": "Assess balance sheet quality for {company}. Focus on asset quality, liability structure, and off-balance-sheet exposures if any. Data: {financial_data}",
    "07_working_capital_analysis": "Analyse working capital dynamics for {company}. Calculate and trend inventory days, debtor days, creditor days, and cash conversion cycle. Flag any deterioration. Data: {financial_data}",
    "08_debt_liquidity_structure": "Examine debt quantum, maturity profile, and liquidity position for {company}. Assess refinancing risk and covenant sensitivity. Data: {financial_data}",
    "09_management_commentary": "Analyse management commentary for narrative consistency and guidance accuracy. Identify any language shifts or hedging patterns. Data: {management_commentary}",
    "10_earnings_transcript_intelligence": "Extract key analytical signals from earnings transcript data for {company}. Flag any guidance-vs-actual divergences. Data: {management_commentary}",
    "11_macro_sensitivity_mapping": "Map {company}'s business model sensitivity to current macro regime. Identify the top 3 macro variables most likely to impact earnings quality. Regime: {macro_context}",
    "12_second_order_risks": "Identify 3-5 second-order risks for {company} that are not visible in headline financial metrics. These must be non-obvious observations requiring cross-referencing multiple data sources.",
    "13_valuation_fragility": "Assess whether current valuation multiple for {company} is sustainable given actual earnings quality and return profile. PE: {pe}, PBV: {pbv}. Data: {financial_data}",
    "14_institutional_risk_assessment": "Produce a structured risk assessment for a concentrated value-oriented institutional investor holding {company}. Focus on position sizing implications.",
    "15_capital_allocation_analysis": "Assess how {company} allocates capital — capex intensity, dividend policy, buyback history, and acquisition track record. Is capital being deployed productively? Data: {financial_data}",
    "16_governance_red_flags": "Scan for governance indicators — promoter pledge, related party transactions, auditor changes, regulatory actions, and ownership concentration for {company}. Data: {financial_data} {sector_context}",
    "17_scenario_stress_testing": "Run three scenarios for {company}: Base case (current trajectory continues), Bear case (macro deterioration + sector stress), Bull case (operational improvement + re-rating). For each describe key assumptions and impact on earnings quality.",
    "18_competitive_positioning": "Assess {company}'s competitive position relative to sector peers. Market share trend, pricing power, switching costs, and entry barrier analysis. Data: {competitive_position}",
    "19_final_institutional_verdict": "Produce the final institutional verdict for {company}. Not a buy/sell recommendation. A structured assessment of: analytical confidence level, key variables to monitor, what would change the assessment positively, what would change it negatively, and the central institutional question this analysis leaves unresolved for a concentrated holder.",
    "20_thesis_evolution": "Generate the Thesis Evolution Analysis section for {company} ({ticker}). Evaluate whether each observation category is strengthening, stable, weakening, or reversing. Categorize: margin, funding_cost, governance, capital_allocation, valuation, macro, management_commentary, liquidity, business_quality. Provide an overall directional assessment and highlight key changes, confirmed observations, invalidated observations, and new findings.",
    "21_observation_validation_audit": "Generate the Observation Validation & Edge Tracking Audit for {company} ({ticker}). This section retroactively scores every prior observation against actual outcomes. For each observation category (margin, funding_cost, governance, capital_allocation, valuation, macro, management_commentary, liquidity, business_quality), state: (a) the original observation, (b) whether it was CONFIRMED, PARTIALLY_CONFIRMED, MONITORING, or INVALIDATED, (c) the accuracy contribution (+1, +0.5, 0, -1), (d) institutional lesson for future analysis. Provide the overall edge accuracy rate as a percentage and edge score out of 100. Highlight the institution's strongest and weakest predictive categories. Use data: {observation_data}",
}

SECTION_LABELS = {
    "01_executive_summary": "Executive Summary",
    "02_business_overview": "Business Overview",
    "03_financial_trend_analysis": "Financial Trend Analysis",
    "04_revenue_margin_structure": "Revenue & Margin Structure",
    "05_roe_roce_analysis": "ROE / ROCE Analysis",
    "06_balance_sheet_review": "Balance Sheet Review",
    "07_working_capital_analysis": "Working Capital Analysis",
    "08_debt_liquidity_structure": "Debt & Liquidity Structure",
    "09_management_commentary": "Management Commentary Analysis",
    "10_earnings_transcript_intelligence": "Earnings Transcript Intelligence",
    "11_macro_sensitivity_mapping": "Macro Sensitivity Mapping",
    "12_second_order_risks": "Second-Order Risk Factors",
    "13_valuation_fragility": "Valuation Fragility",
    "14_institutional_risk_assessment": "Institutional Risk Assessment",
    "15_capital_allocation_analysis": "Capital Allocation Analysis",
    "16_governance_red_flags": "Governance & Red Flags",
    "17_scenario_stress_testing": "Scenario Stress Testing",
    "18_competitive_positioning": "Competitive Positioning",
    "19_final_institutional_verdict": "Final Institutional Verdict",
    "20_thesis_evolution": "Thesis Evolution Analysis",
    "21_observation_validation_audit": "Observation Validation & Edge Tracking Audit",
}

def _generate_section(section_key: str, company: str, ticker: str, context: Dict) -> str:
    if not GROQ_API_KEY:
        return "Section generation unavailable. Groq API key not configured."
    prompt = SECTION_PROMPTS.get(section_key, "Analyse {company} ({ticker})").format(
        company=company, ticker=ticker,
        financial_data=json.dumps(context.get("financial_data", {}), indent=2)[:2000],
        management_commentary=(context.get("management_commentary") or "")[:2000],
        sector_context=(context.get("sector_context") or "")[:1500],
        competitive_position=(context.get("competitive_position") or "")[:1500],
        macro_context=json.dumps(context.get("macro_context", {}), indent=2)[:1000],
        pe=context.get("pe", "N/A"), pbv=context.get("pbv", "N/A"),
        observation_data=json.dumps(context.get("observation_data", {}), indent=2)[:2000],
    )
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.15,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Section generation temporarily unavailable. Data recorded for manual review. [{str(e)[:100]}]"

def generate_all_sections(company_name: str, ticker: str, context: Dict) -> Dict[str, str]:
    sections = {}
    for key in SECTION_PROMPTS:
        sections[key] = _generate_section(key, company_name, ticker, context)
    return sections

def _sign_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def format_sections_to_html(reference: str, company_name: str, ticker: str, sector: str, sections: Dict[str, str], scores: Dict, flags: List, confidence: float, pe: float = None, pbv: float = None) -> str:
    scorecard_rows = ""
    if scores:
        for label, key in [("Risk Intensity", "risk_intensity"), ("Confidence", "confidence"), ("Regime Sensitivity", "regime_sensitivity"), ("Structural Quality", "structural_quality")]:
            val = scores.get(key)
            scorecard_rows += f"<tr><td>{label}</td><td>{f'{val:.1f}/10' if val is not None else 'N/A'}</td></tr>"
        comp = scores.get("composite_score") or scores.get("composite")
        if comp is not None:
            scorecard_rows += f"<tr class='composite'><td><strong>Composite</strong></td><td><strong>{float(comp):.1f}/10</strong></td></tr>"
    confidence_pct = int(confidence * 100) if confidence <= 1 else int(confidence)
    confidence_bars = "█" * (confidence_pct // 10) + "░" * (10 - confidence_pct // 10)
    if confidence_pct > 80:
        conf_color = "#00ff9f"
        conf_label = "HIGH CONFIDENCE"
    elif confidence_pct > 60:
        conf_color = "#ffb800"
        conf_label = "MODERATE CONFIDENCE"
    else:
        conf_color = "#ff4444"
        conf_label = "LIMITED DATA — treat with caution"
    flags_html = ""
    if flags:
        for f in flags:
            ft = f.get("flag_type", "").replace("_", " ").upper()
            fsev = f.get("severity", "low").lower()
            fcolor = "#ff4444" if fsev in ("high","critical") else "#ffb800" if fsev == "medium" else "#4488cc"
            flags_html += f"<span class='flag-pill' style='border-color:{fcolor};color:{fcolor};'>{ft}</span>"
    sections_html = ""
    section_num = 1
    for key in SECTION_PROMPTS:
        label = SECTION_LABELS.get(key, key)
        content = sections.get(key, "")
        content_html = content.replace("\n", "<br>")
        sections_html += f"""
        <div class="report-section" id="section-{section_num:02d}">
            <div class="section-header">
                <span class="section-number">{section_num:02d}</span>
                <span class="section-title">{label}</span>
            </div>
            <div class="section-divider"></div>
            <div class="section-content">{content_html}</div>
        </div>"""
        section_num += 1
    nav_links = ""
    for i in range(1, 22):
        nav_links += f"<a href='#section-{i:02d}' class='nav-section'>{i:02d}</a>"
    now = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Sovereign Alpha Deep Research — {reference}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,'Segoe UI','Inter',sans-serif; background:#0a0b0e; color:#d8dae0; line-height:1.6; }}
.content {{ max-width:960px; margin:0 auto; padding:2rem 1.5rem; }}
.report-header {{ border-bottom:1px solid #1e1e1e; padding-bottom:1.5rem; margin-bottom:1.5rem; }}
.report-header .ref {{ font-family:'Courier New',monospace; font-size:0.75rem; color:#00ff9f; letter-spacing:1px; }}
.report-header h1 {{ font-size:1.6rem; font-weight:700; margin:0.5rem 0 0.25rem; color:#fff; }}
.report-header .meta {{ font-size:0.75rem; color:#888; font-family:'Courier New',monospace; }}
.confidence-meter {{ display:flex; align-items:center; gap:0.75rem; margin:0.75rem 0; font-family:'Courier New',monospace; font-size:0.8rem; }}
.confidence-meter .bar {{ font-size:1.1rem; letter-spacing:2px; }}
.confidence-meter .label {{ font-weight:700; }}
.flag-pills {{ display:flex; flex-wrap:wrap; gap:0.4rem; margin:0.75rem 0; }}
.flag-pill {{ padding:0.15rem 0.5rem; font-size:0.65rem; font-weight:700; font-family:'Courier New',monospace; border:1px solid; text-transform:uppercase; letter-spacing:0.5px; }}
.scorecard {{ background:#111316; border:1px solid #1e1e1e; padding:1rem; margin:1rem 0; font-size:0.8rem; }}
.scorecard table {{ width:100%; border-collapse:collapse; }}
.scorecard td {{ padding:0.4rem 0.6rem; border-bottom:1px solid #1e1e1e; }}
.scorecard .composite td {{ border-top:2px solid #00ff9f; border-bottom:none; color:#00ff9f; }}
.side-nav {{ position:fixed; left:0; top:50%; transform:translateY(-50%); display:flex; flex-direction:column; gap:2px; padding:0.5rem; background:#0d0d0d; border:1px solid #1e1e1e; }}
.side-nav .nav-section {{ color:#555; font-size:0.6rem; font-family:'Courier New',monospace; text-decoration:none; padding:2px 6px; text-align:center; transition:color 0.1s; }}
.side-nav .nav-section:hover {{ color:#00ff9f; }}
.report-section {{ margin-bottom:1.5rem; }}
.section-header {{ display:flex; align-items:center; gap:0.6rem; margin-bottom:0.4rem; }}
.section-number {{ font-family:'Courier New',monospace; font-size:0.7rem; color:#00ff9f; font-weight:700; min-width:28px; }}
.section-title {{ font-family:'Courier New',monospace; font-size:0.75rem; color:#888; text-transform:uppercase; letter-spacing:1px; }}
.section-divider {{ height:1px; background:linear-gradient(90deg,#1e1e1e,transparent); margin-bottom:0.6rem; }}
.section-content {{ font-size:0.82rem; line-height:1.7; color:#c8d0d8; }}
.actions {{ display:flex; gap:0.5rem; margin:1rem 0; }}
.btn {{ background:#00ff9f; color:#000; border:none; padding:0.5rem 1.2rem; font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.7px; cursor:pointer; font-family:'Courier New',monospace; }}
.btn:hover {{ opacity:0.85; }}
.btn.outline {{ background:transparent; border:1px solid #333; color:#888; }}
.btn.outline:hover {{ border-color:#00ff9f; color:#00ff9f; }}
@media (max-width:768px) {{ .side-nav {{ display:none; }} .content {{ padding:1rem; }} }}
</style>
</head>
<body>
<div class="side-nav" id="side-nav">{nav_links}</div>
<div class="content">
<div class="report-header">
<div class="ref">{reference}</div>
<h1>{company_name} ({ticker})</h1>
<div class="meta">{sector} · {now}</div>
<div class="actions">
<a href="/research/download/{reference}" class="btn outline">DOWNLOAD PDF</a>
</div>
<div class="confidence-meter">
<span style="color:{conf_color};">INTELLIGENCE CONFIDENCE: <span class="bar">{confidence_bars}</span> {confidence_pct}%</span>
<span style="color:{conf_color};" class="label">{conf_label}</span>
</div>
<div class="flag-pills">{flags_html}</div>
</div>
<div class="scorecard">
<table>{scorecard_rows}</table>
</div>
<div class="sections-container">{sections_html}</div>
</div>
<script>
var nav = document.getElementById('side-nav');
if (nav) {{
    var sections = document.querySelectorAll('.report-section');
    window.addEventListener('scroll', function() {{
        var current = '';
        sections.forEach(function(s) {{
            if (window.scrollY >= s.offsetTop - 200) current = s.id;
        }});
        nav.querySelectorAll('.nav-section').forEach(function(a) {{
            a.style.color = a.getAttribute('href') === '#' + current ? '#00ff9f' : '#555';
        }});
    }});
}}
</script>
</body>
</html>"""

# Re-export existing functions from note_generator for convenience
