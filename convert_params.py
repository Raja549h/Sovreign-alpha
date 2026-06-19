import os
import re

def convert_params(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    
    # We want to replace '?' with '%s', but ONLY inside SQL strings.
    # Usually SQL strings are passed to execute(), executemany(), or they contain standard SQL keywords.
    # A simple approach that catches most is looking for ? and replacing with %s
    # Let's do a smart regex: replace '?' with '%s' on any line that has 'execute', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', or is inside a multi-line string that we know is SQL.
    # Actually, across the codebase, ? is almost exclusively used for SQL params.
    # Let's replace '?' with '%s' where it's not preceded by a quote or something, but the simplest is just content.replace('?', '%s').
    # Let's check where '?' is used other than SQL. Maybe in print statements or comments?
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Only replace ? if the line looks like it contains SQL or is inside a known file
        # We can just replace all '?' except in obvious comments
        if '?' in line:
            # Avoid replacing in URLs or docs
            if 'http' in line or 'help?' in line or 'Why?' in line or '?' in line and 'TODO' in line:
                continue
            # Replacing ? with %s
            lines[i] = line.replace('?', '%s')
            
    content = '\n'.join(lines)
    
    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Converted params in {path}")

for root, _, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root or 'sqlite_archive' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            path_lower = path.lower()
            if 'database.py' in path_lower or 'convert_params' in path_lower:
                continue
            convert_params(path)

print("Param Conversion Complete.")
