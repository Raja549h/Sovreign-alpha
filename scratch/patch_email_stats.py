import re

with open('automation/email_digest.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace get_today_stats() with regex since the previous string match failed
content = re.sub(r'def get_today_stats\(\):.*?return \{.*?\n\s+\}', r'''def get_today_stats():
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
            c.execute("""
                SELECT asset, status, confidence_score, thesis
                FROM prediction_ledger 
                WHERE timestamp >= %s AND status = 'cleared'
                ORDER BY confidence_score DESC LIMIT 1
            """, (cutoff,))
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
        }''', content, flags=re.DOTALL)

with open('automation/email_digest.py', 'w', encoding='utf-8') as f:
    f.write(content)
