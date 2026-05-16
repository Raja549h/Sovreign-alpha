"""
KEEP-ALIVE — Ping dashboard every 10 minutes to prevent Render spin-down
"""

import requests
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "automation" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DASHBOARD_URL = "https://sovereign-alpha.onrender.com/health"


def ping_dashboard():
    """Ping the dashboard health endpoint."""
    try:
        response = requests.get(DASHBOARD_URL, timeout=30)
        status = response.status_code
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Dashboard alive: {status}")
        
        # Log to file
        log_file = LOGS_DIR / f"keepalive_{datetime.now().strftime('%Y-%m-%d')}.txt"
        with open(log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - Status: {status}\n")
        
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ping failed: {e}")
        return False


if __name__ == '__main__':
    ping_dashboard()