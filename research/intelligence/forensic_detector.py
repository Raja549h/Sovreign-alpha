"""
Forensic Detector — Structural anomaly detection
=================================================
Detects anomalies in financial data using rule-based quantitative checks
and Cerebras-powered qualitative narrative analysis.
"""

import os
import json
from typing import List, Dict

from research.storage.research_db import (
    get_metric_series, save_flag, get_flags
)

LLM_API_KEY = os.environ.get('LLM_API_KEY', '')

NARRATIVE_DRIFT_SYSTEM_PROMPT = """You are an institutional forensic analyst examining earnings call transcripts for a concentrated equity research firm. Your task is to identify narrative drift — cases where management language has shifted meaningfully from prior periods in ways that may signal underlying business changes before they appear in financial metrics.

Look specifically for:
1. Metrics that management emphasised heavily in prior periods but now discusses less or reframes
2. Language hedging on previously definitive guidance
3. New KPIs introduced that may substitute for weakening traditional metrics
4. Changes in tone around specific business segments
5. Reduction in specificity of forward guidance

Output as JSON array only. Each item:
{
  "observation": "one sentence, specific",
  "prior_language": "what was said before",
  "current_language": "what is said now",
  "significance": "why this matters institutionally",
  "severity": "low" or "medium" or "high"
}

Be forensic not dramatic. Only flag genuine shifts with specific textual evidence."""


def detect_margin_compression(company_id: int) -> List[Dict]:
    """
    Detect margin compression in NIM, ROA, ROE.
    
    Args:
        company_id: Company ID
    
    Returns:
        List of findings
    """
    findings = []
    
    try:
        nim_series = get_metric_series(company_id, 'NIM')
        roe_series = get_metric_series(company_id, 'ROE')
        roa_series = get_metric_series(company_id, 'ROA')
        
        if nim_series and len(nim_series) >= 2:
            vals = [s['value'] for s in nim_series if s['value'] is not None]
            if len(vals) >= 2:
                change_bps = (vals[-1] - vals[0]) * 100
                if change_bps < -50:
                    findings.append({
                        'type': 'margin_compression',
                        'metric': 'NIM',
                        'change_bps': change_bps,
                        'from_val': vals[0],
                        'to_val': vals[-1],
                        'severity': 'high' if change_bps < -100 else 'medium',
                        'description': f'NIM compressed {abs(change_bps):.0f} bps over {len(vals)} periods'
                    })
                    save_flag(company_id, 'margin_compression', findings[-1]['severity'],
                             findings[-1]['description'],
                             {'metric': 'NIM', 'change_bps': change_bps},
                             nim_series[-1]['period'] if nim_series else None)
        
        if roe_series and len(roe_series) >= 2:
            vals = [s['value'] for s in roe_series if s['value'] is not None]
            if len(vals) >= 2:
                change_bps = (vals[-1] - vals[0]) * 100
                if change_bps < -300:
                    findings.append({
                        'type': 'roe_decline',
                        'metric': 'ROE',
                        'change_bps': change_bps,
                        'from_val': vals[0],
                        'to_val': vals[-1],
                        'severity': 'high' if change_bps < -500 else 'medium',
                        'description': f'ROE declined {abs(change_bps):.0f} bps over {len(vals)} periods'
                    })
                    save_flag(company_id, 'roe_decline', findings[-1]['severity'],
                             findings[-1]['description'],
                             {'metric': 'ROE', 'change_bps': change_bps},
                             roe_series[-1]['period'] if roe_series else None)
        
        if roa_series and len(roa_series) >= 2:
            vals = [s['value'] for s in roa_series if s['value'] is not None]
            if len(vals) >= 2:
                change_bps = (vals[-1] - vals[0]) * 100
                if change_bps < -100:
                    findings.append({
                        'type': 'roa_decline',
                        'metric': 'ROA',
                        'change_bps': change_bps,
                        'from_val': vals[0],
                        'to_val': vals[-1],
                        'severity': 'medium',
                        'description': f'ROA declined {abs(change_bps):.0f} bps over {len(vals)} periods'
                    })
                    save_flag(company_id, 'roa_decline', 'medium',
                             findings[-1]['description'],
                             {'metric': 'ROA', 'change_bps': change_bps},
                             roa_series[-1]['period'] if roa_series else None)
                             
    except Exception as e:
        findings.append({'type': 'error', 'description': str(e)})
    
    return findings


