import os
import re

directories = ['c:/Users/lokes/Downloads/project/sovereign-alpha']

replacements = [
    (r'\bcerebras\b', 'mistral'),
    (r'\bCerebras\b', 'Mistral'),
    (r'\bCEREBRAS\b', 'MISTRAL'),
    (r'csk-[a-zA-Z0-9]+', ''),
    (r'mistral-large-latest', 'mistral-large-latest'),
    (r'https://api\.mistral\.ai/v1', 'https://api.mistral.ai/v1')
]

updated_files = 0
for root, _, files in os.walk(directories[0]):
    if '.git' in root or '__pycache__' in root or 'node_modules' in root:
        continue
    for file in files:
        if file.endswith(('.py', '.env', '.example', '.html', '.md', '.json', '.txt')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old, new in replacements:
                    new_content = re.sub(old, new, new_content)
                    
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated {filepath}")
                    updated_files += 1
            except Exception as e:
                pass
                
print(f"Total files updated: {updated_files}")
