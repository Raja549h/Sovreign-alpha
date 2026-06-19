"""
Institutional Scorer — Four-dimensional scoring system
======================================================
Generates risk intensity, confidence, regime sensitivity, and structural quality scores.
All scores 0-10. Higher is worse for risk scores, better for quality scores.
"""

from typing import Dict

from research.storage.research_db import (
    get_flags, get_financial_series, get_metric_series, get_filings_count,
    save_scores
)
from research.intelligence.regime_connector import calculate_regime_sensitivity_score

SEVERITY_WEIGHTS = {'low': 1, 'medium': 2, 'high': 3, 'critical': 5}


def calculate_risk_intensity(company_id: int) -> Dict:
    """
    Calculate risk intensity score (0-10, higher = more risk).
    
    Args:
        company_id: Company ID
    
    Returns:
        Dict with score and rationale
    """
    flags = get_flags(company_id)
    flag_count_weighted = sum(SEVERITY_WEIGHTS.get(f.get('severity', 'low'), 1) for f in flags)
    
    base = (flag_count_weighted / 20) * 10
    
    nim_series = get_metric_series(company_id, 'NIM')
    compression_adj = 0
    if nim_series and len(nim_series) >= 2:
        vals = [s['value'] for s in nim_series if s['value'] is not None]
        if len(vals) >= 2:
            nim_compression_bps = abs((vals[-1] - vals[0]) * 100)
            compression_adj = min(nim_compression_bps / 100, 2)
    
    cc_series = get_metric_series(company_id, 'CREDIT_COST')
    credit_adj = 0
    if cc_series and len(cc_series) >= 2:
        vals = [s['value'] for s in cc_series if s['value'] is not None]
        if len(vals) >= 2 and vals[0] > 0:
            credit_cost_change = (vals[-1] - vals[0]) / vals[0]
            credit_adj = min(abs(credit_cost_change) / 0.5, 2)
    
    risk_intensity = min(base + compression_adj + credit_adj, 10)
    
    return {
        'score': round(risk_intensity, 1),
        'rationale': {
            'flag_component': round(base, 1),
            'compression_component': round(compression_adj, 1),
            'credit_component': round(credit_adj, 1),
            'flag_count': len(flags),
            'flag_weighted': flag_count_weighted
        },
        'label': _risk_label(risk_intensity)
    }


def calculate_confidence(company_id: int) -> Dict:
    """
    Calculate confidence score (0-10, higher = more certain).
    
    Args:
        company_id: Company ID
    
    Returns:
        Dict with score and rationale
    """
    metrics = get_financial_series(company_id)
    periods_available = len(set(m['period'] for m in metrics))
    filings_count = get_filings_count(company_id)
    
    has_transcripts = False
    try:
        has_transcripts = True
    except ImportError:
        pass
    
    cross_verified = len(metrics) > 5
    
    confidence = (
        min(periods_available / 8, 1) * 4 +
        min(filings_count / 4, 1) * 3 +
        (1 if has_transcripts else 0) * 2 +
        (1 if cross_verified else 0) * 1
    )
    
    return {
        'score': round(min(confidence, 10), 1),
        'rationale': {
            'periods_component': round(min(periods_available / 8, 1) * 4, 1),
            'filings_component': round(min(filings_count / 4, 1) * 3, 1),
            'transcript_component': 2 if has_transcripts else 0,
            'cross_verify_component': 1 if cross_verified else 0,
            'periods_available': periods_available,
            'filings_count': filings_count
        },
        'label': _confidence_label(confidence)
    }


def calculate_regime_sensitivity(company_id: int, sector: str) -> Dict:
    """
    Calculate regime sensitivity score (0-10, higher = more exposed).
    
    Args:
        company_id: Company ID
        sector: Company sector
    
    Returns:
        Dict with score and rationale
    """
    score = calculate_regime_sensitivity_score(company_id, sector)
    
    return {
        'score': round(score, 1),
        'rationale': {
            'sector': sector,
            'description': f'{sector} sector sensitivity to current macro regime'
        },
        'label': _sensitivity_label(score)
    }


def calculate_structural_quality(company_id: int) -> Dict:
    """
    Calculate structural quality score (0-10, higher = better quality).
    
    Args:
        company_id: Company ID
    
    Returns:
        Dict with score and rationale
    """
    roe_series = get_metric_series(company_id, 'ROE')
    roa_series = get_metric_series(company_id, 'ROA')
    opex_series = get_metric_series(company_id, 'OPEX_NTI')
    gnpa_series = get_metric_series(company_id, 'GNPA')
    
    avg_roe = 0
    roe_improving = False
    if roe_series:
        vals = [s['value'] for s in roe_series if s['value'] is not None]
        if vals:
            avg_roe = sum(vals) / len(vals)
            if len(vals) >= 2:
                roe_improving = vals[-1] > vals[0]
    
    opex_improving = False
    if opex_series:
        vals = [s['value'] for s in opex_series if s['value'] is not None]
        if len(vals) >= 2:
            opex_improving = vals[-1] < vals[0]
    
    npa_declining = False
    if gnpa_series:
        vals = [s['value'] for s in gnpa_series if s['value'] is not None]
        if len(vals) >= 2:
            npa_declining = vals[-1] < vals[0]
    
    quality = (
        min(avg_roe / 25, 1) * 3 +
        (1 if roe_improving else 0) * 2 +
        (1 if opex_improving else 0) * 2 +
        (1 if npa_declining else 0) * 2 +
        0
    )
    
    return {
        'score': round(min(quality, 10), 1),
        'rationale': {
            'roe_component': round(min(avg_roe / 25, 1) * 3, 1),
            'roe_trend_component': 2 if roe_improving else 0,
            'opex_component': 2 if opex_improving else 0,
            'npa_component': 2 if npa_declining else 0,
            'avg_roe': round(avg_roe, 1),
            'roe_improving': roe_improving,
            'opex_improving': opex_improving,
            'npa_declining': npa_declining
        },
        'label': _quality_label(quality)
    }


