import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from dotenv import load_dotenv
load_dotenv()
from database import get_connection

def insert_job(ticker):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO analysis_runs (ticker, run_type) VALUES (%s, %s) RETURNING run_id", (ticker, "MANUAL"))
    run_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    return run_id

def check_status(run_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT status, progress_pct, current_step FROM analysis_runs WHERE run_id = %s", (run_id,))
    res = c.fetchone()
    conn.close()
    return res

if __name__ == "__main__":
    import uuid
    ticker = "RELIANCE"
    print(f"Inserting job for {ticker}...")
    run_id = insert_job(ticker)
    print(f"Inserted job {run_id}")
    
    for i in range(20):
        time.sleep(5)
        status, pct, step = check_status(run_id)
        print(f"Status: {status}, Progress: {pct}%, Step: {step}")
        if status in ['COMPLETED', 'FAILED']:
            break
