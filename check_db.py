import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['NEON_URL'])
c = conn.cursor()
c.execute("SELECT error_log FROM analysis_runs WHERE error_log IS NOT NULL LIMIT 5")
for row in c.fetchall():
    print("ERROR:", row[0])
