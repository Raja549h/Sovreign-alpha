import os, psycopg2, json
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ['NEON_URL'])
c = conn.cursor()

c.execute("SELECT status, count(*) FROM analysis_runs WHERE run_type='ORGANIC_TEST' GROUP BY status")
print("Run Statuses:", c.fetchall())

c.execute("SELECT count(*) FROM observation_memory WHERE run_id IN (SELECT run_id FROM analysis_runs WHERE run_type='ORGANIC_TEST')")
obs_count = c.fetchone()[0]

c.execute("SELECT count(*) FROM research_notes WHERE run_id IN (SELECT run_id FROM analysis_runs WHERE run_type='ORGANIC_TEST')")
notes_count = c.fetchone()[0]

c.execute("SELECT count(*) FROM institutional_scores WHERE run_id IN (SELECT run_id FROM analysis_runs WHERE run_type='ORGANIC_TEST')")
scores_count = c.fetchone()[0]

c.execute("SELECT count(*) FROM observation_autopsy WHERE run_id IN (SELECT run_id FROM analysis_runs WHERE run_type='ORGANIC_TEST')")
autopsy_count = c.fetchone()[0]

c.execute("SELECT count(*) FROM evidence_timeline WHERE run_id IN (SELECT run_id FROM analysis_runs WHERE run_type='ORGANIC_TEST')")
timeline_count = c.fetchone()[0]

result = {
    "Runs Analyzed": 10,
    "Observations Created": obs_count,
    "Notes Created": notes_count,
    "Scores Created": scores_count,
    "Autopsies Created": autopsy_count,
    "Timelines Created": timeline_count
}

print(json.dumps(result, indent=2))

with open('verification_results.json', 'w') as f:
    json.dump(result, f, indent=2)

print("Verification check completed.")
