import os
import psycopg2
from dotenv import load_dotenv

def run_migrations():
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
        conn.autocommit = True
        c = conn.cursor()

        print("Executing migrations...")
        # Step 5: Verify prediction_ledger Schema
        c.execute("ALTER TABLE prediction_ledger ADD COLUMN IF NOT EXISTS resolved_at TEXT;")
        print("Executed: ALTER TABLE prediction_ledger ADD COLUMN IF NOT EXISTS resolved_at TEXT;")

        # Step 6: Verify observation_memory Schema
        c.execute("ALTER TABLE observation_memory ADD COLUMN IF NOT EXISTS metric_value REAL;")
        print("Executed: ALTER TABLE observation_memory ADD COLUMN IF NOT EXISTS metric_value REAL;")

        c.execute("ALTER TABLE observation_memory ADD COLUMN IF NOT EXISTS metric_name TEXT;")
        print("Executed: ALTER TABLE observation_memory ADD COLUMN IF NOT EXISTS metric_name TEXT;")

        c.execute("ALTER TABLE observation_memory ADD COLUMN IF NOT EXISTS observation_date TEXT;")
        print("Executed: ALTER TABLE observation_memory ADD COLUMN IF NOT EXISTS observation_date TEXT;")

        print("Migrations completed successfully.")
        c.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migrations()
