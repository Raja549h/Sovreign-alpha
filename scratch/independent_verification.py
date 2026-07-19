import os
import psycopg2
import sys

def mask_url(url):
    if not url: return "NONE"
    if "@" in url:
        start = url.find("://") + 3
        end = url.find("@")
        creds = url[start:end]
        if ":" in creds:
            user = creds.split(":")[0]
            masked_url = url.replace(creds, f"{user}:********")
            return masked_url
    return url

print("--- Step 2: Environment Variable Check ---")
db_url = os.environ.get("DATABASE_URL")
if db_url:
    masked = mask_url(db_url)
    print(f"DATABASE_URL (masked): {masked}")
    print(f"First 40 chars: {masked[:40]}")
else:
    print("DATABASE_URL is missing!")

print("\n--- Step 1: Direct Database Verification ---")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM prediction_ledger;")
    print(f"prediction_ledger count: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM observations;")
    print(f"observations count: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM veto_archive;")
    print(f"veto_archive count: {cur.fetchone()[0]}")

    cur.execute("SELECT status, COUNT(*) FROM prediction_ledger GROUP BY status;")
    print(f"Statuses: {cur.fetchall()}")

    cur.execute("SELECT COUNT(*) FROM prediction_ledger WHERE asset IN ('AMD', 'TSM', 'CVX', 'XOM');")
    print(f"US Tickers (asset in AMD, TSM, CVX, XOM): {cur.fetchone()[0]}")

    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'veto_archive' AND column_name = 'veto_correct';")
    print(f"veto_correct schema: {cur.fetchone()}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"Database Verification Failed: {e}")

print("\n--- Step 3: Application Connection Test ---")
try:
    # Need to add the project root to sys.path to import dashboard.gateway
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from dashboard.gateway import get_db_connection
    
    with get_db_connection() as app_conn:
        cur = app_conn.cursor()
        cur.execute("SELECT 1")
        res = cur.fetchone()[0]
        print(f"Application Connection Test: SUCCESS (SELECT 1 returned {res})")
except Exception as e:
    print(f"Application Connection Test Failed: {e}")

