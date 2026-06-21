import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['NEON_URL'])
conn.autocommit = True
c = conn.cursor()

print("Cleaning up old test data...")
c.execute("DELETE FROM evidence_timeline WHERE run_id IS NOT NULL")
c.execute("DELETE FROM observation_autopsy WHERE run_id IS NOT NULL")
c.execute("DELETE FROM institutional_scores WHERE run_id IS NOT NULL")
c.execute("DELETE FROM research_notes WHERE run_id IS NOT NULL")
c.execute("DELETE FROM observation_memory WHERE run_id IS NOT NULL")
c.execute("DELETE FROM analysis_run_events")
c.execute("DELETE FROM analysis_runs")

print("Cleaned up database.")
