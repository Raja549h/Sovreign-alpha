import os
import psycopg2
from dotenv import load_dotenv

def purge_duplicate_active_trades():
    load_dotenv()
    url = os.environ.get('DATABASE_URL') or os.environ.get('AIVEN_DATABASE_URL')
    if not url:
        print("Error: DATABASE_URL not found.")
        return
        
    print("Connecting to database...")
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    # Check total active before
    cur.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'active'")
    before_count = cur.fetchone()[0]
    print(f"Active trades before purge: {before_count}")
    
    # Delete duplicates (keeping the one with the smallest id, which is the oldest)
    delete_query = """
    DELETE FROM prediction_ledger
    WHERE status = 'active'
    AND id NOT IN (
        SELECT MIN(id)
        FROM prediction_ledger
        WHERE status = 'active'
        GROUP BY asset
    )
    """
    cur.execute(delete_query)
    deleted_count = cur.rowcount
    
    # Check total active after
    cur.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'active'")
    after_count = cur.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    print(f"Purged {deleted_count} duplicate active trades.")
    print(f"Active trades remaining: {after_count}")

if __name__ == '__main__':
    purge_duplicate_active_trades()
