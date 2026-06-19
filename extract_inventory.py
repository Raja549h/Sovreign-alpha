from database import get_connection, json
from pathlib import Path

db_paths = [Path('billing/db'), Path('billing/db'), Path('billing/db'), Path('billing/db')]
inventory = {}

for db_path in db_paths:
    if not db_path.exists():
        continue
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM information_schema.tables WHERE table_schema='public';")
    tables = [r[0] for r in c.fetchall()]
    
    db_info = {'size_bytes': db_path.stat().st_size, 'tables': {}}
    for table in tables:
        c.execute(f"SELECT COUNT(*) FROM {table};")
        count = c.fetchone()[0]
        c.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = ({table});")
        columns = c.fetchall()
        c.execute(f"PRAGMA index_list({table});")
        indexes = c.fetchall()
        c.execute(f"PRAGMA foreign_key_list({table});")
        fks = c.fetchall()
        db_info['tables'][table] = {
            'row_count': count,
            'columns': [{'cid': col[0], 'name': col[1], 'type': col[2], 'notnull': col[3], 'dflt_value': col[4], 'pk': col[5]} for col in columns],
            'indexes': indexes,
            'foreign_keys': fks
        }
    inventory[db_path.name] = db_info

with open('inventory.json', 'w') as f:
    json.dump(inventory, f, indent=2)
