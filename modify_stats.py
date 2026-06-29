import re

with open('dashboard/app.py', 'r') as f:
    text = f.read()
    
old_resolved = '''        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != '' OR status IN ('resolved', 'HIT', 'MISS', 'hit', 'miss')")
        resolved_outcomes = c.fetchone()[0]
        print(f"DEBUG: SELECT COUNT(*) FROM prediction_ledger WHERE resolved IS TRUE -> {resolved_outcomes}")'''

new_resolved = '''        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != '' OR status IN ('resolved', 'HIT', 'MISS', 'hit', 'miss')")
        resolved_outcomes = c.fetchone()[0]
        print(f"DEBUG: SELECT COUNT(*) FROM prediction_ledger WHERE resolved IS TRUE -> {resolved_outcomes}")
        
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status IN ('HIT', 'hit') OR actual_outcome IN ('HIT', 'hit')")
        hits = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status IN ('MISS', 'miss') OR actual_outcome IN ('MISS', 'miss')")
        misses = c.fetchone()[0]
'''

if 'hits = c.fetchone()[0]' not in text:
    text = text.replace(old_resolved, new_resolved)

old_return1 = "'resolved_predictions': resolved_outcomes,"
new_return1 = "'resolved_predictions': resolved_outcomes, 'hits': hits, 'misses': misses,"
old_return2 = "'resolved_predictions': resolved_outcomes}"
new_return2 = "'resolved_predictions': resolved_outcomes, 'hits': hits, 'misses': misses}"

text = text.replace(old_return1, new_return1)
text = text.replace(old_return2, new_return2)

with open('dashboard/app.py', 'w') as f:
    f.write(text)
print('Hits and misses added to app.py')
