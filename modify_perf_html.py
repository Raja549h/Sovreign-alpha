import re

with open('dashboard/templates/performance.html', 'r') as f:
    text = f.read()

old_metrics = '''            <div class="panel-header">
                <h2>Key Metrics</h2>
            </div>
            <div class="panel-body padded">'''

new_metrics = '''            <div class="panel-header">
                <h2>Key Metrics</h2>
            </div>
            <div class="panel-body padded">
                <!-- Prediction Maturity Breakdown (Task C3) -->
                <div style="margin-bottom: 1rem; padding: 0.5rem; background: rgba(0,255,159,0.05); border: 1px solid var(--accent); border-radius: 4px;">
                    <strong style="color:var(--accent); font-family:var(--font-mono); font-size:0.8rem; text-transform:uppercase;">Prediction Maturity Calendar</strong>
                    <div style="display:flex; justify-content:space-between; margin-top:0.5rem; font-family:var(--font-mono); font-size:0.85rem;">
                        <div><span style="color:#888;">&lt; 30 Days:</span> <strong>{{ maturity_stats['<30'] | default(0) }}</strong></div>
                        <div><span style="color:#888;">30-60 Days:</span> <strong>{{ maturity_stats['30-60'] | default(0) }}</strong></div>
                        <div><span style="color:#888;">&gt; 60 Days:</span> <strong>{{ maturity_stats['>60'] | default(0) }}</strong></div>
                    </div>
                </div>
'''

if "Prediction Maturity Calendar" not in text:
    text = text.replace(old_metrics, new_metrics)

with open('dashboard/templates/performance.html', 'w') as f:
    f.write(text)
print('performance.html updated')
