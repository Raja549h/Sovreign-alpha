import sys, os

with open('dashboard/app.py', 'r') as f:
    content = f.read()

content = content.replace('with get_connection() as conn:\n            pass', 'conn = get_connection()\n        if not conn:\n            raise Exception("DB Offline")\n        conn.close()')

with open('dashboard/app.py', 'w') as f:
    f.write(content)
print('Fixed before_request in dashboard/app.py')
