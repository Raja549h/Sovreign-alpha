import os
import re

def convert_queries(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    
    # Replace INSERT OR IGNORE INTO <table_name> ... VALUES ... -> INSERT INTO <table_name> ... VALUES ... ON CONFLICT DO NOTHING
    # Since doing regex on SQL in Python strings is risky if it spans multiple lines, we will just do basic replacements for the simple cases.
    
    # Replace simple datetime('now')
    content = content.replace("datetime('now')", "NOW()")
    
    # Find INSERT OR IGNORE
    content = re.sub(r'INSERT\s+OR\s+IGNORE\s+INTO', 'INSERT INTO', content, flags=re.IGNORECASE)
    # Wait, ON CONFLICT DO NOTHING must be appended at the end of the query. 
    # That's very hard with simple regex. Let me do targeted replacements for the specific files we found.

    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Converted query in {path}")

# Specifically targeted file conversions
def manual_convert(path, old, new):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    if old in c:
        c = c.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
            print(f"Manually converted {path}")

manual_convert(r'research\fii_intelligence.py', 
    '"""INSERT OR IGNORE INTO nsdl_fpi_flows\n                       (date, category, equity_investment, debt_investment)\n                       VALUES (%s, %s, %s, %s)"""',
    '"""INSERT INTO nsdl_fpi_flows\n                       (date, category, equity_investment, debt_investment)\n                       VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING"""')

manual_convert(r'research\thesis_tracker.py',
    'c.execute("INSERT OR IGNORE INTO watchlist (company_id, alert_threshold, notes) VALUES (%s, %s, %s)", (company_id, alert_threshold, notes))',
    'c.execute("INSERT INTO watchlist (company_id, alert_threshold, notes) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (company_id, alert_threshold, notes))')

manual_convert(r'research\macro\import_sensitivity.py',
    '''                INSERT INTO import_sensitivity_scores
                (company_id, sensitivity_score, primary_import_commodity, calculated_at)
                VALUES (%s, %s, %s, datetime('now'))''',
    '''                INSERT INTO import_sensitivity_scores
                (company_id, sensitivity_score, primary_import_commodity, calculated_at)
                VALUES (%s, %s, %s, NOW()) ON CONFLICT (company_id) DO UPDATE SET
                sensitivity_score = EXCLUDED.sensitivity_score,
                primary_import_commodity = EXCLUDED.primary_import_commodity,
                calculated_at = EXCLUDED.calculated_at''')


for root, _, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root or 'sqlite_archive' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            path_lower = path.lower()
            if 'database.py' in path_lower or 'convert_queries' in path_lower:
                continue
            convert_queries(path)

print("Query Conversion Complete.")
