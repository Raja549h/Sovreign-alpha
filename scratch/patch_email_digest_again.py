import sys
import os
import re

with open('email_digest_old.py', 'r', encoding='utf-16le') as f:
    content = f.read()

# 1. Replace imports and setup
old_setup = """
import smtplib
from dashboard.gateway import IntegrityError, get_connection
import random
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BILLING_DIR = BASE_DIR / "billing"

def load_env():
"""
new_setup = """
import smtplib
from dashboard.gateway import DatabaseConnection
import random
import uuid
from datetime import datetime, timedelta, timezone
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import concurrent.futures

BILLING_DIR = BASE_DIR / "billing"

def load_env():
"""
content = content.replace(old_setup.strip(), new_setup.strip())

# 2. Replace get_db_connection
old_get_db = """def get_db_connection():
    return get_connection()"""
new_get_db = """def get_db_connection():
    try:
        return DatabaseConnection()
    except Exception as e:
        raise Exception(f"Database connection failed: {e}")"""
content = content.replace(old_get_db, new_get_db)

# 3. Replace get_today_observations
old_get_obs = """def get_today_observations():
    try:
        conn = get_db_connection()
        if not conn:
            return []
        c = conn.cursor()
        c.execute("SELECT timestamp, headline FROM observations WHERE timestamp::timestamp > (NOW() AT TIME ZONE 'Asia/Kolkata') - INTERVAL '1 day' ORDER BY timestamp DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching observations: {e}")
        return []"""

new_get_obs = """def get_today_observations():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=1)
        c.execute("SELECT timestamp, headline FROM observations WHERE timestamp >= %s ORDER BY timestamp DESC LIMIT 10", (cutoff_time.isoformat(),))
        return c.fetchall()
    finally:
        conn.close()"""
content = content.replace(old_get_obs, new_get_obs)

# 4. Replace get_today_stats
old_stats = """def get_today_stats():
    init_tables()
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
    conn = get_db_connection()
    if not conn:
        print("[ERROR] get_today_stats: Database connection failed! NEON_URL may be missing.")
        print(f"[DEBUG] NEON_URL present: {bool(os.environ.get('NEON_URL'))}")
        return {
            'total': 0, 'approved': 0, 'rejected': 0, 'avg_conf': 0,
            'top': None, 'total_all': 0, 'accuracy': 0, 'avoided': 0
        }
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM prediction_ledger WHERE timestamp >= %s", (cutoff,))
    total = c.fetchone()['total'] or 0
    c.execute("SELECT COUNT(*) as approved FROM prediction_ledger WHERE timestamp >= %s AND status = 'cleared'", (cutoff,))
    approved = c.fetchone()['approved'] or 0
    c.execute("SELECT COUNT(*) as rejected FROM prediction_ledger WHERE timestamp >= %s AND status = 'risk-rejected'", (cutoff,))
    rejected = c.fetchone()['rejected'] or 0
    c.execute("SELECT AVG(confidence_score) as avg_conf FROM prediction_ledger WHERE timestamp >= %s", (cutoff,))
    avg_conf = c.fetchone()['avg_conf'] or 0
    c.execute(\"\"\"
        SELECT asset, status, confidence_score, thesis
        FROM prediction_ledger 
        WHERE timestamp >= %s AND status = 'cleared'
        ORDER BY confidence_score DESC LIMIT 1
    \"\"\", (cutoff,))
    top = c.fetchone()
    c.execute("SELECT COUNT(*) as total FROM prediction_ledger")
    total_all = c.fetchone()['total'] or 0
    c.execute("SELECT COUNT(*) as correct FROM prediction_ledger WHERE actual_outcome = 'correct'")
    correct = c.fetchone()['correct'] or 0
    c.execute("SELECT COUNT(*) as with_outcome FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
    with_outcome = c.fetchone()['with_outcome'] or 0
    c.execute("SELECT COALESCE(SUM(avoided_drawdown), 0) as avoided FROM veto_archive")
    avoided = c.fetchone()['avoided'] or 0
    conn.close()
    accuracy = (correct / with_outcome * 100) if with_outcome > 0 else 0
    return {
        'total': total,
        'approved': approved,
        'rejected': rejected,
        'avg_conf': avg_conf,
        'top': top,
        'total_all': total_all,
        'accuracy': accuracy,
        'avoided': avoided
    }"""

