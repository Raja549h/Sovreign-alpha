"""
SOVEREIGN ALPHA — FULL SYSTEM AUDIT
Tests every route, every API endpoint, every DB table, every module.
"""
import sys, os, json, time, traceback
sys.path.insert(0, '.')
os.environ.setdefault('TESTING', '1')

import config
from dashboard.app import app
from unittest.mock import patch
from datetime import datetime

PASS = 0
FAIL = 0
WARN = 0
results = []

def log(category, name, status, detail=""):
    global PASS, FAIL, WARN
    icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠"}[status]
    if status == "PASS": PASS += 1
    elif status == "FAIL": FAIL += 1
    else: WARN += 1
    line = f"  [{icon}] {category:.<30s} {name:.<45s} {status} {detail}"
    print(line)
    results.append({"category": category, "name": name, "status": status, "detail": detail})

print("=" * 100)
print("  SOVEREIGN ALPHA — COMPREHENSIVE SYSTEM AUDIT")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)

# ============================================================
# 1. DATABASE CONNECTIVITY
# ============================================================
print("\n── DATABASE CONNECTIVITY ──")
try:
    from dashboard.gateway import get_connection, init_pool, _PG_POOL
    init_pool()
    if _PG_POOL:
        log("DB", "Pool initialized", "PASS", f"maxconn={_PG_POOL.maxconn}")
    else:
        log("DB", "Pool initialized", "FAIL", "Pool is None")
except Exception as e:
    log("DB", "Pool initialized", "FAIL", str(e)[:80])

try:
    conn = get_connection()
    if conn:
        log("DB", "get_connection()", "PASS")
        conn.close()
    else:
        log("DB", "get_connection()", "FAIL", "returned None")
except Exception as e:
    log("DB", "get_connection()", "FAIL", str(e)[:80])

# ============================================================
# 2. TABLE INTEGRITY — check every table has rows
# ============================================================
print("\n── TABLE INTEGRITY ──")
EXPECTED_TABLES = [
    "prediction_ledger", "veto_archive", "decisions", "performance_log",
    "inference_log", "monthly_summary", "companies", "filings",
    "financial_series", "forensic_flags", "research_notes",
    "institutional_scores", "nsdl_fpi_flows", "fii_flows",
    "fii_flow_snapshots", "edge_scorecard", "watchlist",
    "observation_memory", "observation_validations", "evidence_timeline",
    "multi_source_evidence", "framework_performance", "reproducibility_log",
    "observation_autopsy", "reasoning_audit", "failure_analysis",
    "calibration_history", "edge_discovery_framework", "shadow_portfolio",
    "credibility_evidence", "research_quality_metrics", "confidence_calibration",
    "portfolios", "portfolio_positions", "portfolio_scores",
    "portfolio_stress_results", "theses", "thesis_checks", "observations",
]
try:
    conn = get_connection()
    c = conn.cursor()
    for tbl in EXPECTED_TABLES:
        try:
            c.execute(f"SELECT COUNT(*) as cnt FROM {tbl}")
            row = c.fetchone()
            cnt = row['cnt'] if row else 0
            if cnt > 0:
                log("TABLE", tbl, "PASS", f"{cnt} rows")
            else:
                log("TABLE", tbl, "WARN", "0 rows (empty)")
        except Exception as e:
            log("TABLE", tbl, "FAIL", str(e)[:60])
    conn.close()
except Exception as e:
    log("TABLE", "connection", "FAIL", str(e)[:80])

# ============================================================
# 3. MODULE IMPORTS — every critical module
# ============================================================
print("\n── MODULE IMPORTS ──")
MODULES = [
    "config", "database", "dashboard.app",
    "engine.data_layer", "engine.regime",
    "agents.analyst", "agents.risk_manager", "agents.auditor",
    "data.market_feed", "data.market_signals",
    "research.evolution_quality", "research.observation_registry",
    "research.auto_review_engine", "research.fii_intelligence",
    "research.storage.research_db",
    "automation.master_daily", "automation.email_digest",
    "dashboard.security",
]
for mod in MODULES:
    try:
        __import__(mod)
        log("IMPORT", mod, "PASS")
    except Exception as e:
        log("IMPORT", mod, "FAIL", str(e)[:80])

