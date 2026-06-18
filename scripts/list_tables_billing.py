import sqlite3
conn = sqlite3.connect('c:/Users/lokes/Downloads/project/sovereign-alpha/billing/billing.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in billing.db:")
for table in tables:
    print(table[0])
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
    print(f"  Count: {cursor.fetchone()[0]}")
conn.close()
