"""
Thesis Tracker & Watchlist
Manages investment theses lifecycle: creation, status monitoring,
narrative drift detection, and watchlist with alert thresholds.
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).parent.parent
BILLING_DIR = BASE_DIR / "billing"
RESEARCH_DB = BILLING_DIR / "research.db"

def get_connection():
    conn = sqlite3.connect(str(RESEARCH_DB))
    conn.row_factory = sqlite3.Row
    return conn

def create_thesis(company_id: int, title: str, thesis_text: str, key_variables: str = "", timeframe_days: int = 90, conviction: float = 0.0) -> int:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO theses (company_id, title, thesis_text, key_variables, timeframe_days, conviction) VALUES (?, ?, ?, ?, ?, ?)", (company_id, title, thesis_text, key_variables, timeframe_days, conviction))
        conn.commit()
        return c.lastrowid

def get_theses(company_id: int = None, status: str = None) -> List[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        query = "SELECT t.*, c.ticker, c.company_name FROM theses t JOIN companies c ON c.id = t.company_id"
        params = []
        where = []
        if company_id:
            where.append("t.company_id = ?")
            params.append(company_id)
        if status:
            where.append("t.status = ?")
            params.append(status)
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY t.created_at DESC"
        c.execute(query, params)
        return [dict(r) for r in c.fetchall()]

def get_thesis(thesis_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT t.*, c.ticker, c.company_name FROM theses t JOIN companies c ON c.id = t.company_id WHERE t.id = ?", (thesis_id,))
        r = c.fetchone()
        return dict(r) if r else None

def update_thesis_status(thesis_id: int, status: str, notes: str = ""):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE theses SET status = ?, updated_at = CURRENT_TIMESTAMP, notes = notes || ? WHERE id = ?", (status, f"\n[{datetime.utcnow().isoformat()}] {notes}", thesis_id))
        conn.commit()

def add_check(thesis_id: int, variable: str, expected_range: str, actual_value: str, flag_severity: str = None, notes: str = ""):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO thesis_checks (thesis_id, variable, expected_range, actual_value, flag_severity, notes) VALUES (?, ?, ?, ?, ?, ?)", (thesis_id, variable, expected_range, actual_value, flag_severity, notes))
        conn.commit()

def get_checks(thesis_id: int) -> List[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM thesis_checks WHERE thesis_id = ? ORDER BY checked_at DESC", (thesis_id,))
        return [dict(r) for r in c.fetchall()]

def assess_thesis_status(thesis_id: int) -> Dict:
    thesis = get_thesis(thesis_id)
    if not thesis:
        return {"status": "UNKNOWN", "reason": "Thesis not found"}
    checks = get_checks(thesis_id)
    if not checks:
        return {"status": thesis.get("status", "INTACT"), "reason": "No checks recorded", "checks_analyzed": 0}
    high_flags = sum(1 for c in checks if c.get("flag_severity") == "HIGH")
    med_flags = sum(1 for c in checks if c.get("flag_severity") == "MEDIUM")
    recent = [c for c in checks if datetime.fromisoformat(c["checked_at"]) > datetime.utcnow() - timedelta(days=30)]
    recent_high = sum(1 for c in recent if c.get("flag_severity") == "HIGH")
    if high_flags >= 2 or recent_high >= 1:
        status = "BROKEN"
        reason = f"Core assumption violated: {high_flags} high-severity flags"
    elif med_flags >= 2 or high_flags == 1:
        status = "WEAKENING"
        reason = f"Adverse movement detected: {med_flags} medium, {high_flags} high flags"
    else:
        status = "INTACT"
        reason = "All key variables in range"
    update_thesis_status(thesis_id, status, f"Auto-assessment: {reason}")
    return {"status": status, "reason": reason, "checks_analyzed": len(checks), "high_flags": high_flags, "med_flags": med_flags}

def detect_narrative_drift(thesis_id: int, new_facts: str) -> Dict:
    thesis = get_thesis(thesis_id)
    if not thesis:
        return {"drift_detected": False, "score": 0, "details": "Thesis not found"}
    drift_score = 0
    drift_factors = []
    original = (thesis.get("thesis_text") or "").lower()
    new_lower = new_facts.lower()
    contradictions = ["contrary to expectation", "worse than expected", "reversal", "deterioration", "weakened", "missed guidance"]
    for word in contradictions:
        if word in new_lower:
            drift_score += 15
            drift_factors.append(f"{word} mentioned in new facts")
    key_terms = thesis.get("key_variables") or ""
    for term in key_terms.split(","):
        term = term.strip().lower()
        if term and term in original and term not in new_lower:
            drift_score += 10
            drift_factors.append(f"Key variable '{term}' absent from new facts")
    if drift_score > 30:
        drift_level = "HIGH"
        drift_detected = True
    elif drift_score > 15:
        drift_level = "MEDIUM"
        drift_detected = True
    else:
        drift_level = "LOW"
        drift_detected = False
    return {"drift_detected": drift_detected, "score": drift_score, "level": drift_level, "factors": drift_factors}

def add_to_watchlist(company_id: int, alert_threshold: str = "MEDIUM", notes: str = "") -> int:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO watchlist (company_id, alert_threshold, notes) VALUES (?, ?, ?)", (company_id, alert_threshold, notes))
        conn.commit()
        c.execute("SELECT id FROM watchlist WHERE company_id = ?", (company_id,))
        r = c.fetchone()
        return r["id"] if r else 0

def remove_from_watchlist(company_id: int):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM watchlist WHERE company_id = ?", (company_id,))
        conn.commit()

def get_watchlist() -> List[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT w.*, c.ticker, c.company_name, c.sector,
                   (SELECT COUNT(*) FROM forensic_flags f WHERE f.company_id = c.id AND f.severity IN ('HIGH','CRITICAL')) as critical_flags,
                   (SELECT COUNT(*) FROM theses t WHERE t.company_id = c.id AND t.status = 'BROKEN') as broken_theses
            FROM watchlist w
            JOIN companies c ON c.id = w.company_id
            ORDER BY w.added_at DESC
        """)
        return [dict(r) for r in c.fetchall()]

def get_watchlist_companies() -> List[Dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT c.id, c.ticker, c.company_name, c.sector, w.alert_threshold, w.notes, w.added_at
            FROM watchlist w
            JOIN companies c ON c.id = w.company_id
            ORDER BY w.added_at DESC
        """)
        return [dict(r) for r in c.fetchall()]

def is_on_watchlist(company_id: int) -> bool:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM watchlist WHERE company_id = ?", (company_id,))
        return c.fetchone()["cnt"] > 0
