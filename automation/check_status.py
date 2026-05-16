"""
CHECK STATUS — Verify all automation components are operational
Run this to audit the entire Sovereign Alpha system.
"""

import os
import sys
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
LOGS_DIR = AUTOMATION_DIR / "logs"
BILLING_DIR = BASE_DIR / "billing"
FUND_DATA_DB = BILLING_DIR / "fund_data.db"


def load_env():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def check_task_scheduler():
    """Verify Windows Task Scheduler tasks are registered."""
    print("\n[Task Scheduler]")
    tasks = [
        "SovereignAlpha_DailyCycle",
        "SovereignAlpha_KeepAlive",
        "SovereignAlpha_WeeklyReport"
    ]
    all_ok = True
    for task_name in tasks:
        try:
            result = subprocess.run(
                ['schtasks', '/query', '/tn', task_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"  [OK] {task_name}")
            else:
                print(f"  [MISSING] {task_name}")
                all_ok = False
        except Exception as e:
            print(f"  [ERROR] {task_name}: {e}")
            all_ok = False
    return all_ok


def check_database():
    """Verify database integrity and record counts."""
    print("\n[Database]")
    if not FUND_DATA_DB.exists():
        print(f"  [MISSING] {FUND_DATA_DB}")
        return False

    try:
        conn = sqlite3.connect(str(FUND_DATA_DB))
        cursor = conn.cursor()

        # Check prediction_ledger
        cursor.execute("SELECT COUNT(*) FROM prediction_ledger")
        pred_count = cursor.fetchone()[0]
        print(f"  [OK] prediction_ledger: {pred_count} records")

        # Check veto_archive
        cursor.execute("SELECT COUNT(*) FROM veto_archive")
        veto_count = cursor.fetchone()[0]
        print(f"  [OK] veto_archive: {veto_count} records")

        # Check recent predictions
        cursor.execute(
            "SELECT COUNT(*) FROM prediction_ledger WHERE timestamp > datetime('now', '-7 days')"
        )
        recent = cursor.fetchone()[0]
        print(f"  [OK] Predictions (last 7 days): {recent}")

        conn.close()
        return True
    except Exception as e:
        print(f"  [ERROR] Database check failed: {e}")
        return False


def check_email_config():
    """Verify email digest configuration."""
    print("\n[Email Digest]")
    load_env()
    email = os.environ.get("DIGEST_EMAIL", "")
    password = os.environ.get("DIGEST_PASSWORD", "")

    if email and password:
        print(f"  [OK] DIGEST_EMAIL: {email}")
        print(f"  [OK] DIGEST_PASSWORD: {'*' * len(password)}")
        return True
    else:
        print("  [WARN] Email not configured")
        return False


def check_batch_files():
    """Verify .bat wrapper files exist."""
    print("\n[Batch Files]")
    bat_files = [
        "run_daily.bat",
        "run_keep_alive.bat",
        "run_weekly_report.bat"
    ]
    all_ok = True
    for bat in bat_files:
        bat_path = AUTOMATION_DIR / bat
        if bat_path.exists():
            print(f"  [OK] {bat}")
        else:
            print(f"  [MISSING] {bat}")
            all_ok = False
    return all_ok


def check_logs():
    """Verify recent log activity."""
    print("\n[Logs]")
    if not LOGS_DIR.exists():
        print("  [MISSING] logs directory")
        return False

    log_files = list(LOGS_DIR.glob("*.txt"))
    if not log_files:
        print("  [WARN] No log files found")
        return False

    today = datetime.now().strftime('%Y-%m-%d')
    today_logs = [f for f in log_files if today in f.name]

    print(f"  [OK] Total log files: {len(log_files)}")
    print(f"  [OK] Today's logs: {len(today_logs)}")

    for log in today_logs:
        print(f"    - {log.name}")

    return True


def check_dashboard():
    """Ping dashboard health endpoint."""
    print("\n[Dashboard]")
    try:
        import requests
        url = "https://sovereign-alpha.onrender.com/health"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            print(f"  [OK] Dashboard responding: {response.status_code}")
            return True
        else:
            print(f"  [WARN] Dashboard status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] Dashboard unreachable: {e}")
        return False


def main():
    print("=" * 60)
    print("SOVEREIGN ALPHA — SYSTEM STATUS CHECK")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    checks = {
        "Task Scheduler": check_task_scheduler(),
        "Database": check_database(),
        "Email Config": check_email_config(),
        "Batch Files": check_batch_files(),
        "Logs": check_logs(),
        "Dashboard": check_dashboard()
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_ok = True
    for name, status in checks.items():
        symbol = "[OK]" if status else "[FAIL]"
        print(f"  {symbol} {name}")
        if not status:
            all_ok = False

    print("=" * 60)
    if all_ok:
        print("STATUS: ALL SYSTEMS OPERATIONAL")
    else:
        print("STATUS: ATTENTION REQUIRED")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
