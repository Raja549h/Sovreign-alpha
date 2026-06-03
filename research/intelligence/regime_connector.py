"""
Regime Connector — Macro context integrator
============================================
Connects macro regime data to company-specific analysis.
Reuses existing engine.regime module and FII flow intelligence.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

SECTOR_SENSITIVITY = {
    'NBFC': {
        'high_sensitivity': ['rates', 'credit_spreads', 'liquidity'],
        'medium_sensitivity': ['equity_markets', 'fii_flows'],
        'low_sensitivity': ['commodities', 'fx'],
    },
    'BANK': {
        'high_sensitivity': ['rates', 'credit_spreads', 'liquidity', 'regulation'],
        'medium_sensitivity': ['equity_markets', 'fii_flows'],
        'low_sensitivity': ['commodities'],
    },
    'TECHNOLOGY': {
        'high_sensitivity': ['dollar_index', 'us_rates', 'global_risk'],
        'medium_sensitivity': ['equity_markets', 'fii_flows'],
        'low_sensitivity': ['credit_spreads', 'commodities'],
    },
    'CONSUMER': {
        'high_sensitivity': ['inflation', 'credit_conditions', 'rural_stress'],
        'medium_sensitivity': ['rates', 'equity_markets'],
        'low_sensitivity': ['dollar_index', 'commodities'],
    },
    'ENERGY': {
        'high_sensitivity': ['commodities', 'dollar_index', 'geopolitical'],
        'medium_sensitivity': ['rates', 'global_growth'],
        'low_sensitivity': ['credit_spreads'],
    },
    'PHARMA': {
        'high_sensitivity': ['regulation', 'dollar_index', 'us_rates'],
        'medium_sensitivity': ['global_risk', 'fii_flows'],
        'low_sensitivity': ['commodities', 'credit_spreads'],
    },
    'INFRASTRUCTURE': {
        'high_sensitivity': ['rates', 'credit_spreads', 'government_spending'],
        'medium_sensitivity': ['commodities', 'inflation'],
        'low_sensitivity': ['dollar_index'],
    },
    'FMCG': {
        'high_sensitivity': ['inflation', 'rural_stress', 'commodities'],
        'medium_sensitivity': ['credit_conditions', 'equity_markets'],
        'low_sensitivity': ['rates', 'dollar_index'],
    },
}


def get_regime_context() -> Dict:
    """
    Get current macro regime context from existing engine.
    
    Returns:
        Regime context dict with macro indicators
    """
    context = {
        'vix': None,
        'india_vix': None,
        'treasury_10y': None,
        'fed_funds_rate': None,
        'credit_spread': None,
        'dollar_index': None,
        'fii_flow_5d': None,
        'regime': 'NEUTRAL',
        'india_regime': 'NEUTRAL',
        'summary': 'No regime data available'
    }
    
    try:
        from engine.regime import MarketRegimeEngine
        engine = MarketRegimeEngine()
        regime = engine.classify()
        
        context['regime'] = regime.regime
        context['summary'] = regime.summary
        context['confidence'] = regime.confidence
        
        indicators = regime.indicators or {}
        context['vix'] = indicators.get('vix')
        context['treasury_10y'] = indicators.get('treasury_10y')
        context['dollar_index'] = indicators.get('dxy')
        context['gold'] = indicators.get('gold')
        context['oil'] = indicators.get('oil_wti')
        
    except Exception as e:
        context['error'] = f'Regime engine unavailable: {e}'
    
    try:
        from research.macro.fii_flow import calculate_flow_aggregates, classify_flow_regime
        flow_agg = calculate_flow_aggregates(7)
        weekly_net = flow_agg.get('weekly_net_cr')
        if weekly_net is not None:
            context['fii_flow_5d'] = round(weekly_net, 2)
        monthly_net = flow_agg.get('monthly_net_cr')
        if monthly_net is not None:
            regime_info = classify_flow_regime(monthly_net)
            context['fii_regime'] = regime_info.get('regime', 'UNKNOWN')
            context['fii_regime_label'] = regime_info.get('label', 'Unknown')
            context['fii_regime_risk'] = regime_info.get('risk', 'MEDIUM')
    except Exception as e:
        context['fii_error'] = str(e)

    return context


def assess_regime_sensitivity(company_id: int, sector: str) -> Dict:
    """
    Assess company's sensitivity to current macro regime.
    
    Args:
        company_id: Company ID
        sector: Company sector
    
    Returns:
        Sensitivity assessment dict
    """
    regime = get_regime_context()
    sector_info = SECTOR_SENSITIVITY.get(sector.upper(), SECTOR_SENSITIVITY.get('NBFC'))
    
    result = {
        'sector': sector,
        'regime': regime.get('regime', 'NEUTRAL'),
        'regime_headwinds': [],
        'regime_tailwinds': [],
        'sensitivity_score': 5.0,
        'key_macro_risk': 'None identified',
        'regime_summary': regime.get('summary', 'No regime data'),
        'details': {}
    }
    
    current_regime = regime.get('regime', 'NEUTRAL')
    
    if current_regime == 'RISK_OFF':
        if 'rates' in sector_info['high_sensitivity']:
            result['regime_headwinds'].append('Rising rates pressure net interest margins')
        if 'credit_spreads' in sector_info['high_sensitivity']:
            result['regime_headwinds'].append('Widening credit spreads increase funding costs')
        if 'liquidity' in sector_info['high_sensitivity']:
            result['regime_headwinds'].append('Tightening liquidity constrains asset growth')
        
        result['key_macro_risk'] = 'Risk-off regime pressures funding and valuation multiples'
        result['sensitivity_score'] = 7.5
        
    elif current_regime == 'RISK_ON':
        if 'equity_markets' in sector_info.get('medium_sensitivity', []):
            result['regime_tailwinds'].append('Risk-on supports valuation multiples')
        if 'fii_flows' in sector_info.get('medium_sensitivity', []):
            result['regime_tailwinds'].append('FII inflows support liquidity')
        
        result['key_macro_risk'] = 'Risk-on regime may mask underlying fundamental deterioration'
        result['sensitivity_score'] = 4.0
        
    else:
        result['regime_summary'] = 'Neutral regime — company-specific factors dominate'
        result['sensitivity_score'] = 5.0
        result['key_macro_risk'] = 'Neutral regime — monitor for regime shift signals'
    
    vix = regime.get('vix')
    if vix:
        if vix > 25:
            result['regime_headwinds'].append(f'Elevated VIX ({vix:.1f}) signals market stress')
            result['sensitivity_score'] = min(result['sensitivity_score'] + 1.5, 10)
        elif vix < 15:
            result['regime_tailwinds'].append(f'Low VIX ({vix:.1f}) supports risk appetite')
            result['sensitivity_score'] = max(result['sensitivity_score'] - 1.0, 0)
    
    treasury = regime.get('treasury_10y')
    if treasury and 'rates' in sector_info['high_sensitivity']:
        if treasury > 4.5:
            result['regime_headwinds'].append(f'10Y yield at {treasury:.2f}% pressures valuations')
            result['sensitivity_score'] = min(result['sensitivity_score'] + 1.0, 10)
    
    result['sensitivity_score'] = round(result['sensitivity_score'], 1)
    
    return result


def calculate_regime_sensitivity_score(company_id: int, sector: str) -> float:
    """
    Calculate numerical regime sensitivity score (0-10).
    
    Args:
        company_id: Company ID
        sector: Company sector
    
    Returns:
        Float score 0-10, higher = more exposed
    """
    assessment = assess_regime_sensitivity(company_id, sector)
    return assessment['sensitivity_score']
