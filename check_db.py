import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from database import get_connection

try:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE asset ILIKE '%demo%' OR asset ILIKE '%test%' OR asset ILIKE '%emergency%' OR asset ILIKE '%safety%' OR prediction_id ILIKE '%safety%';")
        count = c.fetchone()[0]
        print(f'Found {count} fake predictions.')
        
        if count > 0:
            c.execute("DELETE FROM prediction_ledger WHERE asset ILIKE '%demo%' OR asset ILIKE '%test%' OR asset ILIKE '%emergency%' OR asset ILIKE '%safety%' OR prediction_id ILIKE '%safety%';")
            c.execute("DELETE FROM decisions WHERE decision_id ILIKE '%safety%';")
            conn.commit()
            print('Fake predictions deleted.')
except Exception as e:
    print('Error:', e)
