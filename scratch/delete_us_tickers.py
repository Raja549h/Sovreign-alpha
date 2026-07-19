import os
import sys
from dotenv import load_dotenv
load_dotenv()

# database is in root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dashboard.gateway import get_db_connection

def run_deletions():
    print("Deleting US tickers from prediction_ledger and observations...")
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            us_tickers = ('AMD', 'TSM', 'CVX', 'XOM')
            
            c.execute("DELETE FROM prediction_ledger WHERE asset IN %s", (us_tickers,))
            print(f"Deleted {c.rowcount} rows from prediction_ledger.")
            
            c.execute("DELETE FROM observations WHERE ticker IN %s", (us_tickers,))
            print(f"Deleted {c.rowcount} rows from observations.")
            
            # Also clean up veto_archive just in case
            c.execute("DELETE FROM veto_archive WHERE asset IN %s", (us_tickers,))
            print(f"Deleted {c.rowcount} rows from veto_archive.")
            
    except Exception as e:
        print(f"Error during deletions: {e}")

if __name__ == "__main__":
    run_deletions()
