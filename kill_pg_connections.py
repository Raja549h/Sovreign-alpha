import psycopg2

NEON_URL = "postgresql://neondb_owner:npg_HxbKeITV73Gl@ep-super-art-adot6eyq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

try:
    conn = psycopg2.connect(NEON_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = 'neondb' AND pid <> pg_backend_pid();
    """)
    print("Terminated other connections.")
except Exception as e:
    print(f"Failed: {e}")
