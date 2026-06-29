import re

with open('dashboard/app.py', 'r') as f:
    text = f.read()

old_perf_route = '''@app.route('/performance')
@login_required
def performance():
    """Performance page."""
    try:
        stats = get_dashboard_stats()'''

new_perf_route = '''@app.route('/performance')
@login_required
def performance():
    """Performance page."""
    try:
        from database import get_connection as db_get_connection
        conn = db_get_connection()
        c = conn.cursor()
        
        # Calculate Prediction Maturity Breakdown
        maturity_stats = {'<30': 0, '30-60': 0, '>60': 0}
        c.execute("SELECT expected_timeline_days FROM prediction_ledger WHERE status NOT IN ('HIT', 'MISS', 'hit', 'miss', 'resolved')")
        for row in c.fetchall():
            days = row[0]
            if days is not None:
                if days < 30: maturity_stats['<30'] += 1
                elif days <= 60: maturity_stats['30-60'] += 1
                else: maturity_stats['>60'] += 1
        
        c.close()
        conn.close()
        
        stats = get_dashboard_stats()'''

if "maturity_stats = " not in text:
    text = text.replace(old_perf_route, new_perf_route)
    
old_return_perf = '''return_distribution=return_distribution)'''
new_return_perf = '''return_distribution=return_distribution, maturity_stats=maturity_stats)'''
text = text.replace(old_return_perf, new_return_perf)

with open('dashboard/app.py', 'w') as f:
    f.write(text)
print('performance route updated in app.py')
