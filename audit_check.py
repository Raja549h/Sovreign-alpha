"""
SOVEREIGN ALPHA - INTERNAL AUDIT DIVISION
Automated forensic audit: schema, data integrity, code quality, security.
"""
import sqlite3, json, os, sys, hashlib, importlib, inspect, re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
BILLING = BASE / "billing"
RESEARCH_DB = BILLING / "research.db"
FUND_DB = BILLING / "fund_data.db"

sys.path.insert(0, str(BASE))

PASS = 0; FAIL = 0; WARN = 0
findings = []
recommendations = []
critical_issues = []
readiness_checks = {}

def check(desc, cond, severity="low"):
    global PASS, FAIL, WARN
    if cond:
        PASS += 1
    elif severity == "critical":
        FAIL += 1
        critical_issues.append(desc)
        findings.append("[CRITICAL] " + desc)
    elif severity == "high":
        FAIL += 1
        findings.append("[FAIL] " + desc)
    elif severity == "medium":
        WARN += 1
        findings.append("[WARN] " + desc)
    else:
        WARN += 1
        findings.append("[NOTE] " + desc)

def rec(desc, priority="medium"):
    recommendations.append("[" + priority.upper() + "] " + desc)

print("=" * 70)
print("SOVEREIGN ALPHA - INTERNAL AUDIT DIVISION")
print("Audit started: " + datetime.utcnow().isoformat())
print("=" * 70)

# --- 1. DATABASE SCHEMA AUDIT ---
print("\n--- 1. DATABASE SCHEMA AUDIT ---")

check("research.db exists", RESEARCH_DB.exists(), "critical")
check("fund_data.db exists", FUND_DB.exists(), "critical")

if RESEARCH_DB.exists():
    conn = sqlite3.connect(str(RESEARCH_DB))
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in c.fetchall() if r[0] != 'sqlite_sequence']
    check("research.db has tables", len(tables) > 0, "critical")
    print("  Tables (" + str(len(tables)) + "): " + ", ".join(tables))

    REQUIRED_TABLES = [
        'companies', 'observation_memory', 'observation_validations',
        'research_notes', 'failure_analysis', 'confidence_calibration',
        'evidence_timeline', 'framework_performance', 'reproducibility_log',
        'edge_discovery_framework', 'challenge_records', 'memo_evolution',
        'shadow_portfolio', 'shadow_trades', 'credibility_evidence',
        'financial_series', 'forensic_flags', 'filings'
    ]
    for t in REQUIRED_TABLES:
        check("Required table '" + t + "' exists", t in tables, "critical")

    c.execute("PRAGMA table_info(observation_memory)")
    obs_cols = {r[1] for r in c.fetchall()}
    REQUIRED_OBS_COLS = ['id', 'company_id', 'observation_text', 'confidence',
        'validation_status', 'model_version', 'agent_version',
        'expected_outcome', 'actual_outcome', 'is_immutable']
    for col in REQUIRED_OBS_COLS:
        check("obs_memory column '" + col + "' exists", col in obs_cols, "high")

    for t in tables:
        try:
            c.execute("SELECT COUNT(*) FROM \"" + t + "\"")
            cnt = c.fetchone()[0]
            if cnt == 0 and t != 'sqlite_sequence':
                check("Table '" + t + "' has data", cnt > 0, "low")
        except Exception:
            pass

    c.execute("PRAGMA foreign_key_check")
    fk_violations = c.fetchall()
    check("No foreign key violations", len(fk_violations) == 0, "high")
    if fk_violations:
        for v in fk_violations[:5]:
            findings.append("  FK violation: " + str(v))

    conn.close()
else:
    check("research.db required for audit", False, "critical")

