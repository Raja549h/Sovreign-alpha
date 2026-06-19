import os
import re

def process_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    
    # 1. Remove import sqlite3
    content = re.sub(r'^import sqlite3\s*\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^from sqlite3 import .*\n', '', content, flags=re.MULTILINE)
    
    # 2. Replace row_factory
    content = re.sub(r'^[ \t]*\w+\.row_factory\s*=\s*sqlite3\.Row.*%s\n', '', content, flags=re.MULTILINE)
    
    # 3. Replace exceptions
    needs_exceptions = False
    if 'sqlite3.IntegrityError' in content or 'sqlite3.OperationalError' in content or 'sqlite3.DatabaseError' in content:
        needs_exceptions = True
        content = content.replace('sqlite3.IntegrityError', 'IntegrityError')
        content = content.replace('sqlite3.OperationalError', 'OperationalError')
        content = content.replace('sqlite3.DatabaseError', 'DatabaseError')
        
    # 4. Replace sqlite3.connect
    # Many files have conn = get_connection()
    # We replace with get_connection()
    # We need to make sure from database import get_connection is present
    if 'sqlite3.connect' in content:
        content = re.sub(r'sqlite3\.connect\([^)]*\)', 'get_connection()', content)
        if 'get_connection' not in content:
            # We need to import it
            if 'from database import' in content:
                content = content.replace('from database import ', 'from database import get_connection, ')
            else:
                content = 'from database import get_connection\n' + content

    if needs_exceptions:
        if 'from database import' in content:
            content = content.replace('from database import ', 'from database import IntegrityError, OperationalError, DatabaseError, ')
        else:
            content = 'from database import IntegrityError, OperationalError, DatabaseError\n' + content

    # 5. Replace any remaining .db paths passed to get_connection
    content = re.sub(r'get_connection\([^)]+\)', 'get_connection()', content)

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Refactored: {path}")

for root, _, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root or 'sqlite_archive' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            path_lower = path.lower()
            if 'database.py' in path_lower or 'eradicate.py' in path_lower or 'verify' in path_lower or 'simulate' in path_lower or 'test' in path_lower or 'script' in path_lower or 'archive' in path_lower or 'seed_db' in path_lower:
                continue
            process_file(path)

print("Eradication complete.")
