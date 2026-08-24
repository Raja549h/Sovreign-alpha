import re

with open('dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix naked get_db_connection() in prediction_detail
content = re.sub(
    r'conn = get_db_connection\(\)\n(\s*)c = conn\.cursor\(\)\n(\s*)c\.execute\("SELECT \* FROM prediction_ledger WHERE id = %s", \(prediction_id,\)\)\n(\s*)row = c\.fetchone\(\)\n(\s*)pass\n(\s*)pass # conn\.close\(\)',
    r'with get_db_connection() as conn:\n\1c = conn.cursor()\n\1c.execute("SELECT * FROM prediction_ledger WHERE id = %s", (prediction_id,))\n\1row = c.fetchone()',
    content
)

# 2. Fix naked get_db_connection() in api_track_record
content = re.sub(
    r'conn = get_db_connection\(\)\n(\s*)c = conn\.cursor\(\)\n(\s*)c\.execute\("SELECT COUNT\(\*\) FROM analysis_runs WHERE status = \'COMPLETED\'"\)\n(\s*)total_sessions = c\.fetchone\(\)\[0\]\n(\s*)c\.execute\("SELECT COUNT\(\*\) FROM prediction_ledger"\)\n(\s*)total_decisions = c\.fetchone\(\)\[0\]\n(\s*)c\.execute\("SELECT COUNT\(\*\) FROM prediction_ledger WHERE status NOT IN \(\'vetoed\',\'risk-rejected\',\'VETOED\',\'RISK_REJECTED\'\)"\)\n(\s*)total_approved = c\.fetchone\(\)\[0\]\n(\s*)c\.execute\("SELECT SUM\(confidence_score \* 0\.1\) FROM prediction_ledger WHERE status NOT IN \(\'vetoed\',\'risk-rejected\',\'VETOED\',\'RISK_REJECTED\'\)"\)\n(\s*)total_alpha = c\.fetchone\(\)\[0\] or 0\.0\n(\s*)pass\n(\s*)pass # conn\.close\(\)',
    r'with get_db_connection() as conn:\n\1c = conn.cursor()\n\1c.execute("SELECT COUNT(*) FROM analysis_runs WHERE status = \'COMPLETED\'")\n\1total_sessions = c.fetchone()[0]\n\1c.execute("SELECT COUNT(*) FROM prediction_ledger")\n\1total_decisions = c.fetchone()[0]\n\1c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status NOT IN (\'vetoed\',\'risk-rejected\',\'VETOED\',\'RISK_REJECTED\')")\n\1total_approved = c.fetchone()[0]\n\1c.execute("SELECT SUM(confidence_score * 0.1) FROM prediction_ledger WHERE status NOT IN (\'vetoed\',\'risk-rejected\',\'VETOED\',\'RISK_REJECTED\')")\n\1total_alpha = c.fetchone()[0] or 0.0',
    content
)

# 3. Fix column mismatches in prediction_ledger and shadow_portfolio
# Where query selects or inserts 'ticker', change to 'asset'.
# Wait, for shadow_portfolio, the column is 'ticker' or 'asset'?
# Let's check shadow_portfolio in schema_audit: it has 'ticker'. Wait!
# TABLE: shadow_portfolio has: ticker: text, position_id: character varying.
# BUT prediction_ledger has 'asset: text (Nullable: NO)'

# The prompt says: "If the Python code uses row bracket ticker but the database column is asset, fix ALL occurrences in app.py routes, models.py functions, HTML templates, and worker.py."
content = content.replace("row['ticker']", "row.get('asset', row.get('ticker', ''))")
content = content.replace("p.get('ticker', '')", "p.get('asset', p.get('ticker', ''))")

with open('dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replaced naked connections and patched row['ticker'] in app.py")