if RESEARCH_DB.exists():
    conn2 = sqlite3.connect(str(RESEARCH_DB))
    c2 = conn2.cursor()
    c2.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [r[0] for r in c2.fetchall()]
    # prediction_ledger and veto_archive are created at Flask runtime, not at DB init
    has_ledger = 'prediction_ledger' in all_tables
    has_veto = 'veto_archive' in all_tables
    check("prediction_ledger table (Flask runtime) exists", has_ledger, "medium")
    check("veto_archive table (Flask runtime) exists", has_veto, "medium")
    if has_ledger:
        c2.execute("PRAGMA table_info(prediction_ledger)")
        cols = {r[1] for r in c2.fetchall()}
        check("prediction_ledger has 'actual_outcome' column", 'actual_outcome' in cols, "high")
        check("prediction_ledger has 'confidence' column", 'confidence' in cols, "high")
        check("prediction_ledger has 'status' column", 'status' in cols, "high")
    if not has_ledger:
        rec("prediction_ledger table is created by Flask at runtime. Start the app to create it.", "low")
    conn2.close()

# --- 2. DATA INTEGRITY AUDIT ---
print("\n--- 2. DATA INTEGRITY AUDIT ---")

conn = sqlite3.connect(str(RESEARCH_DB))
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM companies WHERE ticker IS NULL OR ticker = ''")
check("All companies have tickers", c.fetchone()[0] == 0, "high")

c.execute("""SELECT COUNT(*) FROM observation_memory o
    LEFT JOIN companies c ON c.id = o.company_id
    WHERE c.id IS NULL""")
check("All observations reference valid companies", c.fetchone()[0] == 0, "high")

c.execute("SELECT COUNT(*) FROM observation_memory WHERE confidence < 0 OR confidence > 1")
check("All observations have valid confidence (0-1)", c.fetchone()[0] == 0, "high")

c.execute("""SELECT COUNT(*) FROM observation_memory
    WHERE validation_status NOT IN ('ACTIVE','CONFIRMED','INVALIDATED','MONITORING','PARTIALLY_CONFIRMED')""")
check("All observations have valid status", c.fetchone()[0] == 0, "medium")

c.execute("""SELECT COUNT(*) FROM observation_validations v
    LEFT JOIN observation_memory o ON o.id = v.observation_id
    WHERE o.id IS NULL""")
check("All validations reference valid observations", c.fetchone()[0] == 0, "high")

c.execute("""SELECT COUNT(*) FROM failure_analysis f
    LEFT JOIN observation_memory o ON o.id = f.observation_id
    WHERE o.id IS NULL""")
check("All failures reference valid observations", c.fetchone()[0] == 0, "high")

c.execute("SELECT COUNT(*) FROM confidence_calibration WHERE confidence_error IS NULL")
check("All calibration records have confidence_error", c.fetchone()[0] == 0, "medium")

c.execute("""SELECT COUNT(*) FROM evidence_timeline e
    LEFT JOIN observation_memory o ON o.id = e.observation_id
    WHERE e.observation_id IS NOT NULL AND o.id IS NULL""")
check("No orphaned timeline events", c.fetchone()[0] == 0, "medium")

# --- 3. BUSINESS LOGIC INTEGRITY ---
print("\n--- 3. BUSINESS LOGIC INTEGRITY ---")

c.execute("SELECT COUNT(*) as cnt FROM observation_validations")
validations = c.fetchone()['cnt']
c.execute("SELECT COUNT(*) as cnt FROM confidence_calibration")
calibrated = c.fetchone()['cnt']
c.execute("SELECT COUNT(*) as cnt FROM observation_memory")
total_obs = c.fetchone()['cnt']
c.execute("SELECT COUNT(*) as cnt FROM observation_memory WHERE validation_status IN ('CONFIRMED','INVALIDATED')")
resolved = c.fetchone()['cnt']
c.execute("SELECT COUNT(*) as cnt FROM failure_analysis")
failures = c.fetchone()['cnt']
c.execute("SELECT COUNT(*) as cnt FROM evidence_timeline")
timeline = c.fetchone()['cnt']

cov_pct = round(resolved / total_obs * 100, 1) if total_obs > 0 else 0
check("Validation coverage > 0% (actual: " + str(cov_pct) + "%)", cov_pct > 0, "medium")
check("Validation coverage >= 10% (actual: " + str(cov_pct) + "%)", cov_pct >= 10, "medium")

