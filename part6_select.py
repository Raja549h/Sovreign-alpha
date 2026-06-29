import psycopg2, os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
conn = psycopg2.connect(os.environ['NEON_URL'])

print("--- OPERATION A: STRESS TEST OBSERVATIONS ---")
query_a = """
SELECT id, ticker, headline || ' ' || supporting_data as observation_text,
timestamp as created_at, severity
FROM observations
WHERE LOWER(headline || ' ' || supporting_data) LIKE '%stress test%'
OR LOWER(headline || ' ' || supporting_data) LIKE '%test data%'
OR LOWER(headline || ' ' || supporting_data) LIKE '%sample%'
OR LOWER(headline || ' ' || supporting_data) LIKE '%placeholder%'
OR LOWER(headline || ' ' || supporting_data) LIKE '%seed%';
"""
try:
    df_a = pd.read_sql(query_a, conn)
    if len(df_a) == 0:
        print("0 rows found.")
    else:
        print(f"Found {len(df_a)} rows.")
        print(df_a.to_string())
except Exception as e:
    print("Error in query A:", e)

print("\n--- OPERATION B: TSLA TEST DATA ---")
query_b1 = """
SELECT c.id, c.ticker, c.company_name as name,
COUNT(o.id) as observation_count,
COUNT(p.id) as prediction_count
FROM companies c
LEFT JOIN observations o ON o.company = c.company_name
LEFT JOIN prediction_ledger p ON p.asset = c.ticker
WHERE c.ticker = 'TSLA'
GROUP BY c.id, c.ticker, c.company_name;
"""
try:
    df_b1 = pd.read_sql(query_b1, conn)
    if len(df_b1) == 0:
        print("0 rows found in companies.")
    else:
        print(f"Found {len(df_b1)} rows in companies.")
        print(df_b1.to_string())
except Exception as e:
    print("Error in query B1:", e)

query_b2 = """
SELECT headline || ' ' || supporting_data as observation_text, timestamp as created_at
FROM observations
WHERE ticker = 'TSLA'
ORDER BY timestamp DESC
LIMIT 20;
"""
try:
    df_b2 = pd.read_sql(query_b2, conn)
    if len(df_b2) == 0:
        print("0 rows found in observations for TSLA.")
    else:
        print(f"Found {len(df_b2)} rows in observations for TSLA.")
        print(df_b2.to_string())
except Exception as e:
    print("Error in query B2:", e)
