import os

filepath = r'c:\Users\lokes\Downloads\project\sovereign-alpha\.github\workflows\daily-pipeline.yml'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('NEON_URL', 'DATABASE_URL')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed {filepath}")
