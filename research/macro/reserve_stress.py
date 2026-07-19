from dashboard.gateway import get_connection
"""
Foreign Reserves Stress Indicator — RBI reserve adequacy monitoring
====================================================================
Tracks India's foreign exchange reserve trends and classifies reserve stress
levels (NORMAL/WATCH/ELEVATED/HIGH). Provides macro stress framework for
portfolio context — NOT a prediction or warning system.

Framework based on:
- Reserve trend (3m/6m/12m changes)
- Import cover (months)
- Short-term debt coverage ratio
- Reserve volatility
"""


import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent.parent
BILLING_DIR = BASE_DIR / "billing"
RESEARCH_DB = BILLING_DIR / "research.db"

RESERVE_STRESS_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS reserve_stress_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    reserve_level_usd_bn REAL,
    stress_level TEXT,
    stress_score REAL,
    three_month_change_pct REAL,
    six_month_change_pct REAL,
    twelve_month_change_pct REAL,
    import_cover_months REAL,
    short_term_debt_coverage REAL,
    reserve_volatility REAL,
    details TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

# India-specific thresholds (based on RBI + IMF framework)
RESERVE_THRESHOLDS = {
    'import_cover_months': {
        'ADEQUATE': 10.0, 'WATCH': 7.0, 'ELEVATED': 5.0,
        'description': 'Months of import cover — standard adequacy: >8 months'
    },
    'short_term_debt_coverage': {
        'ADEQUATE': 1.5, 'WATCH': 1.0, 'ELEVATED': 0.7,
        'description': 'Ratio of reserves to short-term external debt'
    },
    'reserve_change_12m_pct': {
        'ADEQUATE': 5.0, 'WATCH': -2.0, 'ELEVATED': -8.0,
        'description': '12-month reserve change percentage'
    },
}

STRESS_LEVELS = [
    ('NORMAL', 0, 25, 'Reserve position comfortable. No macro stress from reserve adequacy.'),
    ('WATCH', 25, 50, 'Reserve trends warrant monitoring. Select indicators below adequacy thresholds.'),
    ('ELEVATED', 50, 75, 'Reserve stress indicators elevated. Portfolio should factor in currency volatility risk.'),
    ('HIGH', 75, 100, 'Significant reserve stress. Historical parallels suggest elevated macro risk for Indian equities.'),
]


def init_reserve_tables():
    with get_connection() as conn:
        conn.cursor().execute(RESERVE_STRESS_TABLES_SQL)


def _get_db():
    conn = get_connection()
    return conn


def calculate_import_cover_score(import_cover_months: Optional[float]) -> float:
    if import_cover_months is None:
        return 30.0  # Default to moderate stress when no data
    thresholds = RESERVE_THRESHOLDS['import_cover_months']
    if import_cover_months >= thresholds['ADEQUATE']:
        return 5.0
    elif import_cover_months >= thresholds['WATCH']:
        decay = (thresholds['ADEQUATE'] - import_cover_months) / (thresholds['ADEQUATE'] - thresholds['WATCH'])
        return 5.0 + decay * 30.0
    elif import_cover_months >= thresholds['ELEVATED']:
        decay = (thresholds['WATCH'] - import_cover_months) / (thresholds['WATCH'] - thresholds['ELEVATED'])
        return 35.0 + decay * 35.0
    else:
        return 80.0


def calculate_debt_coverage_score(st_debt_coverage: Optional[float]) -> float:
    if st_debt_coverage is None:
        return 30.0
    thresholds = RESERVE_THRESHOLDS['short_term_debt_coverage']
    if st_debt_coverage >= thresholds['ADEQUATE']:
        return 5.0
    elif st_debt_coverage >= thresholds['WATCH']:
        decay = (thresholds['ADEQUATE'] - st_debt_coverage) / (thresholds['ADEQUATE'] - thresholds['WATCH'])
        return 5.0 + decay * 30.0
    elif st_debt_coverage >= thresholds['ELEVATED']:
        decay = (thresholds['WATCH'] - st_debt_coverage) / (thresholds['WATCH'] - thresholds['ELEVATED'])
        return 35.0 + decay * 35.0
    else:
        return 80.0


def calculate_change_score(change_pct: Optional[float], period_months: int) -> float:
    if change_pct is None:
        return 30.0
    threshold_key = 'reserve_change_12m_pct'
    thresholds = RESERVE_THRESHOLDS[threshold_key]
    if period_months != 12 and change_pct is not None:
        annualized = change_pct * (12.0 / period_months)
    else:
        annualized = change_pct

    if annualized >= thresholds['ADEQUATE']:
        return 5.0
    elif annualized >= thresholds['WATCH']:
        decay = (thresholds['ADEQUATE'] - annualized) / (thresholds['ADEQUATE'] - thresholds['WATCH'])
        return 5.0 + decay * 25.0
    elif annualized >= thresholds['ELEVATED']:
        decay = (thresholds['WATCH'] - annualized) / (thresholds['WATCH'] - thresholds['ELEVATED'])
        return 30.0 + decay * 35.0
    else:
        return 75.0


