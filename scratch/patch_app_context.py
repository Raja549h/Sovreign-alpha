import sys
import re

with open('dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace block 1: save_prediction
old_1 = """def save_prediction(prediction_data: dict) -> bool:
    \"\"\"Save a prediction to the ledger. Write-once, never update timestamp.\"\"\"
    conn = get_db_connection()
    c = conn.cursor()
    try:"""
new_1 = """def save_prediction(prediction_data: dict) -> bool:
    \"\"\"Save a prediction to the ledger. Write-once, never update timestamp.\"\"\"
    try:
        with get_db_connection() as conn:
            c = conn.cursor()"""
content = content.replace(old_1, new_1)
content = content.replace("            conn.commit()\n            return True\n    except Exception as e:\n        if conn:\n            conn.rollback()", "            return True\n    except Exception as e:")

# Replace block 2: update_prediction_outcome
old_2 = """def update_prediction_outcome(prediction_id: str, outcome: str) -> bool:
    \"\"\"Mark an observation as HIT or MISS.\"\"\"
    if outcome not in ['correct', 'incorrect', 'invalid']:
        return False
        
    try:
        conn = get_db_connection()
        if not conn:
            return False
        c = conn.cursor()"""
new_2 = """def update_prediction_outcome(prediction_id: str, outcome: str) -> bool:
    \"\"\"Mark an observation as HIT or MISS.\"\"\"
    if outcome not in ['correct', 'incorrect', 'invalid']:
        return False
        
    try:
        with get_db_connection() as conn:
            c = conn.cursor()"""
content = content.replace(old_2, new_2)
content = content.replace("            conn.commit()\n            return True\n    except Exception as e:\n        print(f\"Outcome update failed: {e}\")", "            return True\n    except Exception as e:\n        print(f\"Outcome update failed: {e}\")")

# Wait, we must be careful with conn.close() removal. 
# Let's just remove conn.close(), conn.commit(), and conn.rollback() entirely using regex safely.
content = re.sub(r'^\s*conn\.close\(\)\s*\n?', '', content, flags=re.MULTILINE)
content = re.sub(r'^\s*conn\.commit\(\)\s*\n?', '', content, flags=re.MULTILINE)
content = re.sub(r'^\s*if conn:\s*\n\s*conn\.rollback\(\)\s*\n?', '', content, flags=re.MULTILINE)
content = re.sub(r'^\s*conn\.rollback\(\)\s*\n?', '', content, flags=re.MULTILINE)

# Let's manually replace the remaining conn = get_db_connection() patterns
def replacer(match):
    indent = match.group(1)
    return f"{indent}with get_db_connection() as conn:\n{indent}    c = conn.cursor()"

# We need to target conn = get_db_connection()\n[indent]c = conn.cursor()
content = re.sub(r'^(\s*)conn = get_db_connection\(\)\n\s*(?:if not conn:\n\s*return.*?\n\s*)?c = conn\.cursor\(\)', replacer, content, flags=re.MULTILINE)

# There's also some that do `conn = get_db_connection()` and then `try:\n c = conn.cursor()`
# Let's fix those
content = re.sub(r'^(\s*)conn = get_db_connection\(\)\n\s*try:\n\s*(?:if not conn:\n\s*return.*?\n\s*)?c = conn\.cursor\(\)', r'\1try:\n\1    with get_db_connection() as conn:\n\1        c = conn.cursor()', content, flags=re.MULTILINE)

# Let's fix the indenting for the rest of the block by indenting everything after `with get_db_connection() as conn:` 
# Wait, this regex approach is too fragile for a 1500 line file.

# Instead, we will wrap the db_get_connection in app.py to be a legacy-compatible wrapper!
# The user said: "When refactoring get_db_connection() to return raw psycopg2 connections, please ensure it uses the @contextmanager decorator from contextlib so that with get_db_connection() as conn: works correctly...". They did not explicitly forbid a legacy wrapper inside `app.py`. BUT they said: "Every query in the entire codebase must use with get_db_connection as conn."

# Okay, I will do it the safest way: I will use AST or a robust parser.
