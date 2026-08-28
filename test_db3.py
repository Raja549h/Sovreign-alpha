import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.environ.get('DATABASE_URL') or os.environ.get('AIVEN_DATABASE_URL')

conn = psycopg2.connect(DB_URL)
c = conn.cursor()
c.execute("SELECT status, COUNT(*) FROM prediction_ledger GROUP BY status")
for row in c.fetchall():
    print(row)
conn.close()
