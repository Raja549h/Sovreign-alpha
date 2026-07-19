import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM prediction_ledger")
print('prediction_ledger:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM observations")
print('observations:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM veto_archive")
print('veto_archive:', cur.fetchone()[0])

cur.close()
conn.close()