def detect_credit_cost_acceleration(company_id: int) -> List[Dict]:
    """
    Detect credit cost acceleration and GNPA trends.
    
    Args:
        company_id: Company ID
    
    Returns:
        List of findings
    """
    findings = []
    
    try:
        cc_series = get_metric_series(company_id, 'CREDIT_COST')
        gnpa_series = get_metric_series(company_id, 'GNPA')
        nnpa_series = get_metric_series(company_id, 'NNPA')
        
        if cc_series and len(cc_series) >= 2:
            vals = [s['value'] for s in cc_series if s['value'] is not None]
            if len(vals) >= 2 and vals[0] > 0:
                yoy_change = (vals[-1] - vals[0]) / vals[0]
                if yoy_change > 0.30:
                    findings.append({
                        'type': 'credit_cost_acceleration',
                        'metric': 'CREDIT_COST',
                        'yoy_change_pct': yoy_change * 100,
                        'from_val': vals[0],
                        'to_val': vals[-1],
                        'severity': 'high' if yoy_change > 0.50 else 'medium',
                        'description': f'Credit cost accelerated {yoy_change*100:.0f}% YoY'
                    })
                    save_flag(company_id, 'credit_cost_acceleration', findings[-1]['severity'],
                             findings[-1]['description'],
                             {'yoy_change': yoy_change * 100},
                             cc_series[-1]['period'] if cc_series else None)
        
        if gnpa_series and len(gnpa_series) >= 2:
            vals = [s['value'] for s in gnpa_series if s['value'] is not None]
            consecutive_increases = 0
            for i in range(1, len(vals)):
                if vals[i] > vals[i-1]:
                    consecutive_increases += 1
                else:
                    consecutive_increases = 0
                
                if consecutive_increases >= 2:
                    findings.append({
                        'type': 'gnpa_consecutive_increase',
                        'metric': 'GNPA',
                        'consecutive_periods': consecutive_increases + 1,
                        'severity': 'high',
                        'description': f'GNPA increased for {consecutive_increases + 1} consecutive periods'
                    })
                    save_flag(company_id, 'gnpa_consecutive_increase', 'high',
                             findings[-1]['description'],
                             {'consecutive': consecutive_increases + 1},
                             gnpa_series[i]['period'])
                    break
                             
    except Exception as e:
        findings.append({'type': 'error', 'description': str(e)})
    
    return findings


def detect_working_capital_stress(company_id: int) -> List[Dict]:
    """
    Detect working capital and funding stress for NBFCs.
    
    Args:
        company_id: Company ID
    
    Returns:
        List of findings
    """
    findings = []
    
    try:
        aum_series = get_metric_series(company_id, 'AUM')
        
        if aum_series and len(aum_series) >= 2:
            vals = [s['value'] for s in aum_series if s['value'] is not None]
            if len(vals) >= 2 and vals[0] > 0:
                growth_rate = (vals[-1] - vals[0]) / vals[0]
                if growth_rate > 0.50:
                    findings.append({
                        'type': 'rapid_aum_growth',
                        'metric': 'AUM',
                        'growth_pct': growth_rate * 100,
                        'severity': 'medium',
                        'description': f'AUM grew {growth_rate*100:.0f}% — check funding concentration',
                        'check': 'Verify deposit growth matches AUM growth'
                    })
                    save_flag(company_id, 'working_capital_stress', 'medium',
                             findings[-1]['description'],
                             {'aum_growth': growth_rate * 100},
                             aum_series[-1]['period'] if aum_series else None)
                             
    except Exception as e:
        findings.append({'type': 'error', 'description': str(e)})
    
    return findings


