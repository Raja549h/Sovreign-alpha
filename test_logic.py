import sys
from automation.email_digest import load_env
load_env()
from database import get_connection as db_get_connection
import json

try:
    conn = db_get_connection()
    c = conn.cursor()
    
    maturity_stats = {'<30': 0, '30-60': 0, '>60': 0}
    c.execute("SELECT expected_timeline_days FROM prediction_ledger WHERE status NOT IN ('HIT', 'MISS', 'hit', 'miss', 'resolved')")
    for row in c.fetchall():
        days = row[0]
        if days is not None:
            if days < 30: maturity_stats['<30'] += 1
            elif days <= 60: maturity_stats['30-60'] += 1
            else: maturity_stats['>60'] += 1
    
    c.close()
    conn.close()
    print("Maturity Stats OK")
except Exception as e:
    print("Maturity Stats ERROR:", e)

try:
    from dashboard.app import get_dashboard_stats
except Exception:
    pass