check("Calibration events exist (actual: " + str(calibrated) + ")", calibrated > 0, "medium")
check("Calibration >= 3 events needed for stats (actual: " + str(calibrated) + ")", calibrated >= 3, "medium")

check("Failure records exist (actual: " + str(failures) + ")", failures > 0, "low")
check("Timeline events exist (actual: " + str(timeline) + ")", timeline > 0, "low")

c.execute("SELECT COUNT(*) as cnt FROM edge_scorecard")
edge_scores = c.fetchone()['cnt']
check("Edge score records exist (actual: " + str(edge_scores) + ")", edge_scores > 0, "low")

# --- 4. CODE QUALITY AUDIT ---
print("\n--- 4. CODE QUALITY AUDIT ---")

modules_to_check = [
    'research.storage.research_db',
    'research.evolution_quality',
    'research.observation_registry',
    'research.observation_stream',
    'research.macro.macro_engine',
    'research.macro.macro_health',
    'research.macro.fii_flow',
    'research.thesis_tracker',
    'research.portfolio_intelligence',
]
for mod_name in modules_to_check:
    try:
        importlib.import_module(mod_name)
        check("Module '" + mod_name + "' imports cleanly", True, "high")
    except Exception as e:
        check("Module '" + mod_name + "' imports cleanly", False, "critical")
        findings.append("    Import error: " + str(e))

try:
    from dashboard.app import app
    rules = [r.rule for r in app.url_map.iter_rules() if not r.rule.startswith('/static')]
    check("Flask app loads with " + str(len(rules)) + " routes", len(rules) > 10, "critical")
except Exception as e:
    check("Flask app loads", False, "critical")
    findings.append("    Flask import error: " + str(e))

# --- 5. SECURITY AUDIT ---
print("\n--- 5. SECURITY AUDIT ---")

app_content = (BASE / 'dashboard' / 'app.py').read_text(encoding='utf-8', errors='ignore')
# Use regex to avoid false-positives from substrings like "sk-" in "risk-rejected" or "Flask-based"
secret_patterns = [
    (re.compile(r'gh[paso]_[a-zA-Z0-9]{10,}'), 'GitHub token (ghp_/ghs_/gho_/gha_)'),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), 'OpenAI API key (sk-...)'),
    (re.compile(r'api_key\s*=\s*["\'][a-zA-Z0-9]{16,}'), 'API key assignment'),
    (re.compile(r'password\s*=\s*["\'][a-zA-Z0-9!@#$%^&*()]{8,}'), 'Password assignment'),
    (re.compile(r'secret\s*=\s*["\'][a-zA-Z0-9!@#$%^&*()]{8,}'), 'Secret assignment'),
]
for pattern, label in secret_patterns:
    if pattern.search(app_content):
        check("No exposed " + label + " in source", False, "critical")

route_count = len([l for l in app_content.split('\n') if '@app.route' in l])
try_count = len([l for l in app_content.split('\n') if 'try:' in l])
check("Routes have try/except blocks", try_count >= route_count * 0.7, "high")

csrf_check = 'csrf' in app_content.lower() or '@limiter.limit' in app_content
check("CSRF/rate limiting exists", csrf_check, "high")

# --- 6. PREDICTION SYSTEM AUDIT ---
print("\n--- 6. PREDICTION SYSTEM AUDIT ---")

