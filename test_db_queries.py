import os
from dotenv import load_dotenv
load_dotenv('.env')
import psycopg2
from psycopg2.extras import DictCursor

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    c = conn.cursor(cursor_factory=DictCursor)
    
    c.execute('SELECT COUNT(*) as total FROM prediction_ledger')
    print('Total:', c.fetchone()['total'])

    c.execute("SELECT COUNT(*) as correct FROM prediction_ledger WHERE actual_outcome = 'correct'")
    print('Correct:', c.fetchone()['correct'])

    c.execute("SELECT COUNT(*) as with_outcome FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
    print('With outcome:', c.fetchone()['with_outcome'])

    c.execute("SELECT COALESCE(SUM(avoided_drawdown), 0) as avoided FROM veto_archive")
    print('Avoided:', c.fetchone()['avoided'])
except Exception as e:
    print('Error:', e)
