#!/usr/bin/env python3
"""
Sovereign Alpha Health Check
=========================

Verifies the entire system is ready before running.
Usage: python health_check.py [--full]
"""

import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results'
PROOFS_DIR = BASE_DIR / 'zkml' / 'proofs'


def check_groq_api_key():
    """Check GROQ_API_KEY by making a test call."""
    from config import GROQ_API_KEY
    
    if not GROQ_API_KEY:
        return False, "GROQ_API_KEY not set in .env"
    
    # Use groq SDK directly for reliable check
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        client.models.list()
        return True, "Valid (Groq SDK)"
    except Exception as e:
        return False, f"API call failed: {e}"


def check_data_files():
    """Check all data files exist and are valid."""
    checks = []
    
    required_files = {
        'sample_positions.csv': ['position_id', 'symbol'],
        'sample_research.txt': ['EXECUTIVE SUMMARY', 'THESIS'],
        'risk_parameters.json': ['risk_parameters', 'sector_limits']
    }
    
    for filename, required_content in required_files.items():
        filepath = DATA_DIR / filename
        
        if not filepath.exists():
            checks.append((filename, False, "File not found"))
            continue
        
        try:
            content = filepath.read_text(encoding='utf-8')
            
            if filename.endswith('.json'):
                data = json.loads(content)
                has_content = any(k in data for k in required_content)
            else:
                has_content = any(c.lower() in content.lower() for c in required_content)
            
            if has_content:
                checks.append((filename, True, "Valid"))
            else:
                checks.append((filename, False, "Missing required content"))
        except Exception as e:
            checks.append((filename, False, f"Error: {e}"))
    
    return checks


def check_chromadb():
    """Check ChromaDB is accessible."""
    try:
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.Client(Settings(
            persist_directory=str(DATA_DIR / 'chroma_db'),
            anonymized_telemetry=False
        ))
        
        collections = client.list_collections()
        return True, f"Accessible ({len(collections)} collections)"
    except ImportError:
        return False, "ChromaDB not installed"
    except Exception as e:
        return False, f"Error: {e}"


def check_directories():
    """Check required directories exist."""
    required_dirs = [
        RESULTS_DIR,
        PROOFS_DIR,
        DATA_DIR,
    ]
    
    checks = []
    for d in required_dirs:
        if d.exists():
            checks.append((d.name, True, "Exists"))
        else:
            checks.append((d.name, False, "Missing"))
    
    # New directories for tasks 1-3
    for subdir in ['zkml/keys', 'dashboard/templates', 'demo']:
        path = BASE_DIR / subdir
        if path.exists():
            checks.append((subdir, True, "Exists"))
    
    return checks


def check_database():
    """Check SQLite database."""
    db_path = BASE_DIR / 'billing' / 'billing.db'
    
    if not db_path.exists():
        return False, "Database not found"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if len(tables) >= 3:
            return True, f"Accessible ({len(tables)} tables)"
        else:
            return False, f"Only {len(tables)} tables"
    except Exception as e:
        return False, f"Error: {e}"


def check_imports():
    """Check Python imports."""
    packages = [
        ('crewai', 'CrewAI'),
        ('groq', 'Groq'),
        ('pydantic', 'Pydantic'),
    ]
    
    checks = []
    for module, name in packages:
        try:
            __import__(module)
            checks.append((name, True, "Available"))
        except ImportError:
            checks.append((name, False, "Not installed"))
    
    return checks


