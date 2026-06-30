import sys
import os
sys.path.insert(0, 'C:/Users/lokes/Downloads/project/sovereign-alpha')
from dotenv import load_dotenv
load_dotenv()
from database import get_connection, init_pool

def purge_non_indian_tickers():
    init_pool()
    conn = get_connection()
    c = conn.cursor()
    
    indian_tickers = ('RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'KOTAKBANK.NS', 'HCLTECH.NS', 'BAJFINANCE.NS', 'TRENT.NS', 'SUNPHARMA.NS', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'HCLTECH', 'BAJFINANCE', 'TRENT', 'SUNPHARMA')
    
    # 1. prediction_ledger
    c.execute(f"DELETE FROM prediction_ledger WHERE asset NOT IN {indian_tickers}")
    print(f"Deleted {c.rowcount} non-Indian rows from prediction_ledger.")
    
    # 2. veto_archive
    c.execute(f"DELETE FROM veto_archive WHERE asset NOT IN {indian_tickers}")
    print(f"Deleted {c.rowcount} non-Indian rows from veto_archive.")
    
    # 3. observations
    # For observations, we discovered earlier it might use 'ticker'
    try:
        c.execute(f"DELETE FROM observations WHERE ticker NOT IN {indian_tickers}")
        print(f"Deleted {c.rowcount} non-Indian rows from observations.")
    except Exception as e:
        print("Error deleting from observations:", e)

    # 4. evidence_timeline
    print("Purging STRESS_TEST from evidence_timeline...")
    try:
        c.execute("DELETE FROM evidence_timeline WHERE event_type = 'STRESS_TEST'")
        print(f"Deleted {c.rowcount} STRESS_TEST rows from evidence_timeline.")
    except Exception as e:
        print("Error deleting STRESS_TEST from evidence_timeline:", e)
        
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == '__main__':
    purge_non_indian_tickers()
