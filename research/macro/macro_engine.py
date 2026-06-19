from database import get_connection
"""
Macro & Currency Intelligence Engine — Orchestrator
====================================================
Ties together all 5 macro intelligence modules for portfolio-level analysis.
Provides the single entry point for the dashboard routes.
"""


from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from research.macro import fii_flow
from research.macro import currency_sensitivity
from research.macro import macro_health
from research.macro import import_sensitivity
from research.macro import reserve_stress

BASE_DIR = Path(__file__).parent.parent.parent
BILLING_DIR = BASE_DIR / "billing"
RESEARCH_DB = BILLING_DIR / "research.db"

ALL_MACRO_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS macro_portfolio_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER,
    company_id INTEGER,
    linked_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_macro_tables():
    with get_connection() as conn:
        conn.executescript(ALL_MACRO_TABLES_SQL)
    fii_flow.init_fii_tables()
    macro_health.init_macro_tables()
    import_sensitivity.init_import_tables()
    reserve_stress.init_reserve_tables()


def get_macro_overview() -> Dict:
    """
    Dashboard overview — returns FII flow, macro health, and reserve stress.
    For full intelligence including currency and import sensitivity, use get_full_intelligence().
    """
    fii_report = fii_flow.build_flow_intelligence_report()
    macro_report = macro_health.build_macro_health_report()
    reserve_report = reserve_stress.build_reserve_stress_report()
    latest_reserve = reserve_stress.get_latest_reserve_snapshot()
    latest_macro = macro_health.get_latest_snapshot()

    return {
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'fii_flow': {
            'regime': fii_report['flow_regime'],
            'monthly_net_cr': fii_report['monthly'].get('monthly_net_cr'),
            'vulnerability': fii_report['vulnerability'],
            'observation': fii_report['observation'],
            'data_quality': fii_report['data_quality'],
        },
        'macro_health': {
            'composite_score': macro_report['composite_score'],
            'status': macro_report['status'],
            'active_indicators': macro_report['active_indicators'],
            'total_indicators': macro_report['total_indicators'],
            'observation': macro_report['observation'],
        },
        'reserve_stress': {
            'stress_level': reserve_report['stress_level'],
            'stress_score': reserve_report['stress_score'],
            'reserve_level_usd_bn': reserve_report['reserve_level_usd_bn'],
            'observation': reserve_report['observation'],
        },
        'observations': [
            fii_report['observation'],
            macro_report['observation'],
            reserve_report['observation'],
        ],
        'composite_observation': _composite_observation(
            macro_report.get('status', 'NO_DATA'),
            fii_report.get('flow_regime', {}),
            reserve_report.get('stress_level', 'NORMAL'),
        ),
    }


def get_full_intelligence(positions: List[Dict] = None,
                           macro_indicators: Dict = None,
                           reserve_data: Dict = None) -> Dict:
    if positions is None:
        positions = []

    if macro_indicators is None:
        macro_indicators = {}

    if reserve_data is None:
        reserve_data = {}

    expected_keys = {'reserve_level_usd_bn', 'import_cover_months', 'forex_swap_book_usd_bn', 'short_term_debt_pct'}
    reserve_data = {k: v for k, v in reserve_data.items() if k in expected_keys}

    fii_flow_report = fii_flow.build_flow_intelligence_report()
    macro_health_report = macro_health.build_macro_health_report(macro_indicators)
    currency_view = currency_sensitivity.build_portfolio_currency_view(positions)
    import_overlay = import_sensitivity.build_import_sensitivity_overlay(positions)
    reserve_report = reserve_stress.build_reserve_stress_report(**reserve_data)

    return {
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'fii_flow': fii_flow_report,
        'macro_health': macro_health_report,
        'currency_intelligence': currency_view,
        'import_sensitivity': import_overlay,
        'reserve_stress': reserve_report,
        'composite_observation': _composite_observation(
            macro_health_report.get('status', 'NO_DATA'),
            fii_flow_report.get('flow_regime', {}),
            reserve_report.get('stress_level', 'NORMAL'),
        ),
    }


def _composite_observation(macro_status: str, fii_flow_regime: Dict, reserve_level: str) -> str:
    signals = []
    if macro_status == 'RED':
        signals.append('Macro health: RED')
    elif macro_status == 'AMBER':
        signals.append('Macro health: AMBER')

    fii_risk = fii_flow_regime.get('risk', 'MEDIUM')
    fii_code = fii_flow_regime.get('regime', '')
    if fii_risk == 'HIGH':
        signals.append('FII flow risk: HIGH')
    elif fii_code in ('HEAVY_OUTFLOW', 'MODERATE_OUTFLOW'):
        signals.append('FII outflows ongoing')

    if reserve_level == 'ELEVATED':
        signals.append('Reserve stress: ELEVATED')
    elif reserve_level == 'HIGH':
        signals.append('Reserve stress: HIGH')

    if not signals:
        return 'India macro indicators broadly stable. Portfolio-level company factors remain primary driver of returns.'

    return ' | '.join(signals) + '. Portfolio sensitivity to macro factors elevated — review positioning and hedge coverage.'
