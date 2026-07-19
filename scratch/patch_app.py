import re
import sys

with open('dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace get_db_connection() definition to not be redundant if it's there
# app.py defines `def get_db_connection(): return db_get_connection()`
# But we just want it to import it, or yield from it.
# Actually, the simplest is to redefine it in app.py to just be an alias to the database one,
# but since it's already an alias:
# def get_db_connection():
#     conn = db_get_connection()
#     return conn
# If db_get_connection is a context manager, then this will return the context manager, which is fine.

# Replace standard patterns:
# conn = get_db_connection()
# c = conn.cursor()
# (code)
# conn.commit()
# conn.close()

# We need a regex that finds conn = get_db_connection() or db_get_connection() and wraps the subsequent block.
# Actually, since it's a huge file, a simple regex might break indentation. 
# Let's write a script that does line-by-line parsing to inject 'with get_db_connection() as conn:' and indent the rest until conn.close()

lines = content.split('\n')
new_lines = []
in_db_block = False
db_indent = 0
skip_close = False

i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # Check if we are opening a connection
    if "conn = get_db_connection()" in line or "conn = db_get_connection()" in line:
        indent = len(line) - len(line.lstrip())
        new_lines.append(" " * indent + "try:")
        new_lines.append(" " * (indent + 4) + "with get_db_connection() as conn:")
        in_db_block = True
        db_indent = indent
        i += 1
        
        # Now we need to process the block and indent it by +8 spaces total (+4 for try, +4 for with)
        while i < len(lines):
            sub_line = lines[i]
            sub_stripped = sub_line.strip()
            sub_indent = len(sub_line) - len(sub_line.lstrip())
            
            if sub_indent <= db_indent and sub_stripped != "" and not sub_stripped.startswith("except ") and not sub_stripped.startswith("finally:"):
                # End of block implicitly
                in_db_block = False
                break
                
            if "conn.close()" in sub_line:
                # Skip it, context manager handles it
                i += 1
                continue
                
            if "conn.commit()" in sub_line:
                # Context manager handles commit automatically on success
                i += 1
                continue
                
            if sub_stripped != "":
                # Wait, if we added a try, we only want to indent the `with` block by +4?
                # Actually, wrapping in `with get_db_connection() as conn:` is enough for most if we don't catch exceptions broadly.
                pass
                
            i += 1
            
# This line-by-line is risky for such a big file.
