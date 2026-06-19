import os
import re

for root, _, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root or 'sqlite_archive' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            path_lower = path.lower()
            if 'database.py' in path_lower or 'fix_imports.py' in path_lower:
                continue
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            orig = content
            
            # 1. Fix get_connection())
            content = content.replace('get_connection())', 'get_connection()')
            
            # 2. Fix scripts missing from database import get_connection
            if 'get_connection()' in content and 'from database import' not in content:
                # Add it after sys.path if exists
                if 'sys.path.insert' in content:
                    content = re.sub(r'(sys\.path\.insert.*?\n)', r'\1from database import get_connection\n', content, count=1)
                else:
                    content = 'from database import get_connection\n' + content
                    
            if content != orig:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed {path}")
