import os
os.environ["NEON_URL"] = "postgresql://neondb_owner:npg_HxbKeITV73Gl@ep-super-art-adot6eyq-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
from database import get_connection

def fix_sequences():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT c.relname FROM pg_class c WHERE c.relkind = 'S'")
    sequences = c.fetchall()
    
    for seq in sequences:
        seq_name = seq[0]
        # Sequence name is typically table_name_id_seq
        if seq_name.endswith('_id_seq'):
            tbl = seq_name[:-7]
            try:
                c.execute(f"SELECT MAX(id) FROM {tbl}")
                max_id = c.fetchone()[0]
                if max_id:
                    c.cursor.execute(f"SELECT setval('{seq_name}', {max_id + 1})")
                    print(f"Fixed {tbl} sequence to {max_id + 1}")
            except Exception as e:
                print(f"Could not fix {tbl}: {e}")
                conn.rollback()
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    fix_sequences()
