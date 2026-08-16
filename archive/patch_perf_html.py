import os
import re

filepath = r"c:\Users\lokes\Downloads\project\sovereign-alpha\dashboard\templates\performance.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Total Predictions format (integer instead of float if there was one)
# The user said: "Total Predictions: Fix the decimal point issue (1.9). Ensure the variable is rendered as an integer (e.g., {{ total_predictions }} without any formatting that adds a decimal)."
# Let's replace: {{ ledgers_stats.total_predictions if ledgers_stats is defined else (ledger_stats.total_predictions | default(0)) }}
# with {{ ledger_stats.total_predictions | default(0) | int }}
old_tot = "{{ ledgers_stats.total_predictions if ledgers_stats is defined else (ledger_stats.total_predictions | default(0)) }}"
new_tot = "{{ (ledger_stats.total_predictions | default(0)) | int }}"
content = content.replace(old_tot, new_tot)

old_tot_2 = """<span class="val">{{ ledger_stats.total_predictions | default(0) }}</span>"""
new_tot_2 = """<span class="val">{{ (ledger_stats.total_predictions | default(0)) | int }}</span>"""
content = content.replace(old_tot_2, new_tot_2)

# 2. Hit/Miss Ratio
old_hitmiss = "{{ ledger_stats.hits | default(0) }} / {{ ledger_stats.misses | default(0) }}"
new_hitmiss = "{{ hit_count }} / {{ miss_count }}"
content = content.replace(old_hitmiss, new_hitmiss)

# 3. Veto Accuracy
old_veto = "{{ (ledger_stats.veto_efficiency | default(0)) | round(1) }}%"
new_veto = "{{ veto_accuracy | round(1) }}%"
content = content.replace(old_veto, new_veto)

# 4. Resolved Outcomes
old_resolved = """<span class="key">Resolved Outcomes</span><span class="val">{{ ledger_stats.resolved_count | default(0) }}</span>"""
new_resolved = """<span class="key">Resolved Outcomes</span><span class="val">{{ resolved_outcomes }}</span>"""
content = content.replace(old_resolved, new_resolved)

# 5. Table asset
old_asset = """<td class="symbol-col">{{ d.symbol }}</td>"""
new_asset = """<td class="symbol-col">{{ d.asset }}</td>"""
content = content.replace(old_asset, new_asset)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated performance.html")
