import os

filepath = r"c:\Users\lokes\Downloads\project\sovereign-alpha\dashboard\app.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the feed query in index()
old_feed = """        try:
            from research.observation_stream import build_live_feed
            feed = build_live_feed(40)
            observations = feed.get('observations', [])
            
            # Sort observations by severity
            severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            observations.sort(key=lambda x: severity_order.get(x.get('severity', 'LOW'), 99))
            
            macro_alerts = feed.get('macro_alerts', [])
            high_severity_7d = feed.get('high_severity_7d', 0)
        except Exception:
            pass"""

new_feed = """        try:
            from engine.db import get_connection as db_get_connection
            with db_get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT id, timestamp, ticker, source, headline, severity, confidence FROM observations ORDER BY timestamp DESC LIMIT 10")
                rows = c.fetchall()
                for row in rows:
                    observations.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'ticker': row[2],
                        'source': row[3],
                        'headline': row[4],
                        'severity': row[5],
                        'confidence': row[6]
                    })
        except Exception as e:
            print("ERROR FETCHING FEED:", e)"""

content = content.replace(old_feed, new_feed)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated app.py feed logic")
