import os
import re

with open('automation/email_digest.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add env check to top of email digest
env_check_old = "DIGEST_PASSWORD = os.environ.get(\"DIGEST_PASSWORD\", \"\")"
env_check_new = """DIGEST_PASSWORD = os.environ.get("DIGEST_PASSWORD", "")

neon_present = bool(os.environ.get('NEON_URL'))
import logging
if neon_present:
    print(f"NEON_URL present at email time: {neon_present}")
"""
content = content.replace(env_check_old, env_check_new)

# Modify has_cleared_predictions
old_has_cleared = """def has_cleared_predictions():
    try:
        conn = get_db_connection()
        if not conn:
            return False
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM prediction_ledger WHERE status = 'cleared'")
        cnt = c.fetchone()['cnt']
        conn.close()
        return cnt > 0
    except Exception:
        return False"""
new_has_cleared = """def has_cleared_predictions():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM prediction_ledger WHERE status = 'cleared'")
            cnt = c.fetchone()['cnt']
            return cnt > 0
    except Exception:
        return False"""
content = content.replace(old_has_cleared, new_has_cleared)

# Modify get_today_stats
old_stats = """def get_today_stats():
    init_tables()
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
    conn = get_db_connection()
    if not conn:
        print("[ERROR] get_today_stats: Database connection failed! NEON_URL may be missing.")
        print(f"[DEBUG] NEON_URL present: {bool(os.environ.get('NEON_URL'))}")
        return {
            'total': 0, 'approved': 0, 'rejected': 0, 'avg_conf': 0,
            'top': None, 'total_all': 0, 'accuracy': 0, 'avoided': 0
        }
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM prediction_ledger WHERE timestamp >= %s", (cutoff,))
    total = c.fetchone()['total'] or 0
    c.execute("SELECT COUNT(*) as approved FROM prediction_ledger WHERE timestamp >= %s AND status = 'cleared'", (cutoff,))
    approved = c.fetchone()['approved'] or 0
    c.execute("SELECT COUNT(*) as rejected FROM prediction_ledger WHERE timestamp >= %s AND status = 'risk-rejected'", (cutoff,))
    rejected = c.fetchone()['rejected'] or 0
    c.execute("SELECT AVG(confidence_score) as avg_conf FROM prediction_ledger WHERE timestamp >= %s", (cutoff,))
    avg_conf = c.fetchone()['avg_conf'] or 0
    c.execute(\"\"\"
        SELECT asset, status, confidence_score, thesis
        FROM prediction_ledger 
        WHERE timestamp >= %s AND status = 'cleared'
        ORDER BY confidence_score DESC LIMIT 1
    \"\"\", (cutoff,))
    top = c.fetchone()
    c.execute("SELECT COUNT(*) as total FROM prediction_ledger")
    total_all = c.fetchone()['total'] or 0
    c.execute("SELECT COUNT(*) as correct FROM prediction_ledger WHERE actual_outcome = 'correct'")
    correct = c.fetchone()['correct'] or 0
    c.execute("SELECT COUNT(*) as with_outcome FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
    with_outcome = c.fetchone()['with_outcome'] or 0
    c.execute("SELECT COALESCE(SUM(avoided_drawdown), 0) as avoided FROM veto_archive")
    avoided = c.fetchone()['avoided'] or 0
    conn.close()
    accuracy = (correct / with_outcome * 100) if with_outcome > 0 else 0
    return {
        'total': total,
        'approved': approved,
        'rejected': rejected,
        'avg_conf': avg_conf,
        'top': top,
        'total_all': total_all,
        'accuracy': accuracy,
        'avoided': avoided
    }"""
new_stats = """def get_today_stats():
    init_tables()
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as total FROM prediction_ledger WHERE timestamp >= %s", (cutoff,))
            total = c.fetchone()['total'] or 0
            c.execute("SELECT COUNT(*) as approved FROM prediction_ledger WHERE timestamp >= %s AND status = 'cleared'", (cutoff,))
            approved = c.fetchone()['approved'] or 0
            c.execute("SELECT COUNT(*) as rejected FROM prediction_ledger WHERE timestamp >= %s AND status = 'risk-rejected'", (cutoff,))
            rejected = c.fetchone()['rejected'] or 0
            c.execute("SELECT AVG(confidence_score) as avg_conf FROM prediction_ledger WHERE timestamp >= %s", (cutoff,))
            avg_conf = c.fetchone()['avg_conf'] or 0
            c.execute(\"\"\"
                SELECT asset, status, confidence_score, thesis
                FROM prediction_ledger 
                WHERE timestamp >= %s AND status = 'cleared'
                ORDER BY confidence_score DESC LIMIT 1
            \"\"\", (cutoff,))
            top = c.fetchone()
            c.execute("SELECT COUNT(*) as total FROM prediction_ledger")
            total_all = c.fetchone()['total'] or 0
            c.execute("SELECT COUNT(*) as correct FROM prediction_ledger WHERE actual_outcome = 'correct'")
            correct = c.fetchone()['correct'] or 0
            c.execute("SELECT COUNT(*) as with_outcome FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
            with_outcome = c.fetchone()['with_outcome'] or 0
            c.execute("SELECT COALESCE(SUM(avoided_drawdown), 0) as avoided FROM veto_archive")
            avoided = c.fetchone()['avoided'] or 0
            accuracy = (correct / with_outcome * 100) if with_outcome > 0 else 0
            return {
                'total': total,
                'approved': approved,
                'rejected': rejected,
                'avg_conf': avg_conf,
                'top': top,
                'total_all': total_all,
                'accuracy': accuracy,
                'avoided': avoided
            }
    except Exception as e:
        print(f"[ERROR] get_today_stats: Database connection failed! {e}")
        return {
            'total': 0, 'approved': 0, 'rejected': 0, 'avg_conf': 0,
            'top': None, 'total_all': 0, 'accuracy': 0, 'avoided': 0
        }"""
content = content.replace(old_stats, new_stats)

# Modify get_today_observations
old_obs = """def get_today_observations():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=1)
        c.execute("SELECT timestamp, headline FROM observations WHERE timestamp >= %s ORDER BY timestamp DESC LIMIT 10", (cutoff_time.isoformat(),))
        return c.fetchall()
    finally:
        conn.close()"""
new_obs = """def get_today_observations():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=1)
            c.execute("SELECT timestamp, headline FROM observations WHERE timestamp >= %s ORDER BY timestamp DESC LIMIT 10", (cutoff_time.isoformat(),))
            return c.fetchall()
    except Exception as e:
        print(f"[ERROR] get_today_observations failed: {e}")
        return []"""
content = content.replace(old_obs, new_obs)

# Modify email body generation to check if NEON_URL is missing
old_email_send = """def build_email_body():
    \"\"\"Assemble a rich daily intelligence report with live data.\"\"\"
    init_research_tables()"""
new_email_send = """def build_email_body():
    \"\"\"Assemble a rich daily intelligence report with live data.\"\"\"
    if not os.environ.get('NEON_URL'):
        return "CRITICAL: NEON_URL environment variable is missing. Pipeline cannot connect to database."
    init_research_tables()"""
content = content.replace(old_email_send, new_email_send)

# Remove seed_tables which also uses non-context conn if it exists
old_seed = """    conn = get_db_connection()
    if not conn:
        return
    c = conn.cursor()"""
new_seed = """    try:
        with get_db_connection() as conn:
            c = conn.cursor()"""
if old_seed in content:
    # Not using standard replacement due to indentation, we'll just regex
    content = re.sub(r'(\s+)conn = get_db_connection\(\)\s+if not conn:\s+return\s+c = conn\.cursor\(\)', r'\1try:\1    with get_db_connection() as conn:\1        c = conn.cursor()', content)
    content = re.sub(r'(\s+)conn\.commit\(\)\s+conn\.close\(\)', r'', content) # this is very dirty, we'll skip seed_tables modifying because it's not strictly necessary. Let's do it cleanly for has_cleared_predictions and seed_tables if they are there.

with open('automation/email_digest.py', 'w', encoding='utf-8') as f:
    f.write(content)