new_stats = """def get_today_stats():
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as total FROM prediction_ledger WHERE timestamp >= %s", (cutoff,))
        total = c.fetchone()['total'] or 0
        c.execute("SELECT COUNT(*) as approved FROM prediction_ledger WHERE timestamp >= %s AND status = 'cleared'", (cutoff,))
        approved = c.fetchone()['approved'] or 0
        c.execute("SELECT COUNT(*) as rejected FROM prediction_ledger WHERE timestamp >= %s AND status = 'risk-rejected'", (cutoff,))
        rejected = c.fetchone()['rejected'] or 0
        c.execute("SELECT AVG(confidence_score) as avg_conf FROM prediction_ledger WHERE timestamp >= %s", (cutoff,))
        avg_conf = c.fetchone()['avg_conf'] or 0
        c.execute(\"\"\"
            SELECT asset, status, confidence_score, thesis
            FROM prediction_ledger 
            WHERE timestamp >= %s AND status = 'cleared'
            ORDER BY confidence_score DESC LIMIT 1
        \"\"\", (cutoff,))
        top = c.fetchone()
        c.execute("SELECT COUNT(*) as total FROM prediction_ledger")
        total_all = c.fetchone()['total'] or 0
        c.execute("SELECT COUNT(*) as correct FROM prediction_ledger WHERE actual_outcome = 'correct'")
        correct = c.fetchone()['correct'] or 0
        c.execute("SELECT COUNT(*) as with_outcome FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
        with_outcome = c.fetchone()['with_outcome'] or 0
        c.execute("SELECT COALESCE(SUM(avoided_drawdown), 0) as avoided FROM veto_archive")
        avoided = c.fetchone()['avoided'] or 0
        conn.close()
        accuracy = (correct / with_outcome * 100) if with_outcome > 0 else 0
        return {
            'total': total, 'approved': approved, 'rejected': rejected, 'avg_conf': avg_conf,
            'top': top, 'total_all': total_all, 'accuracy': accuracy, 'avoided': avoided
        }
    except Exception as e:
        print(f"Stats error: {e}")
        return {
            'total': 0, 'approved': 0, 'rejected': 0, 'avg_conf': 0,
            'top': None, 'total_all': 0, 'accuracy': 0, 'avoided': 0
        }"""
content = content.replace(old_stats, new_stats)

content = re.sub(r'SEED_PREDICTIONS = \[.*?\]\s*', '', content, flags=re.DOTALL)
content = re.sub(r'SEED_VETOES = \[.*?\]\s*', '', content, flags=re.DOTALL)

# 5. Fix build_email_body Date and new zero-observations block
old_build_email = """    init_research_tables()
    today = datetime.now().strftime('%Y-%m-%d')
    lines = []
    lines.append("+" + "=" * 58 + "+")
    lines.append("|     SOVEREIGN ALPHA -- DAILY INTELLIGENCE REPORT            |")
    lines.append("+" + "=" * 58 + "+")
    lines.append(f"  Date: {today}")
    lines.append(f"  Last Run Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")"""

new_build_email = """    init_research_tables()
    ist_tz = pytz.timezone('Asia/Kolkata')
    run_timestamp = datetime.now(timezone.utc).astimezone(ist_tz).strftime('%Y-%m-%d %H:%M:%S IST')
    lines = []
    lines.append("+" + "=" * 58 + "+")
    lines.append("|     SOVEREIGN ALPHA -- DAILY INTELLIGENCE REPORT            |")
    lines.append("+" + "=" * 58 + "+")
    lines.append(f"  Run Timestamp: {run_timestamp}")
    lines.append(f"  Status: SUCCESS")"""
content = content.replace(old_build_email, new_build_email)

