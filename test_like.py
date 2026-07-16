from automation.email_digest import load_env
load_env()
from database import get_connection
c = get_connection().cursor()
try:
    c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE timestamp LIKE '2026-07-13%'")
    print("Success:", c.fetchone()[0])
except Exception as e:
    print("Error:", type(e), e)
