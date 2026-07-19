import re

with open('automation/email_digest.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Exact string deletion of the leftover block from the previous bad regex
bad_block = """    c = conn.cursor()
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
        'avg_conf': avg_conf * 100,
        'top': dict(top) if top else None,
        'total_all': total_all,
        'accuracy': accuracy,
        'avoided': avoided,
    }"""

if bad_block in content:
    content = content.replace(bad_block, "")
else:
    # try slightly different formatting
    print("WARNING: Exact match failed, falling back to regex")
    content = re.sub(r'\s+c = conn\.cursor\(\)\s+c\.execute\("SELECT COUNT\(\*\) as total FROM prediction_ledger WHERE timestamp >= %s", \(cutoff,\)\).*?\'avoided\': avoided,\n\s+\}', '', content, flags=re.DOTALL)

with open('automation/email_digest.py', 'w', encoding='utf-8') as f:
    f.write(content)
