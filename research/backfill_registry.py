"""
Backfill Registry — Migrate existing observation_memory rows
to the new validation schema.
Run once: python -m research.backfill_registry
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research.storage.research_db import init_validation_tables
from research.observation_registry import ObservationRegistry, _get_db
from datetime import datetime, timedelta, timezone


def backfill():
    init_validation_tables()
    reg = ObservationRegistry()

    remaining = reg.get_registry(status=None, limit=10000)
    updated = 0

    for obs in remaining:
        obs_id = obs.get('id')
        if not obs_id:
            continue
        obs_date = obs.get('observation_date', '')
        if obs_date:
            obs_dt = datetime.strptime(obs_date, '%Y-%m-%d')
        else:
            obs_dt = datetime.now(timezone.utc)

        d30 = (obs_dt + timedelta(days=30)).strftime('%Y-%m-%d')
        d90 = (obs_dt + timedelta(days=90)).strftime('%Y-%m-%d')
        d180 = (obs_dt + timedelta(days=180)).strftime('%Y-%m-%d')

        expected = obs.get('expected_implication') or ''
        vstatus = obs.get('validation_status') or 'ACTIVE'

        conn = _get_db()
        try:
            c = conn.cursor()
            c.execute(
                """UPDATE observation_memory
                   SET review_date_30 = %s,
                       review_date_90 = %s,
                       review_date_180 = %s,
                       expected_implication = COALESCE(NULLIF(%s, ''), expected_implication),
                       validation_status = COALESCE(NULLIF(%s, ''), validation_status)
                   WHERE id = %s""",
                (d30, d90, d180, expected, vstatus, obs_id)
            )
            updated += c.rowcount
            conn.commit()
        finally:
            pass
            pass # conn.close()

    reg.calculate_edge_score()

    print(f"Backfill complete. {updated} observations updated.")
    print("Validation tables initialized. Edge scorecard calculated.")


if __name__ == '__main__':
    backfill()
