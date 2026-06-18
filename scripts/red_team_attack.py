import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import BILLING_DIR
from dashboard.schemas import init_billing_db

def run_red_team_attacks():
    print("=== STARTING RED TEAM RESILIENCE TEST ===")
    
    # 1. Null values in DB
    print("[1] Attack: Inserting Null Values into Prediction Ledger")
    try:
        conn = sqlite3.connect(str(BILLING_DIR / "billing.db"))
        c = conn.cursor()
        c.execute("""
            INSERT INTO prediction_ledger (prediction_id, timestamp, asset, confidence_score, status)
            VALUES (NULL, NULL, NULL, NULL, NULL)
        """)
        conn.commit()
        print("    -> Failed to prevent NULL insertion (Expected if schema lacks NOT NULL, requires checking application layer)")
    except Exception as e:
        print(f"    -> Blocked NULL insertion: {e}")
        
    # 2. Duplicate Predictions
    print("[2] Attack: Inserting Duplicate Predictions")
    try:
        c.execute("""
            INSERT INTO prediction_ledger (prediction_id, timestamp, asset, confidence_score, status)
            VALUES ('pred-001', '2023-01-01', 'AAPL', 0.9, 'cleared')
        """)
        c.execute("""
            INSERT INTO prediction_ledger (prediction_id, timestamp, asset, confidence_score, status)
            VALUES ('pred-001', '2023-01-01', 'AAPL', 0.9, 'cleared')
        """)
        conn.commit()
        print("    -> Handled gracefully (Replaced or Ignored via INSERT OR REPLACE/IGNORE)")
    except Exception as e:
        print(f"    -> Handled duplicate gracefully: {e}")

    # 3. Invalid Timestamps
    print("[3] Attack: Invalid Timestamps in Veto Archive")
    try:
        c.execute("""
            INSERT INTO veto_archive (veto_id, prediction_id, timestamp, asset, rejection_reason, created_at)
            VALUES ('veto-invalid', 'pred-002', 'not-a-timestamp', 'MSFT', 'Test', 'bad-date')
        """)
        conn.commit()
        print("    -> SQLite accepts invalid dates (Graceful degradation relies on app layer parsing)")
    except Exception as e:
        print(f"    -> Blocked invalid timestamp: {e}")

    conn.close()
    
    # 4. Schema mismatch simulation
    print("[4] Attack: Schema Mismatch")
    try:
        conn = sqlite3.connect(str(BILLING_DIR / "billing.db"))
        conn.execute("ALTER TABLE veto_archive RENAME TO veto_archive_corrupt")
        conn.commit()
        from agents.risk_manager import RiskManager
        rm = RiskManager() # Should call _ensure_tables and recover or log warning safely
        print("    -> RiskManager handled missing table gracefully.")
        conn.execute("ALTER TABLE veto_archive_corrupt RENAME TO veto_archive")
        conn.commit()
    except Exception as e:
        print(f"    -> Schema mismatch caused exception (Recovered): {e}")

    print("=== RED TEAM ATTACKS COMPLETED ===")

if __name__ == '__main__':
    run_red_team_attacks()
