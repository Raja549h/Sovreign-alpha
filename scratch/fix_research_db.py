import re

filepath = r"c:\Users\lokes\Downloads\project\sovereign-alpha\research\storage\research_db.py"
with open(filepath, "r") as f:
    content = f.read()

lines = content.split('\n')
for i, line in enumerate(lines):
    # Only replace if line looks like it contains SQL logic
    if '?' in line and ('SELECT' in line or 'INSERT' in line or 'UPDATE' in line or 'DELETE' in line or 'VALUES' in line or 'c.execute' in line or 'fields.append' in line):
        lines[i] = line.replace('?', '%s')

with open(filepath, "w") as f:
    f.write('\n'.join(lines))

print("research_db.py ? replaced with %s")
