import os
import psycopg2

def run_migration():
    conn_str = os.environ.get('NEON_DB_URL')
    if not conn_str:
        print("Missing NEON_DB_URL")
        return
        
    try:
        conn = psycopg2.connect(conn_str)
        conn.autocommit = True
        c = conn.cursor()
        
        with open('migrate_continuous.sql', 'r') as f:
            sql = f.read()
            
        print("Executing migration...")
        c.execute(sql)
        print("Migration successful.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    run_migration()
