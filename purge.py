import psycopg2
import os
from psycopg2.extras import RealDictCursor

NEON_URL = 'postgresql://neondb_owner:npg_HxbKeITV73Gl@ep-super-art-adot6eyq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require'

try:
    conn = psycopg2.connect(NEON_URL)
    conn.autocommit = True
    c = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check tables and columns
    c.execute("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name IN ('prediction_ledger', 'observation_memory', 'veto_archive', 'companies')
    """)
    schema = c.fetchall()
    
    tables = {}
    for row in schema:
        t = row['table_name']
        col = row['column_name']
        if t not in tables:
            tables[t] = []
        tables[t].append(col)
        
    print('Schema check:')
    for t, cols in tables.items():
        print(f'{t}: {cols}')
    
    us_tickers = ('AMD', 'TSM', 'CVX', 'XOM', 'MSFT', 'LLY', 'UNI', 'MS')
    
    # prediction_ledger
    if 'prediction_ledger' in tables:
        col = 'ticker' if 'ticker' in tables['prediction_ledger'] else ('asset' if 'asset' in tables['prediction_ledger'] else None)
        if col:
            c.execute(f"DELETE FROM prediction_ledger WHERE {col} IN %s", (us_tickers,))
            print(f"Deleted {c.rowcount} rows from prediction_ledger using column {col}")
            
    # observation_memory
    if 'observation_memory' in tables:
        if 'company_id' in tables['observation_memory']:
            c.execute("DELETE FROM observation_memory WHERE company_id IN (SELECT id FROM companies WHERE ticker IN %s)", (us_tickers,))
            print(f"Deleted {c.rowcount} rows from observation_memory")
            
    # veto_archive
    if 'veto_archive' in tables:
        col = 'ticker' if 'ticker' in tables['veto_archive'] else ('asset' if 'asset' in tables['veto_archive'] else None)
        if col:
            c.execute(f"DELETE FROM veto_archive WHERE {col} IN %s", (us_tickers,))
            print(f"Deleted {c.rowcount} rows from veto_archive using column {col}")
            
    conn.close()
except Exception as e:
    print('Error:', e)
