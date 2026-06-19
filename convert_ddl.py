import os
import re

def convert_ddl(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    content = re.sub(r'INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT', 'SERIAL PRIMARY KEY', content, flags=re.IGNORECASE)
    
    # Also remove any "import sqlite3" just in case we missed it
    content = re.sub(r'^import sqlite3\s*\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^from sqlite3 import .*\n', '', content, flags=re.MULTILINE)

    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Converted DDL in {path}")

for root, _, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root or 'sqlite_archive' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            path_lower = path.lower()
            if 'database.py' in path_lower or 'convert_ddl.py' in path_lower:
                continue
            convert_ddl(path)

print("DDL Conversion Complete.")
