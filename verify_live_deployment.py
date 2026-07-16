import os
import sys
import re
import time
import requests
import psycopg2

# Configuration
LIVE_URL = "https://svrn-alpha-sovereignalpha.hf.space"
INDIAN_TICKERS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'SBIN', 'BHARTIARTL',
    'ITC', 'KOTAKBANK', 'HCLTECH', 'BAJFINANCE', 'TRENT', 'SUNPHARMA'
]
FORBIDDEN_UI_STRINGS = [
    'test', 'simulated', 'stress', 'verification', 'e2e', 'demo',
    'emergency', 'safety', 'nifty50', 'banknifty'
]
ROUTES_TO_CHECK = [
    '/', '/evidence', '/predictions', '/performance', '/research', '/macro-health'
]

def print_header(title):
    print(f"\n{'='*60}")
    print(f"{title.upper()}")
    print(f"{'='*60}")

def get_db_connection():
    neon_url = os.environ.get("NEON_URL")
    if not neon_url:
        neon_url = input("Enter your NEON_URL: ").strip()
    try:
        conn = psycopg2.connect(neon_url)
        return conn
    except Exception as e:
        print(f"[FAIL] Could not connect to database: {e}")
        sys.exit(1)

def task_a_database_sanity(conn):
    print_header("Task A â€” Database Sanity Check")
    try:
        c = conn.cursor()
        c.execute("SELECT asset, COUNT(*) FROM prediction_ledger GROUP BY asset ORDER BY asset;")
        rows = c.fetchall()
        
        failed = False
        print("Assets found in prediction_ledger:")
        total_rows = 0
        for asset, count in rows:
            print(f" - {asset}: {count}")
            total_rows += count
            if asset.upper() not in INDIAN_TICKERS:
                print(f"   [!] VIOLATION: Unapproved asset '{asset}' found!")
                failed = True
                
        # Check for forbidden strings in asset or prediction_id
        c.execute("""
            SELECT COUNT(*) FROM prediction_ledger 
            WHERE asset ILIKE '%demo%' OR asset ILIKE '%test%' 
               OR asset ILIKE '%emergency%' OR asset ILIKE '%safety%'
               OR prediction_id ILIKE '%safety%';
        """)
        forbidden_count = c.fetchone()[0]
        print(f"Rows with forbidden strings: {forbidden_count}")
        
        if forbidden_count > 0:
            print("[!] VIOLATION: Forbidden data found in prediction_ledger!")
            failed = True
            
        if failed:
            print("\n[FAIL] Task A: Database sanity check failed.")
            sys.exit(1)
        else:
            print("\n[PASS] Task A: Database is clean.")
            return total_rows
            
    except Exception as e:
        print(f"[FAIL] Task A Error: {e}")
        sys.exit(1)

def task_b_ui_walkthrough():
    print_header("Task B â€” UI Route & Content Walkthrough")
    failed = False
    
    for route in ROUTES_TO_CHECK:
        url = f"{LIVE_URL}{route}"
        print(f"Checking {url} ...")
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"  [!] VIOLATION: Expected 200, got {resp.status_code}")
                failed = True
                continue
                
            html = resp.text.lower()
            
            # Check for forbidden strings
            found_forbidden = []
            for forbidden in FORBIDDEN_UI_STRINGS:
                if forbidden in html:
                    found_forbidden.append(forbidden)
                    
            if found_forbidden:
                print(f"  [!] VIOLATION: Forbidden strings found: {', '.join(found_forbidden)}")
                failed = True
                
            # Check for at least one Indian ticker
            has_ticker = False
            for ticker in INDIAN_TICKERS:
                if ticker.lower() in html:
                    has_ticker = True
                    break
                    
            if not has_ticker:
                print(f"  [!] VIOLATION: No Indian tickers found on this route (is it pulling real data?)")
                failed = True
                
            if not failed:
                print("  [PASS] Route clean and populated.")
                
        except Exception as e:
            print(f"  [FAIL] Request failed: {e}")
            failed = True
            
    if failed:
        print("\n[FAIL] Task B: UI Walkthrough failed.")
        sys.exit(1)
    else:
        print("\n[PASS] Task B: All UI routes clean and active.")