# ============================================================
# 4. RESEARCH MODULES — functional tests
# ============================================================
print("\n── RESEARCH MODULES ──")
try:
    from research.evolution_quality import (
        EvidenceTimeline, ConfidenceCalibrator, ObservationAutopsy,
        EdgeDiscoveryFramework, AntiVanityAudit, InstitutionalCredibility,
        WeeklyICReport
    )
    
    with app.app_context():
        # EvidenceTimeline
        try:
            et = EvidenceTimeline()
            tl = et.get_timeline(limit=3)
            log("RESEARCH", "EvidenceTimeline.get_timeline()", "PASS", f"{len(tl)} events")
        except Exception as e:
            log("RESEARCH", "EvidenceTimeline.get_timeline()", "FAIL", str(e)[:80])
        
        # ConfidenceCalibrator
        try:
            cc = ConfidenceCalibrator()
            summary = cc.get_calibration_summary()
            log("RESEARCH", "ConfidenceCalibrator.get_summary()", "PASS", f"MAE={summary.get('mean_absolute_error','?')}")
        except Exception as e:
            log("RESEARCH", "ConfidenceCalibrator.get_summary()", "FAIL", str(e)[:80])
        
        # ObservationAutopsy
        try:
            oa = ObservationAutopsy()
            quality = oa.get_quality_distribution()
            log("RESEARCH", "ObservationAutopsy.quality_dist()", "PASS", f"{len(quality)} entries")
        except Exception as e:
            log("RESEARCH", "ObservationAutopsy.quality_dist()", "FAIL", str(e)[:80])

        # AntiVanityAudit
        try:
            av = AntiVanityAudit()
            audit = av.run_audit()
            log("RESEARCH", "AntiVanityAudit.run_audit()", "PASS", f"verdict={audit.get('verdict','?')[:30]}")
        except Exception as e:
            log("RESEARCH", "AntiVanityAudit.run_audit()", "FAIL", str(e)[:80])

        # InstitutionalCredibility
        try:
            ic = InstitutionalCredibility()
            cred = ic.calculate()
            log("RESEARCH", "InstitutionalCredibility.calc()", "PASS", f"grade={cred.get('grade','?')}")
        except Exception as e:
            log("RESEARCH", "InstitutionalCredibility.calc()", "FAIL", str(e)[:80])

        # WeeklyICReport
        try:
            wr = WeeklyICReport()
            report = wr.generate()
            log("RESEARCH", "WeeklyICReport.generate()", "PASS", f"sections={len(report.get('sections',{}))}")
        except Exception as e:
            log("RESEARCH", "WeeklyICReport.generate()", "FAIL", str(e)[:80])

        # EdgeDiscoveryFramework
        try:
            edf = EdgeDiscoveryFramework()
            rankings = edf.get_framework_rankings()
            log("RESEARCH", "EdgeDiscoveryFramework.rankings()", "PASS", f"frameworks={rankings.get('total_frameworks',0)}")
        except Exception as e:
            log("RESEARCH", "EdgeDiscoveryFramework.rankings()", "FAIL", str(e)[:80])

except Exception as e:
    log("RESEARCH", "module import", "FAIL", str(e)[:80])

# ============================================================
# 5. OBSERVATION REGISTRY
# ============================================================
print("\n── OBSERVATION REGISTRY ──")
try:
    from research.observation_registry import ObservationRegistry
    with app.app_context():
        reg = ObservationRegistry()
        try:
            obs = reg.get_observations(limit=3)
            log("REGISTRY", "get_observations()", "PASS", f"{len(obs)} obs")
        except Exception as e:
            log("REGISTRY", "get_observations()", "FAIL", str(e)[:80])
        try:
            score = reg.calculate_edge_score()
            log("REGISTRY", "calculate_edge_score()", "PASS", f"score={score}")
        except Exception as e:
            log("REGISTRY", "calculate_edge_score()", "FAIL", str(e)[:80])
except Exception as e:
    log("REGISTRY", "ObservationRegistry import", "FAIL", str(e)[:80])

# ============================================================
# 6. FII INTELLIGENCE
# ============================================================
print("\n── FII INTELLIGENCE ──")
try:
    from research.fii_intelligence import FIIFlowAnalyzer
    with app.app_context():
        fii = FIIFlowAnalyzer()
        try:
            summary = fii.get_flow_summary(days=30)
            log("FII", "get_flow_summary()", "PASS", f"trend={summary.get('trend','?')}")
        except Exception as e:
            log("FII", "get_flow_summary()", "FAIL", str(e)[:80])
except Exception as e:
    log("FII", "FIIFlowAnalyzer import", "FAIL", str(e)[:80])

# ============================================================
# 7. ALL PAGE ROUTES (GET)
# ============================================================
print("\n── PAGE ROUTES ──")
PAGE_ROUTES = [
    "/login",
    "/",
    "/dashboard",
    "/evidence",
    "/research",
    "/watchlist",
    "/macro",
    "/shadow-portfolio",
    "/portfolio",
    "/edge-discovery",
    "/forensics",
    "/observations",
    "/audit-trail",
    "/fii-flows",
    "/calibration",
]

