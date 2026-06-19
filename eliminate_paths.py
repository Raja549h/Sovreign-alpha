import os
import re

def rewrite_paths(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    
    # Remove module-level variables
    content = re.sub(r'^[A-Z_]+_DB\s*=\s*BILLING_DIR\s*/\s*["\'][^"\']+["\'].*\n', '', content, flags=re.MULTILINE)
    
    # dashboard/schemas.py: remove db_path arg from init functions
    if 'schemas.py' in path:
        content = re.sub(r'def init_([a-z_]+)_db\(db_path:\s*Path\)', r'def init_\1_db()', content)
        content = re.sub(r'def init_([a-z_]+)_db\(.*%s\)', r'def init_\1_db()', content)
    
    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Eliminated paths in {path}")

for root, _, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root or 'sqlite_archive' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            path_lower = path.lower()
            if 'database.py' in path_lower or 'eliminate_paths.py' in path_lower:
                continue
            rewrite_paths(path)

print("Path Elimination Pass 1 Complete.")
