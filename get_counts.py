import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.environ['NEON_URL'])
c = conn.cursor()
c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [r[0] for r in c.fetchall()]

def get_count(table_name):
    if table_name in tables:
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        return c.fetchone()[0]
    return "TABLE NOT FOUND"

counts = {
    "observations": get_count("observations"),
    "predictions": get_count("prediction_ledger"),
    "validated_outcomes": get_count("observation_validations"),
    "evidence_events": get_count("evidence_timeline"),
    "calibration_events": get_count("calibration_history")
}

print("Baseline counts:")
for k, v in counts.items():
    print(f"{k}: {v}")
