import sys
sys.path.insert(0, '.')
from automation.email_digest import load_env
load_env()
import dashboard.app
dashboard.app.seed_database_on_startup = lambda: None

from dashboard.app import app, performance

with app.test_request_context():
    try:
        res = performance()
        print("Performance returned OK")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Performance error:", e)
