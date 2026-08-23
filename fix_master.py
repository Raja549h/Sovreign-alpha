import re
import os

with open('automation/master_daily.py', 'r') as f:
    content = f.read()

conn_code = '''
import psycopg2
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(os.environ.get('AIVEN_DATABASE_URL') or os.environ.get('DATABASE_URL'))
    try:
        yield conn
    finally:
        conn.close()

get_connection = get_db_connection
'''
content = content.replace('import traceback', conn_code + '\nimport traceback')

content = content.replace('from dashboard.gateway import get_db_connection, get_connection', 'pass  # locally defined')
content = content.replace('from dashboard.gateway import get_connection as _get_conn', '_get_conn = get_db_connection')

obs_check_code = '''
    # Step 2.5: Validate new observations
    log("[2.5/8] Validating fresh observations...")
    new_observations = []
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM observations WHERE timestamp >= NOW() - INTERVAL '14 days'")
            new_observations = c.fetchall()
    except Exception as e:
        log(f"      WARN: Failed to query observations: {e}")

    if len(new_observations) == 0:
        log("      Predictions Today: 0")
        log("      No data was processed. No fresh observations found in the last 14 days.")
        predictions = []
        results["steps"]["predictions"] = "0 generated (no new observations)"
    else:
        log(f"      Found {len(new_observations)} recent observations.")
        # Step 3: Run analyst predictions
        log("[3/8] Running analyst predictions...")
        predictions = []
        try:
            from agents.analyst import AnalystAgent
            analyst = AnalystAgent()
            predictions = analyst.run_full_analysis()
            results["steps"]["predictions"] = f"{len(predictions)} generated"
            log(f"      Generated {len(predictions)} predictions")
        except Exception as e:
            results["steps"]["predictions"] = f"FAIL: {str(e)}"
            results["errors"].append(f"predictions: {str(e)}")
            log(f"      ERROR: {e}")
'''

step_3_regex = r'# Step 3: Run analyst predictions.*?log\(f"      ERROR: \{e\}"\)'
content = re.sub(step_3_regex, obs_check_code.strip(), content, flags=re.DOTALL)

with open('automation/master_daily.py', 'w') as f:
    f.write(content)

print('Done')
