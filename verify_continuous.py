import os
import time
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

from dashboard.worker import BackgroundEngine

TICKERS = ['TCS', 'RELIANCE', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK']

def run_verification():
    print("Starting Background Engine...")
    bg = BackgroundEngine(max_workers=5)
    bg.start()
    
    conn = psycopg2.connect(os.environ['NEON_URL'])
    conn.autocommit = True
    c = conn.cursor()
    
    run_ids = []
    print("Submitting 10 runs...")
    for ticker in TICKERS:
        c.execute(
            "INSERT INTO analysis_runs (ticker, run_type, status, current_step) VALUES (%s, %s, %s, %s) RETURNING run_id",
            (ticker, 'ORGANIC_TEST', 'PENDING', 'Queued')
        )
        rid = c.fetchone()[0]
        run_ids.append(rid)
    
    print("Waiting for runs to complete...")
    completed = 0
    while completed < 10:
        c.execute("SELECT status, current_step FROM analysis_runs WHERE run_id = ANY(%s::uuid[])", (run_ids,))
        rows = c.fetchall()
        
        completed = sum(1 for r in rows if r[0] in ('COMPLETED', 'FAILED'))
        print(f"Progress: {completed}/10 completed...")
        if completed < 10:
            time.sleep(5)
            
    print("All runs finished executing. Verifying...")
    
    failures = 0
    for rid in run_ids:
        c.execute("SELECT status FROM analysis_runs WHERE run_id = %s", (rid,))
        status = c.fetchone()[0]
        if status == 'FAILED':
            failures += 1
            
    c.execute("SELECT count(*) FROM observation_memory WHERE run_id = ANY(%s::uuid[])", (run_ids,))
    obs_count = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM research_notes WHERE run_id = ANY(%s::uuid[])", (run_ids,))
    notes_count = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM institutional_scores WHERE run_id = ANY(%s::uuid[])", (run_ids,))
    scores_count = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM observation_autopsy WHERE run_id = ANY(%s::uuid[])", (run_ids,))
    autopsy_count = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM evidence_timeline WHERE run_id = ANY(%s::uuid[])", (run_ids,))
    timeline_count = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM analysis_runs WHERE status = 'COMPLETED' AND run_id = ANY(%s::uuid[])", (run_ids,))
    successful_runs = c.fetchone()[0]
    
    result = {
        "Total Runs": 10,
        "Successful": successful_runs,
        "Failed": failures,
        "Observations Created": obs_count,
        "Notes Created": notes_count,
        "Scores Created": scores_count,
        "Autopsies Created": autopsy_count,
        "Timelines Created": timeline_count
    }
    
    print(json.dumps(result, indent=2))
    
    bg.stop()
    
    with open('verification_results.json', 'w') as f:
        json.dump(result, f, indent=2)

if __name__ == '__main__':
    run_verification()
