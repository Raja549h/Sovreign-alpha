import os
import re

filepath = r'c:\Users\lokes\Downloads\project\sovereign-alpha\dashboard\app.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_timeline = """        from research.evolution_quality import EvidenceTimeline
        et = EvidenceTimeline()
        company_id = request.args.get('company_id', type=int)
        obs_id = request.args.get('observation_id', type=int)
        event_type = request.args.get('event_type')
        timeline = et.get_timeline(company_id=company_id, observation_id=obs_id,
                                   event_type=event_type, limit=200)"""

new_timeline = """        from dashboard.gateway import get_connection as db_get_connection
        timeline = []
        with db_get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT timestamp, headline, severity, source FROM observations ORDER BY timestamp DESC LIMIT 200")
            for row in c.fetchall():
                timeline.append({
                    'timestamp': row[0],
                    'event_detail': row[1],
                    'event_label': row[2],
                    'source': row[3]
                })"""

if old_timeline in content:
    content = content.replace(old_timeline, new_timeline)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Evidence timeline updated.')
else:
    print('Evidence timeline string not found.')
