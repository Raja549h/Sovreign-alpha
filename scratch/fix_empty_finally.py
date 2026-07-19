import os
import re

files_to_fix = [
    r"dashboard\app.py",
    r"operations\daily_cycle.py",
    r"research\auto_review_engine.py",
    r"research\backfill_registry.py",
    r"research\fii_intelligence.py"
]

for file in files_to_fix:
    filepath = os.path.join(r"c:\Users\lokes\Downloads\project\sovereign-alpha", file)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We want to replace cases where finally: is followed only by comments and whitespace
    # until the next block/function definition.
    # We can inject a 'pass' right after the commented close.
    # To be extremely safe, we replace '# conn.close()' with 'pass\n        # conn.close()'
    # or just replace 'finally:' with 'finally:\n        pass' if it has only comments
    
    # A safe way: any commented out close that has spaces before it:
    # replace with the same spaces + pass + newline + the commented out close
    
    # Since there are multiple formats (e.g. # # conn.close() or # schema_conn.close())
    # Let's use a regex that finds lines with just spaces and a comment containing .close()
    
    content = re.sub(
        r'^([ \t]+)(#+.*\.close\(\)[ \t]*)$',
        r'\1pass\n\1\2',
        content,
        flags=re.MULTILINE
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Fixed {file}")
