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

# Safe function replacements
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

# seed_meaningful_data (regex)
old_seed = """    conn = get_db_connection()
    if not conn:
        return
    c = conn.cursor()"""
new_seed = """    try:
        with get_db_connection() as conn:
            c = conn.cursor()"""

# We'll just replace the whole seed_meaningful_data since we know it.
content = re.sub(r'def seed_meaningful_data\(\):.*?conn\.close\(\)', r'''def seed_meaningful_data():
    init_tables()
    if has_cleared_predictions():
        return
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            now = datetime.utcnow()
            today_cleared = 0
            c.execute("SELECT COUNT(*) as cnt FROM prediction_ledger WHERE timestamp LIKE %s AND status = 'cleared'",
                      (f"{now.strftime('%Y-%m-%d')}%",))
            row = c.fetchone()
            if row:
                today_cleared = row['cnt'] or 0
            c.execute("SELECT COUNT(*) as cnt FROM veto_archive")
            veto_count = c.fetchone()['cnt'] or 0
            if today_cleared == 0:
                cleared_count = 0
                for i in range(3):
                    try:
                        c.execute("""
                            INSERT INTO prediction_ledger 
                            (prediction_id, timestamp, asset, sector, thesis, confidence_score, status, expected_timeline_days, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            str(uuid.uuid4()),
                            (now - timedelta(hours=i)).isoformat() + "Z",
                            random.choice(['NVDA', 'AAPL', 'RELIANCE.NS', 'TCS.NS', 'BTC-USD']),
                            'Technology',
                            f"Sample intelligence generated for layout visualization {i}",
                            round(random.uniform(70.0, 95.0), 1),
                            'cleared',
                            30,
                            now.isoformat() + "Z",
                            now.isoformat() + "Z"
                        ))
                        cleared_count += 1
                    except Exception:
                        pass
                print(f"[seed] Inserted {cleared_count} cleared predictions")
            if veto_count < 10:
                seeded_vetoes = 0
                for i in range(5):
                    try:
                        c.execute("""
                            INSERT INTO veto_archive 
                            (veto_id, timestamp, asset, sector, rejection_reason, expected_loss_pct, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            str(uuid.uuid4()),
                            (now - timedelta(hours=i*2)).isoformat() + "Z",
                            random.choice(['TSLA', 'GME', 'AMC', 'ZOMATO.NS', 'PAYTM.NS']),
                            'Volatile',
                            f"Sample risk veto for excessive volatility {i}",
                            round(random.uniform(5.0, 15.0), 1),
                            now.isoformat() + "Z"
                        ))
                        seeded_vetoes += 1
                    except Exception:
                        pass
                if seeded_vetoes > 0:
                    print(f"[seed] Inserted {seeded_vetoes} veto records")
    except Exception as e:
        print(f"[seed] Error seeding: {e}")''', content, flags=re.DOTALL)


# get_today_stats
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
        'top': dict(top) if top else None,
        'total_all': total_all,
        'accuracy': accuracy,
        'avoided': avoided,
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
                'top': dict(top) if top else None,
                'total_all': total_all,
                'accuracy': accuracy,
                'avoided': avoided,
            }
    except Exception as e:
        print(f"[ERROR] get_today_stats: Database connection failed! {e}")
        return {
            'total': 0, 'approved': 0, 'rejected': 0, 'avg_conf': 0,
            'top': None, 'total_all': 0, 'accuracy': 0, 'avoided': 0
        }"""
content = content.replace(old_stats, new_stats)


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

with open('automation/email_digest.py', 'w', encoding='utf-8') as f:
    f.write(content)
