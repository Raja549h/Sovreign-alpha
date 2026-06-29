import os, sys
sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv()
from dashboard.app import db_get_connection
from database import init_pool

init_pool()

try:
    from research.macro.fii_flow import build_flow_intelligence_report
    report = build_flow_intelligence_report()
    print("FII FLOW REPORT:", report)
except Exception as e:
    print("ERROR:", e)
