import os
import sys
import psycopg2
from urllib.parse import urlparse
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def main():
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        print("DATABASE_URL environment variable is not set. Migration skipped.")
        sys.exit(0)

    print("Connecting to the database...")
    try:
        # Add sslmode parameter for Aiven compatibility if not present
        if '?' not in db_url:
            db_url += "?sslmode=require"
        elif "sslmode=" not in db_url:
            db_url += "&sslmode=require"

        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()

        print("Executing migrations...")

        # Alter prediction_ledger to add columns
        alter_statements = [
            "ALTER TABLE prediction_ledger ADD COLUMN IF NOT EXISTS trade_signal VARCHAR(10);",
            "ALTER TABLE prediction_ledger ADD COLUMN IF NOT EXISTS entry_price DECIMAL(10,2);",
            "ALTER TABLE prediction_ledger ADD COLUMN IF NOT EXISTS target_price DECIMAL(10,2);",
            "ALTER TABLE prediction_ledger ADD COLUMN IF NOT EXISTS stop_loss DECIMAL(10,2);",
            "ALTER TABLE prediction_ledger ADD COLUMN IF NOT EXISTS position_size_pct DECIMAL(5,2);"
        ]

        for stmt in alter_statements:
            try:
                cursor.execute(stmt)
                print(f"Executed: {stmt}")
            except psycopg2.Error as e:
                # If column already exists (in older Postgres without IF NOT EXISTS)
                conn.rollback()
                print(f"Skipping alter statement, column might already exist: {e.pgerror}")

        # Clear US tickers from prediction_ledger
        cursor.execute("DELETE FROM prediction_ledger WHERE asset NOT LIKE '%.NS'")
        print("Cleared US tickers from prediction_ledger.")

        # Create alternative_mentions table
        create_stmt = """
        CREATE TABLE IF NOT EXISTS alternative_mentions (
            mention_id SERIAL PRIMARY KEY,
            ticker VARCHAR(10),
            source_type VARCHAR(20),
            source_name VARCHAR(100),
            mention_date TIMESTAMP,
            sentiment_score DECIMAL(3,2),
            excerpt_text TEXT
        );
        """
        cursor.execute(create_stmt)
        print("Executed CREATE TABLE for alternative_mentions.")

        conn.commit()
        print("Migrations completed successfully.")

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        print(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    main()