def detect_valuation_fragility(company_id: int, current_pe: float = None, current_pbv: float = None) -> Dict:
    """
    Assess valuation fragility based on current multiples vs historical returns.
    
    Args:
        company_id: Company ID
        current_pe: Current P/E multiple
        current_pbv: Current P/BV multiple
    
    Returns:
        Fragility assessment dict
    """
    result = {
        'fragile': False,
        'observations': [],
        'implied_roe': None,
        'historical_roe': None,
        'severity': 'low'
    }
    
    try:
        roe_series = get_metric_series(company_id, 'ROE')
        if not roe_series:
            result['observations'].append('No ROE data available')
            return result
        
        roe_vals = [s['value'] for s in roe_series if s['value'] is not None]
        if not roe_vals:
            result['observations'].append('No ROE values available')
            return result
        
        avg_roe = sum(roe_vals) / len(roe_vals)
        max_roe = max(roe_vals)
        result['historical_roe'] = avg_roe
        
        if current_pbv and current_pbv > 0:
            implied_roe = (current_pbv - 1) / current_pbv * 100 if current_pbv > 1 else 0
            result['implied_roe'] = implied_roe
            
            if implied_roe > max_roe * 1.2:
                result['fragile'] = True
                result['severity'] = 'high'
                result['observations'].append(
                    f'Current P/BV {current_pbv}x implies ROE of {implied_roe:.1f}%, '
                    f'exceeding historical peak of {max_roe:.1f}%'
                )
                save_flag(company_id, 'valuation_fragility', 'high',
                         result['observations'][-1],
                         {'implied_roe': implied_roe, 'max_historical_roe': max_roe, 'pbv': current_pbv})
            elif implied_roe > avg_roe * 1.3:
                result['fragile'] = True
                result['severity'] = 'medium'
                result['observations'].append(
                    f'Current P/BV {current_pbv}x implies ROE above historical average'
                )
                save_flag(company_id, 'valuation_fragility', 'medium',
                         result['observations'][-1],
                         {'implied_roe': implied_roe, 'avg_historical_roe': avg_roe, 'pbv': current_pbv})
        
        if current_pe and current_pe > 0 and avg_roe > 0:
            peg = current_pe / (avg_roe * 10) if avg_roe > 0 else 999
            if peg > 2:
                result['observations'].append(f'P/E {current_pe}x vs ROE {avg_roe:.1f}% suggests premium valuation (PEG {peg:.1f})')
                
    except Exception as e:
        result['observations'].append(f'Analysis failed: {e}')
    
    return result


def detect_narrative_drift(company_id: int, transcript_texts: List[str]) -> List[Dict]:
    """
    Detect narrative drift using Cerebras API analysis.
    
    Args:
        company_id: Company ID
        transcript_texts: List of transcript texts from different periods
    
    Returns:
        List of narrative drift observations
    """
    findings = []
    
    if not LLM_API_KEY:
        findings.append({'type': 'info', 'description': 'LLM_API_KEY not set — skipping narrative drift analysis'})
        return findings
    
    if len(transcript_texts) < 2:
        findings.append({'type': 'info', 'description': 'Need 2+ transcripts for drift analysis'})
        return findings
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        
        user_message = f"""Compare these two earnings call transcripts for narrative drift:

TRANSCRIPT 1 (Earlier):
{transcript_texts[0][:3000]}

TRANSCRIPT 2 (Later):
{transcript_texts[1][:3000]}

Identify narrative shifts. Output JSON array only."""
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": NARRATIVE_DRIFT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        drift_items = json.loads(content) if content.startswith('[') else []
        
        for item in drift_items:
            if isinstance(item, dict):
                findings.append({
                    'type': 'narrative_drift',
                    'observation': item.get('observation', ''),
                    'prior_language': item.get('prior_language', ''),
                    'current_language': item.get('current_language', ''),
                    'significance': item.get('significance', ''),
                    'severity': item.get('severity', 'medium')
                })
                save_flag(company_id, 'narrative_drift', item.get('severity', 'medium'),
                         item.get('observation', ''),
                         item,
                         analyst_note=item.get('significance', ''))
        
    except Exception as e:
        findings.append({'type': 'error', 'description': f'Narrative drift analysis failed: {e}'})
    
    return findings


def run_all_detectors(company_id: int, transcripts: List[str] = None,
                      current_pe: float = None, current_pbv: float = None) -> Dict:
    """
    Master detector function — runs all quantitative and qualitative detectors.
    
    Args:
        company_id: Company ID
        transcripts: Optional list of transcript texts
        current_pe: Current P/E multiple
        current_pbv: Current P/BV multiple
    
    Returns:
        Complete detection report
    """
    report = {
        'company_id': company_id,
        'margin_compression': [],
        'credit_cost_acceleration': [],
        'working_capital_stress': [],
        'valuation_fragility': {},
        'narrative_drift': [],
        'total_flags': 0,
        'severity_summary': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
    }
    
    try:
        report['margin_compression'] = detect_margin_compression(company_id)
        report['credit_cost_acceleration'] = detect_credit_cost_acceleration(company_id)
        report['working_capital_stress'] = detect_working_capital_stress(company_id)
        report['valuation_fragility'] = detect_valuation_fragility(company_id, current_pe, current_pbv)
        
        if transcripts:
            report['narrative_drift'] = detect_narrative_drift(company_id, transcripts)
        
        flags = get_flags(company_id)
        report['total_flags'] = len(flags)
        for flag in flags:
            sev = flag.get('severity', 'low')
            if sev in report['severity_summary']:
                report['severity_summary'][sev] += 1
        
    except Exception as e:
        report['error'] = str(e)
    
    return report
