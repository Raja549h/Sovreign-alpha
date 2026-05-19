#!/usr/bin/env python3
"""
Initialize billing/meter.db — Legacy billing meter database
============================================================
Creates the billing meter database with required tables.
This file exists for backward compatibility with existing pipeline code.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "billing" / "meter.db"


def init_meter_db():
    """Create meter.db with required tables if it doesn't exist."""
    if DB_PATH.exists():
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # Decisions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT,
            symbol TEXT,
            action TEXT,
            confidence REAL,
            alpha_generated REAL,
            status TEXT,
            created_at TEXT
        )
    """)
    
    # Proofs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS proofs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT,
            proof_hash TEXT,
            verified INTEGER,
            created_at TEXT
        )
    """)
    
    # Performance table
    c.execute("""
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            portfolio_value REAL,
            benchmark_value REAL,
            alpha REAL
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"OK: Created {DB_PATH}")


if __name__ == "__main__":
    init_meter_db()
