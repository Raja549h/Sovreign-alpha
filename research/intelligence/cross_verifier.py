"""
Cross Verification Engine — Forensic core
==========================================
Compares management statements against financial data.
Detects divergences between guidance and actuals.
"""

from typing import List, Dict, Optional

from research.storage.research_db import (
    get_financial_series, get_metric_series, save_flag, get_flags,
    get_company, get_connection
)

DIVERGENCE_THRESHOLDS = {
    'NIM': 0.30,
    'ROA': 0.20,
    'CREDIT_COST': 0.25,
    'AUM_GROWTH': 5.0,
    'ROE': 0.30,
    'COF': 0.30,
    'GNPA': 0.25,
}


def verify_guidance_vs_actuals(company_id: int) -> List[Dict]:
    """
    Compare guidance claims against actual financial outcomes.
    
    Args:
        company_id: Company ID
    
    Returns:
        List of divergence observations
    """
    divergences = []
    
    try:
        for metric, threshold in DIVERGENCE_THRESHOLDS.items():
            series = get_metric_series(company_id, metric)
            if len(series) < 2:
                continue
            
            values = [(s['period'], s['value']) for s in series if s['value'] is not None]
            if len(values) < 2:
                continue
            
            for i in range(1, len(values)):
                prev_period, prev_val = values[i-1]
                curr_period, curr_val = values[i]
                
                if prev_val == 0:
                    continue
                
                change_pct = abs(curr_val - prev_val) / abs(prev_val)
                
                if change_pct > threshold:
                    divergence = {
                        'metric': metric,
                        'guided_period': prev_period,
                        'actual_period': curr_period,
                        'guided_value': prev_val,
                        'actual_value': curr_val,
                        'divergence_pct': change_pct * 100,
                        'threshold_pct': threshold * 100,
                        'severity': 'high' if change_pct > threshold * 2 else 'medium'
                    }
                    divergences.append(divergence)
                    
                    save_flag(
                        company_id,
                        'guidance_divergence',
                        divergence['severity'],
                        f"{metric} diverged {change_pct*100:.1f}% from prior period",
                        {'metric': metric, 'change_pct': change_pct * 100, 'threshold': threshold * 100},
                        curr_period
                    )
                    
    except Exception as e:
        print(f"  [ERROR] Guidance verification failed: {e}")
    
    return divergences


def verify_trend_consistency(company_id: int, metric_name: str) -> Dict:
    """
    Detect directional inconsistencies in metric trends.
    
    Args:
        company_id: Company ID
        metric_name: Metric to analyze
    
    Returns:
        Observation dict with supporting data
    """
    result = {
        'metric': metric_name,
        'consistent': True,
        'observations': [],
        'severity': 'low'
    }
    
    try:
        series = get_metric_series(company_id, metric_name)
        values = [(s['period'], s['value']) for s in series if s['value'] is not None]
        
        if len(values) < 3:
            result['observations'].append('Insufficient data for trend analysis')
            return result
        
        directions = []
        for i in range(1, len(values)):
            prev_val = values[i-1][1]
            curr_val = values[i][1]
            if curr_val > prev_val:
                directions.append('up')
            elif curr_val < prev_val:
                directions.append('down')
            else:
                directions.append('flat')
        
        consecutive = 1
        for i in range(1, len(directions)):
            if directions[i] == directions[i-1]:
                consecutive += 1
                if consecutive >= 3:
                    result['consistent'] = False
                    result['observations'].append(
                        f"{metric_name} moved {directions[i]} for {consecutive}+ consecutive periods"
                    )
                    result['severity'] = 'medium' if consecutive == 3 else 'high'
            else:
                consecutive = 1
        
        if not result['observations']:
            result['observations'].append('Trend is consistent')
            
    except Exception as e:
        result['observations'].append(f'Analysis failed: {e}')
    
    return result


