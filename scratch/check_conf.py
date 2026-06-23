import os, sys
sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv()
from dashboard.app import get_decisions

decs = get_decisions()
print("Total Decisions:", len(decs))
confidences = [d.get('confidence') for d in decs[:10]]
print("First 10 confidences:", confidences)

has_none = any(d.get('confidence') is None for d in decs)
print("Has None?", has_none)
