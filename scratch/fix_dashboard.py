import os

file_path = r'c:\Users\lokes\Downloads\project\sovereign-alpha\dashboard\app.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Comment out connection close statements
content = content.replace('conn.close()', '# conn.close()')
content = content.replace('schema_conn.close()', '# schema_conn.close()')
content = content.replace('_fconn.close()', '# _fconn.close()')
content = content.replace('_vconn.close()', '# _vconn.close()')

# Fix 2: Replace boolean conditions in SQL with integer conditions
content = content.replace('veto_correct = true', 'veto_correct = 1')
content = content.replace('veto_correct = false', 'veto_correct = 0')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied fixes successfully to dashboard/app.py")
