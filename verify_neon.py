import os
os.environ["NEON_URL"] = "postgresql://neondb_owner:npg_HxbKeITV73Gl@ep-super-art-adot6eyq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
from database import get_connection

def verify():
    conn = get_connection("research.db")
    c = conn.cursor()
    
    print("=== OBSERVATION ===")
    c.execute("SELECT * FROM observations ORDER BY id DESC LIMIT 1")
    print(dict(c.fetchone()))
    
    print("=== VALIDATION ===")
    c.execute("SELECT * FROM observation_validations ORDER BY id DESC LIMIT 1")
    print(dict(c.fetchone()))
    
    print("=== CHALLENGE ===")
    c.execute("SELECT * FROM challenge_records ORDER BY id DESC LIMIT 1")
    print(dict(c.fetchone()))
    
    print("=== FAILURE ===")
    c.execute("SELECT * FROM failure_analysis ORDER BY id DESC LIMIT 1")
    print(dict(c.fetchone()))
    
    print("=== TIMELINE ===")
    c.execute("SELECT * FROM evidence_timeline ORDER BY id DESC LIMIT 1")
    print(dict(c.fetchone()))
    
    print("=== CALIBRATION ===")
    c.execute("SELECT * FROM confidence_calibration ORDER BY id DESC LIMIT 1")
    print(dict(c.fetchone()))
    
    print("=== FRAMEWORK ===")
    c.execute("SELECT * FROM framework_performance ORDER BY evaluation_date DESC LIMIT 1")
    print(dict(c.fetchone()))
    
    conn.close()

    conn = get_connection("billing.db")
    c = conn.cursor()
    print("=== PREDICTION ===")
    c.execute("SELECT * FROM prediction_ledger ORDER BY id DESC LIMIT 1")
    print(dict(c.fetchone()))
    conn.close()

if __name__ == '__main__':
    verify()
