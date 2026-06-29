import sys, os, traceback
sys.path.insert(0, os.path.abspath('dashboard'))
from app import calculate_ledger_stats

try:
    stats = calculate_ledger_stats()
    print("STATS:")
    import pprint
    pprint.pprint(stats)
except Exception as e:
    traceback.print_exc()
