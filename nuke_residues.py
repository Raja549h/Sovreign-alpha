from database import get_connection
import os
import re

def nuke_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    
    # 1. Replace INSERT OR REPLACE
    content = re.sub(r'INSERT\s+OR\s+REPLACE', 'INSERT', content, flags=re.IGNORECASE)
    # 2. Replace sqlite3.Row
    content = re.sub(r'conn\.row_factory\s*=\s*sqlite3\.Row', '', content)
    # 3. Replace sqlite3.connect
    content = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection()', content)
    # 4. Replace .db strings
    content = re.sub(r'billing\.db|research\.db|fund_data\.db|meter\.db', 'db', content)
    content = re.sub(r'BILLING_DIR\s*/\s*["\']db["\']', 'None', content)
    content = re.sub(r'BASE_DIR\s*/\s*["\']billing["\']\s*/\s*["\']db["\']', 'None', content)
    content = re.sub(r'PROJECT_DIR\s*/\s*["\']billing["\']\s*/\s*["\']db["\']', 'None', content)
    content = re.sub(r'get_connection\(["\']db["\']\)', 'get_connection()', content)
    
    # 5. Replace sqlite_master
    content = re.sub(r'sqlite_master', 'information_schema.tables', content)
    content = re.sub(r"type='table'", "table_schema='public'", content)
    
    # 6. Replace PRAGMA table_info
    content = re.sub(r'PRAGMA\s+table_info', 'SELECT column_name FROM information_schema.columns WHERE table_name = ', content)
    
    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Nuked residues in {path}")

for root, _, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root or 'sqlite_archive' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            path_lower = path.lower()
            if 'database.py' in path_lower or 'nuke_residues' in path_lower or 'generate_pg_schema' in path_lower or 'verify' in path_lower or 'migrate_all_sqlite' in path_lower:
                continue
            nuke_file(path)

print("Nuke Pass Complete.")
