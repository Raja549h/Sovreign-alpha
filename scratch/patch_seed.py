import os
import re

files_to_patch = [
    "dashboard/seed_db.py",
    "research/backfill_memory.py",
    "research/storage/research_db.py"
]

def indent_block(code_str):
    lines = code_str.split("\n")
    # indent every line by 4 spaces
    return "\n".join("    " + line if line.strip() else line for line in lines)

for filepath in files_to_patch:
    if not os.path.exists(filepath):
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Find function definitions that contain `conn = get_connection()`
    # We will replace `conn = get_connection()` with `with get_connection() as conn:` and indent the rest of the function!
    # This is slightly tricky, so we'll just replace the specific function bodies manually or using regex.

    if filepath == "dashboard/seed_db.py":
        content = content.replace(
            "    conn = get_connection()\n    c = conn.cursor()",
            "    with get_connection() as conn:\n        c = conn.cursor()"
        )
        # Indent everything after `c = conn.cursor()` until the end of the function.
        # It's easier to just catch all `c.execute(` and `conn.commit()` and indent them.
        content = re.sub(r'(\n    )(c\.execute|conn\.commit|print)', r'\1    \2', content)

    elif filepath == "research/backfill_memory.py":
        content = content.replace(
            "    conn = get_connection()\n    c = conn.cursor()",
            "    with get_connection() as conn:\n        c = conn.cursor()"
        )
        content = re.sub(r'(\n    )(c\.execute|conn\.commit|print|c\.fetchone|return|for |if |obs_text|cat|c\.fetchall)', r'\1    \2', content)

    elif filepath == "research/storage/research_db.py":
        # init_extended_tables
        content = content.replace(
            "    conn = get_connection()\n    c = conn.cursor()",
            "    with get_connection() as conn:\n        c = conn.cursor()"
        )
        content = re.sub(r'(\n    )(c\.execute|conn\.commit)', r'\1    \2', content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        print(f"Patched {filepath}")

# Also patch schemas.py for the Exception
schemas_path = "dashboard/schemas.py"
with open(schemas_path, "r", encoding="utf-8") as f:
    schemas = f.read()
schemas = schemas.replace("except OperationalError:", "except Exception:")
with open(schemas_path, "w", encoding="utf-8") as f:
    f.write(schemas)
print("Patched dashboard/schemas.py")
