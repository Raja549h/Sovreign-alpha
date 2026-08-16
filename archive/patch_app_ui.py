import os

filepath = r"c:\Users\lokes\Downloads\project\sovereign-alpha\dashboard\app.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. get_decisions fix
old_get_decisions = "            asset AS symbol,"
new_get_decisions = "            asset,"
if old_get_decisions in content:
    content = content.replace(old_get_decisions, new_get_decisions)
    print("Replaced get_decisions asset AS symbol")
else:
    print("Failed to replace get_decisions")

# 2. Performance route calculation fix
import re
perf_pattern = re.compile(r"        c\.close\(\)\n        pass\n        pass # conn\.close\(\)\n        \n        stats = get_dashboard_stats\(\)")
new_perf = """        # Calculate hits, misses, and vetoes dynamically
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'HIT'")
        hit_count = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'MISS'")
        miss_count = c.fetchone()[0] or 0
        resolved_outcomes = hit_count + miss_count

        c.execute("SELECT COUNT(*) FROM veto_archive")
        total_vetoes = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM veto_archive WHERE veto_correct = 1 OR veto_correct = TRUE")
        correct_vetoes = c.fetchone()[0] or 0
        
        veto_accuracy = (correct_vetoes / total_vetoes * 100) if total_vetoes > 0 else 0

        c.close()
        pass
        pass # conn.close()
        
        stats = get_dashboard_stats()"""

if perf_pattern.search(content):
    content = perf_pattern.sub(new_perf, content)
    print("Replaced performance route calc")
else:
    print("Failed to replace performance calc")

# 3. Performance route render_template fix
render_pattern = re.compile(r"                             decisions=decisions,\n                             is_demo=is_demo_mode\(\)\)")
new_render = """                             decisions=decisions,
                             hit_count=hit_count,
                             miss_count=miss_count,
                             resolved_outcomes=resolved_outcomes,
                             veto_accuracy=veto_accuracy,
                             is_demo=is_demo_mode())"""
if render_pattern.search(content):
    content = render_pattern.sub(new_render, content)
    print("Replaced render_template")
else:
    print("Failed to replace render_template")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done patching app.py")
