import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
DB_URL = os.environ.get('DATABASE_URL') or os.environ.get('AIVEN_DATABASE_URL')

conn = psycopg2.connect(DB_URL)
c = conn.cursor()
c.execute("UPDATE prediction_ledger SET status = 'resolved' WHERE actual_outcome IN ('HIT', 'MISS', 'EXPIRED') AND status != 'resolved'")
print(f"Updated {c.rowcount} already resolved predictions.")
conn.commit()
conn.close()
