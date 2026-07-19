from automation.email_digest import load_env
load_env()
from dashboard.gateway import get_connection

c = get_connection().cursor()
c.execute('SELECT expected_loss_pct, actual_return_pct, actual_outcome, veto_correct FROM veto_archive LIMIT 5')
print([dict(r) for r in c.fetchall()])