def calculate_composite(risk: float, confidence: float, regime_sens: float, quality: float) -> float:
    """
    Calculate composite score.
    
    Args:
        risk: Risk intensity (0-10, higher = worse)
        confidence: Confidence (0-10, higher = better)
        regime_sens: Regime sensitivity (0-10, higher = worse)
        quality: Structural quality (0-10, higher = better)
    
    Returns:
        Composite score (0-10, higher = better)
    """
    composite = (
        (10 - risk) * 0.35 +
        confidence * 0.15 +
        (10 - regime_sens) * 0.20 +
        quality * 0.30
    )
    return round(min(max(composite, 0), 10), 1)


def score_company(company_id: int, sector: str = 'NBFC') -> Dict:
    """
    Run all four scores and save to database.
    
    Args:
        company_id: Company ID
        sector: Company sector
    
    Returns:
        Complete scoring dict
    """
    risk = calculate_risk_intensity(company_id)
    confidence = calculate_confidence(company_id)
    regime = calculate_regime_sensitivity(company_id, sector)
    quality = calculate_structural_quality(company_id)
    
    composite = calculate_composite(
        risk['score'], confidence['score'], regime['score'], quality['score']
    )
    
    scores = {
        'risk_intensity': risk['score'],
        'confidence': confidence['score'],
        'regime_sensitivity': regime['score'],
        'structural_quality': quality['score'],
        'composite': composite,
        'composite_score': composite,
        'forensic_flags_count': len(get_flags(company_id))
    }
    
    rationale = {
        'risk': risk['rationale'],
        'confidence': confidence['rationale'],
        'regime': regime['rationale'],
        'quality': quality['rationale']
    }
    
    save_scores(company_id, 'current', scores, rationale)
    
    return {
        **scores,
        'labels': {
            'risk': risk['label'],
            'confidence': confidence['label'],
            'regime': regime['label'],
            'quality': quality['label'],
            'composite': _composite_label(composite)
        },
        'rationale': rationale
    }


def format_scorecard(scores: Dict) -> str:
    """
    Format scorecard for research note inclusion.
    
    Args:
        scores: Scoring dict from score_company or database
    
    Returns:
        Formatted scorecard string
    """
    labels = scores.get('labels', {})
    risk_label = labels.get('risk', _risk_label(scores.get('risk_intensity', 0)))
    conf_label = labels.get('confidence', _confidence_label(scores.get('confidence', 0)))
    regime_label = labels.get('regime', _sensitivity_label(scores.get('regime_sensitivity', 0)))
    quality_label = labels.get('quality', _quality_label(scores.get('structural_quality', 0)))
    composite_val = scores.get('composite_score') or scores.get('composite', 0)
    comp_label = labels.get('composite', _composite_label(composite_val))
    
    return f"""INSTITUTIONAL SCORECARD
━━━━━━━━━━━━━━━━━━━━━━
Risk Intensity:       {scores.get('risk_intensity', 0):.1f} / 10  [{risk_label}]
Confidence:           {scores.get('confidence', 0):.1f} / 10  [{conf_label}]
Regime Sensitivity:   {scores.get('regime_sensitivity', 0):.1f} / 10  [{regime_label}]
Structural Quality:   {scores.get('structural_quality', 0):.1f} / 10  [{quality_label}]
━━━━━━━━━━━━━━━━━━━━━━
Composite:            {composite_val:.1f} / 10  [{comp_label}]"""


def _risk_label(score: float) -> str:
    if score >= 8:
        return 'CRITICAL'
    elif score >= 6:
        return 'ELEVATED'
    elif score >= 4:
        return 'MODERATE'
    elif score >= 2:
        return 'LOW'
    return 'MINIMAL'


def _confidence_label(score: float) -> str:
    if score >= 8:
        return 'HIGH'
    elif score >= 6:
        return 'MODERATE'
    elif score >= 4:
        return 'LIMITED'
    return 'LOW'


def _sensitivity_label(score: float) -> str:
    if score >= 8:
        return 'HIGHLY EXPOSED'
    elif score >= 6:
        return 'ELEVATED'
    elif score >= 4:
        return 'MODERATE'
    return 'LOW'


def _quality_label(score: float) -> str:
    if score >= 8:
        return 'STRONG'
    elif score >= 6:
        return 'MODERATE'
    elif score >= 4:
        return 'WEAK'
    return 'POOR'


def _composite_label(score: float) -> str:
    if score >= 8:
        return 'STRONG'
    elif score >= 6:
        return 'WATCH'
    elif score >= 4:
        return 'CAUTION'
    return 'ELEVATED RISK'
