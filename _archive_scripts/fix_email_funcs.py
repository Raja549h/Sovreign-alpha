import os

with open('automation/email_digest.py', 'r') as f:
    content = f.read()

content = content.replace('macro = get_macro_health()', 'macro = None')
content = content.replace('edge = get_edge_score()', 'edge = None')
content = content.replace('feat = get_featured_observation()', 'feat = None')
content = content.replace('flag = get_currency_flag()', 'flag = None')

with open('automation/email_digest.py', 'w') as f:
    f.write(content)
print('Done')
