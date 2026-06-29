import os, sys
sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv()
from dashboard.app import db_get_connection
from database import init_pool

init_pool()
conn = db_get_connection()
c = conn.cursor()

c.execute("SELECT id, ticker, headline FROM observations WHERE headline ILIKE '%stress test%'")
stress_tests = c.fetchall()
print("STRESS TESTS FOUND:", len(stress_tests))
for row in stress_tests:
    print(f" - {row['ticker']} | {row['headline']}")

c.execute("SELECT COUNT(*) as count FROM companies WHERE ticker = 'TSLA'")
tsla_company = c.fetchone()['count']
print("\nTSLA IN COMPANIES:", tsla_company)

c.execute("SELECT COUNT(*) as count FROM observations WHERE ticker = 'TSLA'")
tsla_obs = c.fetchone()['count']
print("TSLA IN OBSERVATIONS:", tsla_obs)

conn.close()