if RESEARCH_DB.exists():
    conn3 = sqlite3.connect(str(RESEARCH_DB))
    conn3.row_factory = sqlite3.Row
    c3 = conn3.cursor()
    try:
        c3.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prediction_ledger'")
        if c3.fetchone():
            c3.execute("SELECT COUNT(*) as cnt FROM prediction_ledger")
            total_preds = c3.fetchone()['cnt']
            check("Predictions exist (actual: " + str(total_preds) + ")", total_preds > 0, "medium")

            c3.execute("SELECT COUNT(*) as cnt FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
            resolved_preds = c3.fetchone()['cnt']
            check("Resolved predictions exist (actual: " + str(resolved_preds) + ")", resolved_preds > 0, "medium")

            if resolved_preds > 0:
                c3.execute("""SELECT confidence, actual_outcome FROM prediction_ledger
                    WHERE actual_outcome IS NOT NULL AND actual_outcome != ''
                    AND confidence IS NOT NULL""")
                preds = [dict(r) for r in c3.fetchall()]
                high_conf = [p for p in preds if p['confidence'] and float(p['confidence']) >= 0.7]
                check("High-confidence predictions exist (actual: " + str(len(high_conf)) + ")",
                      len(high_conf) > 0, "medium")
        else:
            # prediction_ledger is created by Flask at runtime
            pass
    except Exception as e:
        check("prediction_ledger queryable", False, "high")
        findings.append("    Query error: " + str(e))
    conn3.close()

# --- 7. INSTITUTIONAL READINESS CHECKLIST ---
print("\n--- 7. INSTITUTIONAL READINESS ---")

readiness_checks["Evidence engine with timeline"] = timeline > 0
readiness_checks["Validation coverage tracked"] = cov_pct > 0
readiness_checks["Calibration system active"] = calibrated > 0
readiness_checks["Failure ledgers maintained"] = failures > 0

c.execute("SELECT COUNT(*) FROM reproducibility_log")
repro_count = c.fetchone()[0]
readiness_checks["Reproducibility logging"] = repro_count > 0

readiness_checks["Immutable observation flag"] = 'is_immutable' in obs_cols if 'obs_cols' in dir() else False

proof_dir = BASE / 'proofs'
cert_dir = BASE / 'dashboard' / 'certs'
has_proofs = (proof_dir.exists() and len(list(proof_dir.glob('*'))) > 0) or \
             (cert_dir.exists() and len(list(cert_dir.glob('*'))) > 0)
readiness_checks["SHA-256 proof hashes"] = has_proofs
# proof_dir exists but empty - that's acceptable (no proofs generated yet)
if not has_proofs and proof_dir.exists():
    rec("No proof hashes generated yet. They are created when predictions are recorded.", "low")
if not proof_dir.exists():
    rec("Create proofs/ directory for SHA-256 proof hash storage.", "low")

readiness_checks["System health dashboard"] = (BASE / 'dashboard' / 'templates' / 'system_health.html').exists()
readiness_checks["Audit trail page"] = (BASE / 'dashboard' / 'templates' / 'audit.html').exists()
readiness_checks["Calibration page"] = (BASE / 'dashboard' / 'templates' / 'calibration.html').exists()

for check_name, result in readiness_checks.items():
    check("Readiness: " + check_name, result, "high")

# --- 8. SUMMARY ---
print("\n" + "=" * 70)
print("AUDIT SUMMARY")
print("=" * 70)
print("  PASS: " + str(PASS))
print("  FAIL: " + str(FAIL))
print("  WARN: " + str(WARN))
print("  TOTAL: " + str(PASS + FAIL + WARN))

total_checks = PASS + FAIL + WARN
inst_score = round((PASS / total_checks) * 10, 1) if total_checks > 0 else 0
print("\n  INSTITUTIONAL READINESS SCORE: " + str(inst_score) + "/10")
print("\n  CRITICAL ISSUES: " + str(len(critical_issues)))
print("\n  ALL FINDINGS (" + str(len(findings)) + "):")
for f in findings:
    print("    " + f)

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)

result = {
    "timestamp": datetime.utcnow().isoformat(),
    "score": inst_score,
    "passed": PASS, "failed": FAIL, "warned": WARN,
    "critical_issues": len(critical_issues),
    "findings": findings,
    "recommendations": recommendations,
    "readiness_checks": readiness_checks,
}
Path("audit_result.json").write_text(json.dumps(result, indent=2))
print("\nFull results written to audit_result.json")
conn.close()
