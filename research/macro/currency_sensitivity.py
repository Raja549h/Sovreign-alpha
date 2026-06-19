"""
Currency Sensitivity Mapping — Portfolio-level INR/USD exposure intelligence
============================================================================
Maps currency exposure across portfolio positions using sector metadata and
annual report disclosures. Calculates sensitivity scores and identifies
concentrated currency risk.

Design principle: institutional risk awareness, NOT forecasting.
"""

from typing import Dict, List
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent

SECTOR_CURRENCY_MAP = {
    'TECHNOLOGY': {
        'revenue_exposure': 'HIGH',
        'cost_exposure': 'LOW',
        'debt_exposure': 'LOW',
        'direction': 'INR_WEAK_BEARISH',
        'rationale': 'Majority revenue in USD, costs in INR — weak INR boosts margins',
        'sensitivity_per_1pct': 0.45,
    },
    'IT': {
        'revenue_exposure': 'HIGH',
        'cost_exposure': 'LOW',
        'debt_exposure': 'LOW',
        'direction': 'INR_WEAK_BEARISH',
        'rationale': 'Majority revenue in USD, costs in INR — weak INR boosts margins',
        'sensitivity_per_1pct': 0.50,
    },
    'PHARMA': {
        'revenue_exposure': 'HIGH',
        'cost_exposure': 'MEDIUM',
        'debt_exposure': 'LOW',
        'direction': 'INR_WEAK_BEARISH',
        'rationale': 'Significant export revenue (US/EU), some USD-denominated input costs',
        'sensitivity_per_1pct': 0.35,
    },
    'ENERGY': {
        'revenue_exposure': 'MEDIUM',
        'cost_exposure': 'HIGH',
        'debt_exposure': 'MEDIUM',
        'direction': 'INR_STRONG_BULLISH',
        'rationale': 'Crude oil imports in USD, some export earnings — net importer',
        'sensitivity_per_1pct': -0.30,
    },
    'OIL_GAS': {
        'revenue_exposure': 'MEDIUM',
        'cost_exposure': 'HIGH',
        'debt_exposure': 'MEDIUM',
        'direction': 'INR_STRONG_BULLISH',
        'rationale': 'Crude oil imports in USD, some export earnings — net importer',
        'sensitivity_per_1pct': -0.35,
    },
    'AUTO': {
        'revenue_exposure': 'MEDIUM',
        'cost_exposure': 'MEDIUM',
        'debt_exposure': 'LOW',
        'direction': 'NEUTRAL',
        'rationale': 'Mix of export earnings and import components — partially hedged',
        'sensitivity_per_1pct': 0.10,
    },
    'CONSUMER': {
        'revenue_exposure': 'LOW',
        'cost_exposure': 'MEDIUM',
        'debt_exposure': 'LOW',
        'direction': 'INR_STRONG_BULLISH',
        'rationale': 'Import content in raw materials/packaging, domestic revenue',
        'sensitivity_per_1pct': -0.15,
    },
    'FMCG': {
        'revenue_exposure': 'LOW',
        'cost_exposure': 'MEDIUM',
        'debt_exposure': 'LOW',
        'direction': 'INR_STRONG_BULLISH',
        'rationale': 'Import content in raw materials (edible oils, palm, etc.)',
        'sensitivity_per_1pct': -0.12,
    },
    'NBFC': {
        'revenue_exposure': 'LOW',
        'cost_exposure': 'LOW',
        'debt_exposure': 'MEDIUM',
        'direction': 'INR_WEAK_BEARISH',
        'rationale': 'Some external commercial borrowing exposure, domestic operations',
        'sensitivity_per_1pct': 0.05,
    },
    'BANK': {
        'revenue_exposure': 'LOW',
        'cost_exposure': 'LOW',
        'debt_exposure': 'MEDIUM',
        'direction': 'INR_WEAK_BEARISH',
        'rationale': 'Limited direct FX exposure, some ECB and trade finance',
        'sensitivity_per_1pct': 0.05,
    },
    'INFRASTRUCTURE': {
        'revenue_exposure': 'LOW',
        'cost_exposure': 'MEDIUM',
        'debt_exposure': 'HIGH',
        'direction': 'INR_STRONG_BULLISH',
        'rationale': 'Imported equipment/machinery, possible foreign-currency debt',
        'sensitivity_per_1pct': -0.20,
    },
    'METALS': {
        'revenue_exposure': 'MEDIUM',
        'cost_exposure': 'MEDIUM',
        'debt_exposure': 'MEDIUM',
        'direction': 'INR_WEAK_BEARISH',
        'rationale': 'Export earnings in USD, coking coal imports, foreign debt',
        'sensitivity_per_1pct': 0.20,
    },
    'TEXTILES': {
        'revenue_exposure': 'HIGH',
        'cost_exposure': 'MEDIUM',
        'debt_exposure': 'LOW',
        'direction': 'INR_WEAK_BEARISH',
        'rationale': 'Export-oriented, cotton/raw material costs partially import-linked',
        'sensitivity_per_1pct': 0.30,
    },
}

EXPOSURE_WEIGHTS = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}


