from dashboard.gateway import get_connection
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT name FROM information_schema.tables WHERE table_schema='public';")
tables = cursor.fetchall()
print("Tables in db:")
for table in tables:
    print(table[0])
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
    print(f"  Count: {cursor.fetchone()[0]}")
conn.close()
