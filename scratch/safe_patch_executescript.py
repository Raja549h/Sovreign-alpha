import os

dirs_to_check = ['dashboard', 'research/macro', 'research/storage', 'research']

for d in dirs_to_check:
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                # 1. Read the content entirely FIRST
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 2. Modify in memory
                if '.executescript(' in content:
                    content = content.replace('.executescript(', '.cursor().execute(')
                    
                    # 3. Write back safely
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed executescript in {filepath}")
