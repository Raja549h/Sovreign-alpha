import sys
import os
import re

with open('automation/master_daily.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add env print
env_print = """
import os
import sys
import json
"""
new_env_print = """
import os
import sys
import json

print(f"NEON_URL present: {bool(os.environ.get('NEON_URL'))}")
"""
content = content.replace(env_print.strip(), new_env_print.strip())

# Fix subprocesses to pass env=os.environ.copy()
content = re.sub(r"(__import__\('subprocess'\)\.run\(\[sys\.executable,\s*str\(BASE_DIR\s*/\s*\"data\"\s*/\s*\"market_[a-z]+\.py\"\)\],)", r"\g<1> env=os.environ.copy(),", content)
content = re.sub(r"(subprocess\.run\(\s*\[.*?\],\s*cwd=str\(BASE_DIR\),)", r"\g<1>\n                env=os.environ.copy(),", content)

# Fix Step 6: Record to prediction ledger
old_step_6 = """    # Step 6: Record to prediction ledger
    log("[6/8] Recording to prediction ledger...")
    try:
        from database import get_connection
        conn = get_connection()
        if not conn:
            raise Exception("Database connection unavailable")
        c = conn.cursor()
        for pred in predictions:
            status = 'cleared' if any(a.ticker == pred.ticker for a in approved) else 'risk-rejected'
            try:
                c.execute(\"\"\"
                    INSERT INTO prediction_ledger 
                    (prediction_id, timestamp, asset, sector, thesis, confidence_score, 
                     status, expected_timeline_days, proof_hash, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                \"\"\", (
                    pred.prediction_id,
                    pred.timestamp,
                    pred.ticker,
                    pred.institutional_positioning.get('sector', ''),
                    pred.thesis,
                    pred.confidence,
                    status,
                    pred.expected_timeline_days,
                    certificates[0].commitment_hash if certificates else '',
                    datetime.utcnow().isoformat() + 'Z',
                    datetime.utcnow().isoformat() + 'Z'
                ))
            except Exception as insert_err:
                log(f"      WARN: Could not insert prediction {pred.prediction_id}: {insert_err}")
        conn.commit()
        conn.close()"""

new_step_6 = """    # Step 6: Record to prediction ledger
    log("[6/8] Recording to prediction ledger...")
    try:
        from database import get_connection
        with get_connection() as conn:
            c = conn.cursor()
            for pred in predictions:
                status = 'cleared' if any(a.ticker == pred.ticker for a in approved) else 'risk-rejected'
                try:
                    c.execute(\"\"\"
                        INSERT INTO prediction_ledger 
                        (prediction_id, timestamp, asset, sector, thesis, confidence_score, 
                         status, expected_timeline_days, proof_hash, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    \"\"\", (
                        pred.prediction_id,
                        pred.timestamp,
                        pred.ticker,
                        pred.institutional_positioning.get('sector', ''),
                        pred.thesis,
                        pred.confidence,
                        status,
                        pred.expected_timeline_days,
                        certificates[0].commitment_hash if certificates else '',
                        datetime.utcnow().isoformat() + 'Z',
                        datetime.utcnow().isoformat() + 'Z'
                    ))
                except Exception as insert_err:
                    log(f"      WARN: Could not insert prediction {pred.prediction_id}: {insert_err}")"""
content = content.replace(old_step_6, new_step_6)

# Fix Step 8: Update prediction validation statuses
old_step_8 = """    # Step 8: Update prediction validation statuses (BEFORE email so email has latest data)
    log("[8/9] Updating prediction validation statuses...")
    try:
        from database import get_connection as _get_conn
        _vconn = _get_conn()
        if _vconn:
            _vc = _vconn.cursor()
            _vc.execute("UPDATE prediction_ledger SET status = 'HIT' WHERE actual_outcome = 'correct' AND status NOT IN ('HIT', 'MISS');")
            hits = _vc.rowcount
            _vc.execute("UPDATE prediction_ledger SET status = 'MISS' WHERE actual_outcome = 'incorrect' AND status NOT IN ('HIT', 'MISS');")
            misses = _vc.rowcount
            _vconn.commit()
            _vconn.close()
            results["steps"]["validation"] = f"Hits: {hits}, Misses: {misses}"
            log(f"      Validation updated: {hits} HITs, {misses} MISSes resolved.")
        else:
            results["steps"]["validation"] = "SKIP: no DB connection"
            log("      SKIP: no DB connection for validation")"""

new_step_8 = """    # Step 8: Update prediction validation statuses (BEFORE email so email has latest data)
    log("[8/9] Updating prediction validation statuses...")
    try:
        from database import get_connection as _get_conn
        with _get_conn() as _vconn:
            _vc = _vconn.cursor()
            _vc.execute("UPDATE prediction_ledger SET status = 'HIT' WHERE actual_outcome = 'correct' AND status NOT IN ('HIT', 'MISS');")
            hits = _vc.rowcount
            _vc.execute("UPDATE prediction_ledger SET status = 'MISS' WHERE actual_outcome = 'incorrect' AND status NOT IN ('HIT', 'MISS');")
            misses = _vc.rowcount
            results["steps"]["validation"] = f"Hits: {hits}, Misses: {misses}"
            log(f"      Validation updated: {hits} HITs, {misses} MISSes resolved.")
    except Exception as e:
        results["steps"]["validation"] = f"FAIL: {str(e)}"
        log(f"      ERROR: {str(e)}")"""
content = content.replace(old_step_8, new_step_8)

with open('automation/master_daily.py', 'w', encoding='utf-8') as f:
    f.write(content)
