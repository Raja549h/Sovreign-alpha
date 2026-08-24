import sys
sys.path.insert(0, '.')
from automation.email_digest import load_env
load_env()
# # import dashboard decommissioned.app decommissioned
dashboard.app.seed_database_on_startup = lambda: None

# dashboard.app decommissioned

with app.test_request_context():
    try:
        res = performance()
        print("Performance returned OK")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Performance error:", e)
