import os
import psycopg2
from dotenv import load_dotenv
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
DB_URL = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DB_URL)
c = conn.cursor()
c.execute("SELECT id, asset, thesis, timestamp FROM prediction_ledger WHERE status = 'active' LIMIT 1")
row = c.fetchone()
print(f"ID: {row[0]}")
print(f"Asset: {row[1]}")
print(f"Timestamp: {row[3]}")
print(f"Thesis: {row[2][:500]}...")
conn.close()
