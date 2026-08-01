import re

filepath = r"c:\Users\lokes\Downloads\project\sovereign-alpha\dashboard\templates\index.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_miss = """                <div><span style="color:#555;">Verified (MISS)</span><br><span style="font-size:1.1rem;font-weight:700;color:var(--warning);">{{ stats.misses }}</span></div>"""
content = content.replace(old_miss, "")

old_grid = """<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:0.5rem;font-family:var(--font-mono);font-size:0.65rem;margin-bottom:0.75rem;">"""
new_grid = """<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:0.5rem;font-family:var(--font-mono);font-size:0.65rem;margin-bottom:0.75rem;">"""
content = content.replace(old_grid, new_grid)

# Also rename "Logged Misses" to "Verified (MISS)"
old_logged = """<span style="color:#555;">Logged Misses</span>"""
new_logged = """<span style="color:#555;">Verified (MISS)</span>"""
content = content.replace(old_logged, new_logged)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated index.html duplicate label")
