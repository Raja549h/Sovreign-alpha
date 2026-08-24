from dotenv import load_dotenv
load_dotenv()
from engine.db import get_connection
with get_connection() as conn:
    c = conn.cursor()
    c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = [t[0] for t in c.fetchall()]
    print('Tables:', tables)
    for t in tables:
        c.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t}'")
        cols = [r[0] for r in c.fetchall()]
        if 'created_at' in cols or 'generated_at' in cols or 'timestamp' in cols:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            count = c.fetchone()[0]
            if count > 0:
                time_col = 'created_at' if 'created_at' in cols else ('generated_at' if 'generated_at' in cols else 'timestamp')
                c.execute(f"SELECT {time_col} FROM {t} ORDER BY 1 DESC LIMIT 1")
                latest = c.fetchone()[0]
                print(f"{t}: count={count}, latest={latest}")
