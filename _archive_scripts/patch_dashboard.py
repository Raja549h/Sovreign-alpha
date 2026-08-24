import os
import re

conn_code = '''
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
@contextmanager
def get_connection():
    conn = psycopg2.connect(os.environ.get('AIVEN_DATABASE_URL') or os.environ.get('DATABASE_URL'), cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()
'''

for file in ['research/macro/fii_flow.py', 'agents/risk_manager.py']:
    with open(file, 'r') as f:
        content = f.read()
    content = content.replace('from dashboard.gateway import get_connection', conn_code)
    with open(file, 'w') as f:
        f.write(content)

with open('automation/master_daily.py', 'r') as f:
    content = f.read()
content = content.replace("import subprocess\n        import sys", "")
with open('automation/master_daily.py', 'w') as f:
    f.write(content)
print('Done')
