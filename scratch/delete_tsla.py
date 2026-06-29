import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.environ['NEON_URL'])
conn.autocommit = True
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE asset = 'TSLA'")
p_count = c.fetchone()[0]
print(f'prediction_ledger TSLA count before: {p_count}')
if p_count > 0:
    c.execute("DELETE FROM prediction_ledger WHERE asset = 'TSLA'")
    print('Deleted TSLA from prediction_ledger')

c.execute("SELECT COUNT(*) FROM observations WHERE ticker = 'TSLA'")
o_count = c.fetchone()[0]
print(f'observations TSLA count before: {o_count}')
if o_count > 0:
    c.execute("DELETE FROM observations WHERE ticker = 'TSLA'")
    print('Deleted TSLA from observations')

c.execute("SELECT COUNT(*) FROM observations WHERE ticker = 'TSLA'")
print(f'observations TSLA count after: {c.fetchone()[0]}')
