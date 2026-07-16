from automation.email_digest import load_env
load_env()
from database import get_connection

c = get_connection().cursor()
c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'veto_archive'")
print([dict(r) for r in c.fetchall()])
