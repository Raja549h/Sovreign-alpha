import sqlite3
from pathlib import Path
import json

db_path = Path('c:/Users/lokes/Downloads/project/sovereign-alpha/billing/billing.db')
research_db = Path('c:/Users/lokes/Downloads/project/sovereign-alpha/data/research.db')

conn1 = sqlite3.connect(db_path)
c1 = conn1.cursor()

c1.execute("SELECT COUNT(*) FROM prediction_ledger")
predictions = c1.fetchone()[0]

c1.execute("SELECT COUNT(*) FROM veto_archive")
vetoes = c1.fetchone()[0]

c1.execute("SELECT COUNT(*) FROM performance_log")
failures = c1.fetchone()[0] # Actually, failures are in performance log or autopsy

print(f"Predictions (billing.db): {predictions}")
print(f"Vetoes (billing.db): {vetoes}")

conn1.close()

if research_db.exists():
    conn2 = sqlite3.connect(research_db)
    c2 = conn2.cursor()
    c2.execute("SELECT COUNT(*) FROM observations")
    obs = c2.fetchone()[0]
    print(f"Observations (research.db): {obs}")
    
    try:
        c2.execute("SELECT COUNT(*) FROM observation_autopsy")
        auto = c2.fetchone()[0]
        print(f"Autopsies (research.db): {auto}")
    except:
        pass
        
    try:
        c2.execute("SELECT COUNT(*) FROM failures")
        fail = c2.fetchone()[0]
        print(f"Failures (research.db): {fail}")
    except:
        pass
    conn2.close()
