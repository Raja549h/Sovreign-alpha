import sys
import os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from database import get_connection

approved_tickers = ('RELIANCE.NS','TCS.NS','HDFCBANK.NS','INFY.NS','SBIN.NS','BHARTIARTL.NS','ITC.NS','KOTAKBANK.NS','HCLTECH.NS','BAJFINANCE.NS','TRENT.NS','SUNPHARMA.NS')
approved_assets = tuple([t.replace('.NS', '') for t in approved_tickers])

queries = [
    f"DELETE FROM prediction_ledger WHERE asset NOT IN {approved_assets};",
    f"DELETE FROM observations WHERE company NOT IN {approved_assets};",
    f"DELETE FROM veto_archive WHERE asset NOT IN {approved_assets};",
    "DELETE FROM evidence_timeline WHERE event_type ILIKE ANY(ARRAY['%test%', '%simulated%', '%stress%', '%verification%', '%e2e%']);"
]

try:
    with get_connection() as conn:
        c = conn.cursor()
        for q in queries:
            print(f'Executing: {q}')
            c.execute(q)
        conn.commit()
        print('Sweep complete.')
except Exception as e:
    print('Failed:', e)