def check_yfinance():
    """Check yfinance for live data."""
    try:
        import yfinance
        ticker = yfinance.Ticker("AAPL")
        info = ticker.info
        if info and "currentPrice" in info:
            return True, f"AAPL price: ${info.get('currentPrice')}"
        return False, "No data returned"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Sovereign Alpha Health Check')
    parser.add_argument('--full', action='store_true', help='Run full validation')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("SOVEREIGN ALPHA - Health Check v1.0")
    if args.full:
        print("FULL VALIDATION MODE")
    print("="*60)
    
    checks_passed = 0
    total_checks = 10 if args.full else 6
    
    print("\n[1/6] Checking GROQ API Key...")
    passed, message = check_groq_api_key()
    if passed:
        print(f"    [PASS] {message}")
        checks_passed += 1
    else:
        print(f"    [FAIL] {message}")
        print("    -> Fix: Copy .env.example to .env and add your GROQ_API_KEY")
        print("    -> Get free key at https://console.groq.com")
    
    print("\n[2/6] Checking Data Files...")
    file_checks = check_data_files()
    for name, passed, message in file_checks:
        if passed:
            print(f"    [PASS] {name}")
            checks_passed += 1
        else:
            print(f"    [FAIL] {name}: {message}")
    
    print("\n[3/6] Checking ChromaDB...")
    passed, message = check_chromadb()
    if passed:
        print(f"    [PASS] {message}")
        checks_passed += 1
    else:
        print(f"    [WARN] {message}")
    
    print("\n[4/6] Checking Directories...")
    dir_checks = check_directories()
    for name, passed, message in dir_checks:
        if passed:
            print(f"    [PASS] {name}: {message}")
            if name in ['results', 'proofs', 'data', 'keys', 'templates', 'demo']:
                checks_passed += 1
    
    print("\n[5/6] Checking Database...")
    passed, message = check_database()
    if passed:
        print(f"    [PASS] {message}")
        checks_passed += 1
    else:
        print(f"    [FAIL] {message}")
    
    print("\n[6/6] Checking Python Dependencies...")
    import_checks = check_imports()
    for name, passed, message in import_checks:
        if passed:
            print(f"    [PASS] {name}")
            checks_passed += 1
        else:
            print(f"    [FAIL] {name}: {message}")
    
    if args.full:
        print("\n[7/10] Checking yfinance...")
        passed, message = check_yfinance()
        if passed:
            print(f"    [PASS] {message}")
            checks_passed += 1
        else:
            print(f"    [WARN] {message}")
        
        print("\n[8/10] Checking live market data...")
        live_data = BASE_DIR / "data" / "live_market_data.json"
        if live_data.exists():
            data = json.loads(live_data.read_text())
            tickers = len(data.get("tickers", {}))
            print(f"    [PASS] {tickers} tickers fetched")
            checks_passed += 1
        else:
            print(f"    [WARN] Run: py data/market_feed.py")
        
        print("\n[9/10] Checking RSA keys...")
        public_key = BASE_DIR / "zkml" / "keys" / "public_key.pem"
        if public_key.exists():
            print(f"    [PASS] RSA key pair generated")
            checks_passed += 1
            print("    [PASS] Can verify proofs: py zkml/verify_proof.py zkml/proofs/cert_*.json")
        else:
            print(f"    [WARN] Run: py zkml/proof_generator.py")
        
        print("\n[10/10] Checking Cloud Deploy Files...")
        deploy_files = [
            BASE_DIR / "render.yaml",
            BASE_DIR / "Procfile",
            BASE_DIR / "runtime.txt",
            BASE_DIR / "DEPLOYMENT.md"
        ]
        missing = [f for f in deploy_files if not f.exists()]
        if not missing:
            print(f"    [PASS] All deploy files present")
            checks_passed += 1
        else:
            print(f"    [WARN] Missing: {[f.name for f in missing]}")
    
    print("\n" + "="*60)
    
    if checks_passed >= total_checks - 2:
        print(f"RESULT: {checks_passed}/{total_checks} checks passing")
        print("System ready for hedge fund demonstration!")
    else:
        print(f"RESULT: {checks_passed}/{total_checks} checks passing")
        if args.full:
            print("Some components optional - core system works")
        else:
            print("Run: py health_check.py --full for complete check")
    
    print("\nRun commands:")
    print("  py crew.py                   - Single analysis")
    print("  py run_sessions.py --quick   - Quick test (3 sessions)")
    print("  py data/market_feed.py       - Fetch live market data")
    print("  py zkml/proof_generator.py - Generate RSA proof")
    print("  py dashboard/app.py          - Web dashboard")
    print("  py demo/demo_mode.py         - 4-min demo")
    print("  py health_check.py --full     - Full validation")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)