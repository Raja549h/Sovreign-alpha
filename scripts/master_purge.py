import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import timedelta
import dateutil.parser
from dotenv import load_dotenv

def purge_7_day_duplicates():
    load_dotenv(override=True)
    url = os.environ.get('DATABASE_URL') or os.environ.get('AIVEN_DATABASE_URL')
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all trades
    cur.execute("SELECT id, asset, timestamp, status FROM prediction_ledger ORDER BY asset, timestamp ASC")
    trades = cur.fetchall()
    
    last_kept = {}
    to_delete = []
    
    for row in trades:
        asset = row['asset']
        # parse timestamp if string
        ts = row['timestamp']
        if isinstance(ts, str):
            ts = dateutil.parser.parse(ts)
            
        if asset not in last_kept:
            last_kept[asset] = ts
            continue
            
        # Check if within 7 days
        if ts - last_kept[asset] < timedelta(days=7):
            to_delete.append(row['id'])
        else:
            last_kept[asset] = ts
            
    if to_delete:
        print(f"Purging {len(to_delete)} trades that occurred within 7 days of a previous trade for the same asset.")
        cur.execute("DELETE FROM prediction_ledger WHERE id = ANY(%s)", (to_delete,))
        conn.commit()
    else:
        print("No 7-day duplicates found.")
        
    conn.close()

if __name__ == '__main__':
    purge_7_day_duplicates()
