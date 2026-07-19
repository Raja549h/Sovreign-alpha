import os
import sys
import psycopg2
from psycopg2.extras import execute_values

def fetch_table_data(cur, table_name):
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return columns, rows

def insert_data(cur, table_name, columns, rows):
    if not rows:
        print(f"  No data to insert for {table_name}.")
        return

    # Build the INSERT statement dynamically
    cols_str = ", ".join(columns)
    # Use %s for psycopg2
    template = "(" + ", ".join(["%s"] * len(columns)) + ")"
    
    print(f"  Inserting {len(rows)} rows into {table_name}...")
    
    # Truncate first to ensure clean migration, CASCADE will handle foreign keys if any
    try:
        cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
    except psycopg2.errors.UndefinedTable:
        # If the table doesn't exist, we must initialize the database schema first.
        # But assuming the destination has the schema set up by app startup.
        print(f"  WARNING: Table {table_name} does not exist on destination. Schema initialization may be required.")
        raise
    
    query = f"INSERT INTO {table_name} ({cols_str}) VALUES %s"
    execute_values(cur, query, rows)

def main():
    neon_url = os.environ.get("NEON_URL")
    aiven_url = os.environ.get("AIVEN_URL")
    
    if not neon_url:
        print("CRITICAL: NEON_URL environment variable is missing.")
        sys.exit(1)
    if not aiven_url:
        print("CRITICAL: AIVEN_URL environment variable is missing.")
        sys.exit(1)

    tables_to_migrate = [
        "prediction_ledger",
        "observations",
        "veto_archive"
    ]

    print("=== Sovereign Alpha: Pure-Python Database Migration ===")
    
    # Connect to both databases
    try:
        print("\nConnecting to Neon (Source)...")
        neon_conn = psycopg2.connect(neon_url, connect_timeout=10)
        neon_cur = neon_conn.cursor()
        print("Success.")
    except Exception as e:
        print(f"FAILED to connect to Neon: {e}")
        sys.exit(1)
        
    try:
        print("\nConnecting to Aiven (Destination)...")
        aiven_conn = psycopg2.connect(aiven_url, connect_timeout=10)
        aiven_cur = aiven_conn.cursor()
        print("Success.")
    except Exception as e:
        print(f"FAILED to connect to Aiven: {e}")
        sys.exit(1)

    # Perform the migration
    try:
        for table in tables_to_migrate:
            print(f"\nMigrating table: {table}")
            
            # Fetch from Neon
            columns, rows = fetch_table_data(neon_cur, table)
            print(f"  Fetched {len(rows)} rows from Neon.")
            
            # Insert into Aiven
            insert_data(aiven_cur, table, columns, rows)
            
        # Commit changes to Aiven
        aiven_conn.commit()
        print("\nMigration committed successfully!")
        
    except Exception as e:
        print(f"\nERROR during migration: {e}")
        aiven_conn.rollback()
        sys.exit(1)
    finally:
        neon_cur.close()
        neon_conn.close()

    # Verification
    print("\nVerifying data on Aiven...")
    try:
        for table in tables_to_migrate:
            aiven_cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = aiven_cur.fetchone()[0]
            print(f"  [Verified] {table} row count: {count}")
    except Exception as e:
        print(f"FAILED verification query: {e}")
    finally:
        aiven_cur.close()
        aiven_conn.close()

if __name__ == "__main__":
    main()
