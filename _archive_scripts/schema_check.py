"""Final data checks for edge verification."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()
import os, psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Sample predictions - what columns have data?
print("=== prediction_ledger sample (key fields) ===")
cur.execute("""
SELECT prediction_id, timestamp, asset, sector, confidence_score, status,
       trade_signal, entry_price, target_price, stop_loss, actual_outcome, actual_return_pct
FROM prediction_ledger LIMIT 5
""")
cols = [d[0] for d in cur.description]
for r in cur.fetchall():
    row = dict(zip(cols, r))
    print({k: v for k, v in row.items() if v is not None})

# Count predictions by status
print("\n=== Status distribution ===")
cur.execute("SELECT status, COUNT(*) FROM prediction_ledger GROUP BY status ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Count actual_outcome
print("\n=== actual_outcome distribution ===")
cur.execute("SELECT actual_outcome, COUNT(*) FROM prediction_ledger GROUP BY actual_outcome ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Regime observations
print("\n=== Regime observations ===")
cur.execute("SELECT DISTINCT type FROM observations")
for r in cur.fetchall():
    print(f"  {r[0]}")

cur.execute("SELECT regime_relevance, COUNT(*) FROM observations GROUP BY regime_relevance")
for r in cur.fetchall():
    print(f"  regime_relevance={r[0]}: {r[1]}")

cur.execute("SELECT timestamp, regime_relevance, headline FROM observations WHERE type='regime_signal' ORDER BY timestamp DESC LIMIT 5")
for r in cur.fetchall():
    print(f"  {r[0][:16]} | {r[1]} | {r[2][:80]}")

# Macro health snapshots
print("\n=== macro_health date range ===")
cur.execute("SELECT snapshot_date, overall_score, overall_status FROM macro_health_snapshots ORDER BY snapshot_date DESC LIMIT 10")
for r in cur.fetchall():
    print(f"  {r[0]} | score={r[1]} | status={r[2]}")

conn.close()
