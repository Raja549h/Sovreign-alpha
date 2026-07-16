import sys
import os
sys.path.insert(0, '.')

from automation.email_digest import load_env
load_env()

# Mock seed_database_on_startup before importing app
import dashboard.app
dashboard.app.seed_database_on_startup = lambda: None

from dashboard.app import get_dashboard_stats, get_decisions, get_sector_stats, get_return_distribution, load_results_files, calculate_ledger_stats

try:
    print("get_dashboard_stats")
    get_dashboard_stats()
except Exception as e: print("FAILED get_dashboard_stats:", e)

try:
    print("get_decisions")
    get_decisions()
except Exception as e: print("FAILED get_decisions:", e)

try:
    print("get_sector_stats")
    get_sector_stats()
except Exception as e: print("FAILED get_sector_stats:", e)

try:
    print("get_return_distribution")
    get_return_distribution()
except Exception as e: print("FAILED get_return_distribution:", e)

try:
    print("load_results_files")
    load_results_files()
except Exception as e: print("FAILED load_results_files:", e)

try:
    print("calculate_ledger_stats")
    calculate_ledger_stats()
except Exception as e: print("FAILED calculate_ledger_stats:", e)
