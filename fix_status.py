import sys
import os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from database import get_connection

queries = [
    "UPDATE prediction_ledger SET status = 'HIT' WHERE actual_outcome = 'correct' AND status NOT IN ('HIT', 'MISS');",
    "UPDATE prediction_ledger SET status = 'MISS' WHERE actual_outcome = 'incorrect' AND status NOT IN ('HIT', 'MISS');",
    "UPDATE prediction_ledger SET status = 'PENDING' WHERE actual_outcome IS NULL AND status NOT IN ('HIT', 'MISS', 'PENDING');"
]

try:
    with get_connection() as conn:
        c = conn.cursor()
        for q in queries:
            print(f'Executing: {q}')
            c.execute(q)
            print(f'Rows updated: {c.rowcount}')
        conn.commit()
        print('Status updates complete.')
except Exception as e:
    print('Failed:', e)
