import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from research.storage.research_db import get_all_companies
from research.intelligence.forensic_detector import run_all_detectors

companies = get_all_companies()
print(f"Running forensic detector on {len(companies)} companies...")
for c in companies:
    try:
        flags = run_all_detectors(c['id'])
        print(f"{c['ticker']}: found {len(flags)} flags")
    except Exception as e:
        print(f"{c['ticker']}: error - {e}")
