import re

with open('dashboard/app.py', 'r') as f:
    content = f.read()

misses_route = '''
@app.route('/misses')
def misses_ledger():
    try:
        from database import get_connection as db_get_connection
        conn = db_get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT prediction_id, asset, thesis, outcome_notes, actual_return_pct, timestamp
            FROM prediction_ledger 
            WHERE status IN ('MISS', 'miss') OR actual_outcome IN ('MISS', 'miss')
            ORDER BY timestamp DESC
        """)
        misses = c.fetchall()
        c.close()
        conn.close()
    except Exception as e:
        print('MISSES ERROR:', e)
        misses = []
    
    return render_template('misses.html', misses=misses)
'''
if "@app.route('/misses')" not in content:
    content = content.replace("@app.route('/predictions')", misses_route + "\n@app.route('/predictions')")

old_stats = '''        c.execute("SELECT COUNT(*) FROM prediction_ledger")
        total = c.fetchone()[0]'''
new_stats = '''        c.execute("SELECT COUNT(*) FROM prediction_ledger")
        total = c.fetchone()[0]
        print(f"DEBUG: SELECT COUNT(*) FROM prediction_ledger -> {total}")'''
content = content.replace(old_stats, new_stats)

old_resolved = '''        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
        resolved_outcomes = c.fetchone()[0]'''
new_resolved = '''        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != '' OR status IN ('resolved', 'HIT', 'MISS', 'hit', 'miss')")
        resolved_outcomes = c.fetchone()[0]
        print(f"DEBUG: SELECT COUNT(*) FROM prediction_ledger WHERE resolved IS TRUE -> {resolved_outcomes}")'''
content = content.replace(old_resolved, new_resolved)

content = content.replace("last_verified=datetime.utcnow().strftime('%H:%M:%S'),", "last_verified=datetime.utcnow().strftime('%H:%M:%S'),\n                           data_verified_at=datetime.utcnow(),")

with open('dashboard/app.py', 'w') as f:
    f.write(content)
print("app.py updated")
