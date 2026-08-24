import os
import re

with open('scratch/old_email.py', 'r') as f:
    old_content = f.read()
    
with open('automation/email_digest.py', 'r') as f:
    current_content = f.read()

# Extract the block of functions we need from old_email.py
# from def _with_timeout up to def init_research_tables
start_idx = old_content.find('def _with_timeout')
end_idx = old_content.find('def init_research_tables')

if start_idx != -1 and end_idx != -1:
    missing_funcs = old_content[start_idx:end_idx]
    
    # We need to insert this before get_today_stats or build_email_body
    insert_idx = current_content.find('def get_today_stats')
    
    new_content = current_content[:insert_idx] + missing_funcs + '\n\n' + current_content[insert_idx:]
    
    # Restore the function calls in build_email_body
    new_content = new_content.replace('market = None', 'market = get_market_snapshot_v2()')
    new_content = new_content.replace('regime = None', 'regime = get_regime(market)')
    new_content = new_content.replace('fii = None', 'fii = get_fii_flow_summary()')
    new_content = new_content.replace('macro = None', 'macro = get_macro_health()')
    new_content = new_content.replace('edge = None', 'edge = get_edge_score()')
    new_content = new_content.replace('feat = None', 'feat = get_featured_observation()')
    new_content = new_content.replace('flag = None', 'flag = get_currency_flag()')
    
    with open('automation/email_digest.py', 'w') as f:
        f.write(new_content)
    print('Successfully restored missing functions!')
else:
    print('Could not find the function block')
