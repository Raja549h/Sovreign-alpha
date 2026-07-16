import sys
sys.path.insert(0, '.')
from automation.email_digest import load_env
load_env()
import dashboard.app
dashboard.app.seed_database_on_startup = lambda: None
from dashboard.app import get_dashboard_stats, get_decisions, get_sector_stats, get_return_distribution

try:
    print("Dashboard stats:", get_dashboard_stats())
except Exception as e:
    print("get_dashboard_stats error:", e)

try:
    print("Decisions:", len(get_decisions()))
except Exception as e:
    print("get_decisions error:", e)

try:
    print("Sector stats:", get_sector_stats())
except Exception as e:
    print("get_sector_stats error:", e)

try:
    print("Return dist:", get_return_distribution())
except Exception as e:
    print("get_return_distribution error:", e)
