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
    c.execute("INSERT INTO analysis_runs (ticker, run_type) VALUES (%s, %s) RETURNING run_id", (ticker, "ORGANIC_VERIFICATION"))
    run_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    return run_id

tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "JNJ"]
for t in tickers:
    rid = insert_job(t)
    print(f"Enqueued {t} -> {rid}")
