from automation.email_digest import load_env
load_env()
from dashboard.gateway import get_connection
c = get_connection().cursor()
c.execute("SELECT timestamp, status FROM prediction_ledger LIMIT 10")
for r in c.fetchall():
    print(dict(r))
