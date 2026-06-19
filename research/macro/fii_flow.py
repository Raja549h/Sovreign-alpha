"""
FII Flow Intelligence — Institutional risk awareness for FII-driven volatility
=============================================================================
Tracks daily, weekly, and monthly FII flow patterns to assess portfolio
vulnerability to FII-driven dislocations. Provides flow regime classification
and risk alerts for concentrated Indian equity portfolios.

Design principle: institutional risk awareness, NOT trading signals.
Flow data must be entered manually (NSDL, SEBI, Bloomberg sources) or
collected via automation master_daily step.
"""

from database import get_connection
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent.parent
BILLING_DIR = BASE_DIR / "billing"

FII_FLOW_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS fii_flows (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    flow_type TEXT NOT NULL,
    category TEXT NOT NULL,
    amount_cr REAL,
    source TEXT DEFAULT 'external',
    notes TEXT DEFAULT '',
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fii_flow_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date TEXT NOT NULL,
    daily_net_cr REAL,
    weekly_net_cr REAL,
    monthly_net_cr REAL,
    regime TEXT,
    risk_level TEXT,
    portfolio_vulnerability REAL,
    details TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

FLOW_REGIMES = {
    'HEAVY_INFLOW': {'label': 'Heavy Inflow', 'threshold_cr': 5000, 'risk': 'LOW',
                     'observation': 'Aggressive FII buying — supports liquidity and multiples'},
    'MODERATE_INFLOW': {'label': 'Moderate Inflow', 'threshold_cr': 1000, 'risk': 'LOW',
                        'observation': 'Steady FII participation — neutral to positive'},
    'NEUTRAL': {'label': 'Neutral', 'threshold_cr': -1000, 'risk': 'MEDIUM',
                'observation': 'FII flows within normal range — company factors dominate'},
    'MODERATE_OUTFLOW': {'label': 'Moderate Outflow', 'threshold_cr': -5000, 'risk': 'MEDIUM',
                         'observation': 'FII selling accelerating — monitor for regime shift'},
    'HEAVY_OUTFLOW': {'label': 'Heavy Outflow', 'threshold_cr': float('-inf'), 'risk': 'HIGH',
                      'observation': 'Sustained FII selling — portfolio vulnerability elevated'},
}


VALID_SOURCES = {'NSDL', 'SEBI', 'BLOOMBERG', 'EXTERNAL', 'MANUAL'}

_INIT_DONE = False


def init_fii_tables():
    global _INIT_DONE
    if _INIT_DONE:
        return
    _INIT_DONE = True
    with get_connection() as conn:
        conn.executescript(FII_FLOW_TABLES_SQL)


def _get_db():
    conn = get_connection()
    return conn


def record_flow_entry(date: str, flow_type: str, category: str,
                      amount_cr: float, source: str = 'EXTERNAL',
                      notes: str = ''):
    source_upper = source.upper()
    if source_upper not in VALID_SOURCES:
        source_upper = 'EXTERNAL'
    with _get_db() as conn:
        conn.execute(
            "INSERT INTO fii_flows (date, flow_type, category, amount_cr, source, notes) VALUES (%s, %s, %s, %s, %s, %s)",
            (date, flow_type, category, amount_cr, source_upper, notes)
        )
        conn.commit()


def get_recent_flows(days: int = 30) -> List[Dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')
    with _get_db() as conn:
        cur = conn.execute(
            "SELECT * FROM fii_flows WHERE date >= %s ORDER BY date DESC", (cutoff,)
        )
        return [dict(r) for r in cur.fetchall()]


def calculate_flow_aggregates(days: int = 30) -> Dict:
    flows = get_recent_flows(days)
    if not flows:
        return {'daily_net_cr': 0, 'weekly_net_cr': 0, 'monthly_net_cr': 0,
                'total_inflow_cr': 0, 'total_outflow_cr': 0, 'num_entries': 0}

    total_inflow = sum(f['amount_cr'] for f in flows if f['amount_cr'] and f['amount_cr'] > 0)
    total_outflow = sum(f['amount_cr'] for f in flows if f['amount_cr'] and f['amount_cr'] < 0)
    net = total_inflow + total_outflow

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')

    daily_flows = [f for f in flows if f['date'] == today]
    weekly_flows = [f for f in flows if f['date'] >= week_ago]

    daily_net = sum(f['amount_cr'] for f in daily_flows if f['amount_cr']) if daily_flows else None
    weekly_net = sum(f['amount_cr'] for f in weekly_flows if f['amount_cr']) if weekly_flows else None

    return {
        'daily_net_cr': daily_net,
        'weekly_net_cr': weekly_net,
        'monthly_net_cr': round(net, 2),
        'total_inflow_cr': round(total_inflow, 2),
        'total_outflow_cr': round(abs(total_outflow), 2),
        'num_entries': len(flows),
    }


FLOW_COLOR_MAP = {
    'HEAVY_INFLOW': 'var(--accent)',
    'MODERATE_INFLOW': 'var(--accent)',
    'NEUTRAL': 'var(--warning)',
    'MODERATE_OUTFLOW': 'var(--warning)',
    'HEAVY_OUTFLOW': 'var(--danger)',
}


def classify_flow_regime(net_flow_cr: float) -> Dict:
    if net_flow_cr is None:
        return {'regime': 'UNKNOWN', 'label': 'Unknown', 'risk': 'MEDIUM',
                'observation': 'Insufficient flow data', 'color': 'var(--warning)'}

    for regime, config in sorted(FLOW_REGIMES.items(), key=lambda x: -x[1]['threshold_cr']):
        if net_flow_cr >= config['threshold_cr']:
            return {
                'regime': regime,
                'label': config['label'],
                'risk': config['risk'],
                'observation': config['observation'],
                'color': FLOW_COLOR_MAP.get(regime, 'var(--text-dim)'),
            }
    return {'regime': 'UNKNOWN', 'label': 'Unknown', 'risk': 'MEDIUM',
            'observation': 'Unable to classify', 'color': 'var(--warning)'}


def assess_portfolio_vulnerability() -> Dict:
    aggregates = calculate_flow_aggregates(30)
    regime = classify_flow_regime(aggregates.get('monthly_net_cr'))

    vulnerability = 0.0
    factors = []

    if regime['risk'] == 'HIGH':
        vulnerability += 4.0
        factors.append('Sustained FII outflows increase sector-wide selling pressure')
    elif regime['risk'] == 'MEDIUM' and 'OUTFLOW' in regime.get('regime', ''):
        vulnerability += 2.0
        factors.append('Moderate FII outflows — watch for acceleration')

    outflow_pct = 0
    if aggregates.get('total_inflow_cr', 0) + aggregates.get('total_outflow_cr', 0) > 0:
        total_volume = aggregates['total_inflow_cr'] + aggregates['total_outflow_cr']
        outflow_pct = (aggregates['total_outflow_cr'] / total_volume * 100) if total_volume > 0 else 0
        if outflow_pct > 70:
            vulnerability += 2.0
            factors.append(f'Outflows constitute {outflow_pct:.0f}% of total FII flow volume')
        elif outflow_pct > 50:
            vulnerability += 1.0
            factors.append(f'Outflows dominate at {outflow_pct:.0f}% of total FII flow volume')

    if not aggregates.get('monthly_net_cr'):
        vulnerability += 1.0
        factors.append('Limited FII flow data — higher uncertainty')

    vulnerability = min(vulnerability, 10.0)
    vulnerability = round(vulnerability, 1)

    vuln_level = 'LOW'
    if vulnerability >= 7.0:
        vuln_level = 'HIGH'
    elif vulnerability >= 4.0:
        vuln_level = 'MEDIUM'

    return {
        'vulnerability_score': vulnerability,
        'vulnerability_level': vuln_level,
        'flow_regime': regime,
        'aggregates': aggregates,
        'factors': factors,
        'outflow_pct': round(outflow_pct, 1),
        'portfolio_exposure_note': _portfolio_exposure_note(vulnerability, regime),
    }


def _portfolio_exposure_note(vulnerability: float, regime: Dict) -> str:
    if vulnerability >= 7.0:
        return 'Elevated portfolio vulnerability to FII-driven dislocations. Consider reviewing concentration in FII-heavy names, evaluating hedge coverage, and maintaining liquidity buffer.'
    elif vulnerability >= 4.0:
        return 'Moderate FII sensitivity. Monitor weekly flow trends and sector-level FII ownership for early warning signals.'
    return 'Current FII flow environment does not indicate elevated portfolio vulnerability. Standard monitoring sufficient.'


def build_flow_intelligence_report() -> Dict:
    init_fii_tables()
    aggregates = calculate_flow_aggregates(30)
    weekly_agg = calculate_flow_aggregates(7)
    regime = classify_flow_regime(aggregates.get('monthly_net_cr'))
    vuln = assess_portfolio_vulnerability()

    recent = get_recent_flows(7)

    return {
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'flow_regime': regime,
        'monthly': aggregates,
        'weekly': weekly_agg,
        'vulnerability': vuln,
        'recent_flows': recent[:10],
        'observation': _generate_observation(regime, aggregates),
        'data_quality': 'LIVE' if aggregates.get('num_entries', 0) > 0 else 'NO_DATA',
    }


def _generate_observation(regime: Dict, aggregates: Dict) -> str:
    regime_label = regime.get('label', 'Unknown')
    net = aggregates.get('monthly_net_cr', 0)
    if net is None:
        return 'FII flow data insufficient for observation. Enter flow data to enable monitoring.'
    net_str = f'₹{abs(net):,.0f} Cr {"inflow" if net >= 0 else "outflow"}'
    return f'FII regime: {regime_label} ({net_str} monthly net). {regime.get("observation", "")}'