with app.test_client() as client:
    with patch('privacy.verify_session_token', return_value='fund-123'):
        client.set_cookie('session_token', 'mock')
        
        for route in PAGE_ROUTES:
            try:
                resp = client.get(route, follow_redirects=True)
                ct = resp.content_type or ""
                if resp.status_code == 200 and "text/html" in ct:
                    body = resp.get_data(as_text=True)
                    if "error" in body.lower() and "error.html" in body.lower():
                        log("PAGE", route, "WARN", f"200 but rendered error page")
                    else:
                        log("PAGE", route, "PASS", f"{resp.status_code} ({len(body)} bytes)")
                elif resp.status_code == 200:
                    log("PAGE", route, "PASS", f"{resp.status_code}")
                elif resp.status_code in (301, 302, 308):
                    loc = resp.headers.get('Location', '?')
                    log("PAGE", route, "WARN", f"redirect -> {loc}")
                else:
                    log("PAGE", route, "FAIL", f"status={resp.status_code}")
            except Exception as e:
                log("PAGE", route, "FAIL", str(e)[:80])

# ============================================================
# 8. ALL API ENDPOINTS
# ============================================================
print("\n── API ENDPOINTS ──")
API_ROUTES = [
    "/api/evidence/timeline",
    "/api/evidence/calibration-dashboard",
    "/api/evidence/institutional-credibility",
    "/api/evidence/anti-vanity",
    "/api/evidence/weekly-ic-report",
    "/api/predictions",
    "/api/vetoes",
    "/api/performance",
    "/api/companies",
    "/api/watchlist",
    "/api/macro/health",
    "/api/macro/regime",
    "/api/observations",
    "/api/edge-scorecard",
    "/api/shadow-portfolio",
    "/api/fii/flows",
    "/api/fii/summary",
    "/api/forensics/flags",
    "/api/audit-trail",
    "/api/portfolio/list",
]

with app.test_client() as client:
    with patch('privacy.verify_session_token', return_value='fund-123'):
        client.set_cookie('session_token', 'mock')
        
        for route in API_ROUTES:
            try:
                resp = client.get(route, follow_redirects=True)
                ct = resp.content_type or ""
                data_str = resp.get_data(as_text=True)
                
                if resp.status_code == 200 and "json" in ct:
                    try:
                        d = json.loads(data_str)
                        if isinstance(d, dict) and d.get('success') == False:
                            log("API", route, "WARN", f"200 JSON but success=false: {d.get('error','?')[:40]}")
                        else:
                            log("API", route, "PASS", f"200 JSON ({len(data_str)} bytes)")
                    except json.JSONDecodeError:
                        log("API", route, "FAIL", f"200 but invalid JSON")
                elif resp.status_code == 200 and "html" in ct:
                    # API returned HTML — likely redirect to login or error page
                    if "login" in data_str.lower() or "Login" in data_str:
                        log("API", route, "WARN", f"200 but got login HTML (auth issue)")
                    else:
                        log("API", route, "WARN", f"200 but got HTML instead of JSON")
                elif resp.status_code in (301, 302):
                    log("API", route, "WARN", f"redirect (auth?) -> {resp.headers.get('Location','?')}")
                elif resp.status_code == 404:
                    log("API", route, "WARN", f"404 — route may not exist")
                elif resp.status_code == 503:
                    log("API", route, "FAIL", f"503 — DB unavailable")
                else:
                    log("API", route, "FAIL", f"status={resp.status_code} body={data_str[:60]}")
            except Exception as e:
                log("API", route, "FAIL", str(e)[:80])

# ============================================================
# 9. EVIDENCE TIMELINE DEEP TEST
# ============================================================
print("\n── EVIDENCE TIMELINE DEEP TEST ──")
try:
    from research.evolution_quality import EvidenceTimeline
    with app.app_context():
        et = EvidenceTimeline()
        
        # Test with no filters
        tl = et.get_timeline(limit=5)
        log("TIMELINE", "no filters (limit=5)", "PASS", f"{len(tl)} events")
        
        # Test with company_id filter
        try:
            tl2 = et.get_timeline(company_id=1, limit=3)
            log("TIMELINE", "company_id=1", "PASS", f"{len(tl2)} events")
        except Exception as e:
            log("TIMELINE", "company_id=1", "FAIL", str(e)[:80])
        
        # Test with event_type filter
        try:
            tl3 = et.get_timeline(event_type="PIPELINE_EXECUTION", limit=3)
            log("TIMELINE", "event_type=PIPELINE", "PASS", f"{len(tl3)} events")
        except Exception as e:
            log("TIMELINE", "event_type=PIPELINE", "FAIL", str(e)[:80])
        
        # Verify JSON serialization
        try:
            json_str = json.dumps(tl)
            log("TIMELINE", "JSON serializable", "PASS", f"{len(json_str)} chars")
        except Exception as e:
            log("TIMELINE", "JSON serializable", "FAIL", str(e)[:80])
        
