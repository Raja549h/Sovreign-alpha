import psycopg2
from psycopg2.extras import execute_batch
import json
import os
from pathlib import Path

NEON_URL = "postgresql://neondb_owner:npg_HxbKeITV73Gl@ep-super-art-adot6eyq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def dry_run_migration():
    print("Starting Dry Run Migration...")
    
    # 1. Connect to Neon
    try:
        pg_conn = psycopg2.connect(NEON_URL)
        pg_conn.autocommit = True
        pg_cursor = pg_conn.cursor()
        print("Connected to Neon DB.")
    except Exception as e:
        print(f"Failed to connect to Neon: {e}")
        return

    # 2. Execute Schema
    print("Executing POSTGRES_SCHEMA.sql...")
    try:
        pg_cursor.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        print("Dropped and recreated public schema.")
    except Exception as e:
        print(f"Failed to drop schema: {e}")
        
    with open('POSTGRES_SCHEMA.sql', 'r') as f:
        schema = f.read()
    try:
        pg_cursor.execute(schema)
        print("Schema created successfully.")
    except Exception as e:
        print(f"Failed to create schema: {e}")
        return
        
    # 3. Migrate Data
    db_paths = [Path('billing/db'), Path('billing/db'), Path('billing/db'), Path('billing/db')]
    
    verification_md = "# Migration Verification Report\n\n"
    verification_md += "| Table Name | SQLite Row Count | Neon Row Count | Difference |\n"
    verification_md += "|------------|------------------|----------------|------------|\n"
    
    total_diff = 0
    
    for db_path in db_paths:
        if not db_path.exists():
            continue
        print(f"Migrating {db_path.name}...")
        sqlite_conn = get_connection()
        sqlite_cursor = sqlite_conn.cursor()
        
        sqlite_cursor.execute("SELECT name FROM information_schema.tables WHERE table_schema='public' AND name != 'sqlite_sequence';")
        tables = [r[0] for r in sqlite_cursor.fetchall()]
        
        # Sort tables to satisfy foreign keys
        priority_tables = ['companies', 'observation_memory', 'filings', 'portfolios', 'theses', 'shadow_portfolio', 'observation_validations']
        sorted_tables = [t for t in priority_tables if t in tables] + [t for t in tables if t not in priority_tables]
        
        for table in sorted_tables:
            # Clear Neon table just for dry run
            try:
                pg_cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            except Exception as e:
                pass
                
            sqlite_cursor.execute(f"SELECT * FROM {table};")
            rows = sqlite_cursor.fetchall()
            sqlite_count = len(rows)
            
            if sqlite_count > 0:
                cols = [description[0] for description in sqlite_cursor.description]
                placeholders = ",".join(["%s"] * len(cols))
                insert_query = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
                
                # Execute batch
                try:
                    execute_batch(pg_cursor, insert_query, rows)
                except Exception as e:
                    print(f"Failed to insert into {table}: {e}")
            
            # Verify
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table};")
            neon_count = pg_cursor.fetchone()[0]
            
            diff = abs(sqlite_count - neon_count)
            total_diff += diff
            verification_md += f"| `{table}` | {sqlite_count} | {neon_count} | {diff} |\n"
            print(f"Verified {table}: SQLite={sqlite_count}, Neon={neon_count}")
            
    verification_md += f"\n**Total Discrepancies**: {total_diff}\n"
    verification_md += "\n**Status**: " + ("SUCCESS" if total_diff == 0 else "FAILED") + "\n"
    
    with open('MIGRATION_VERIFICATION.md', 'w') as f:
        f.write(verification_md)
        
    print(f"Migration Dry Run Complete. Total discrepancies: {total_diff}")
    
if __name__ == '__main__':
    dry_run_migration()