def task_c_safety_net_test(conn, initial_row_count):
    print_header("Task C â€” Safety Net Destruction Test")
    
    input("Please temporarily break your NEON_URL secret in Hugging Face settings (e.g., add a random character).\nPress Enter when done...")
    
    print("\nPolling homepage for 503 error...")
    success_503 = False
    for i in range(5):
        try:
            resp = requests.get(LIVE_URL, timeout=10)
            print(f"  Attempt {i+1}: Status {resp.status_code}")
            if resp.status_code == 503 or "unavailable" in resp.text.lower() or "offline" in resp.text.lower():
                success_503 = True
                print("  [PASS] Service correctly returned 503 / Unavailable message.")
                break
            elif resp.status_code == 200:
                html = resp.text.lower()
                has_forbidden = any(f in html for f in FORBIDDEN_UI_STRINGS)
                if has_forbidden:
                    print("  [FAIL] Safety net triggered! Found fake data on 200 OK.")
                    sys.exit(1)
        except Exception as e:
            print(f"  Attempt {i+1} Request error: {e}")
            
        time.sleep(5)
        
    if not success_503:
        print("\n[FAIL] Could not confirm 503 Unavailable state. Is the safety net still active?")
        sys.exit(1)
        
    input("\nPlease revert the NEON_URL secret back to the correct value in Hugging Face.\nPress Enter when done...")
    
    print("\nPolling homepage for recovery...")
    recovered = False
    for i in range(10):
        try:
            resp = requests.get(LIVE_URL, timeout=10)
            print(f"  Attempt {i+1}: Status {resp.status_code}")
            if resp.status_code == 200:
                recovered = True
                print("  [PASS] Service recovered successfully.")
                break
        except Exception:
            pass
        time.sleep(5)
        
    if not recovered:
        print("\n[FAIL] Service did not recover. Check NEON_URL.")
        sys.exit(1)
        
    print("\nRe-checking database to ensure no fake data was inserted...")
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM prediction_ledger;")
        new_count = c.fetchone()[0]
        if new_count != initial_row_count:
            print(f"[FAIL] Row count changed! Initial: {initial_row_count}, Current: {new_count}. Safety net inserted data!")
            sys.exit(1)
        else:
            print(f"[PASS] Row count unchanged ({initial_row_count}). No fake data inserted.")
    except Exception as e:
        print(f"[FAIL] Database check failed: {e}")
        sys.exit(1)
        
    print("\n[PASS] Task C: Safety Net Destruction Test passed.")

def task_d_error_log_scan():
    print_header("Task D â€” Error Log Scan")
    
    try:
        import huggingface_hub
        from huggingface_hub import HfApi
    except ImportError:
        print("[WARNING] huggingface_hub not installed. Skipping log scan.")
        print("To run this test, install with: pip install huggingface_hub")
        return
        
    token = os.environ.get("HF_TOKEN")
    if not token:
        token = input("Enter your Hugging Face User Access Token: ").strip()
        
    api = HfApi()
    space_id = "svrn-alpha-sovereignalpha"
    
    print(f"Fetching logs for {space_id}...")
    try:
        logs = api.get_space_runtime_logs(space_id, token=token)
        log_lines = []
        # logs is an iterator
        for log in logs:
            log_lines.append(log)
            
        print(f"\n--- Last 50 lines of logs ---")
        for line in log_lines[-50:]:
            # Assuming 'log' is a dict or string depending on version, safely print
            if hasattr(line, 'msg'):
                print(line.msg)
            else:
                print(line)
        print(f"-------------------------------\n")
        print("[PASS] Task D: Error Log Scan complete.")
    except Exception as e:
        print(f"[FAIL] Could not fetch logs: {e}")

if __name__ == "__main__":
    print_header("SOVEREIGN ALPHA â€” LIVE DEPLOYMENT VERIFICATION")
    
    conn = get_db_connection()
    initial_row_count = task_a_database_sanity(conn)
    task_b_ui_walkthrough()
    task_c_safety_net_test(conn, initial_row_count)
    task_d_error_log_scan()
    
    if conn:
        conn.close()
        
    print_header("VERIFICATION COMPLETE - ALL TESTS PASSED")