except Exception as e:
    log("TIMELINE", "deep test", "FAIL", str(e)[:80])

# ============================================================
# 10. CONNECTION POOL STRESS TEST
# ============================================================
print("\n── CONNECTION POOL STRESS TEST ──")
try:
    from dashboard.gateway import get_connection
    conns = []
    opened = 0
    for i in range(15):
        try:
            c = get_connection()
            if c:
                conns.append(c)
                opened += 1
        except Exception:
            break
    log("POOL", f"opened {opened} concurrent conns", "PASS" if opened >= 10 else "WARN", f"{opened}/15")
    for c in conns:
        c.close()
    log("POOL", "all connections returned", "PASS")
except Exception as e:
    log("POOL", "stress test", "FAIL", str(e)[:80])

# ============================================================
# 11. TEMPLATE RENDERING
# ============================================================
print("\n── TEMPLATE RENDERING ──")
TEMPLATES_TO_CHECK = [
    "evidence.html", "dashboard.html", "login.html",
    "macro_health.html", "watchlist.html", "error.html",
    "unavailable.html",
]
template_dir = os.path.join(os.path.dirname(__file__), "dashboard", "templates")
for tmpl in TEMPLATES_TO_CHECK:
    path = os.path.join(template_dir, tmpl)
    if os.path.exists(path):
        size = os.path.getsize(path)
        log("TEMPLATE", tmpl, "PASS", f"{size} bytes")
    else:
        log("TEMPLATE", tmpl, "WARN", "file not found")

# ============================================================
# 12. CONFIG & ENVIRONMENT
# ============================================================
print("\n── CONFIG & ENVIRONMENT ──")
env_vars = ["NEON_URL", "JWT_SECRET", "CEREBRAS_API_KEY", "OPENAI_API_KEY", "FRED_API_KEY"]
for var in env_vars:
    val = os.environ.get(var, "")
    if val and len(val) > 5:
        log("ENV", var, "PASS", f"set ({len(val)} chars)")
    elif val:
        log("ENV", var, "WARN", f"set but short ({len(val)} chars)")
    else:
        log("ENV", var, "WARN", "not set")

# ============================================================
# 13. GITHUB ACTIONS WORKFLOW VALIDATION
# ============================================================
print("\n── GITHUB ACTIONS WORKFLOW ──")
workflow_path = os.path.join(os.path.dirname(__file__), ".github", "workflows", "daily-pipeline.yml")
if os.path.exists(workflow_path):
    with open(workflow_path, 'r') as f:
        wf = f.read()
    log("WORKFLOW", "daily-pipeline.yml exists", "PASS", f"{len(wf)} bytes")
    
    # Check for common issues
    if "NEON_URL" in wf:
        log("WORKFLOW", "NEON_URL secret referenced", "PASS")
    else:
        log("WORKFLOW", "NEON_URL secret referenced", "FAIL", "missing")
    
    if "psycopg2" in wf or "requirements" in wf:
        log("WORKFLOW", "dependencies install step", "PASS")
    else:
        log("WORKFLOW", "dependencies install step", "WARN", "may be missing")
    
    if "timeout" in wf.lower():
        log("WORKFLOW", "timeout configured", "PASS")
    else:
        log("WORKFLOW", "timeout configured", "WARN", "no timeout found")
else:
    log("WORKFLOW", "daily-pipeline.yml exists", "FAIL", "file not found")

# ============================================================
# 14. REQUIREMENTS VALIDATION
# ============================================================
print("\n── REQUIREMENTS ──")
req_path = os.path.join(os.path.dirname(__file__), "requirements-pipeline.txt")
if os.path.exists(req_path):
    with open(req_path, 'r') as f:
        reqs = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    log("REQS", "requirements-pipeline.txt", "PASS", f"{len(reqs)} packages")
    
    critical = ["psycopg2", "flask", "pandas", "requests", "openai"]
    for pkg in critical:
        if any(pkg in r.lower() for r in reqs):
            log("REQS", f"{pkg} listed", "PASS")
        else:
            log("REQS", f"{pkg} listed", "FAIL", "missing from requirements")
else:
    log("REQS", "requirements-pipeline.txt", "FAIL", "file not found")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 100)
print(f"  AUDIT COMPLETE — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  ✓ PASSED: {PASS}   ⚠ WARNINGS: {WARN}   ✗ FAILED: {FAIL}")
print(f"  Total checks: {PASS + WARN + FAIL}")
print("=" * 100)

# Write results to JSON for artifact
with open("audit_results.json", "w") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "passed": PASS, "warnings": WARN, "failed": FAIL,
        "total": PASS + WARN + FAIL,
        "results": results
    }, f, indent=2)
print(f"\nDetailed results saved to audit_results.json")
