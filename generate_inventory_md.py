import json
from pathlib import Path

def generate_inventory():
    with open('inventory.json', 'r') as f:
        data = json.load(f)
        
    md = "# Database Inventory Report\n\n"
    
    for db_name, db_info in data.items():
        md += f"## `{db_name}`\n"
        md += f"- **File Size**: {db_info['size_bytes'] / 1024:.2f} KB\n"
        md += f"- **Total Tables**: {len(db_info['tables'])}\n\n"
        
        for table_name, table_info in db_info['tables'].items():
            if table_name == "sqlite_sequence":
                continue
            
            md += f"### Table: `{table_name}`\n"
            md += f"- **Row Count**: {table_info['row_count']}\n"
            
            pk = [c['name'] for c in table_info['columns'] if c['pk']]
            md += f"- **Primary Key(s)**: {', '.join(pk) if pk else 'None'}\n"
            
            if table_info['foreign_keys']:
                md += "- **Foreign Keys**:\n"
                for fk in table_info['foreign_keys']:
                    md += f"  - `{fk[3]}` references `{fk[2]}({fk[4]})`\n"
            else:
                md += "- **Foreign Keys**: None\n"
                
            if table_info['indexes']:
                md += "- **Indexes**:\n"
                for idx in table_info['indexes']:
                    md += f"  - `{idx[1]}` (Unique: {bool(idx[2])})\n"
            else:
                md += "- **Indexes**: None\n"
            
            md += "\n"
            
    with open('DATABASE_INVENTORY.md', 'w') as f:
        f.write(md)

if __name__ == "__main__":
    generate_inventory()
