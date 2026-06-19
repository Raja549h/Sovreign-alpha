from database import get_connection
import re
from pathlib import Path

def convert_schema():
    db_paths = [Path('billing/billing.db'), Path('billing/research.db'), Path('billing/fund_data.db'), Path('billing/meter.db')]
    schema = "-- Neon PostgreSQL Migration Schema\n\n"
    
    for db_path in db_paths:
        if not db_path.exists():
            continue
        schema += f"-- Source: {db_path.name}\n\n"
        
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
        tables = c.fetchall()
        
        for t in tables:
            sql = t[0]
            if not sql:
                continue
                
            # Convert SQLite AUTOINCREMENT to Postgres SERIAL
            sql = re.sub(r'SERIAL PRIMARY KEY', 'SERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)
            
            # Convert SQLite boolean check constraints (if any) or DATETIME defaults
            sql = re.sub(r"DEFAULT\s+\(datetime\('now'\)\)", "DEFAULT CURRENT_TIMESTAMP", sql, flags=re.IGNORECASE)
            
            # Format nicely
            if not sql.endswith(';'):
                sql += ';'
                
            schema += sql + "\n\n"
            
    with open('POSTGRES_SCHEMA.sql', 'w') as f:
        f.write(schema)

if __name__ == '__main__':
    convert_schema()
