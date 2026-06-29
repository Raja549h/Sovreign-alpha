import sys
import sqlite3
import traceback

sys.path.insert(0, 'C:/Users/lokes/Downloads/project/sovereign-alpha')

try:
    from dashboard.app import app, performance, calculate_ledger_stats
    print("Ledger stats:")
    print(calculate_ledger_stats())
    
    with app.test_request_context('/performance'):
        # Mock login user maybe not needed for the function if we just call it directly
        try:
            print("Running performance()...")
            res = performance()
            print("Performance returned successfully.")
        except Exception as e:
            print("Exception in performance:")
            traceback.print_exc()
            
except Exception as e:
    traceback.print_exc()
