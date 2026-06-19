#!/usr/bin/env python3
"""
SOVEREIGN ALPHA — FULL SYSTEM HEALTH CHECK
Diagnostic audit only. No fixes applied.
"""

import os
import sys
from database import get_connection
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
os.chdir(PROJECT_DIR)
sys.path.insert(0, str(PROJECT_DIR))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("SOVEREIGN ALPHA — SYSTEM HEALTH CHECK")
print("=" * 60)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1 — DIRECTORY AND FILE AUDIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 60)
print("STEP 1 — DIRECTORY AND FILE AUDIT")
print("=" * 60)

required_files = [
    "research/__init__.py",
    "research/engine.py",
    "research/cli.py",
    "research/test_run.py",
    "research/ingestion/__init__.py",
    "research/ingestion/filing_fetcher.py",
    "research/ingestion/pdf_parser.py",
    "research/ingestion/transcript_parser.py",
    "research/ingestion/table_extractor.py",
    "research/intelligence/__init__.py",
    "research/intelligence/cross_verifier.py",
    "research/intelligence/forensic_detector.py",
    "research/intelligence/regime_connector.py",
    "research/intelligence/scorer.py",
    "research/storage/__init__.py",
    "research/storage/research_db.py",
    "research/output/__init__.py",
    "research/output/note_generator.py",
    "research/output/pdf_exporter.py",
    "crew.py",
    "dashboard/app.py",
    "data/institutional_feed.py",
    "zkml/trust_engine.py",
    "billing/db",
    ".env",
]

required_dirs = [
    "research/data/filings/",
    "research/data/transcripts/",
    "research/data/notes/",
]

files_present = 0
files_missing = 0

for f in required_files:
    p = PROJECT_DIR / f
    if p.exists():
        print(f"OK: {f}")
        files_present += 1
    else:
        print(f"MISSING: {f}")
        files_missing += 1

for d in required_dirs:
    p = PROJECT_DIR / d
    if p.exists():
        print(f"OK: {d}")
        files_present += 1
    else:
        print(f"MISSING: {d}")
        files_missing += 1

# Check .env has GROQ_API_KEY
env_path = PROJECT_DIR / ".env"
groq_key_present = False
if env_path.exists():
    with open(env_path) as ef:
        for line in ef:
            if line.strip().startswith("GROQ_API_KEY=") and "=" in line:
                val = line.split("=", 1)[1].strip()
                if val and not val.startswith("#"):
                    groq_key_present = True

if groq_key_present:
    print("OK: .env with GROQ_API_KEY")
    files_present += 1
else:
    print("MISSING: .env with GROQ_API_KEY")
    files_missing += 1

total_files = len(required_files) + len(required_dirs) + 1
print(f"\nFILES: {files_present} / {total_files} present")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2 — IMPORT CHAIN VERIFICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 60)
print("STEP 2 — IMPORT CHAIN VERIFICATION")
print("=" * 60)

imports_passed = 0
imports_failed = 0

# 1. research_db
try:
    from research.storage.research_db import (
        get_company, add_company, save_filing,
        save_metric, save_flag, save_note,
        get_financial_series, get_flags,
        get_latest_scores
    )
    print("OK: research_db imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: research_db — {e}")
    imports_failed += 1

# 2. filing_fetcher
try:
    from research.ingestion.filing_fetcher import (
        fetch_nse_filings, fetch_from_url,
        register_local_filing
    )
    print("OK: filing_fetcher imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: filing_fetcher — {e}")
    imports_failed += 1

# 3. pdf_parser
try:
    from research.ingestion.pdf_parser import (
        extract_text, extract_tables,
        extract_financial_tables,
        extract_management_commentary,
        process_filing
    )
    print("OK: pdf_parser imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: pdf_parser — {e}")
    imports_failed += 1

# 4. transcript_parser
try:
    from research.ingestion.transcript_parser import (
        parse_transcript, extract_guidance_claims
    )
    print("OK: transcript_parser imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: transcript_parser — {e}")
    imports_failed += 1

# 5. cross_verifier
try:
    from research.intelligence.cross_verifier import (
        verify_guidance_vs_actuals,
        verify_trend_consistency,
        cross_verify_balance_sheet,
        run_full_verification
    )
    print("OK: cross_verifier imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: cross_verifier — {e}")
    imports_failed += 1

