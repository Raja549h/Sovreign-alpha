"""
Import Sensitivity Overlay — Portfolio-level import dependency intelligence
============================================================================
Calculates import dependency scores by sector and assesses currency headwind
risk for portfolio positions. Provides concentration risk alerts when multiple
holdings share similar import-vulnerability profiles.

Design principle: institutional risk awareness for concentrated equity portfolios.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent.parent
BILLING_DIR = BASE_DIR / "billing"
RESEARCH_DB = BILLING_DIR / "research.db"

IMPORT_SENSITIVITY_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS import_sensitivity_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    ticker TEXT,
    sector TEXT,
    import_dependency_score REAL,
    raw_material_import_pct REAL,
    capex_import_pct REAL,
    currency_headwind_risk TEXT,
    observation TEXT,
    scored_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

SECTOR_IMPORT_PROFILES = {
    'ENERGY': {
        'raw_material_dependency': 'HIGH',
        'capex_dependency': 'MEDIUM',
        'import_dependency_score': 8.5,
        'key_imports': 'Crude oil, LNG, petrochemicals',
        'substitution_possibility': 'LOW',
        'currency_headwind_detail': 'Every 1% INR depreciation increases import bill significantly',
    },
    'OIL_GAS': {
        'raw_material_dependency': 'HIGH',
        'capex_dependency': 'MEDIUM',
        'import_dependency_score': 8.0,
        'key_imports': 'Crude oil, natural gas, specialty chemicals',
        'substitution_possibility': 'LOW',
        'currency_headwind_detail': 'Over 80% of crude requirement imported — direct passthrough',
    },
    'ELECTRONICS': {
        'raw_material_dependency': 'HIGH',
        'capex_dependency': 'HIGH',
        'import_dependency_score': 9.0,
        'key_imports': 'Semiconductors, PCBs, display panels, precision components',
        'substitution_possibility': 'LOW',
        'currency_headwind_detail': 'High import content with limited domestic alternatives',
    },
    'PHARMA': {
        'raw_material_dependency': 'MEDIUM',
        'capex_dependency': 'MEDIUM',
        'import_dependency_score': 5.5,
        'key_imports': 'API intermediates, specialty chemicals, lab equipment',
        'substitution_possibility': 'MEDIUM',
        'currency_headwind_detail': 'API imports from China create cost pressure on INR weakness',
    },
    'AUTO': {
        'raw_material_dependency': 'MEDIUM',
        'capex_dependency': 'MEDIUM',
        'import_dependency_score': 5.0,
        'key_imports': 'Electronics, specialty steel, precision components',
        'substitution_possibility': 'MEDIUM',
        'currency_headwind_detail': 'Import content varies by segment; luxury/EV segments higher',
    },
    'SPECIALTY_CHEMICAL': {
        'raw_material_dependency': 'HIGH',
        'capex_dependency': 'MEDIUM',
        'import_dependency_score': 7.5,
        'key_imports': 'Chemical intermediates, solvents, catalysts',
        'substitution_possibility': 'LOW',
        'currency_headwind_detail': 'High import dependency with thin margins amplifies FX risk',
    },
    'METALS': {
        'raw_material_dependency': 'HIGH',
        'capex_dependency': 'MEDIUM',
        'import_dependency_score': 7.0,
        'key_imports': 'Coking coal, scrap, specialized alloys',
        'substitution_possibility': 'LOW',
        'currency_headwind_detail': 'Coking coal is largest import cost — direct FX sensitivity',
    },
    'FMCG': {
        'raw_material_dependency': 'MEDIUM',
        'capex_dependency': 'LOW',
        'import_dependency_score': 4.0,
        'key_imports': 'Edible oils, palm oil, packaging materials',
        'substitution_possibility': 'MEDIUM',
        'currency_headwind_detail': 'Import content in raw materials; partial hedging typical',
    },
    'CONSUMER': {
        'raw_material_dependency': 'MEDIUM',
        'capex_dependency': 'LOW',
        'import_dependency_score': 4.0,
        'key_imports': 'Packaging materials, select food ingredients',
        'substitution_possibility': 'MEDIUM',
        'currency_headwind_detail': 'Limited import exposure, selective commodity imports',
    },
    'TEXTILES': {
        'raw_material_dependency': 'MEDIUM',
        'capex_dependency': 'MEDIUM',
        'import_dependency_score': 5.0,
        'key_imports': 'Specialty fibers, dyes, chemicals, machinery',
        'substitution_possibility': 'MEDIUM',
        'currency_headwind_detail': 'Cotton largely domestic; synthetic fibers have import content',
    },
    'TECHNOLOGY': {
        'raw_material_dependency': 'LOW',
        'capex_dependency': 'LOW',
        'import_dependency_score': 2.0,
        'key_imports': 'Minimal — services-based model',
        'substitution_possibility': 'HIGH',
        'currency_headwind_detail': 'Negligible import dependency; net beneficiary of INR weakness',
    },
    'IT': {
        'raw_material_dependency': 'LOW',
        'capex_dependency': 'LOW',
        'import_dependency_score': 1.5,
        'key_imports': 'Minimal — services-based model, some software licensing',
        'substitution_possibility': 'HIGH',
        'currency_headwind_detail': 'Negligible import dependency; net beneficiary of INR weakness',
    },
    'NBFC': {
        'raw_material_dependency': 'LOW',
        'capex_dependency': 'LOW',
        'import_dependency_score': 1.0,
        'key_imports': 'Negligible direct import exposure',
        'substitution_possibility': 'HIGH',
        'currency_headwind_detail': 'No material import cost exposure',
    },
    'BANK': {
        'raw_material_dependency': 'LOW',
        'capex_dependency': 'LOW',
        'import_dependency_score': 1.0,
        'key_imports': 'Negligible direct import exposure',
        'substitution_possibility': 'HIGH',
        'currency_headwind_detail': 'No material import cost exposure',
    },
    'INFRASTRUCTURE': {
        'raw_material_dependency': 'MEDIUM',
        'capex_dependency': 'HIGH',
        'import_dependency_score': 6.0,
        'key_imports': 'Construction equipment, specialized machinery, steel',
        'substitution_possibility': 'LOW',
        'currency_headwind_detail': 'Capex-heavy with imported equipment — depreciation raises project costs',
    },
    'MEDIA': {
        'raw_material_dependency': 'LOW',
        'capex_dependency': 'MEDIUM',
        'import_dependency_score': 3.0,
        'key_imports': 'Broadcast equipment, content licensing',
        'substitution_possibility': 'MEDIUM',
        'currency_headwind_detail': 'Limited direct import cost exposure',
    },
}

RISK_THRESHOLDS = [
    ('CRITICAL', 8.0, 'Severe import dependency creates material currency headwind risk'),
    ('HIGH', 6.0, 'High import dependency — INR depreciation directly impacts margins'),
    ('MEDIUM', 3.5, 'Moderate import dependency — monitor INR trends'),
    ('LOW', 0.0, 'Limited import dependency — minimal currency headwind risk'),
]


def init_import_tables():
    with sqlite3.connect(str(RESEARCH_DB)) as conn:
        conn.executescript(IMPORT_SENSITIVITY_TABLES_SQL)


def _get_db():
    conn = sqlite3.connect(str(RESEARCH_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_import_profile(sector: str) -> Dict:
    return SECTOR_IMPORT_PROFILES.get(sector.upper(), {
        'raw_material_dependency': 'LOW', 'capex_dependency': 'LOW',
        'import_dependency_score': 1.0, 'key_imports': 'Unknown',
        'substitution_possibility': 'MEDIUM',
        'currency_headwind_detail': 'No sector-specific import profile available',
    })


def assess_currency_headwind_risk(import_score: float) -> str:
    for risk, threshold, _ in RISK_THRESHOLDS:
        if import_score >= threshold:
            return risk
    return 'LOW'


def assess_import_sensitivity(company_id: int, company_name: str, ticker: str,
                               sector: str, weight_pct: float = None) -> Dict:
    profile = get_import_profile(sector)
    base_score = profile['import_dependency_score']

    risk = assess_currency_headwind_risk(base_score)

    weighted_score = round(base_score * (weight_pct / 100) if weight_pct else base_score, 2)

    observation = _import_observation(profile, base_score, risk)

    result = {
        'company_id': company_id,
        'company_name': company_name,
        'ticker': ticker,
        'sector': sector,
        'import_dependency_score': base_score,
        'weighted_score': weighted_score,
        'raw_material_dependency': profile['raw_material_dependency'],
        'capex_dependency': profile['capex_dependency'],
        'key_imports': profile['key_imports'],
        'substitution_possibility': profile['substitution_possibility'],
        'currency_headwind_risk': risk,
        'observation': observation,
        'detail': profile['currency_headwind_detail'],
    }

    # Persist to DB
    try:
        with _get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO import_sensitivity_scores
                (company_id, ticker, sector, import_dependency_score,
                 raw_material_import_pct, capex_import_pct,
                 currency_headwind_risk, observation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_id, ticker, sector, base_score,
                _pct_from_dependency(profile['raw_material_dependency']),
                _pct_from_dependency(profile['capex_dependency']),
                risk, observation,
            ))
            conn.commit()
    except Exception:
        pass

    return result


def _pct_from_dependency(dep: str) -> Optional[float]:
    mapping = {'HIGH': 70.0, 'MEDIUM': 40.0, 'LOW': 10.0}
    return mapping.get(dep)


def _import_observation(profile: Dict, score: float, risk: str) -> str:
    if score >= 8.0:
        return f'Critical import dependency — {profile.get("key_imports", "key inputs")} primarily imported. INR depreciation directly and materially impacts cost structure.'
    elif score >= 6.0:
        return f'High import dependency on {profile.get("key_imports", "imported inputs")}. Consider INR hedge effectiveness.'
    elif score >= 3.5:
        return f'Moderate import exposure via {profile.get("key_imports", "select imported inputs")}. Monitor INR trends.'
    return f'Minimal import dependency. Currency risk not material for cost structure.'


def build_import_sensitivity_overlay(positions: List[Dict]) -> Dict:
    init_import_tables()

    assessments = []
    high_risk_count = 0
    total_weighted = 0
    total_weight = 0
    sector_exposure = {}

    for pos in positions:
        assessment = assess_import_sensitivity(
            pos.get('company_id'), pos.get('company_name', ''),
            pos.get('ticker', ''), pos.get('sector', ''),
            pos.get('weight_pct')
        )
        assessments.append(assessment)

        if assessment['currency_headwind_risk'] in ('CRITICAL', 'HIGH'):
            high_risk_count += 1

        if pos.get('sector'):
            sector = pos['sector']
            sector_exposure.setdefault(sector, 0)
            sector_exposure[sector] += pos.get('weight_pct', 0) or 0

        if pos.get('weight_pct'):
            total_weighted += assessment['weighted_score']
            total_weight += pos['weight_pct']

    avg_sensitivity = round(total_weighted / (total_weight / 100) if total_weight > 0 else 0, 1)

    concentration_risk = _detect_import_concentration(assessments, sector_exposure)

    return {
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'assessments': assessments,
        'average_import_sensitivity': avg_sensitivity,
        'high_risk_positions': high_risk_count,
        'total_positions': len(positions),
        'sector_exposure': sector_exposure,
        'concentration_risk': concentration_risk,
        'observation': _overlay_observation(avg_sensitivity, high_risk_count, concentration_risk),
    }


def _detect_import_concentration(assessments: List[Dict], sector_exposure: Dict) -> Dict:
    high_risk_sectors = {}
    for sector, weight in sector_exposure.items():
        profile = get_import_profile(sector)
        if profile['import_dependency_score'] >= 6.0:
            high_risk_sectors[sector] = {
                'weight_pct': round(weight, 1),
                'import_score': profile['import_dependency_score'],
            }

    alert = None
    total_high_weight = sum(s['weight_pct'] for s in high_risk_sectors.values())
    if total_high_weight > 40:
        alert = f'CONCENTRATION WARNING: {total_high_weight:.0f}% of portfolio in high-import-dependency sectors'
    elif total_high_weight > 25:
        alert = f'CAUTION: {total_high_weight:.0f}% of portfolio in high-import-dependency sectors — monitor INR'

    return {
        'high_risk_sectors': high_risk_sectors,
        'total_high_import_weight_pct': round(total_high_weight, 1),
        'concentration_alert': alert,
    }


def _overlay_observation(avg: float, high_count: int, concentration: Dict) -> str:
    obs = []
    if avg >= 6:
        obs.append(f'Portfolio-wide import sensitivity: {avg:.1f}/10 — elevated.')
    elif avg >= 3.5:
        obs.append(f'Portfolio-wide import sensitivity: {avg:.1f}/10 — moderate.')
    else:
        obs.append(f'Portfolio-wide import sensitivity: {avg:.1f}/10 — low.')

    if concentration.get('concentration_alert'):
        obs.append(concentration['concentration_alert'])

    if high_count > 0:
        obs.append(f'{high_count} position(s) carry high/critical import dependency risk.')

    return ' '.join(obs)
