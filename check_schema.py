from automation.email_digest import load_env
load_env()
from dashboard.gateway import get_connection
c = get_connection().cursor()
c.execute("SELECT column_name, column_default, is_nullable FROM information_schema.columns WHERE table_name = 'prediction_ledger'")
print('\n'.join(str(dict(r)) for r in c.fetchall()))
