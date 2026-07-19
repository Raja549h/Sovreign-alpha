import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('DATABASE_URL')

try:
    conn = psycopg2.connect(db_url)
    c = conn.cursor()
    
    print('--- Query 1: Recent Observations Count ---')
    c.execute("SELECT COUNT(*) FROM observations WHERE timestamp::timestamp > NOW() - INTERVAL '2 days';")
    count = c.fetchone()[0]
    print(f'Count: {count}')
    
    print('\n--- Query 2: Last 5 Observations ---')
    c.execute("SELECT timestamp, headline FROM observations ORDER BY timestamp DESC LIMIT 5;")
    rows = c.fetchall()
    for row in rows:
        print(f'{row[0]} | {row[1]}')
        
    conn.close()
except Exception as e:
    print(f'Error: {e}')
