import re
import os

filepath = r'c:\Users\lokes\Downloads\project\sovereign-alpha\dashboard\templates\research_home.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove Watchlist Summary block entirely
watchlist_block_pattern = re.compile(r'{%\s*if watchlist_companies\s*%}.*?{%\s*endif\s*%}\n+', re.DOTALL)
content = watchlist_block_pattern.sub('', content)

# 2. Update Companies Under Coverage table headers
old_headers = """                            <th>Ticker</th>
                            <th>Company</th>
                            <th>Sector</th>
                            <th>Actions</th>"""
new_headers = """                            <th>Ticker</th>
                            <th>Company</th>
                            <th>Sector</th>
                            <th>Threshold</th>
                            <th>Actions</th>"""
content = content.replace(old_headers, new_headers)

# 3. Update Companies Under Coverage table rows
old_row = """                            <td class="ticker-cell">{{ c.ticker }}</td>
                            <td>{{ c.company_name }}</td>
                            <td style="font-size:0.65rem;">{{ c.sector or '—' }}</td>
                            <td><a href="/research/{{ c.ticker }}" class="btn outline small">View</a></td>"""
new_row = """                            <td class="ticker-cell">{{ c.ticker }}</td>
                            <td>{{ c.company_name }}</td>
                            <td style="font-size:0.65rem;">{{ c.sector or '—' }}</td>
                            <td><span class="severity-tag {{ (c.alert_threshold|lower) if c.alert_threshold != 'N/A' else 'low' }}">{{ c.alert_threshold }}</span></td>
                            <td><a href="/research/{{ c.ticker }}" class="btn outline small">View</a></td>"""
content = content.replace(old_row, new_row)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated research_home.html")
