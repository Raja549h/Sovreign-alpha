from database import get_connection
import os
from pathlib import Path

BASE_DIR = Path('c:/Users/lokes/Downloads/project/sovereign-alpha')

for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith('.py'):
            filepath = Path(root) / file
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'get_connection()' in content or 'get_connection()' in content or 'get_connection()' in content:
                content = content.replace('get_connection()', 'get_connection()')
                content = content.replace('get_connection()', 'get_connection()')
                content = content.replace('get_connection()', 'get_connection()')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed {file}")
