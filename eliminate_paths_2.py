import os
import re

def rewrite_app(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    
    # 1. Remove from research.storage.research_db import RESEARCH_DB
    content = re.sub(r'from research\.storage\.research_db import RESEARCH_DB.*%s(\n|$)', '', content)
    content = re.sub(r'from research\.storage\.research_db import .*%sRESEARCH_DB.*%s(\n|$)', '', content)
    
    # 2. Fix dashboard file size calculations
    content = re.sub(r'research_db_path = None', 'research_db_path = None', content)
    content = re.sub(r'billing_db_path = None', 'billing_db_path = None', content)
    content = re.sub(r'meter_db_path = None', 'meter_db_path = None', content)
    
    content = re.sub(r'db_research_size_kb = .*%sif research_db_path\.exists\(\) else 0', 'db_research_size_kb = 0', content)
    content = re.sub(r'db_billing_size_kb = .*%sif billing_db_path\.exists\(\) else 0', 'db_billing_size_kb = 0', content)
    content = re.sub(r'db_meter_size_kb = .*%sif meter_db_path\.exists\(\) else 0', 'db_meter_size_kb = 0', content)
    
    content = re.sub(r'db_research_healthy = research_db_path\.exists\(\)', 'db_research_healthy = True', content)
    content = re.sub(r'db_billing_healthy = billing_db_path\.exists\(\)', 'db_billing_healthy = True', content)
    content = re.sub(r'db_meter_healthy = meter_db_path\.exists\(\)', 'db_meter_healthy = True', content)
    
    # 3. Fix seed_all_empty_tables(db_path=str(RESEARCH_DB))
    content = re.sub(r'seed_all_empty_tables\(db_path=str\(RESEARCH_DB\), quiet=False\)', 'seed_all_empty_tables(quiet=False)', content)
    
    # 4. Fix init_research_db(_research_db)
    content = re.sub(r'init_research_db\([^)]+\)', 'init_research_db()', content)

    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Eliminated paths in {path}")

for root, _, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root or 'sqlite_archive' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            path_lower = path.lower()
            if 'database.py' in path_lower or 'eliminate_paths' in path_lower:
                continue
            rewrite_app(path)

print("Path Elimination Pass 2 Complete.")
