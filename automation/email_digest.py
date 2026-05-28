"""
EMAIL DIGEST — Send daily intelligence report via email
Requires Gmail app password in .env
Shows realistic sample data when database is empty (demo mode).
"""

import os
import sys
import smtplib
import sqlite3
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BASE_DIR = Path(__file__).parent.parent
BILLING_DIR = BASE_DIR / "billing"
FUND_DATA_DB = BILLING_DIR / "fund_data.db"

# Load from .env
def load_env():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

DIGEST_EMAIL = os.environ.get("DIGEST_EMAIL", "")
DIGEST_PASSWORD = os.environ.get("DIGEST_PASSWORD", "")

# Realistic sample data for when database is empty
SAMPLE_STATS = {
    'total': 8,
    'approved': 5,
    'rejected': 3,
    'avg_conf': 82.5,
    'total_all': 342,
    'accuracy': 74.6,
    'avoided': 4250000
}

SAMPLE_TOP = {
    'asset': 'NVDA',
    'status': 'cleared',
    'confidence_score': 0.89,
    'thesis': 'AI infrastructure capex cycle accelerating. Data center GPU demand structurally undersupplied through 2027.'
}


def init_tables():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(str(FUND_DATA_DB))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS prediction_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS veto_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    """)
    conn.commit()
    conn.close()


def is_empty_db():
    """Check if database has any prediction data."""
    try:
        conn = sqlite3.connect(str(FUND_DATA_DB))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM prediction_ledger")
        cnt = c.fetchone()[0]
        conn.close()
        return cnt == 0
    except Exception:
        return True


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(FUND_DATA_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_today_stats():
    """Get today's prediction stats. Falls back to sample data if empty."""
    init_tables()

    if is_empty_db():
        return {
            'total': SAMPLE_STATS['total'],
            'approved': SAMPLE_STATS['approved'],
            'rejected': SAMPLE_STATS['rejected'],
            'avg_conf': SAMPLE_STATS['avg_conf'],
            'top': SAMPLE_TOP,
            'total_all': SAMPLE_STATS['total_all'],
            'accuracy': SAMPLE_STATS['accuracy'],
            'avoided': SAMPLE_STATS['avoided'],
            'demo_mode': True
        }

    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as total FROM prediction_ledger WHERE timestamp LIKE ?", (f"{today}%",))
    total = c.fetchone()['total'] or 0
    
    c.execute("SELECT COUNT(*) as approved FROM prediction_ledger WHERE timestamp LIKE ? AND status = 'cleared'", (f"{today}%",))
    approved = c.fetchone()['approved'] or 0
    
    c.execute("SELECT COUNT(*) as rejected FROM prediction_ledger WHERE timestamp LIKE ? AND status = 'risk-rejected'", (f"{today}%",))
    rejected = c.fetchone()['rejected'] or 0
    
    c.execute("SELECT AVG(confidence_score) as avg_conf FROM prediction_ledger WHERE timestamp LIKE ?", (f"{today}%",))
    avg_conf = c.fetchone()['avg_conf'] or 0
    
    # Get top recommendation
    c.execute("""
        SELECT asset, status, confidence_score, thesis 
        FROM prediction_ledger 
        WHERE timestamp LIKE ? AND status = 'cleared' 
        ORDER BY confidence_score DESC LIMIT 1
    """, (f"{today}%",))
    top = c.fetchone()
    
    # Get running totals
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
        'avg_conf': avg_conf * 100,
        'top': top,
        'total_all': total_all,
        'accuracy': accuracy,
        'avoided': avoided,
        'demo_mode': False
    }


def send_email():
    """Send daily digest email."""
    if not DIGEST_EMAIL or not DIGEST_PASSWORD:
        print("[SKIP] Email credentials not configured")
        return False
    
    stats = get_today_stats()
    today = datetime.now().strftime('%Y-%m-%d')
    
    top_rec = ""
    if stats['top']:
        score = stats['top']['confidence_score']
        if score > 1:
            score = score / 100
        top_rec = f"""{stats['top']['asset']} — {'BUY' if stats['top']['status'] == 'cleared' else 'HOLD'} — {score*100:.0f}%
{stats['top']['thesis'][:80]}"""
    else:
        top_rec = "No approved recommendations today"
    
    demo_tag = " [DEMO MODE — showing sample data]" if stats.get('demo_mode') else ""
    
    body = f"""SOVEREIGN ALPHA DAILY INTELLIGENCE REPORT
Date: {today}{demo_tag}
━━━━━━━━━━━━━━━━━━━━━━━━━━
PREDICTIONS TODAY: {stats['total']}
Approved: {stats['approved']}
Risk-Rejected: {stats['rejected']}
Avg Confidence: {stats['avg_conf']:.0f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━
TOP RECOMMENDATION:
{top_rec}
━━━━━━━━━━━━━━━━━━━━━━━━━━
RUNNING TOTALS:
Total predictions to date: {stats['total_all']}
Overall BUY accuracy: {stats['accuracy']:.1f}%
Avoided drawdown to date: ${stats['avoided']:,.0f}
Live days running: {(datetime.now() - datetime(2026, 1, 2)).days}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Dashboard: https://demonsatan-soverignalpha.hf.space
━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    msg = MIMEMultipart()
    msg['From'] = DIGEST_EMAIL
    msg['To'] = DIGEST_EMAIL
    msg['Subject'] = f"Sovereign Alpha — Daily Report [{today}]"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(DIGEST_EMAIL, DIGEST_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[OK] Email digest sent to {DIGEST_EMAIL}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False


if __name__ == '__main__':
    send_email()