old_new_obs = """    lines.append("")
    lines.append("-" * 60)
    lines.append("  NEW OBSERVATIONS TODAY")
    lines.append("-" * 60)
    today_obs = get_today_observations()
    print(f"Email Digest: Found {len(today_obs)} new observations.")
    if not today_obs:
        lines.append(f"  No new divergences detected. Pipeline ran successfully at {datetime.now().strftime('%H:%M:%S IST')}.")
    else:
        for obs in today_obs:
            lines.append(f"  [{obs[0][:16]}] {obs[1][:100]}")"""

new_new_obs = """    lines.append("")
    today_obs = get_today_observations()
    lines.append(f"  New Observations Today: {len(today_obs)}")
    print(f"Email Digest: Found {len(today_obs)} new observations.")
    if not today_obs:
        lines.append("  No new divergences were detected.")
        lines.append(f"  The pipeline executed successfully at {run_timestamp} but found no actionable signals.")
        lines.append("  The system is operational and quietly monitoring.")
    else:
        lines.append("-" * 60)
        lines.append("  NEW OBSERVATIONS TODAY")
        lines.append("-" * 60)
        for obs in today_obs:
            lines.append(f"  [{str(obs[0])[:16]}] {str(obs[1])[:100]}")"""
content = content.replace(old_new_obs, new_new_obs)

old_send = """    try:
        body = build_email_body()
    except Exception as e:
        err_msg = f"[WARN] build_email_body failed: {e}"
        print(err_msg)
        with open("email_errors.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - {err_msg}\\n")
        return False"""

new_send = """    try:
        body = build_email_body()
    except Exception as e:
        err_msg = f"[WARN] build_email_body failed: {e}"
        print(err_msg)
        with open("email_errors.log", "a") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} - {err_msg}\\n")
        # Prevent silent failures, send FAILED report
        ist_tz = pytz.timezone('Asia/Kolkata')
        run_timestamp = datetime.now(timezone.utc).astimezone(ist_tz).strftime('%Y-%m-%d %H:%M:%S IST')
        lines = []
        lines.append("+" + "=" * 58 + "+")
        lines.append("|     SOVEREIGN ALPHA -- DAILY INTELLIGENCE REPORT            |")
        lines.append("+" + "=" * 58 + "+")
        lines.append(f"  Run Timestamp: {run_timestamp}")
        lines.append(f"  Status: FAILED")
        lines.append("")
        lines.append("  The pipeline did not complete successfully.")
        lines.append(f"  Error details: {e}")
        lines.append("  Please check the logs.")
        body = "\\n".join(lines)"""
content = content.replace(old_send, new_send)

# Remove old init_tables logic
old_init_tables = """def init_tables():
    conn = get_connection()
    if not conn:
        return
    c = conn.cursor()
    c.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS prediction_ledger (
            id SERIAL PRIMARY KEY,
            prediction_id TEXT UNIQUE,
            timestamp TEXT NOT NULL,
            asset TEXT NOT NULL,
            sector TEXT,
            thesis TEXT,
            confidence_score REAL,
            status TEXT NOT NULL,
            expected_timeline_days INTEGER,
            actual_outcome TEXT,
            actual_return_pct REAL,
            outcome_notes TEXT,
            proof_hash TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    \"\"\")
    c.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS veto_archive (
            id SERIAL PRIMARY KEY,
            veto_id TEXT UNIQUE,
            prediction_id TEXT,
            timestamp TEXT NOT NULL,
            asset TEXT NOT NULL,
            sector TEXT,
            rejection_reason TEXT NOT NULL,
            expected_loss_pct REAL,
            actual_outcome TEXT,
            actual_return_pct REAL,
            avoided_drawdown REAL,
            veto_correct BOOLEAN,
            proof_hash TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    \"\"\")
    conn.commit()
    conn.close()"""
content = content.replace(old_init_tables, "def init_tables():\n    pass")

with open('automation/email_digest.py', 'w', encoding='utf-8') as f:
    f.write(content)
