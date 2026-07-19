import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM prediction_ledger WHERE asset IN ('AMD','TSM','CVX','XOM')")
print('US Tickers in prediction_ledger:', cur.fetchone()[0])

cur.execute("SELECT status, COUNT(*) FROM prediction_ledger GROUP BY status")
print('Statuses:', cur.fetchall())

cur.close()
conn.close()
