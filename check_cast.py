from automation.email_digest import load_env
load_env()
from database import get_connection
c = get_connection().cursor()
c.execute("SELECT CAST(timestamp AS TEXT) FROM prediction_ledger LIMIT 1")
print(c.fetchone()[0])
