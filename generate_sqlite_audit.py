import os
import re

def generate_sqlite_audit():
    code_dirs = ['agents', 'automation', 'backtesting', 'billing', 'blockchain', 'dashboard', 'engine', 'rag', 'research', 'zkml']
    
    total_sql = 0
    total_sqlite = 0
    imports = []
    autoincrements = []
    insert_ignores = []
    insert_replaces = []
    pragmas = []
    
    for root_dir in code_dirs + ['.']:
        if not os.path.exists(root_dir) or not os.path.isdir(root_dir):
            if root_dir != '.':
                continue
            
        for root, _, files in os.walk(root_dir):
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if 'import sqlite3' in content or 'from sqlite3' in content:
                    imports.append(filepath)
                    
                # Count basic SQL statements
                sqls = re.findall(r'(SELECT|INSERT|UPDATE|DELETE|CREATE TABLE)\s', content, re.IGNORECASE)
                total_sql += len(sqls)
                
                # SQLite specifics
                ais = re.findall(r'AUTOINCREMENT', content, re.IGNORECASE)
                if ais:
                    autoincrements.append(filepath)
                    total_sqlite += len(ais)
                    
                igs = re.findall(r'INSERT OR IGNORE', content, re.IGNORECASE)
                if igs:
                    insert_ignores.append(filepath)
                    total_sqlite += len(igs)
                    
                reps = re.findall(r'INSERT', content, re.IGNORECASE)
                if reps:
                    insert_replaces.append(filepath)
                    total_sqlite += len(reps)
                    
                prgs = re.findall(r'PRAGMA', content, re.IGNORECASE)
                if prgs:
                    pragmas.append(filepath)
                    total_sqlite += len(prgs)

    md = "# SQLite Dependency Audit\n\n"
    md += f"- **Total SQL Statements Detected**: ~{total_sql}\n"
    md += f"- **Total SQLite-Specific Statements Detected**: ~{total_sqlite}\n\n"
    
    md += "## Modules Importing `sqlite3`\n"
    for m in set(imports): md += f"- `{m}`\n"
    
    md += "\n## AUTOINCREMENT Usage\n"
    for m in set(autoincrements): md += f"- `{m}`\n"
    
    md += "\n## INSERT OR IGNORE Usage\n"
    for m in set(insert_ignores): md += f"- `{m}`\n"
    
    md += "\n## INSERT Usage\n"
    for m in set(insert_replaces): md += f"- `{m}`\n"
    
    md += "\n## PRAGMA Usage\n"
    for m in set(pragmas): md += f"- `{m}`\n"
    
    with open('SQLITE_DEPENDENCY_AUDIT.md', 'w') as f:
        f.write(md)

if __name__ == '__main__':
    generate_sqlite_audit()