def get_currency_profile(sector: str) -> Dict:
    default = {
        'revenue_exposure': 'LOW', 'cost_exposure': 'LOW', 'debt_exposure': 'LOW',
        'direction': 'NEUTRAL', 'rationale': 'Sector not in defined currency map',
        'sensitivity_per_1pct': 0.0,
    }
    return SECTOR_CURRENCY_MAP.get(sector.upper(), default)


def calculate_currency_sensitivity_score(sector: str) -> float:
    profile = get_currency_profile(sector)
    raw = sum(EXPOSURE_WEIGHTS.get(profile.get(k, 'LOW'), 1)
              for k in ['revenue_exposure', 'cost_exposure', 'debt_exposure'])
    base_score = (raw / 9.0) * 10.0
    direction_adjustment = 0
    if profile['direction'] == 'INR_WEAK_BEARISH':
        direction_adjustment = 1
    elif profile['direction'] == 'INR_STRONG_BULLISH':
        direction_adjustment = -1
    score = min(max(base_score + direction_adjustment, 0), 10)
    return round(score, 1)


def assess_currency_exposure(company_id: int, company_name: str, ticker: str,
                              sector: str, weight_pct: float = None) -> Dict:
    profile = get_currency_profile(sector)
    sensitivity = calculate_currency_sensitivity_score(sector)

    risk_level = 'LOW'
    if sensitivity >= 7.0:
        risk_level = 'HIGH'
    elif sensitivity >= 4.0:
        risk_level = 'MEDIUM'

    weighted_sensitivity = round(sensitivity * (weight_pct / 100) if weight_pct else sensitivity, 2)

    return {
        'company_id': company_id,
        'company_name': company_name,
        'ticker': ticker,
        'sector': sector,
        'revenue_exposure': profile['revenue_exposure'],
        'cost_exposure': profile['cost_exposure'],
        'debt_exposure': profile['debt_exposure'],
        'direction': profile['direction'],
        'rationale': profile['rationale'],
        'sensitivity_per_1pct_inr': profile['sensitivity_per_1pct'],
        'sensitivity_score': sensitivity,
        'weighted_sensitivity': weighted_sensitivity,
        'risk_level': risk_level,
        'observation': _exposure_observation(profile, sensitivity, risk_level),
    }


def _exposure_observation(profile: Dict, sensitivity: float, risk_level: str) -> str:
    if risk_level == 'HIGH':
        return f'Significant currency exposure via {profile.get("revenue_exposure", "LOW").lower()} revenue and {profile.get("cost_exposure", "LOW").lower()} cost channels. INR move of 1% may impact ~{profile.get("sensitivity_per_1pct", 0):.1f}% on earnings.'
    elif risk_level == 'MEDIUM':
        return f'Moderate currency sensitivity. Monitor INR trends for portfolio impact.'
    return 'Limited direct currency exposure. Company-level factors dominate.'


def build_portfolio_currency_view(positions: List[Dict]) -> Dict:
    exposures = []
    total_weighted = 0
    total_weight = 0
    direction_counts = {'INR_WEAK_BEARISH': 0, 'INR_STRONG_BULLISH': 0, 'NEUTRAL': 0}
    risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

    for pos in positions:
        exp = assess_currency_exposure(
            pos.get('company_id'), pos.get('company_name', ''),
            pos.get('ticker', ''), pos.get('sector', ''),
            pos.get('weight_pct')
        )
        exposures.append(exp)
        if pos.get('weight_pct'):
            total_weighted += exp['weighted_sensitivity']
            total_weight += pos['weight_pct']
        direction_counts[exp['direction']] = direction_counts.get(exp['direction'], 0) + 1
        risk_counts[exp['risk_level']] = risk_counts.get(exp['risk_level'], 0) + 1

    portfolio_sensitivity = round(total_weighted / (total_weight / 100) if total_weight > 0 else 0, 2)

    return {
        'timestamp': __import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'exposures': exposures,
        'portfolio_sensitivity_score': portfolio_sensitivity,
        'direction_summary': direction_counts,
        'risk_summary': risk_counts,
        'high_exposure_count': len([e for e in exposures if e['risk_level'] == 'HIGH']),
        'observation': _portfolio_currency_observation(portfolio_sensitivity, risk_counts, direction_counts),
    }


def _portfolio_currency_observation(sensitivity: float, risk_counts: Dict, direction: Dict) -> str:
    high_count = risk_counts.get('HIGH', 0)
    weak_inr_count = direction.get('INR_WEAK_BEARISH', 0)
    strong_inr_count = direction.get('INR_STRONG_BULLISH', 0)
    net_direction = weak_inr_count - strong_inr_count

    obs = []
    if sensitivity > 5:
        obs.append(f'Portfolio currency sensitivity score of {sensitivity:.1f} indicates material INR exposure.')
    if high_count > 0:
        obs.append(f'{high_count} position(s) with high currency sensitivity require monitoring.')
    if net_direction > 0:
        obs.append(f'Net portfolio bias: benefits from INR weakness ({weak_inr_count} vs {strong_inr_count} positions).')
    elif net_direction < 0:
        obs.append(f'Net portfolio bias: benefits from INR strength ({strong_inr_count} vs {weak_inr_count} positions).')
    if not obs:
        obs.append('Portfolio currency exposure is well-diversified with no dominant directional bias.')

    return ' '.join(obs)