def cross_verify_balance_sheet(company_id: int) -> List[Dict]:
    """
    Check balance sheet relationships for consistency.
    
    Args:
        company_id: Company ID
    
    Returns:
        List of consistency observations
    """
    observations = []
    
    try:
        nii_series = get_metric_series(company_id, 'NII')
        aum_series = get_metric_series(company_id, 'AUM')
        cof_series = get_metric_series(company_id, 'COF')
        gnpa_series = get_metric_series(company_id, 'GNPA')
        opex_series = get_metric_series(company_id, 'OPEX_NTI')
        
        if nii_series and aum_series and len(nii_series) > 1 and len(aum_series) > 1:
            nii_vals = [s['value'] for s in nii_series if s['value'] is not None]
            aum_vals = [s['value'] for s in aum_series if s['value'] is not None]
            
            if len(nii_vals) >= 2 and len(aum_vals) >= 2:
                nii_growth = (nii_vals[-1] - nii_vals[0]) / nii_vals[0] if nii_vals[0] else 0
                aum_growth = (aum_vals[-1] - aum_vals[0]) / aum_vals[0] if aum_vals[0] else 0
                
                if nii_growth > aum_growth * 1.5:
                    observations.append({
                        'type': 'spread_expansion',
                        'observation': 'NII growing faster than AUM suggests spread expansion',
                        'nii_growth': nii_growth * 100,
                        'aum_growth': aum_growth * 100,
                        'check': 'Verify COF trajectory confirms this',
                        'severity': 'medium'
                    })
        
        if gnpa_series and len(gnpa_series) > 1:
            gnpa_vals = [s['value'] for s in gnpa_series if s['value'] is not None]
            if len(gnpa_vals) >= 2:
                if gnpa_vals[-1] < gnpa_vals[0]:
                    observations.append({
                        'type': 'gnpa_improvement',
                        'observation': 'GNPA improving — check provisioning coverage trend',
                        'gnpa_change': (gnpa_vals[-1] - gnpa_vals[0]) / gnpa_vals[0] * 100 if gnpa_vals[0] else 0,
                        'check': 'Declining coverage with improving GNPA is a flag',
                        'severity': 'low'
                    })
        
        if opex_series and len(opex_series) > 1:
            opex_vals = [s['value'] for s in opex_series if s['value'] is not None]
            if len(opex_vals) >= 2:
                if opex_vals[-1] < opex_vals[0]:
                    observations.append({
                        'type': 'opex_efficiency',
                        'observation': 'Opex ratio improving — verify headcount data consistency',
                        'opex_change': (opex_vals[-1] - opex_vals[0]) / opex_vals[0] * 100 if opex_vals[0] else 0,
                        'severity': 'low'
                    })
                    
    except Exception as e:
        observations.append({'type': 'error', 'observation': f'Analysis failed: {e}'})
    
    return observations


def run_full_verification(company_id: int) -> Dict:
    """
    Master verification function — runs all checks.
    
    Args:
        company_id: Company ID
    
    Returns:
        Complete verification report
    """
    report = {
        'company_id': company_id,
        'guidance_divergences': [],
        'trend_inconsistencies': [],
        'balance_sheet_checks': [],
        'total_flags': 0,
        'severity_breakdown': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
    }
    
    try:
        report['guidance_divergences'] = verify_guidance_vs_actuals(company_id)
        
        for metric in ['NIM', 'ROA', 'ROE', 'CREDIT_COST', 'GNPA']:
            trend = verify_trend_consistency(company_id, metric)
            if not trend['consistent']:
                report['trend_inconsistencies'].append(trend)
        
        report['balance_sheet_checks'] = cross_verify_balance_sheet(company_id)
        
        flags = get_flags(company_id)
        report['total_flags'] = len(flags)
        for flag in flags:
            sev = flag.get('severity', 'low')
            if sev in report['severity_breakdown']:
                report['severity_breakdown'][sev] += 1
        
    except Exception as e:
        report['error'] = str(e)
    
    return report
