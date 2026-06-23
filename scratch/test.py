import os, sys, traceback
sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv()
from dashboard.app import get_dashboard_stats

try:
    print('Dashboard Stats:', get_dashboard_stats())
except Exception as e:
    traceback.print_exc()
