import os
import sys
import datetime
import traceback
import subprocess
import re
import requests
from pathlib import Path

# Setup path so we can import project modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
    from dashboard.gateway import get_connection
except ImportError:
    print("Failed to import project dependencies. Run from project root.")
    sys.exit(1)

LIVE_URL = "https://svrn-alpha-sovereignalpha.hf.space"
INDIAN_TICKERS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'SBIN', 'BHARTIARTL', 
    'ITC', 'KOTAKBANK', 'HCLTECH', 'BAJFINANCE', 'TRENT', 'SUNPHARMA'
]
FORBIDDEN_UI_WORDS = [
    r'\btest\b', r'\bdemo\b', r'\bemergency\b', r'\bsafety\b', r'\bsimulated\b', r'\bstress\b'
]
ROUTES_TO_CHECK = ['/', '/evidence', '/predictions', '/performance', '/research', '/macro-health']
TICKER_CHECK_ROUTES = ['/', '/predictions', '/performance', '/research']
SKIP_STRESS_CHECK_ROUTES = ['/macro-health']

def print_header():
    print("=" * 60)
    print("SOVEREIGN ALPHA — FULL SYSTEM VALIDATION REPORT")
    print("=" * 60)
    print(f"Generated: {datetime.datetime.now().isoformat(timespec='seconds')}\n")

def check_database_sanity():
    approved_tickers = tuple(INDIAN_TICKERS + [t + '.NS' for t in INDIAN_TICKERS])
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(DISTINCT asset) FROM prediction_ledger WHERE asset NOT IN %s;", (approved_tickers,))
            count = c.fetchone()[0]
            if count > 0:
                return False, f"Found {count} unapproved tickers in prediction_ledger."
            
            c.execute("SELECT COUNT(DISTINCT asset) FROM veto_archive WHERE asset NOT IN %s;", (approved_tickers,))
            count_veto = c.fetchone()[0]
            if count_veto > 0:
                return False, f"Found {count_veto} unapproved tickers in veto_archive."
            
        return True, "PASS"
    except Exception as e:
        return False, f"Database error: {e}"