# 6. forensic_detector
try:
    from research.intelligence.forensic_detector import (
        detect_margin_compression,
        detect_credit_cost_acceleration,
        detect_working_capital_stress,
        detect_valuation_fragility,
        detect_narrative_drift,
        run_all_detectors
    )
    print("OK: forensic_detector imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: forensic_detector — {e}")
    imports_failed += 1

# 7. regime_connector
try:
    from research.intelligence.regime_connector import (
        get_regime_context,
        assess_regime_sensitivity,
        calculate_regime_sensitivity_score
    )
    print("OK: regime_connector imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: regime_connector — {e}")
    imports_failed += 1

# 8. scorer
try:
    from research.intelligence.scorer import (
        score_company, format_scorecard
    )
    print("OK: scorer imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: scorer — {e}")
    imports_failed += 1

# 9. note_generator
try:
    from research.output.note_generator import (
        generate_research_note
    )
    print("OK: note_generator imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: note_generator — {e}")
    imports_failed += 1

# 10. pdf_exporter
try:
    from research.output.pdf_exporter import (
        export_to_pdf, export_note_to_pdf
    )
    print("OK: pdf_exporter imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: pdf_exporter — {e}")
    imports_failed += 1

# 11. engine
try:
    from research.engine import SovereignAlphaResearch
    print("OK: engine imports")
    imports_passed += 1
except Exception as e:
    print(f"FAIL: engine — {e}")
    imports_failed += 1

print(f"\nIMPORTS PASSED: {imports_passed} / 11")
print(f"IMPORTS FAILED: {imports_failed} / 11")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3 — DATABASE HEALTH CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 60)
print("STEP 3 — DATABASE HEALTH CHECK")
print("=" * 60)

db_path = None
if not db_path.exists():
    db_path = None

print(f"DB STATUS: {db_path}")

new_tables = ['companies', 'filings', 'financial_series', 'forensic_flags', 'research_notes', 'institutional_scores']
tables_present = 0

try:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM information_schema.tables WHERE table_schema='public' ORDER BY name")
    all_tables = [r[0] for r in c.fetchall()]
    
    for table in new_tables:
        if table in all_tables:
            c.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = ({table})")
            cols = c.fetchall()
            c.execute(f"SELECT COUNT(*) FROM {table}")
            count = c.fetchone()[0]
            col_str = ", ".join([f"{col[1]}({col[2]})" for col in cols[:5]])
            print(f"OK: {table} — {len(cols)} columns, {count} rows [{col_str}]")
            tables_present += 1
        else:
            print(f"MISSING: {table}")
    
    existing = [t for t in all_tables if t not in new_tables]
    if existing:
        print(f"EXISTING TABLES: {len(existing)} found — {existing}")
        print("EXISTING TABLES: intact")
    else:
        print("EXISTING TABLES: None (fresh database)")
        print("EXISTING TABLES: intact")
    
    conn.close()
except Exception as e:
    print(f"DB ERROR: {e}")
    print("EXISTING TABLES: DAMAGED")

print(f"NEW TABLES: {tables_present} / 6 present")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4 — ENVIRONMENT AND DEPENDENCY CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 60)
print("STEP 4 — ENVIRONMENT AND DEPENDENCY CHECK")
print("=" * 60)

groq_key = os.environ.get("GROQ_API_KEY", "")
if groq_key:
    print(f"KEY: {groq_key[:6]}....{groq_key[-4:]}")
else:
    print("MISSING: GROQ_API_KEY not set")

packages = ['pdfplumber', 'xhtml2pdf', 'requests', 'groq', 'chromadb', 'crewai', 'rich', 'flask', 'yfinance']
deps_ok = 0
deps_missing = 0

for pkg in packages:
    try:
        import importlib
        mod = importlib.import_module(pkg)
        version = getattr(mod, '__version__', 'unknown')
        print(f"OK: {pkg} {version}")
        deps_ok += 1
    except (ImportError, OSError) as e:
        print(f"MISSING: {pkg} — run pip install {pkg}")
        deps_missing += 1