def calculate_volatility_score(reserve_volatility: Optional[float]) -> float:
    if reserve_volatility is None:
        return 15.0  # Assume low when no data
    if reserve_volatility <= 2.0:
        return 5.0
    elif reserve_volatility <= 5.0:
        return 5.0 + (reserve_volatility - 2.0) / 3.0 * 25.0
    elif reserve_volatility <= 10.0:
        return 30.0 + (reserve_volatility - 5.0) / 5.0 * 30.0
    else:
        return 70.0


def classify_stress_level(stress_score: float) -> Dict:
    for level, threshold_min, threshold_max, description in STRESS_LEVELS:
        if threshold_min <= stress_score <= threshold_max:
            return {'level': level, 'description': description}
    return {'level': 'HIGH', 'description': STRESS_LEVELS[-1][3]}


def build_reserve_stress_report(
    reserve_usd_bn: float = None,
    import_cover_months: float = None,
    st_debt_coverage: float = None,
    three_month_chg: float = None,
    six_month_chg: float = None,
    twelve_month_chg: float = None,
    reserve_volatility: float = None,
) -> Dict:
    init_reserve_tables()

    import_cover_score = calculate_import_cover_score(import_cover_months)
    debt_coverage_score = calculate_debt_coverage_score(st_debt_coverage)
    change_score_3m = calculate_change_score(three_month_chg, 3)
    change_score_6m = calculate_change_score(six_month_chg, 6)
    change_score_12m = calculate_change_score(twelve_month_chg, 12)
    volatility_score = calculate_volatility_score(reserve_volatility)

    composite_stress = (
        import_cover_score * 0.30 +
        debt_coverage_score * 0.25 +
        change_score_12m * 0.20 +
        (change_score_3m + change_score_6m) / 2 * 0.15 +
        volatility_score * 0.10
    )

    stress_info = classify_stress_level(composite_stress)

    details = {
        'import_cover': {
            'value': import_cover_months,
            'score': round(import_cover_score, 1),
            'weight': '30%',
        },
        'debt_coverage': {
            'value': st_debt_coverage,
            'score': round(debt_coverage_score, 1),
            'weight': '25%',
        },
        'change_12m': {
            'value': twelve_month_chg,
            'score': round(change_score_12m, 1),
            'weight': '20%',
        },
        'change_3m_6m_avg': {
            'score': round((change_score_3m + change_score_6m) / 2, 1),
            'weight': '15%',
        },
        'volatility': {
            'value': reserve_volatility,
            'score': round(volatility_score, 1),
            'weight': '10%',
        },
    }

    report = {
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'reserve_level_usd_bn': reserve_usd_bn,
        'stress_level': stress_info['level'],
        'stress_score': round(composite_stress, 1),
        'stress_description': stress_info['description'],
        'import_cover_months': import_cover_months,
        'short_term_debt_coverage': st_debt_coverage,
        'three_month_change_pct': three_month_chg,
        'six_month_change_pct': six_month_chg,
        'twelve_month_change_pct': twelve_month_chg,
        'reserve_volatility': reserve_volatility,
        'details': details,
        'observation': _reserve_observation(stress_info['level'], composite_stress, reserve_usd_bn),
    }

    # Persist
    try:
        with _get_db() as conn:
            conn.execute("""
                INSERT INTO reserve_stress_snapshots
                (snapshot_date, reserve_level_usd_bn, stress_level, stress_score,
                 three_month_change_pct, six_month_change_pct, twelve_month_change_pct,
                 import_cover_months, short_term_debt_coverage, reserve_volatility, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.utcnow().strftime('%Y-%m-%d'), reserve_usd_bn,
                stress_info['level'], round(composite_stress, 1),
                three_month_chg, six_month_chg, twelve_month_chg,
                import_cover_months, st_debt_coverage, reserve_volatility,
                json.dumps(details, default=str),
            ))
            conn.commit()
    except Exception:
        pass

    return report


def get_latest_reserve_snapshot() -> Optional[Dict]:
    with _get_db() as conn:
        cur = conn.execute(
            "SELECT * FROM reserve_stress_snapshots ORDER BY created_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_reserve_history(limit: int = 12) -> List[Dict]:
    with _get_db() as conn:
        cur = conn.execute(
            "SELECT * FROM reserve_stress_snapshots ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [dict(r) for r in cur.fetchall()]


def _reserve_observation(level: str, score: float, reserves: Optional[float]) -> str:
    level_descriptions = {
        'NORMAL': 'India\'s foreign reserve position is adequate. No stress on external account. Standard monitoring sufficient.',
        'WATCH': 'Select reserve adequacy indicators warrant attention. Monitor RBI intervention and import cover trends.',
        'ELEVATED': 'Reserve stress indicators are elevated. Portfolio should consider INR hedging and review import-heavy exposures.',
        'HIGH': 'Reserve stress at elevated levels. Historical context: periods of similar stress have coincided with sharp INR depreciation and equity market drawdowns.',
    }
    base = level_descriptions.get(level, 'Reserve stress assessment unavailable.')
    if reserves:
        base += f' Current reserves: ~${reserves:.1f}B.'
    return base