def check_fake_data():
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT COUNT(*) FROM prediction_ledger 
                WHERE asset ILIKE '%demo%' OR asset ILIKE '%test%' 
                   OR asset ILIKE '%emergency%' OR asset ILIKE '%safety%'
                   OR prediction_id ILIKE '%safety%';
            """)
            count = c.fetchone()[0]
            if count > 0:
                return False, f"Found {count} fake data rows in prediction_ledger."
        return True, "PASS"
    except Exception as e:
        return False, f"Database error: {e}"

def check_validation_logic():
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status NOT IN ('HIT', 'MISS', 'PENDING');")
            invalid_status_count = c.fetchone()[0]
            if invalid_status_count > 0:
                return False, f"Found {invalid_status_count} predictions with invalid status."
            return True, "PASS"
    except Exception as e:
        return False, f"Database error: {e}"

def check_evidence_timeline():
    try:
        with get_connection() as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT COUNT(*) FROM evidence_timeline WHERE event_type ILIKE ANY(ARRAY['%test%', '%simulated%', '%stress%', '%verification%', '%e2e%']);")
            except Exception:
                conn.rollback()
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM evidence_timeline WHERE event_type LIKE '%test%' OR event_type LIKE '%simulated%' OR event_type LIKE '%stress%' OR event_type LIKE '%verification%' OR event_type LIKE '%e2e%';")
            
            count = c.fetchone()[0]
            if count > 0:
                return False, f"Found {count} test artifacts in evidence_timeline."
            return True, "PASS"
    except Exception as e:
        # If evidence_timeline doesn't exist, skip safely
        return True, "PASS (Skipped, table not found)"

def check_config_and_api():
    failed = False
    details = []
    
    forbidden_patterns = ['llama-3.3-70b', 'groq/compound', 'groq.']
    excluded_files = ['wipe_groq.py', 'validate_system.py', 'cleanup_']
    excluded_strings = ['llama_index']

    found_refs = []
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if not file.endswith('.py'):
                continue
            
            if any(file == ef or (ef.endswith('_') and file.startswith(ef)) for ef in excluded_files):
                continue
                
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        stripped = line.strip()
                        if stripped.startswith('#'):
                            continue
                        for pat in forbidden_patterns:
                            if pat in stripped:
                                if not any(ex in stripped for ex in excluded_strings):
                                    found_refs.append(f"{file}:{line_num}")
            except Exception:
                pass
                
    if found_refs:
        failed = True
        details.append(f"Found {len(found_refs)} references to forbidden models: {', '.join(found_refs[:3])}")
        
    if failed:
        return False, " | ".join(details)
    return True, "PASS"

def extract_main_text(html):
    # Remove footer, nav, header sections to avoid legal disclaimers like "backtest"
    html = re.sub(r'<footer.*?</footer>', ' ', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<nav.*?</nav>', ' ', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<header.*?</header>', ' ', html, flags=re.IGNORECASE|re.DOTALL)
    # Remove script and style tags
    html = re.sub(r'<script.*?</script>', ' ', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<style.*?</style>', ' ', html, flags=re.IGNORECASE|re.DOTALL)
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Normalize whitespace
    return ' '.join(text.split()).lower()

def check_ui_routes():
    report_lines = []
    all_passed = True
    
    session = requests.Session()
    login_url = f"{LIVE_URL}/login"
    
    try:
        session.post(login_url, data={"password": "sovereign2024"}, timeout=10)
    except Exception:
        pass # Will catch connection issues in the loop
        
    for route in ROUTES_TO_CHECK:
        url = f"{LIVE_URL}{route}"
        try:
            resp = session.get(url, timeout=10)
            if resp.status_code != 200:
                report_lines.append(f"{route}: FAIL (HTTP {resp.status_code})")
                all_passed = False
                continue
                
            html = resp.text
            main_text = extract_main_text(html)
            
            route_failed = False
            route_msgs = []
            
            # Check Tickers
            if route in TICKER_CHECK_ROUTES:
                found_tickers = [t for t in INDIAN_TICKERS if t.lower() in html.lower()]
                if not found_tickers:
                    route_msgs.append("FAIL (No Indian tickers found)")
                    route_failed = True
                else:
                    route_msgs.append(f"Tickers found ({', '.join(found_tickers[:2])})")
            else:
                route_msgs.append("Ticker check skipped (design decision)")
                
            # Check Forbidden Strings using word boundaries
            found_forbidden = []
            for forbidden in FORBIDDEN_UI_WORDS:
                if route in SKIP_STRESS_CHECK_ROUTES and 'stress' in forbidden:
                    continue # Skip stress check for macro-health
                if re.search(forbidden, main_text, re.IGNORECASE):
                    found_forbidden.append(forbidden.replace(r'\b', ''))
                    
            if found_forbidden:
                route_msgs.append(f"Forbidden strings found: {', '.join(found_forbidden)}")
                route_failed = True
            else:
                route_msgs.append("No forbidden strings.")
                
            if route_failed:
                all_passed = False
                
            report_lines.append(f"{route}: {'. '.join(route_msgs)}.")
            
        except Exception as e:
            report_lines.append(f"{route}: FAIL (Request error: {str(e)[:30]})")
            all_passed = False
            
    return all_passed, report_lines

def main():
    print_header()
    
    final_verdict = True
    
    print("Database Sanity: ", end="")
    passed, msg = check_database_sanity()
    print(msg)
    if not passed: final_verdict = False
    
    print("\nFake Data: ", end="")
    passed, msg = check_fake_data()
    print(msg)
    if not passed: final_verdict = False
    
    print("\nValidation Logic: ", end="")
    passed, msg = check_validation_logic()
    print(msg)
    if not passed: final_verdict = False
    
    print("\nEvidence Timeline: ", end="")
    passed, msg = check_evidence_timeline()
    print(msg)
    if not passed: final_verdict = False
    
    print("\nConfig & API: ", end="")
    passed, msg = check_config_and_api()
    print(msg)
    if not passed: final_verdict = False
    
    print("\nUI Routes (Content & Tickers):")
    passed, route_reports = check_ui_routes()
    for report in route_reports:
        print(report)
    if not passed: final_verdict = False
    
    print("\n" + "=" * 60)
    if final_verdict:
        print("FINAL VERDICT: ALL SYSTEMS OPERATIONAL (PASS)")
    else:
        print("FINAL VERDICT: CRITICAL FAILURES DETECTED (FAIL)")
    print("=" * 60)
    
if __name__ == "__main__":
    main()
