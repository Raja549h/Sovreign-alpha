import psycopg2
from pathlib import Path
import json

NEON_URL = "postgresql://neondb_owner:npg_HxbKeITV73Gl@ep-super-art-adot6eyq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def verify():
    # PHASE 1
    conn = psycopg2.connect(NEON_URL)
    cur = conn.cursor()
    cur.execute("SELECT current_database(), current_schemas(true);")
    db, schemas = cur.fetchone()
    report1 = "# Neon Connection Verification Report\n\n- **Neon URL Reachable**: PASSED\n"
    report1 += f"- **SSL Connection Active**: PASSED (Enforced by pooler)\n"
    report1 += "- **Credentials Valid**: PASSED\n"
    report1 += f"- **Database**: `{db}`\n- **Active Schemas**: `{schemas}`\n"
    with open('NEON_CONNECTION_REPORT.md', 'w') as f: f.write(report1)

    # PHASE 2 & 3
    db_paths = [Path('billing/db'), Path('billing/db'), Path('billing/db'), Path('billing/db')]
    report2 = "# Schema Comparison Report\n\n"
    report3 = "# Row Count Verification Report\n\n| Table | SQLite Count | Neon Count | Difference |\n|---|---|---|---|\n"
    
    total_diff = 0
    tables_verified = 0
    
    for path in db_paths:
        if not path.exists(): continue
        print(f"Processing {path.name}...")
        s_conn = get_connection()
        s_cur = s_conn.cursor()
        s_cur.execute("SELECT name FROM information_schema.tables WHERE table_schema='public' AND name != 'sqlite_sequence';")
        tables = [r[0] for r in s_cur.fetchall()]
        
        for t in tables:
            print(f"Checking table {t}...")
            tables_verified += 1
            # Row counts
            s_cur.execute(f"SELECT COUNT(*) FROM {t};")
            s_count = s_cur.fetchone()[0]
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t};")
                n_count = cur.fetchone()[0]
            except Exception as e:
                conn.rollback()
                n_count = -1
                
            diff = abs(s_count - n_count)
            total_diff += diff
            report3 += f"| `{t}` | {s_count} | {n_count} | {diff} |\n"
            
            # Schema basics
            s_cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = ({t});")
            s_cols = s_cur.fetchall()
            report2 += f"## Table: `{t}`\n- **SQLite Columns**: {len(s_cols)}\n"
            
            try:
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}';")
                n_cols = cur.fetchall()
                report2 += f"- **Neon Columns**: {len(n_cols)}\n"
                report2 += f"- **Schema Match**: {'PASSED' if len(s_cols) == len(n_cols) else 'FAILED'}\n\n"
            except Exception:
                conn.rollback()
                report2 += f"- **Neon Columns**: ERROR\n- **Schema Match**: FAILED\n\n"

    report3 += f"\n**Total Tables Verified**: {tables_verified}\n"
    report3 += f"**Total Discrepancies**: {total_diff}\n"
    report3 += f"**Verdict**: {'PASSED' if total_diff == 0 else 'FAILED'}\n"
    
    with open('SCHEMA_COMPARISON.md', 'w') as f: f.write(report2)
    with open('ROW_COUNT_VERIFICATION.md', 'w') as f: f.write(report3)
    
if __name__ == '__main__':
    verify()
