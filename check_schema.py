import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.environ['NEON_URL'])
c = conn.cursor()
c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'observations'")
print('observations:', c.fetchall())
c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'prediction_ledger'")
print('prediction_ledger:', c.fetchall())
