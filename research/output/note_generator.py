"""
Note Generator — Institutional research note composer
=====================================================
Generates forensic research notes using Groq API.
Produces HTML-formatted notes with cryptographic signing.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from research.storage.research_db import (
    get_company, get_company_by_id, get_financial_series, get_flags, get_latest_scores,
    get_all_metrics, save_note, get_notes, get_note_by_reference
)
from research.intelligence.scorer import format_scorecard
from research.intelligence.regime_connector import get_regime_context

BASE_DIR = Path(__file__).parent.parent.parent
NOTES_DIR = BASE_DIR / "research" / "data" / "notes"
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

NOTE_COUNTER_FILE = BASE_DIR / "research" / "data" / ".note_counter"

SYSTEM_PROMPT = """You are a senior institutional equity analyst at a concentrated hedge fund. You write forensic research observations for sophisticated institutional investors including AIF Category III funds and PMS firms.

Your writing style:
- Calm and forensic, never dramatic
- Evidence-backed, every claim has a number
- Institutional language throughout
- Second-order thinking — not what happened but what it means for valuation and expected return
- Never makes directional buy/sell recommendations
- Focuses on analytical observations that help sophisticated investors calibrate position sizing and expected return assumptions

Format requirement:
Produce a structured research note with these sections:
1. Executive Summary (3-4 sentences, the central observation)
2. Key Analytical Observations (3-5 numbered points, each with supporting data)
3. Supporting Evidence (specific numbers, trends, transcript references)
4. Institutional Assessment (what this means for a concentrated holder specifically)
5. Risk Matrix (table format: vector, direction, relevance)

Tone benchmark: This should read like Goldman Sachs equity research, not a startup pitch or retail blog."""


def _get_next_reference(ticker: str) -> str:
    """Generate next note reference number."""
    year = datetime.now().strftime('%Y')
    counter_file = NOTE_COUNTER_FILE
    
    counter = 0
    if counter_file.exists():
        try:
            with open(counter_file, 'r') as f:
                counters = json.load(f)
            counter = counters.get(ticker, 0)
        except (json.JSONDecodeError, KeyError):
            counter = 0
    
    counter += 1
    
    try:
        with open(counter_file, 'w') as f:
            counters = {}
            if counter_file.exists():
                with open(counter_file, 'r') as rf:
                    try:
                        counters = json.load(rf)
                    except json.JSONDecodeError:
                        pass
            counters[ticker] = counter
            json.dump(counters, f)
    except Exception:
        pass
    
    return f"SR-{year}-{ticker[:3].upper()}-{counter:03d}"


def _format_metrics_table(metrics: Dict) -> str:
    """Format financial metrics as markdown table."""
    lines = ["| Metric | Period | Value | Unit |", "|--------|--------|-------|------|"]
    
    for metric_name, values in sorted(metrics.items()):
        for v in values:
            period = v.get('period', '')
            value = v.get('value')
            unit = v.get('unit', '')
            if value is not None:
                lines.append(f"| {metric_name} | {period} | {value:.2f} | {unit} |")
    
    return '\n'.join(lines)


def _format_flags(flags: List[Dict]) -> str:
    """Format forensic flags as text."""
    if not flags:
        return "No forensic flags detected."
    
    lines = []
    for f in flags:
        severity = f.get('severity', 'low').upper()
        flag_type = f.get('flag_type', 'unknown')
        description = f.get('description', '')
        lines.append(f"- [{severity}] {flag_type}: {description}")
    
    return '\n'.join(lines)


def _sign_content(content: str) -> str:
    """Generate cryptographic hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def generate_research_note(company_id: int, analyst_context: str = '') -> Dict:
    """
    Generate institutional research note using Groq.
    
    Args:
        company_id: Company ID
        analyst_context: Optional analyst context string
    
    Returns:
        Dict with note reference, HTML content, and metadata
    """
    company = get_company_by_id(company_id)
    if not company:
        return {'error': f'Company ID {company_id} not found'}
    
    ticker = company['ticker']
    company_name = company['company_name']
    sector = company.get('sector', 'Unknown')
    
    metrics = get_all_metrics(company_id)
    flags = get_flags(company_id)
    scores = get_latest_scores(company_id)
    regime = get_regime_context()
    
    metrics_table = _format_metrics_table(metrics)
    flags_text = _format_flags(flags)
    scorecard = format_scorecard(scores) if scores else "Scores not available"
    regime_summary = regime.get('summary', 'No regime data')
    
    periods = sorted(set(m['period'] for m in get_financial_series(company_id)))
    
    user_message = f"""Company: {company_name} ({ticker})
Sector: {sector}
Analysis Period: {', '.join(periods) if periods else 'N/A'}

FINANCIAL TIME SERIES:
{metrics_table}

FORENSIC FLAGS DETECTED:
{flags_text}

INSTITUTIONAL SCORES:
{scorecard}

REGIME CONTEXT:
{regime_summary}

Analyst Context: {analyst_context or 'General institutional analysis'}

Generate a forensic institutional research note."""
    
    note_content = ""
    
    if GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=2500
            )
            
            note_content = response.choices[0].message.content
            
        except Exception as e:
            note_content = f"[Groq API Error: {e}]\n\nNote generation failed. Manual analysis required."
    else:
        note_content = _generate_fallback_note(company_name, ticker, sector, metrics, flags, scores, regime)
    
    reference = _get_next_reference(ticker)
    
    html_content = _format_html_note(
        reference, company_name, ticker, sector, note_content, scores, flags, regime
    )
    
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    note_filename = f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    note_path = NOTES_DIR / note_filename
    
    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    note_id = save_note(
        company_id, reference,
        f"Forensic Research Note — {company_name}",
        html_content,
        scores or {},
        summary=note_content[:200] if note_content else ''
    )
    
    return {
        'reference': reference,
        'note_id': note_id,
        'html_path': str(note_path),
        'content_hash': _sign_content(note_content),
        'generated_at': datetime.now().isoformat(),
        'status': 'generated'
    }


