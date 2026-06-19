import os
from pathlib import Path
import re

BASE_DIR = Path('c:/Users/lokes/Downloads/project/sovereign-alpha')

def migrate_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip files that we already migrated or shouldn't touch
    if 'test_' in filepath.name or filepath.name in ['database.py', 'list_tables.py', 'verify_db.py', 'seed_all_empty_tables.py', 'red_team_attack.py', 'generate_pg_schema.py', 'generate_pg_schema_actual.py', 'generate_pg_schema_ordered.py', 'run_all_tests.py', 'dry_run_migration.py']:
        return

    # Skip if no sqlite3.connect
    if 'sqlite3.connect' not in content:
        return

    print(f"Migrating {filepath.name}...")

    # We need to add the import if it's not there
    if 'from database import get_connection' not in content:
        # Add after import sqlite3
        content = re.sub(r'import sqlite3', 'import sqlite3\nfrom database import get_connection', content, count=1)
        if 'import sqlite3' not in content:
            # If no import sqlite3, just add it at the top
            content = 'from database import get_connection\n' + content

    # Replace specific connect patterns
    
    # Pattern 1: db_path or self.db_path or DB_PATH (Billing)
    # Most of these are billing.db, or handled by the fallback in get_connection if they pass a Path
    # Wait, get_connection expects a string: 'billing.db', 'research.db', 'fund_data.db'
    
    # We will use regex to find get_connection() and replace intelligently
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'sqlite3.connect' in line:
            # Determine which db it is
            if 'research.db' in line or 'RESEARCH_DB' in line or '_RDB' in line or 'research' in line.lower():
                lines[i] = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection()', line)
            elif 'fund_data.db' in line or 'FUND_DATA_DB' in line or 'fund_db' in line.lower():
                lines[i] = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection()', line)
            elif 'meter.db' in line or 'init_meter_db' in filepath.name or 'meter.py' in filepath.name:
                # meter.py uses self.db_path which points to billing.db actually!
                # Wait, meter.py lines 22-25: `self.db_path = self.data_dir / "billing.db"`
                if 'meter.db' in line:
                    lines[i] = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection()', line)
                else:
                    lines[i] = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection()', line)
            else:
                lines[i] = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection()', line)

    content = '\n'.join(lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith('.py'):
            migrate_file(Path(root) / file)
