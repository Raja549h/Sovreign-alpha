import os
from dotenv import load_dotenv
import psycopg2

def run_autopsy():
    load_dotenv('c:\\Users\\lokes\\Downloads\\project\\sovereign-alpha\\.env')
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not found.")
        return

    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        c = conn.cursor()
        
        print("--- SCHEMA VERIFICATION: TABLES ---")
        c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in c.fetchall()]
        print(tables)
        
        print("\n--- SCHEMA VERIFICATION: prediction_ledger ---")
        if 'prediction_ledger' in tables:
            c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'prediction_ledger'")
            print(c.fetchall())
            c.execute("SELECT COUNT(*) FROM prediction_ledger")
            print(f"Total Rows: {c.fetchone()[0]}")
            c.execute("SELECT asset, status, created_at FROM prediction_ledger ORDER BY created_at DESC LIMIT 5")
            print("Last 5 rows (asset, status, created_at):")
            for row in c.fetchall():
                print(row)
        else:
            print("Table 'prediction_ledger' not found.")
            
        print("\n--- SCHEMA VERIFICATION: observation_memory ---")
        if 'observation_memory' in tables:
            c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'observation_memory'")
            print(c.fetchall())
            c.execute("SELECT COUNT(*) FROM observation_memory")
            print(f"Total Rows: {c.fetchone()[0]}")
            
            c.execute("""
                SELECT c.ticker, o.created_at, o.observation_text 
                FROM observation_memory o
                LEFT JOIN companies c ON o.company_id = c.id
                ORDER BY o.created_at DESC LIMIT 5
            """)
            print("Last 5 rows (ticker, created_at, observation_text):")
            for row in c.fetchall():
                print(row)
        else:
            print("Table 'observation_memory' not found.")
            
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    run_autopsy()
