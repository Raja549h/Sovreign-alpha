import os
import psycopg2
from dotenv import load_dotenv

def run_verification():
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not set")
        return
    db_url = db_url.strip()
    if 'sslmode=require' not in db_url:
        db_url += '&sslmode=require' if '?' in db_url else '?sslmode=require'

    try:
        conn = psycopg2.connect(db_url)
        c = conn.cursor()

        print("=== PHASE 4: DATA INTEGRITY VERIFICATION ===")
        
        # Step 10: Verify prediction_ledger Has Data
        print("\n--- prediction_ledger ---")
        c.execute("SELECT COUNT(*) FROM prediction_ledger")
        print(f"Total Rows: {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(DISTINCT asset) FROM prediction_ledger")
        print(f"Distinct Assets: {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'cleared'")
        print(f"Status 'cleared': {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'pending'")
        print(f"Status 'pending': {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome = 'HIT'")
        print(f"Outcome 'HIT': {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome = 'MISS'")
        print(f"Outcome 'MISS': {c.fetchone()[0]}")
        
        c.execute("SELECT MIN(created_at), MAX(created_at) FROM prediction_ledger")
        min_date, max_date = c.fetchone()
        print(f"Created At range: {min_date} to {max_date}")

        # Step 11: Verify observation_memory Has Data
        print("\n--- observation_memory ---")
        c.execute("SELECT COUNT(*) FROM observation_memory")
        print(f"Total Rows: {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(DISTINCT company_id) FROM observation_memory")
        print(f"Distinct company_ids: {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(DISTINCT DATE(created_at)) FROM observation_memory")
        print(f"Distinct Dates: {c.fetchone()[0]}")
        
        c.execute("SELECT MIN(created_at), MAX(created_at) FROM observation_memory")
        min_date_obs, max_date_obs = c.fetchone()
        print(f"Created At range: {min_date_obs} to {max_date_obs}")

        # Step 12: Check for Data Quality Issues
        print("\n--- Data Quality Issues ---")
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE asset IS NULL OR asset = ''")
        print(f"Predictions with NULL/empty asset: {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE asset NOT LIKE '%.NS'")
        print(f"Predictions without .NS suffix: {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE entry_price IS NULL")
        print(f"Predictions with NULL entry_price: {c.fetchone()[0]}")
        
        c.execute("SELECT COUNT(*) FROM observation_memory WHERE company_id IS NULL")
        print(f"Observations with NULL company_id: {c.fetchone()[0]}")
        
        c.execute("""
            SELECT asset, created_at, COUNT(*) 
            FROM prediction_ledger 
            GROUP BY asset, created_at 
            HAVING COUNT(*) > 1
        """)
        dups = c.fetchall()
        print(f"Duplicate predictions (asset + created_at): {len(dups)}")

        c.close()
        conn.close()
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    run_verification()
