import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.environ.get('DATABASE_URL') or os.environ.get('AIVEN_DATABASE_URL')

conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
c = conn.cursor()
c.execute("SELECT id, entry_price, target_price, stop_loss FROM prediction_ledger LIMIT 10")
for row in c.fetchall():
    print(row)
conn.close()
