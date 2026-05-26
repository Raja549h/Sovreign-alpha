"""
Seed Database — Run on deploy to populate essential tables.
===========================================================
1. Creates all required tables if they don't exist
2. Runs research/test_run.py to populate Bajaj Finance data
3. Falls back gracefully if Groq API or other dependencies fail
"""

import sys
import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
import uuid

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

BILLING_DIR = BASE_DIR / "billing"
BILLING_DIR.mkdir(exist_ok=True)
DB_PATH = BILLING_DIR / "billing.db"

RESEARCH_DB_PATH = BILLING_DIR / "research.db"


def ensure_tables():
    """Create all essential tables so dashboard never 500s on missing tables."""
    print("[seed] Ensuring essential tables exist...")
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS prediction_ledger (
            prediction_id TEXT PRIMARY KEY,
            symbol TEXT,
            action TEXT,
            status TEXT,
            confidence REAL,
            rationale TEXT,
            timestamp TEXT,
            actual_outcome TEXT,
            actual_return_pct REAL,
            outcome_notes TEXT,
            updated_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS veto_archive (
            veto_id TEXT PRIMARY KEY,
            symbol TEXT,
            reason TEXT,
            risk_score REAL,
            timestamp TEXT,
            actual_outcome TEXT,
            actual_return_pct REAL,
            expected_loss_pct REAL,
            avoided_drawdown REAL,
            veto_correct INTEGER,
            notes TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS performance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT,
            symbol TEXT,
            action TEXT,
            status TEXT,
            alpha_generated REAL,
            fee_calculated REAL,
            timestamp TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS inference_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            cost REAL,
            timestamp TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS monthly_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT,
            total_decisions INTEGER,
            approved INTEGER,
            vetoed INTEGER,
            accuracy REAL
        )
    """)

    conn.commit()
    conn.close()
    print("[seed] Essential tables created/verified")


def seed_sample_predictions():
    """Insert sample predictions so the ledger isn't empty on fresh deploy."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM prediction_ledger")
    if c.fetchone()[0] > 0:
        print("[seed] prediction_ledger already has data, skipping sample seed")
        conn.close()
        return

    print("[seed] Inserting sample predictions...")
    now = datetime.utcnow()
    samples = [
        ("pred-001", "RELIANCE", "LONG", "cleared", 0.82, "Strong momentum in refining margins", (now - timedelta(days=5)).isoformat()),
        ("pred-002", "TCS", "SHORT", "risk-rejected", 0.45, "Weak guidance on IT spending", (now - timedelta(days=3)).isoformat()),
        ("pred-003", "INFY", "LONG", "cleared", 0.71, "Deal wins in AI/ML segment", (now - timedelta(days=2)).isoformat()),
        ("pred-004", "HDFCBANK", "HOLD", "cleared", 0.60, "Stable NIM, awaiting credit growth", (now - timedelta(days=1)).isoformat()),
        ("pred-005", "BAJFINANCE", "LONG", "cleared", 0.78, "AUM growth accelerating, ROE stabilizing", now.isoformat()),
    ]

    for pid, sym, action, status, conf, rationale, ts in samples:
        c.execute("""
            INSERT OR IGNORE INTO prediction_ledger
            (prediction_id, symbol, action, status, confidence, rationale, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pid, sym, action, status, conf, rationale, ts))

    conn.commit()
    conn.close()
    print(f"[seed] Inserted {len(samples)} sample predictions")


def seed_sample_vetoes():
    """Insert sample vetoes so the archive isn't empty on fresh deploy."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM veto_archive")
    if c.fetchone()[0] > 0:
        print("[seed] veto_archive already has data, skipping sample seed")
        conn.close()
        return

    print("[seed] Inserting sample vetoes...")
    now = datetime.utcnow()
    samples = [
        ("veto-001", "ADANIENT", "High promoter pledge risk", 0.91, (now - timedelta(days=7)).isoformat(), "correct", -12.5, 8.0, 12.5, 1, "Stock fell 12.5% after pledge news"),
        ("veto-002", "PAYTM", "Regulatory overhang unresolved", 0.85, (now - timedelta(days=4)).isoformat(), "correct", -8.2, 6.0, 8.2, 1, "RBI restrictions continued"),
        ("veto-003", "ZEEL", "Governance red flags", 0.88, (now - timedelta(days=2)).isoformat(), None, None, 7.0, None, None, None),
    ]

    for vid, sym, reason, risk, ts, outcome, ret, exp_loss, avoided, correct, notes in samples:
        c.execute("""
            INSERT OR IGNORE INTO veto_archive
            (veto_id, symbol, reason, risk_score, timestamp, actual_outcome, actual_return_pct, expected_loss_pct, avoided_drawdown, veto_correct, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vid, sym, reason, risk, ts, outcome, ret, exp_loss, avoided, correct, notes))

    conn.commit()
    conn.close()
    print(f"[seed] Inserted {len(samples)} sample vetoes")


def run_full_seed():
    """Run research/test_run.py for full Bajaj Finance pipeline."""
    print("[seed] Attempting full research pipeline seed...")
    test_script = BASE_DIR / "research" / "test_run.py"
    if not test_script.exists():
        print("[seed] test_run.py not found, skipping full seed")
        return False

    result = os.system(f'python "{test_script}"')
    if result == 0:
        print("[seed] Full research pipeline seed succeeded")
        return True
    else:
        print(f"[seed] Full research pipeline seed failed (exit {result}), using fallback samples")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SOVEREIGN ALPHA — Database Seed on Deploy")
    print("=" * 60)

    ensure_tables()
    seed_sample_predictions()
    seed_sample_vetoes()

    if os.environ.get("SPACE_ID") or os.environ.get("RENDER", "false").lower() == "true":
        run_full_seed()
    else:
        print("[seed] Not on cloud, skipping full pipeline seed")

    print("=" * 60)
    print("[seed] Database seeding complete")
    print("=" * 60)
