import re
from pathlib import Path

def generate_schema():
    db_paths = [Path('billing/billing.db'), Path('billing/research.db'), Path('billing/fund_data.db'), Path('billing/meter.db')]
    
    # Priority tables that must be created first to satisfy foreign keys
    priority_tables = ['companies', 'observation_memory', 'filings', 'portfolios', 'theses', 'shadow_portfolio', 'observation_validations']
    
    all_sqls = []
    seen_tables = set()
    
    for db_path in db_paths:
        if not db_path.exists():
            continue
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
        tables = c.fetchall()
        for name, sql in tables:
            if sql and name not in seen_tables:
                seen_tables.add(name)
                all_sqls.append((name, sql))

    schema = "-- Ordered Neon PostgreSQL Schema\n\n"
    
    def process_sql(sql):
        sql = re.sub(r'SERIAL PRIMARY KEY', 'SERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)
        sql = re.sub(r"DEFAULT\s+\(datetime\('now'\)\)", "DEFAULT CURRENT_TIMESTAMP", sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bBLOB\b', 'BYTEA', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bBOOLEAN\b', 'INTEGER', sql, flags=re.IGNORECASE) # Match SQLite boolean storage
        
        # Remove REFERENCES constraints since local SQLite data contains orphans (e.g. 99999)
        sql = re.sub(r'REFERENCES\s+\w+\s*\([^)]+\)', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'ON\s+DELETE\s+(CASCADE|SET NULL|RESTRICT|NO ACTION)', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'ON\s+UPDATE\s+(CASCADE|SET NULL|RESTRICT|NO ACTION)', '', sql, flags=re.IGNORECASE)
        
        if not sql.endswith(';'):
            sql += ';'
        return sql

    # 1. Priority tables in exact order
    for p_name in priority_tables:
        for name, sql in all_sqls:
            if name == p_name:
                schema += f"-- {name}\n" + process_sql(sql) + "\n\n"
            
    # 2. Rest
    for name, sql in all_sqls:
        if name not in priority_tables:
            schema += f"-- {name}\n" + process_sql(sql) + "\n\n"

    with open('POSTGRES_SCHEMA.sql', 'w') as f:
        f.write(schema)

if __name__ == '__main__':
    generate_schema()
