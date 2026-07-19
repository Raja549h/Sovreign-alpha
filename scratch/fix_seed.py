import re

with open('automation/email_digest.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix seed_meaningful_data block
old_seed = """def seed_meaningful_data():
    init_tables()
    if has_cleared_predictions():
        return
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
    now = datetime.utcnow()"""

# I need to match the rest of the block and indent it, but it's easier to just replace the whole function.
# Wait, I don't want to break the file if I don't know the exact end.