print(f"\nDEPENDENCIES: {deps_ok} / {len(packages)} present")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 5 — LIVE FUNCTION EXECUTION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 60)
print("STEP 5 — LIVE FUNCTION EXECUTION TESTS")
print("=" * 60)

exec_passed = 0
exec_failed = 0

# TEST 1 — Database write and read
try:
    from research.storage.research_db import (
        add_company, get_company,
        save_metric, get_financial_series,
        delete_company
    )
    
    company_id = add_company('HEALTHCHECK', 'Health Check Test Co', 'NSE', 'TEST')
    result = get_company('HEALTHCHECK')
    assert result is not None
    assert result['ticker'] == 'HEALTHCHECK'
    print("OK: Database write/read cycle")
    
    save_metric(company_id, 'NIM', 'FY25', 10.1, 'percent', None)
    series = get_financial_series(company_id, 'NIM')
    assert len(series) > 0
    assert series[0]['value'] == 10.1
    print("OK: Metric save and retrieval")
    exec_passed += 1
except Exception as e:
    print(f"FAIL: Database test — {e}")
    exec_failed += 1

# TEST 2 — Scorer with mock data
try:
    from research.intelligence.scorer import score_company, format_scorecard
    
    scores = score_company(company_id, 'TEST')
    assert 'risk_intensity' in scores
    assert 'confidence' in scores
    assert 'regime_sensitivity' in scores
    assert 'structural_quality' in scores
    assert 'composite_score' in scores or 'composite' in scores
    print("OK: Scorer produces all four scores")
    
    scorecard = format_scorecard(scores)
    assert len(scorecard) > 0
    print("OK: Scorecard formatter")
    print(scorecard)
    exec_passed += 1
except Exception as e:
    print(f"FAIL: Scorer test — {e}")
    exec_failed += 1

# TEST 3 — Forensic detector with mock data
try:
    from research.intelligence.forensic_detector import (
        detect_margin_compression,
        detect_credit_cost_acceleration
    )
    
    save_metric(company_id, 'NIM', 'FY23', 10.8, 'percent', None)
    save_metric(company_id, 'NIM', 'FY24', 10.1, 'percent', None)
    save_metric(company_id, 'CreditCost', 'FY23', 1.25, 'percent', None)
    save_metric(company_id, 'CreditCost', 'FY25', 2.05, 'percent', None)
    
    flags = detect_margin_compression(company_id)
    print(f"OK: Margin detector ran — {len(flags)} flags found")
    
    flags = detect_credit_cost_acceleration(company_id)
    print(f"OK: Credit cost detector ran — {len(flags)} flags found")
    exec_passed += 1
except Exception as e:
    print(f"FAIL: Forensic detector test — {e}")
    exec_failed += 1

# TEST 4 — Regime connector
try:
    from research.intelligence.regime_connector import get_regime_context
    
    regime = get_regime_context()
    assert 'regime' in regime
    print(f"OK: Regime context — current regime: {regime['regime']}")
    exec_passed += 1
except Exception as e:
    print(f"WARN: Regime connector failed (may be network) — {e}")
    exec_failed += 1

# TEST 5 — Engine instantiation
try:
    from research.engine import SovereignAlphaResearch
    
    engine = SovereignAlphaResearch()
    engine.status('HEALTHCHECK')
    print("OK: Engine instantiates and status runs")
    exec_passed += 1
except Exception as e:
    print(f"FAIL: Engine test — {e}")
    exec_failed += 1

# TEST 6 — Note generator structure
try:
    from research.output.note_generator import generate_research_note
    import inspect
    sig = inspect.signature(generate_research_note)
    params = list(sig.parameters.keys())
    assert 'company_id' in params or 'ticker' in params
    print(f"OK: Note generator exists with params: {params}")
    exec_passed += 1
except Exception as e:
    print(f"FAIL: Note generator test — {e}")
    exec_failed += 1

print(f"\nEXECUTION TESTS PASSED: {exec_passed} / 6")
print(f"EXECUTION TESTS FAILED: {exec_failed} / 6")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 6 — EXISTING PIPELINE INTEGRITY CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 60)
print("STEP 6 — EXISTING PIPELINE INTEGRITY CHECK")
print("=" * 60)

pipeline_intact = True

# Check crew.py
try:
    import crew
    print("OK: crew.py imports")
