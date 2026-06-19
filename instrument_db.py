import os
import re

def instrument_database(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    orig = content
    
    # Let's replace _translate_sql with an instrumented version.
    instrumented_code = '''
    def _translate_sql(self, query, params):
        orig_query = query
        changed = False

        if params and '%s' in query:
            query = query.replace('%s', '%s')
            changed = True
            
        if 'INSERT OR IGNORE' in query.upper():
            query = re.sub(r'INSERT\s+OR\s+IGNORE\s+INTO', 'INSERT INTO', query, flags=re.IGNORECASE)
            query += ' ON CONFLICT DO NOTHING'
            changed = True
            
        if 'INSERT' in query.upper():
            query = re.sub(r'INSERT\s+OR\s+REPLACE\s+INTO', 'INSERT INTO', query, flags=re.IGNORECASE)
            query += ' ON CONFLICT (id) DO UPDATE SET ' 
            changed = True

        if 'datetime(' in query.lower():
            query = query.replace("datetime('now')", "NOW()")
            changed = True
            
        if 'AUTOINCREMENT' in query.upper():
            query = re.sub(r'INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT', 'SERIAL PRIMARY KEY', query, flags=re.IGNORECASE)
            query = re.sub(r'AUTOINCREMENT', '', query, flags=re.IGNORECASE)
            changed = True

        if 'BEGIN IMMEDIATE' in query.upper():
            return None

        if changed:
            with open("translation_audit.log", "a", encoding="utf-8") as lf:
                lf.write(f"TRANSLATED: {orig_query.strip()} -> {query.strip()}\\n")

        return query
'''
    
    # Need to match the existing _translate_sql carefully
    # Using regex to replace the function definition block.
    # We will just replace from 'def _translate_sql(self, query, params):' up to 'return query'
    content = re.sub(r'\s*def _translate_sql\(self, query, params\):.*%s(%s=\n\s*class|\Z)', '\n' + instrumented_code + '\n', content, flags=re.DOTALL)

    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Instrumented database.py")
    else:
        print("Failed to instrument database.py")

instrument_database('database.py')
