import os
import glob
import re

base = 'C:/Users/lokes/Downloads/project/sovereign-alpha/'
files = glob.glob(base + '**/*.*', recursive=True)

# Define replacements (no word boundaries so it replaces cerebras_key, etc.)
replacements = [
    (r'cerebras', 'cerebras'),
    (r'Cerebras', 'Cerebras'),
    (r'CEREBRAS', 'CEREBRAS'),
    (r'gpt-oss-120b-?3\.?[0-9]?-[0-9]+[bc]?-?[a-z]*', 'gpt-oss-120b'),
    (r'\bllama\b', 'gpt-oss-120b')
]

for filepath in files:
    if filepath.endswith('.py') or filepath.endswith('.md') or filepath.endswith('.txt') or filepath.endswith('.env') or filepath.endswith('.yml') or filepath.endswith('.html'):
        if 'venv' in filepath or '.git' in filepath or '__pycache__' in filepath:
            continue
            
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        new_content = content
        
        # Don't replace 'gpt-oss-120b' if it's 'llama-index'
        new_content = re.sub(r'llama-index', 'llama-index', new_content)
        
        for old, new in replacements:
            new_content = re.sub(old, new, new_content)
            
        new_content = new_content.replace('llama-index', 'llama-index')
            
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated: {filepath}')

print('Done replacing without word boundaries.')
