import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

DB_URL = os.environ.get('DATABASE_URL') or os.environ.get('AIVEN_DATABASE_URL')

def main():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) as total FROM prediction_ledger;')
        total = c.fetchone()['total']
        
        c.execute('''
            SELECT status, actual_outcome, COUNT(*) as count 
            FROM prediction_ledger 
            GROUP BY status, actual_outcome
        ''')
        breakdown = c.fetchall()
        
        resolved_count = 0
        pending_count = 0
        
        for row in breakdown:
            outcome = str(row['actual_outcome']).upper() if row['actual_outcome'] else 'NONE'
            
            if outcome in ['HIT', 'MISS']:
                resolved_count += row['count']
            else:
                pending_count += row['count']
                
        print('\n--- SOVEREIGN ALPHA PREDICTION STATUS ---')
        print(f'Total Predictions Logged: {total}')
        print(f'Total Resolved (Closed):  {resolved_count}')
        print(f'Total Pending (Active):   {pending_count}')
        print('-----------------------------------------')
        
        print('\nDetailed Breakdown:')
        for row in breakdown:
            print(f" - Status: {row['status']:<15} | Outcome: {str(row['actual_outcome']):<15} | Count: {row['count']}")
            
    except Exception as e:
        print(f'Database error: {e}')
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()
