import re

with open('automation/email_digest.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace import
content = content.replace("from dashboard.gateway import DatabaseConnection", "from dashboard.gateway import get_db_connection")

# Remove local get_db_connection
content = re.sub(r'def get_db_connection\(\):\n\s*try:\n\s*return DatabaseConnection\(\)\n\s*except Exception as e:\n\s*raise Exception\(f"Database connection failed: \{e\}"\)\n', '', content)

with open('automation/email_digest.py', 'w', encoding='utf-8') as f:
    f.write(content)
