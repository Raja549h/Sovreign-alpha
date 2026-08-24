import os
import sys
import psycopg2
from dotenv import load_dotenv

def test_database():
    print("=== STARTING DATABASE VERIFICATION ===")
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("FAIL: DATABASE_URL not set")
        sys.exit(1)
        
    db_url = db_url.strip()
    if 'sslmode=require' not in db_url:
        db_url += '&sslmode=require' if '?' in db_url else '?sslmode=require'

    try:
        conn = psycopg2.connect(db_url)
        c = conn.cursor()
        print("PASS: Connected to database.")

        # Verify tables exist
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('prediction_ledger', 'observation_memory')
        """)
        tables = [r[0] for r in c.fetchall()]
        
        if 'prediction_ledger' not in tables:
            print("FAIL: prediction_ledger table missing")
            sys.exit(1)
        if 'observation_memory' not in tables:
            print("FAIL: observation_memory table missing")
            sys.exit(1)
        print("PASS: Required tables exist.")

        # Verify columns in prediction_ledger
        c.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'prediction_ledger'
        """)
        columns = [r[0] for r in c.fetchall()]
        
        required_cols = ['asset', 'status', 'actual_outcome', 'resolved_at']
        for col in required_cols:
            if col not in columns:
                print(f"FAIL: Missing critical column '{col}' in prediction_ledger")
                sys.exit(1)
        print("PASS: Critical columns exist in prediction_ledger.")

        # Verify rows exist
        c.execute("SELECT COUNT(*) FROM prediction_ledger")
        if c.fetchone()[0] == 0:
            print("FAIL: prediction_ledger is empty.")
            sys.exit(1)
            
        c.execute("SELECT COUNT(*) FROM observation_memory")
        if c.fetchone()[0] == 0:
            print("FAIL: observation_memory is empty.")
            sys.exit(1)
            
        print("PASS: Tables have data.")

        print("=== DATABASE VERIFICATION PASSED ===")
        c.close()
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: Exception during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_database()
