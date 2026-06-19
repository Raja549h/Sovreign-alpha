"""
Backfill Memory — Populate observation_memory from forensic_flags
==================================================================
On first run, backfills observation_memory from existing forensic_flags
so that Bajaj Finance, Muthoot Finance, and all other companies
immediately have populated memory timelines.
"""

import sys
from database import get_connection
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
BILLING_DIR = BASE_DIR / "billing"

FLAG_TO_CATEGORY = {
    'margin_compression': 'margin',
    'nim_compression': 'margin',
    'revenue_decline': 'margin',
    'cost_inflation': 'margin',
    'credit_cost': 'margin',
    'funding_cost': 'funding_cost',
    'cof_increase': 'funding_cost',
    'related_party': 'governance',
    'promoter_pledge': 'governance',
    'auditor_change': 'governance',
    'governance_concern': 'governance',
    'capital_allocation': 'capital_allocation',
    'valuation_expansion': 'valuation',
    'valuation_compression': 'valuation',
    'pe_expansion': 'valuation',
    'pe_compression': 'valuation',
    'macro_sensitivity': 'macro',
    'regime_exposure': 'macro',
    'management_guidance': 'management_commentary',
    'guidance_miss': 'management_commentary',
    'guidance_divergence': 'management_commentary',
    'liquidity_stress': 'liquidity',
    'debt_increase': 'liquidity',
    'liquidity_crunch': 'liquidity',
    'business_quality': 'business_quality',
    'roe_decline': 'business_quality',
    'roa_decline': 'business_quality',
    'roce_decline': 'business_quality',
    'asset_quality': 'business_quality',
}

SEVERITY_CONFIDENCE = {
    'critical': 0.95,
    'high': 0.85,
    'medium': 0.65,
    'low': 0.45,
}

FLAG_DIRECTION = {
    'compression': 'deteriorating',
    'decline': 'deteriorating',
    'stress': 'deteriorating',
    'crunch': 'deteriorating',
    'decrease': 'deteriorating',
    'increase': 'deteriorating',
    'miss': 'deteriorating',
    'exposure': 'deteriorating',
    'pledge': 'deteriorating',
    'concern': 'deteriorating',
    'divergence': 'deteriorating',
    'recovery': 'improving',
    'improvement': 'improving',
    'expansion': 'improving',
}


def _get_db():
    conn = get_connection()
    return conn


def infer_category(flag_type: str) -> str:
    ft = flag_type.lower().strip()
    for prefix, cat in FLAG_TO_CATEGORY.items():
        if ft.startswith(prefix) or ft == prefix:
            return cat
    if 'margin' in ft or 'nim' in ft or 'revenue' in ft or 'cost' in ft or 'credit' in ft:
        return 'margin'
    if 'funding' in ft or 'cof' in ft:
        return 'funding_cost'
    if 'pledge' in ft or 'related' in ft or 'auditor' in ft or 'governance' in ft:
        return 'governance'
    if 'capital' in ft or 'allocation' in ft:
        return 'capital_allocation'
    if 'valuation' in ft or 'pe' in ft or 'pbv' in ft:
        return 'valuation'
    if 'macro' in ft or 'regime' in ft:
        return 'macro'
    if 'guidance' in ft or 'management' in ft:
        return 'management_commentary'
    if 'liquidity' in ft or 'debt' in ft:
        return 'liquidity'
    if 'roe' in ft or 'roa' in ft or 'roce' in ft or 'quality' in ft or 'asset' in ft:
        return 'business_quality'
    return 'business_quality'


def infer_direction(flag_type: str) -> str:
    ft = flag_type.lower()
    for keyword, direction in FLAG_DIRECTION.items():
        if keyword in ft:
            return direction
    return 'deteriorating'


def backfill():
    from research.storage.research_db import init_evolution_tables
    init_evolution_tables()

    conn = _get_db()
    c = conn.cursor()
    c.execute("""SELECT f.*, c.ticker, c.company_name
                 FROM forensic_flags f
                 JOIN companies c ON c.id = f.company_id
                 ORDER BY f.detected_at ASC""")
    flags = [dict(r) for r in c.fetchall()]

    c.execute("SELECT COUNT(*) as cnt FROM observation_memory")
    existing = c.fetchone()['cnt']

    if existing > 0:
        print(f"[SKIP] observation_memory already has {existing} entries. Backfill skipped.")
        conn.close()
        return existing

    inserted = 0
    skipped = 0
    for f in flags:
        flag_type = f.get('flag_type', '')
        description = f.get('description', '')
        severity = f.get('severity', 'low').lower()
        detected_at = f.get('detected_at', '')
        company_id = f.get('company_id')
        supporting = f.get('supporting_data', '')

        if not description or not company_id:
            skipped += 1
            continue

        category = infer_category(flag_type)
        direction = infer_direction(flag_type)
        confidence = SEVERITY_CONFIDENCE.get(severity, 0.65)
        obs_date = detected_at[:10] if detected_at else datetime.now().strftime('%Y-%m-%d')
        source = 'filing'

        try:
            c.execute(
                """INSERT INTO observation_memory
                   (company_id, observation_date, category, observation_text,
                    confidence, source, direction)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (company_id, obs_date, category, description,
                 confidence, source, direction)
            )
            inserted += 1
        except Exception as _e:
            skipped += 1
            if skipped <= 3:
                print(f"[backfill] Skipped row {company_id}/{flag_type}: {_e}")

    conn.commit()
    conn.close()

    print(f"[BACKFILL] Complete: {inserted} observations created from {len(flags)} forensic flags ({skipped} skipped)")
    return inserted


if __name__ == '__main__':
    count = backfill()
    print(f"[DONE] Memory populated with {count} observations.")
