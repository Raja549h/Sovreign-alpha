import os
import re

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        encoding = 'utf-8'
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='utf-16') as f:
            content = f.read()
        encoding = 'utf-16'

    original = content
    
    # 1. Replace straightforward imports
    content = content.replace("from database import get_connection", "from dashboard.gateway import get_connection")
    content = content.replace("from database import get_db_connection", "from dashboard.gateway import get_db_connection")
    
    # 2. Replace complex imports
    content = content.replace("from database import get_connection as db_get_connection", "from dashboard.gateway import get_connection as db_get_connection")
    content = content.replace("from database import get_connection, init_pool", "from dashboard.gateway import get_connection")
    content = content.replace("from database import OperationalError, get_connection", "from dashboard.gateway import OperationalError, get_connection")
    content = content.replace("from database import get_connection, IntegrityError, OperationalError", "from dashboard.gateway import get_connection, IntegrityError, OperationalError")
    content = content.replace("from database import IntegrityError, get_connection", "from dashboard.gateway import IntegrityError, get_connection")
    content = content.replace("from database import DatabaseConnection", "from dashboard.gateway import DatabaseConnection")
    
    # Ensure exact match requested by user in key files
    if filepath.endswith("app.py") or filepath.endswith("master_daily.py") or filepath.endswith("email_digest.py"):
        content = content.replace("from dashboard.gateway import get_connection\n", "from dashboard.gateway import get_db_connection, get_connection\n")
        
    if content != original:
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            # Skip the script itself and gateway.py
            if "replace_gateway.py" in path or "gateway.py" in path:
                continue
            process_file(path)
print("Done.")
