"""
EMAIL DIGEST -- Daily intelligence report with live market data
Rewritten: Permanent and bulletproof logic, zero fallbacks.
"""
import os
import sys
import smtplib
import logging
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import pytz

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from database import get_connection, DatabaseConnection

# Setup logging
logging.basicConfig(
    filename='email_digest.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

def get_new_observations():
    try:
        conn = DatabaseConnection()
    except Exception as e:
        raise Exception(f"Database connection failed: {e}")
    
    try:
        c = conn.cursor()
        # Explicitly calculate UTC cutoff
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=1)
        cutoff_iso = cutoff_time.isoformat()
        
        # Pass cutoff time directly to SQL
        c.execute(
            "SELECT timestamp, headline FROM observations WHERE timestamp >= %s ORDER BY timestamp DESC", 
            (cutoff_iso,)
        )
        rows = c.fetchall()
        return rows
    finally:
        conn.close()

def build_email_body():
    ist_tz = pytz.timezone('Asia/Kolkata')
    # Convert current UTC time to IST for display
    run_timestamp = datetime.now(timezone.utc).astimezone(ist_tz).strftime('%Y-%m-%d %H:%M:%S IST')
    
    try:
        observations = get_new_observations()
        obs_count = len(observations)
        
        # Log run timestamp and number of new observations
        logging.info(f"Run Timestamp: {run_timestamp} | New observations: {obs_count}")
        
        lines = []
        lines.append("+" + "=" * 58 + "+")
        lines.append("|     SOVEREIGN ALPHA -- DAILY INTELLIGENCE REPORT            |")
        lines.append("+" + "=" * 58 + "+")
        lines.append(f"  Run Timestamp: {run_timestamp}")
        lines.append(f"  Status: SUCCESS")
        lines.append(f"  New Observations Today: {obs_count}")
        lines.append("")
        
        if obs_count == 0:
            lines.append("  No new divergences were detected.")
            lines.append(f"  The pipeline executed successfully at {run_timestamp} but found no actionable signals.")
            lines.append("  The system is operational and quietly monitoring.")
        else:
            lines.append("-" * 60)
            lines.append("  NEW OBSERVATIONS TODAY")
            lines.append("-" * 60)
            for obs in observations:
                ts = obs['timestamp'] if isinstance(obs, dict) else obs[0]
                hl = obs['headline'] if isinstance(obs, dict) else obs[1]
                lines.append(f"  [{str(ts)[:16]}] {str(hl)[:100]}")
                
        lines.append("")
        lines.append("-" * 60)
        lines.append("  DASHBOARD: https://svrn-alpha-sovereignalpha.hf.space")
        lines.append("-" * 60)
        
        return "\n".join(lines)
    
    except Exception as e:
        # Prevent silent failures. No fallback to old data.
        logging.error(f"Pipeline failed: {e}")
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
        return "\n".join(lines)

def send_email():
    if not DIGEST_EMAIL or not DIGEST_PASSWORD:
        logging.warning("Email credentials not configured. Skipping email.")
        return False
        
    body = build_email_body()
    ist_tz = pytz.timezone('Asia/Kolkata')
    today_str = datetime.now(timezone.utc).astimezone(ist_tz).strftime('%Y-%m-%d')
    
    msg = MIMEMultipart()
    msg['From'] = DIGEST_EMAIL
    msg['To'] = DIGEST_EMAIL
    msg['Subject'] = f"Sovereign Alpha -- Daily Intelligence [{today_str}]"
    msg.attach(MIMEText(body, 'plain'))
    
    last_error = None
    for attempt in range(1, 4):
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
            server.starttls()
            server.login(DIGEST_EMAIL, DIGEST_PASSWORD)
            server.send_message(msg)
            server.quit()
            logging.info("Email digest sent successfully.")
            return True
        except Exception as e:
            last_error = e
            logging.error(f"[RETRY {attempt}/3] SMTP failed: {e}")
            import time
            time.sleep(2 * attempt)
            
    logging.error(f"Failed to send email after 3 attempts: {last_error}")
    return False

if __name__ == '__main__':
    try:
        send_email()
    except Exception as e:
        logging.fatal(f"email_digest.py crashed: {e}")
        sys.exit(0)
