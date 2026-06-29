import re

with open('dashboard/templates/index.html', 'r') as f:
    text = f.read()

# Add Transparency Badge (Task B2) and Data Verified (Task A3)
old_header = """<div class="container fade-in">
        <h1 style="font-size: 1.5rem; letter-spacing: 1px; margin-bottom: 2px;">AUTONOMOUS FORENSIC INTELLIGENCE PLATFORM</h1>
        <h2 style="font-size:0.85rem;color:var(--text-dim);font-weight:400;letter-spacing:1px;margin-top:2px;margin-bottom:0.5rem;">FOR INSTITUTIONAL ALLOCATORS & PMS</h2>
        <span class="timestamp">Last verified: {{ last_verified }}</span>
    </div>"""

new_header = """<div class="container fade-in">
        <h1 style="font-size: 1.5rem; letter-spacing: 1px; margin-bottom: 2px;">AUTONOMOUS FORENSIC INTELLIGENCE PLATFORM</h1>
        <h2 style="font-size:0.85rem;color:var(--text-dim);font-weight:400;letter-spacing:1px;margin-top:2px;margin-bottom:0.5rem;">FOR INSTITUTIONAL ALLOCATORS & PMS</h2>
        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <span class="timestamp">Last verified: {{ last_verified }}</span>
                <span class="timestamp" style="margin-left:1rem;color:#777;">Data verified: {{ data_verified_at.strftime('%Y-%m-%d %H:%M') }} UTC</span>
            </div>
            <div data-tip="Every incorrect prediction is logged with a post-mortem. This ledger is our commitment to intellectual honesty." style="background:var(--warning); color:#000; padding:4px 8px; font-family:var(--font-mono); font-size:0.75rem; font-weight:bold; border-radius:3px; cursor:help;">
                Self-Auditing: MISS predictions are never deleted.
            </div>
        </div>
    </div>"""

text = text.replace(old_header, new_header)

# Modify Logged Misses (Task B1)
old_misses = '<div><span style="color:#555;">Logged Misses</span><br><span style="font-size:1.1rem;font-weight:700;color:var(--warning);" title="Predictions that did not match the outcome. Logged transparently — not deleted.">{{ trust.failure_records }}</span></div>'
new_misses = '<div style="background:rgba(255,170,0,0.15); padding:4px; border-radius:4px; border:1px solid var(--warning);"><a href="/misses" style="text-decoration:none; display:block;"><span style="color:var(--warning); font-weight:bold;">Logged Misses</span><br><span style="font-size:1.2rem;font-weight:900;color:var(--warning);">{{ stats.misses }}</span></a></div>'
text = text.replace(old_misses, new_misses)

# Add Validation Ledger Summary (Task B3)
old_perf = '            <!-- Row 2: Prediction Performance -->'
new_perf = '''            <!-- Validation Ledger Summary Widget (B3) -->
            <div style="display:flex; gap: 1rem; margin-bottom:1rem; padding:0.5rem; background:#1a1a1a; border-left:3px solid var(--accent);">
                <div style="flex:1;font-family:var(--font-mono);font-size:0.75rem;"><span style="color:#888;">Total Predictions</span><br><strong style="font-size:1.1rem;">{{ stats.total_predictions }}</strong></div>
                <div style="flex:1;font-family:var(--font-mono);font-size:0.75rem;"><span style="color:#888;">Verified (HIT)</span><br><strong style="font-size:1.1rem;color:var(--accent);">{{ stats.hits }}</strong></div>
                <div style="flex:1;font-family:var(--font-mono);font-size:0.75rem;"><span style="color:#888;">Verified (MISS)</span><br><strong style="font-size:1.1rem;color:var(--warning);">{{ stats.misses }}</strong></div>
            </div>
            <!-- Row 2: Prediction Performance -->'''
text = text.replace(old_perf, new_perf)

with open('dashboard/templates/index.html', 'w') as f:
    f.write(text)
print('index.html updated')