def _generate_fallback_note(company_name: str, ticker: str, sector: str,
                            metrics: Dict, flags: List, scores: Dict, regime: Dict) -> str:
    """Generate a basic note when Groq is unavailable."""
    lines = [
        f"# FORENSIC RESEARCH NOTE — {company_name} ({ticker})",
        f"Sector: {sector}",
        f"Date: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## Executive Summary",
        f"This note presents analytical observations on {company_name} based on available financial data.",
        "",
        "## Key Observations",
    ]
    
    for metric_name, values in list(metrics.items())[:5]:
        if values:
            latest = values[-1]
            lines.append(f"- {metric_name}: {latest.get('value', 'N/A')} {latest.get('unit', '')} ({latest.get('period', '')})")
    
    if flags:
        lines.extend(["", "## Forensic Flags", ""])
        for f in flags:
            lines.append(f"- [{f.get('severity', 'low').upper()}] {f.get('flag_type', '')}: {f.get('description', '')}")
    
    lines.extend(["", "## Institutional Assessment", "Based on available data, this company requires continued monitoring."])
    
    return '\n'.join(lines)


def _fmt(v):
    """Format score value safely."""
    if v is None:
        return 'N/A'
    try:
        return f"{float(v):.1f}"
    except (ValueError, TypeError):
        return str(v)

def _format_html_note(reference: str, company_name: str, ticker: str, sector: str,
                      content: str, scores: Dict, flags: List, regime: Dict) -> str:
    """Format note as HTML with institutional styling."""
    scorecard_html = ""
    if scores:
        scorecard_html = f"""
<div class="scorecard">
    <h3>Institutional Scorecard</h3>
    <table>
        <tr><td>Risk Intensity</td><td>{_fmt(scores.get('risk_intensity'))}/10</td></tr>
        <tr><td>Confidence</td><td>{_fmt(scores.get('confidence'))}/10</td></tr>
        <tr><td>Regime Sensitivity</td><td>{_fmt(scores.get('regime_sensitivity'))}/10</td></tr>
        <tr><td>Structural Quality</td><td>{_fmt(scores.get('structural_quality'))}/10</td></tr>
        <tr><td><strong>Composite</strong></td><td><strong>{_fmt(scores.get('composite'))}/10</strong></td></tr>
    </table>
</div>"""
    
    flags_html = ""
    if flags:
        flags_html = "<div class='flags'><h3>Forensic Flags</h3><ul>"
        for f in flags:
            flags_html += f"<li class='flag-{f.get('severity', 'low')}'>[{f.get('severity', 'low').upper()}] {f.get('flag_type', '')}: {f.get('description', '')}</li>"
        flags_html += "</ul></div>"
    
    content_html = content.replace('\n', '<br>').replace('## ', '<h3>').replace('# ', '<h2>')
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Sovereign Alpha Research — {reference}</title>
    <style>
        body {{ font-family: 'Courier New', monospace; background: #0a0a0f; color: #c8d0d8; max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        h1 {{ color: #4a9eff; border-bottom: 1px solid #2a3a4a; padding-bottom: 10px; }}
        h2 {{ color: #6ab0ff; margin-top: 30px; }}
        h3 {{ color: #8ac0ff; }}
        .meta {{ color: #6a7a8a; font-size: 0.9em; margin-bottom: 30px; }}
        .scorecard {{ background: #1a1a2e; border: 1px solid #2a3a4a; padding: 20px; margin: 20px 0; }}
        .scorecard table {{ width: 100%; border-collapse: collapse; }}
        .scorecard td {{ padding: 8px; border-bottom: 1px solid #2a3a4a; }}
        .flags {{ background: #1a1a2e; border: 1px solid #2a3a4a; padding: 20px; margin: 20px 0; }}
        .flag-high {{ color: #ff6b6b; }}
        .flag-medium {{ color: #ffd93d; }}
        .flag-low {{ color: #6bff6b; }}
        .content {{ line-height: 1.8; }}
        .hash {{ color: #4a9eff; font-size: 0.8em; }}
    </style>
</head>
<body>
    <h1>Sovereign Alpha Research</h1>
    <div class="meta">
        Reference: {reference} | {company_name} ({ticker}) | Sector: {sector} | {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
    </div>
    {scorecard_html}
    {flags_html}
    <div class="content">{content_html}</div>
    <div class="hash">Content Hash: {_sign_content(content)}</div>
</body>
</html>"""


def get_note_html(reference: str) -> Optional[str]:
    """Get note HTML content by reference."""
    note = get_note_by_reference(reference)
    if note:
        return note.get('full_content')
    return None
