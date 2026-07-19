import datetime
import os
import smtplib
from email.mime.text import MIMEText
from dashboard.gateway import get_connection as db_get_connection

try:
    from scheduler_instance import scheduler
except ImportError:
    scheduler = None

def check_pipeline_health():
    now = datetime.datetime.utcnow()
    
    status = "PASS"
    checks = {
        "database_connection": "FAIL",
        "scheduler_active": "FAIL",
        "last_run_time": None,
        "last_run_age_hours": None,
        "recent_observations": 0,
        "recent_predictions": 0,
        "scheduler_jobs_count": 0,
        "last_cycle_exception": None
    }
    
    # 1. Check Database Connection
    try:
        with db_get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT 1")
            if c.fetchone() is not None:
                checks["database_connection"] = "PASS"
    except Exception:
        checks["database_connection"] = "FAIL"
        
    # 2. Check Scheduler
    try:
        if scheduler is not None:
            checks["scheduler_active"] = "PASS" if scheduler.running else "FAIL"
            checks["scheduler_jobs_count"] = len(scheduler.get_jobs())
        else:
            checks["scheduler_active"] = "FAIL"
            checks["scheduler_jobs_count"] = 0
    except Exception:
        checks["scheduler_active"] = "FAIL"
        checks["scheduler_jobs_count"] = 0
        
    # 3. Check Last Run Time
    try:
        with db_get_connection() as conn:
            c = conn.cursor()
            # Try to get max created_at from observations or prediction_ledger
            c.execute("SELECT MAX(timestamp) FROM observations")
            obs_max = c.fetchone()[0]
            
            c.execute("SELECT MAX(timestamp) FROM prediction_ledger")
            pred_max = c.fetchone()[0]
            
            max_times = []
            if obs_max:
                try:
                    if isinstance(obs_max, str):
                        max_times.append(datetime.datetime.fromisoformat(obs_max.replace('Z', '+00:00')).replace(tzinfo=None))
                except Exception: pass
            if pred_max:
                try:
                    if isinstance(pred_max, str):
                        max_times.append(datetime.datetime.fromisoformat(pred_max.replace('Z', '+00:00')).replace(tzinfo=None))
                except Exception: pass
                
            if max_times:
                last_run_dt = max(max_times)
                checks["last_run_time"] = last_run_dt.strftime("%Y-%m-%d %H:%M:%S")
                checks["last_run_age_hours"] = round((now - last_run_dt).total_seconds() / 3600, 2)
    except Exception:
        pass
        
    # 4. Check Recent Observations
    try:
        with db_get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM observations WHERE timestamp > %s", ((now - datetime.timedelta(days=1)).isoformat() + 'Z',))
            checks["recent_observations"] = c.fetchone()[0]
    except Exception:
        pass
        
    # 5. Check Recent Predictions
    try:
        with db_get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE timestamp > %s", ((now - datetime.timedelta(days=1)).isoformat() + 'Z',))
            checks["recent_predictions"] = c.fetchone()[0]
    except Exception:
        pass
        
    # Status Evaluation Logic
    if checks["database_connection"] == "FAIL" or checks["scheduler_active"] == "FAIL" or checks["scheduler_jobs_count"] == 0:
        status = "FAIL"
    elif checks.get("last_run_age_hours") is not None and checks["last_run_age_hours"] > 26:
        status = "WARNING"
    elif checks["recent_observations"] == 0 and checks["recent_predictions"] == 0:
        status = "WARNING"
    else:
        status = "PASS"
        
    # Verdict text formatting
    if status == "FAIL":
        verdict = "CRITICAL FAIL: System components offline."
        if checks["database_connection"] == "FAIL": verdict += " Database unreachable."
        if checks["scheduler_active"] == "FAIL" or checks["scheduler_jobs_count"] == 0: verdict += " Scheduler inactive or missing jobs."
    elif status == "WARNING":
        if checks.get("last_run_age_hours") is not None and checks["last_run_age_hours"] > 26:
            verdict = f"WARNING: Last run was {checks['last_run_age_hours']} hours ago. System may be stalled."
        else:
            verdict = "WARNING: Pipeline ran but produced no new data in the last 24 hours."
    else:
        age_str = f"{checks['last_run_age_hours']} hours" if checks.get("last_run_age_hours") is not None else "recently"
        verdict = f"Pipeline running normally. Last run {age_str} ago."
        
    # SLA Check: Send email alert if 08:45 IST run failed to produce new observations within 3 hours (by 11:45 IST)
    ist_now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
    if ist_now.hour == 11 and ist_now.minute >= 45:
        # Check today's observations specifically
        try:
            today_845_ist = datetime.datetime(ist_now.year, ist_now.month, ist_now.day, 8, 45)
            today_845_utc = (today_845_ist - datetime.timedelta(hours=5, minutes=30)).isoformat() + 'Z'
            
            with db_get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM observations WHERE timestamp > %s", (today_845_utc,))
                todays_obs = c.fetchone()[0]
                
            if todays_obs == 0:
                # Need to send alert, ensure we only send once per day by checking a lockfile
                lock_file = "/tmp/pipeline_alert_" + ist_now.strftime('%Y%m%d') + ".lock"
                if not os.path.exists(lock_file):
                    _send_alert_email("Sovereign Alpha: SLA Breach Alert", "The 08:45 IST pipeline run failed to produce any new observations within the 3-hour SLA window.")
                    with open(lock_file, "w") as f:
                        f.write(ist_now.isoformat())
        except Exception as e:
            print(f"Error checking SLA or sending alert: {e}")
            
    return {
        "status": status,
        "checks": checks,
        "verdict": verdict
    }

def _send_alert_email(subject, body):
    digest_email = os.environ.get("DIGEST_EMAIL")
    digest_password = os.environ.get("DIGEST_PASSWORD")
    if not digest_email or not digest_password:
        print("DIGEST_EMAIL or DIGEST_PASSWORD not configured. Cannot send alert.")
        return
        
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = digest_email
        msg['To'] = digest_email
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(digest_email, digest_password)
        server.send_message(msg)
        server.quit()
        print("SLA alert email sent successfully.")
    except Exception as e:
        print(f"Failed to send SLA alert email: {e}")
