import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('DATABASE_URL')
if db_url:
    db_url = db_url.strip()

print(f"Connecting to: {db_url[:40]}...")
conn = psycopg2.connect(db_url)
c = conn.cursor()

c.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
""")
tables = c.fetchall()
for table in tables:
    table_name = table[0]
    print(f"\nTABLE: {table_name}")
    c.execute(f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = '{table_name}'
    """)
    for col in c.fetchall():
        print(f"  - {col[0]}: {col[1]} (Nullable: {col[2]})")
