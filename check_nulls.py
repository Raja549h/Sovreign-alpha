from automation.email_digest import load_env
load_env()
from database import get_connection
c = get_connection().cursor()
c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE sector IS NULL AND asset IS NULL")
print("Null rows:", c.fetchone()[0])
