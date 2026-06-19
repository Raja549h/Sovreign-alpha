import re

def convert_schema_from_source():
    with open('dashboard/schemas.py', 'r') as f:
        content = f.read()

    # Extract all CREATE TABLE statements using regex
    # Matches "CREATE TABLE IF NOT EXISTS name ( ... );" across multiple lines
    tables = re.findall(r'CREATE TABLE IF NOT EXISTS\s+\w+\s*\([^;]+;', content, re.MULTILINE | re.IGNORECASE | re.DOTALL)
    
    schema = "-- Neon PostgreSQL Migration Schema (Ordered)\n\n"
    
    for sql in tables:
        # Convert SQLite AUTOINCREMENT to Postgres SERIAL
        sql = re.sub(r'SERIAL PRIMARY KEY', 'SERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)
        
        # Convert SQLite CURRENT_TIMESTAMP handling
        sql = re.sub(r"DEFAULT\s+\(datetime\('now'\)\)", "DEFAULT CURRENT_TIMESTAMP", sql, flags=re.IGNORECASE)
        
        # Convert BLOB to BYTEA
        sql = re.sub(r'\bBLOB\b', 'BYTEA', sql, flags=re.IGNORECASE)
        
        # Remove IF NOT EXISTS for strict dry run testing
        sql = re.sub(r'IF NOT EXISTS\s+', '', sql, flags=re.IGNORECASE)
        
        schema += sql + "\n\n"
        
    # Also grab the tables from billing/init_meter_db.py
    with open('billing/init_meter_db.py', 'r') as f:
        meter_content = f.read()
    meter_tables = re.findall(r'CREATE TABLE IF NOT EXISTS\s+\w+\s*\([^;]+;', meter_content, re.MULTILINE | re.IGNORECASE | re.DOTALL)
    for sql in meter_tables:
        sql = re.sub(r'SERIAL PRIMARY KEY', 'SERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)
        sql = re.sub(r"DEFAULT\s+\(datetime\('now'\)\)", "DEFAULT CURRENT_TIMESTAMP", sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bBLOB\b', 'BYTEA', sql, flags=re.IGNORECASE)
        sql = re.sub(r'IF NOT EXISTS\s+', '', sql, flags=re.IGNORECASE)
        schema += sql + "\n\n"

    with open('POSTGRES_SCHEMA.sql', 'w') as f:
        f.write(schema)

if __name__ == '__main__':
    convert_schema_from_source()
