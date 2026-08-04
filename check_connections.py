import os
import psycopg2
from dotenv import load_dotenv

def check_connections():
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    if not db_url: return
    db_url = db_url.strip()
    if 'sslmode=require' not in db_url:
        db_url += '&sslmode=require' if '?' in db_url else '?sslmode=require'

    try:
        conn = psycopg2.connect(db_url)
        c = conn.cursor()
        
        c.execute("SHOW max_connections")
        max_conn = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM pg_stat_activity")
        current_conn = c.fetchone()[0]
        
        print(f"Max Connections: {max_conn}")
        print(f"Current Connections: {current_conn}")
        
        c.close()
        conn.close()
    except Exception as e:
        print(f"Error checking connections: {e}")

if __name__ == "__main__":
    check_connections()
