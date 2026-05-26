"""
EMAIL DIGEST — Send daily intelligence report via email
Requires Gmail app password in .env
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


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(FUND_DATA_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_today_stats():
    """Get today's prediction stats."""
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
        'avoided': avoided
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
        top_rec = f"""{stats['top']['asset']} — {'BUY' if stats['top']['status'] == 'cleared' else 'HOLD'} — {stats['top']['confidence_score']*100:.0f}%
{stats['top']['thesis'][:80]}"""
    else:
        top_rec = "No approved recommendations today"
    
    body = f"""SOVEREIGN ALPHA DAILY INTELLIGENCE REPORT
Date: {today}
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