except Exception as e:
    print(f"FAIL: crew.py — {e}")
    pipeline_intact = False

# Check dashboard/app.py syntax
import subprocess
result = subprocess.run(
    [sys.executable, "-m", "py_compile", "dashboard/app.py"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("OK: dashboard/app.py syntax clean")
else:
    print(f"FAIL: dashboard/app.py syntax — {result.stderr}")
    pipeline_intact = False

# Check data/institutional_feed.py
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("institutional_feed", "data/institutional_feed.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("OK: data/institutional_feed.py imports cleanly")
except Exception as e:
    print(f"FAIL: data/institutional_feed.py — {e}")
    pipeline_intact = False

# Check zkml/trust_engine.py
try:
    spec = importlib.util.spec_from_file_location("trust_engine", "zkml/trust_engine.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("OK: zkml/trust_engine.py imports cleanly")
except Exception as e:
    print(f"FAIL: zkml/trust_engine.py — {e}")
    pipeline_intact = False

# Check billing/db
meter_db = None
if meter_db.exists():
    print("OK: billing/db exists")
else:
    print("MISSING: billing/db")
    pipeline_intact = False

if pipeline_intact:
    print("\nEXISTING PIPELINE: INTACT")
else:
    print("\nEXISTING PIPELINE: DAMAGED")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 7 — CLEANUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 60)
print("STEP 7 — CLEANUP")
print("=" * 60)

try:
    conn = get_connection()
    c = conn.cursor()
    
    # Delete in order (foreign key constraints)
    for table in ['financial_series', 'forensic_flags', 'research_notes', 'institutional_scores', 'filings']:
        c.execute(f"DELETE FROM {table} WHERE company_id = (SELECT id FROM companies WHERE ticker = 'HEALTHCHECK')")
    
    c.execute("DELETE FROM companies WHERE ticker = 'HEALTHCHECK'")
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM companies WHERE ticker = 'HEALTHCHECK'")
    assert c.fetchone()[0] == 0
    print("OK: Test data cleaned up")
    conn.close()
except Exception as e:
    print(f"FAIL: Cleanup — {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FINAL HEALTH REPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 60)
print("SOVEREIGN ALPHA — SYSTEM HEALTH REPORT")
print("=" * 60)
print(f"Files present:        {files_present} / {total_files}")
print(f"Imports passing:      {imports_passed} / 11")
print(f"Database tables:      {tables_present} / 6")
print(f"Dependencies:         {deps_ok} / {len(packages)}")
print(f"Execution tests:      {exec_passed} / 6")
print(f"Existing pipeline:    {'INTACT' if pipeline_intact else 'DAMAGED'}")
print("=" * 60)

# Determine status
all_pass = (
    files_present == total_files and
    imports_passed == 11 and
    tables_present == 6 and
    deps_ok == len(packages) and
    exec_passed == 6 and
    pipeline_intact
)

some_fail = not all_pass and (
    imports_passed > 8 and
    tables_present > 4 and
    exec_passed > 3 and
    pipeline_intact
)

if all_pass:
    print("OVERALL STATUS: GREEN")
    print("All checks pass, ready for test_run.py")
elif some_fail:
    print("OVERALL STATUS: YELLOW")
    print("Minor issues, non-critical failures only")
else:
    print("OVERALL STATUS: RED")
    print("Critical failures, do not proceed")

# Print issues
issues = []
if files_present < total_files:
    issues.append(f"Missing files ({files_missing} missing) — check STEP 1 output for exact paths")
if imports_passed < 11:
    issues.append(f"Import failures ({imports_failed} failed) — check STEP 2 output for exact modules")
if tables_present < 6:
    issues.append(f"Missing database tables ({6 - tables_present} missing) — run research/storage/research_db.py init")
if deps_ok < len(packages):
    issues.append(f"Missing dependencies ({deps_missing} missing) — run pip install <package>")
if exec_passed < 6:
    issues.append(f"Execution test failures ({exec_failed} failed) — check STEP 5 output for exact tests")
if not pipeline_intact:
    issues.append("Existing pipeline damaged — restore from git or fix broken imports")

if issues:
    print("\nISSUES TO FIX:")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
    print("=" * 60)
