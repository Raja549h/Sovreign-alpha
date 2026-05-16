"""
SETUP SCHEDULER — Run ONCE to register all automated tasks
===========================================================
This script sets up Windows Task Scheduler to run:
1. Daily cycle at 9:00 AM IST
2. Keep-alive ping every 10 minutes
3. Weekly report every Sunday at 9:00 AM

Run this script ONCE. After that everything runs automatically.
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
LOGS_DIR = AUTOMATION_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"

# Ensure directories exist
for d in [AUTOMATION_DIR, LOGS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def get_python_path():
    """Get the Python executable path."""
    return sys.executable


def get_batch_path():
    """Get the full path to run_daily.bat."""
    return str(AUTOMATION_DIR / "run_daily.bat")


def create_run_daily_bat():
    """Create the Windows batch file for daily cycle."""
    python_path = get_python_path()
    base_dir = str(BASE_DIR)
    
    batch_content = f"""@echo off
REM Sovereign Alpha - Daily Cycle Automation
REM This file runs automatically via Windows Task Scheduler

setlocal

REM Set working directory
cd /d "{base_dir}"

REM Set log file with date
set LOGFILE="{str(LOGS_DIR)}\\daily_log_%DATE:/=-%.txt"

echo ======================================== >> %LOGFILE%
echo Sovereign Alpha Daily Cycle >> %LOGFILE%
echo Started: %DATE% %TIME% >> %LOGFILE%
echo ======================================== >> %LOGFILE%

REM Run daily cycle
"{python_path}" operations\daily_cycle.py >> %LOGFILE% 2>&1

echo. >> %LOGFILE%
echo Daily cycle completed: %TIME% >> %LOGFILE%

REM Run outcome tracker
"{python_path}" automation\outcome_tracker.py >> %LOGFILE% 2>&1

echo Outcome tracking completed: %TIME% >> %LOGFILE%

REM Run email digest (if configured)
"{python_path}" automation\email_digest.py >> %LOGFILE% 2>&1

echo Email digest sent: %TIME% >> %LOGFILE%

REM Git sync
cd /d "{base_dir}"
git add backtesting/historical_data/ backtesting/checkpoints/ billing/fund_data.db >> %LOGFILE% 2>&1
git commit -m "Daily cycle %DATE% automated" >> %LOGFILE% 2>&1
git push origin main >> %LOGFILE% 2>&1

echo Git sync completed: %TIME% >> %LOGFILE%

echo ======================================== >> %LOGFILE%
echo All tasks completed >> %LOGFILE%
echo ======================================== >> %LOGFILE%

endlocal
"""
    
    batch_file = AUTOMATION_DIR / "run_daily.bat"
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    print(f"[OK] Created: {batch_file}")
    return str(batch_file)


def create_keep_alive_bat():
    """Create batch file for keep-alive ping."""
    python_path = get_python_path()
    base_dir = str(BASE_DIR)
    
    batch_content = f"""@echo off
REM Sovereign Alpha - Dashboard Keep-Alive
cd /d "{base_dir}"
"{python_path}" automation\keep_alive.py
"""
    
    batch_file = AUTOMATION_DIR / "run_keep_alive.bat"
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    print(f"[OK] Created: {batch_file}")
    return str(batch_file)


def create_weekly_report_bat():
    """Create batch file for weekly report."""
    python_path = get_python_path()
    base_dir = str(BASE_DIR)
    
    batch_content = f"""@echo off
REM Sovereign Alpha - Weekly Report
cd /d "{base_dir}"
"{python_path}" automation\weekly_report.py
"""
    
    batch_file = AUTOMATION_DIR / "run_weekly_report.bat"
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    print(f"[OK] Created: {batch_file}")
    return str(batch_file)


def task_exists(task_name):
    """Check if a scheduled task already exists."""
    try:
        result = subprocess.run(
            ['schtasks', '/query', '/tn', task_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False


def delete_task(task_name):
    """Delete an existing scheduled task."""
    try:
        subprocess.run(
            ['schtasks', '/delete', '/tn', task_name, '/f'],
            capture_output=True,
            timeout=10
        )
        print(f"  Deleted existing task: {task_name}")
    except:
        pass


def create_task(task_name, batch_path, schedule_type, schedule_args):
    """Create a Windows scheduled task."""
    if task_exists(task_name):
        print(f"  Task already exists: {task_name} (skipping)")
        return True
    
    cmd = [
        'schtasks', '/create',
        '/tn', task_name,
        '/tr', f'"{batch_path}"',
        '/sc', schedule_type,
        '/f'  # Force overwrite
    ]
    cmd.extend(schedule_args)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"[OK] Created task: {task_name}")
            return True
        else:
            print(f"[WARN] Could not create task: {task_name}")
            print(f"  Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to create task: {task_name}: {e}")
        return False


def main():
    """Set up all scheduled tasks."""
    print("="*60)
    print("SOVEREIGN ALPHA — AUTOMATION SETUP")
    print("="*60)
    print(f"Base directory: {BASE_DIR}")
    print(f"Python: {get_python_path()}")
    print()
    
    # Step 1: Create batch files
    print("Step 1: Creating batch files...")
    daily_bat = create_run_daily_bat()
    keepalive_bat = create_keep_alive_bat()
    weekly_bat = create_weekly_report_bat()
    print()
    
    # Step 2: Register with Windows Task Scheduler
    print("Step 2: Registering scheduled tasks...")
    
    # Daily cycle at 9:00 AM
    print("\n  [Daily Cycle] 9:00 AM")
    create_task(
        "SovereignAlpha_DailyCycle",
        daily_bat,
        "daily",
        ["/st", "09:00"]
    )
    
    # Keep-alive every 10 minutes
    print("\n  [Keep-Alive] Every 10 minutes")
    create_task(
        "SovereignAlpha_KeepAlive",
        keepalive_bat,
        "minute",
        ["/mo", "10"]
    )
    
    # Weekly report every Sunday at 9:00 AM
    print("\n  [Weekly Report] Sunday 9:00 AM")
    create_task(
        "SovereignAlpha_WeeklyReport",
        weekly_bat,
        "weekly",
        ["/d", "SUN", "/st", "09:00"]
    )
    
    # Step 3: Verify tasks
    print("\nStep 3: Verifying tasks...")
    tasks = [
        "SovereignAlpha_DailyCycle",
        "SovereignAlpha_KeepAlive",
        "SovereignAlpha_WeeklyReport"
    ]
    
    all_ok = True
    for task_name in tasks:
        if task_exists(task_name):
            print(f"  [OK] {task_name}")
        else:
            print(f"  [MISSING] {task_name}")
            all_ok = False
    
    print()
    if all_ok:
        print("="*60)
        print("SETUP COMPLETE")
        print("="*60)
        print("Daily cycle scheduled successfully")
        print("All tasks registered with Windows Task Scheduler")
        print()
        print("Next steps:")
        print("1. Add Gmail app password to .env for email digest")
        print("2. Run: py automation/check_status.py to verify")
        print("="*60)
    else:
        print("="*60)
        print("SETUP PARTIAL")
        print("="*60)
        print("Some tasks could not be created.")
        print("Run this script as Administrator if needed.")
        print("="*60)


if __name__ == '__main__':
    main()