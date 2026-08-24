from automation.email_digest import load_env
load_env()
from dashboard.gateway import get_connection

c = get_connection().cursor()
c.execute('SELECT veto_correct, count(*) FROM veto_archive group by veto_correct')
rows = c.fetchall()
print('Veto correct distribution:', [dict(r) for r in rows])
