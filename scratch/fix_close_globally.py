import os

dirs_to_check = ['dashboard', 'documents', 'operations', 'research']

for d in dirs_to_check:
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Replace close statements
                content = content.replace('conn.close()', '# conn.close()')
                content = content.replace('schema_conn.close()', '# schema_conn.close()')
                content = content.replace('_fconn.close()', '# _fconn.close()')
                content = content.replace('_vconn.close()', '# _vconn.close()')
                
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Commented out close() in {filepath}")

print("Global cleanup complete.")
