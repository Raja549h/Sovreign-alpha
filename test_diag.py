import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.environ.get('DATABASE_URL') or os.environ.get('AIVEN_DATABASE_URL')

query = """
SELECT 
    COUNT(*) AS total_active,
    COUNT(*) FILTER (WHERE timestamp::timestamptz < NOW() - INTERVAL '30 days') AS older_than_30_days,
    COUNT(*) FILTER (WHERE entry_price IS NULL OR entry_price <= 0) AS missing_entry_price,
    COUNT(*) FILTER (WHERE target_price IS NULL OR stop_loss IS NULL) AS missing_targets,
    COUNT(*) FILTER (WHERE asset IS NULL OR asset = '') AS missing_asset
FROM prediction_ledger
WHERE status = 'active';
"""

try:
    conn = psycopg2.connect(DB_URL)
    c = conn.cursor()
    c.execute(query)
    row = c.fetchone()
    
    print("\n--- DIAGNOSTIC RESULTS: 284 ACTIVE PREDICTIONS ---")
    print(f"Total Active:                  {row[0]}")
    print(f"Older than 30 Days:            {row[1]}")
    print(f"Missing Entry Price:           {row[2]}")
    print(f"Missing Target or Stop Loss:   {row[3]}")
    print(f"Missing Asset/Ticker:          {row[4]}")
    print("--------------------------------------------------")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
