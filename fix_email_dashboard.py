import os
import re

with open('automation/email_digest.py', 'r') as f:
    content = f.read()

content = content.replace('market = get_market_snapshot_v2()', 'market = None')

with open('automation/email_digest.py', 'w') as f:
    f.write(content)

with open('agents/risk_manager.py', 'r') as f:
    content = f.read()
content = content.replace('from dashboard.schemas import init_billing_db', 'pass')
with open('agents/risk_manager.py', 'w') as f:
    f.write(content)
print('Done')
