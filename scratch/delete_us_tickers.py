import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("DELETE FROM prediction_ledger WHERE asset IN ('AMD','TSM','CVX','XOM')")
conn.commit()
print('Deleted US tickers!')

cur.close()
conn.close()
