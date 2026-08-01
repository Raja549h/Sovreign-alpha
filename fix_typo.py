import os

files_to_fix = {
    r'c:\Users\lokes\Downloads\project\sovereign-alpha\.github\workflows\deploy-to-hf.yml': [
        ('svrn-alpha/soverignalpha', 'svrn-alpha/sovereignalpha')
    ],
    r'c:\Users\lokes\Downloads\project\sovereign-alpha\validate_system.py': [
        ('svrn-alpha-soverignalpha.hf.space', 'svrn-alpha-sovereignalpha.hf.space')
    ],
    r'c:\Users\lokes\Downloads\project\sovereign-alpha\verify_live_deployment_automated.py': [
        ('svrn-alpha-soverignalpha.hf.space', 'svrn-alpha-sovereignalpha.hf.space')
    ]
}

for filepath, replacements in files_to_fix.items():
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for old, new in replacements:
            content = content.replace(old, new)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")
    else:
        print(f"File not found: {filepath}")
