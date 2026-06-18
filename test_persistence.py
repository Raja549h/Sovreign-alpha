import os
import sqlite3
os.environ['SPACE_ID'] = 'test'
from dashboard.app import seed_database_on_startup, DB_PATH

print("--- INITIAL STARTUP ---")
seed_database_on_startup()

conn = sqlite3.connect(DB_PATH)
conn.execute("INSERT INTO prediction_ledger (prediction_id, timestamp, asset, status, created_at, updated_at) VALUES ('TEST-001', '2026-06-18', 'TEST', 'cleared', '2026-06-18', '2026-06-18')")
conn.commit()
count = conn.execute("SELECT COUNT(*) FROM prediction_ledger WHERE prediction_id='TEST-001'").fetchone()[0]
print(f"Record created: {count}")

for i in range(1, 4):
    print(f"--- RESTART {i} ---")
    seed_database_on_startup()
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM prediction_ledger WHERE prediction_id='TEST-001'").fetchone()[0]
    print(f"Record exists: {count}")

conn.execute("DELETE FROM prediction_ledger WHERE prediction_id='TEST-001'")
conn.commit()
