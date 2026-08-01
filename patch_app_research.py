import os
import re

filepath = r'c:\Users\lokes\Downloads\project\sovereign-alpha\dashboard\app.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_app = """        companies = get_all_companies()
        notes = get_notes()"""
new_app = """        companies = get_all_companies()
        notes = get_notes()
        watchlist_dict = {w['ticker']: w['alert_threshold'] for w in watchlist} if watchlist else {}
        for c in companies:
            c['alert_threshold'] = watchlist_dict.get(c['ticker'], 'N/A')"""

if old_app in content:
    content = content.replace(old_app, new_app)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("app.py updated")
else:
    print("Could not find app.py string")
