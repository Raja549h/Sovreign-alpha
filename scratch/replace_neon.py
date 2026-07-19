import os
import re

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        encoding = 'utf-8'
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='utf-16') as f:
                content = f.read()
            encoding = 'utf-16'
        except Exception:
            return

    original = content
    
    # 1. Replace straightforward environment variables
    content = content.replace("os.environ.get('NEON_URL')", "os.environ.get('DATABASE_URL')")
    content = content.replace('os.environ.get("NEON_URL")', 'os.environ.get("DATABASE_URL")')
    
    # 2. Replace hardcoded string assignments or keys
    content = content.replace('"NEON_URL"', '"DATABASE_URL"')
    content = content.replace("'NEON_URL'", "'DATABASE_URL'")
    content = content.replace("neon_url", "db_url")
    content = content.replace("neon_present", "db_present")
    content = content.replace("NEON_URL", "DATABASE_URL")
    
    if content != original:
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            if "replace_neon.py" in path:
                continue
            process_file(path)
print("Done.")
