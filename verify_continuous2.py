import os, time, psycopg2, json
from dotenv import load_dotenv

load_dotenv()
from dashboard.worker import BackgroundEngine

conn = psycopg2.connect(os.environ['NEON_URL'])
conn.autocommit = True
c = conn.cursor()

c.execute("DELETE FROM analysis_runs WHERE run_type='ORGANIC_TEST'")

print("Starting Background Engine...")
bg = BackgroundEngine(max_workers=5)
bg.start()

TICKERS = ['TCS', 'RELIANCE', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK']
run_ids = []
for ticker in TICKERS:
    c.execute(
        "INSERT INTO analysis_runs (ticker, run_type, status, current_step) VALUES (%s, %s, %s, %s) RETURNING run_id",
        (ticker, 'ORGANIC_TEST', 'PENDING', 'Queued')
    )
    rid = c.fetchone()[0]
    run_ids.append(rid)

print("Inserted 10 runs. Sleeping for 200 seconds while engine works...")
time.sleep(200)

bg.stop()

c.execute("SELECT count(*) FROM analysis_runs WHERE status = 'COMPLETED' AND run_id = ANY(%s::uuid[])", (run_ids,))
successful_runs = c.fetchone()[0]

c.execute("SELECT status FROM analysis_runs WHERE run_id = ANY(%s::uuid[])", (run_ids,))
statuses = c.fetchall()
failed_runs = sum(1 for s in statuses if s[0] == 'FAILED')

print(f"Successful: {successful_runs}, Failed: {failed_runs}, Pending: {10 - successful_runs - failed_runs}")

result = {
    "Total Runs": 10,
    "Successful": successful_runs,
    "Failed": failed_runs
}

with open('verification_results.json', 'w') as f:
    json.dump(result, f, indent=2)

print("Done.")
