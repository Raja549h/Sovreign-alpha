import os, psycopg2
from dotenv import load_dotenv
load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('NEON_URL'))
    c = conn.cursor()
    c.execute("SELECT id, ticker, headline FROM observations WHERE headline ILIKE '%stress test%'")
    stress_tests = c.fetchall()
    print("STRESS TESTS FOUND:", len(stress_tests))
    for row in stress_tests:
        print(f" - {row[1]} | {row[2]}")

    c.execute("SELECT COUNT(*) FROM companies WHERE ticker = 'TSLA'")
    print("\nTSLA IN COMPANIES:", c.fetchone()[0])

    c.execute("SELECT COUNT(*) FROM observations WHERE ticker = 'TSLA'")
    print("TSLA IN OBSERVATIONS:", c.fetchone()[0])
    
    conn.close()
except Exception as e:
    print("ERROR:", e)
