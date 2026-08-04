import re

f = 'c:/Users/lokes/Downloads/project/sovereign-alpha/research/evolution_quality.py'
with open(f, 'r') as file:
    txt = file.read()

txt = re.sub(r"c\.fetchone\(\)\['cnt'\]", "c.fetchone()[0]", txt)
txt = re.sub(r"c\.fetchone\(\)\['total'\]", "c.fetchone()[0]", txt)

with open(f, 'w') as file:
    file.write(txt)
