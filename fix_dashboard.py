import sys, os, re

with open('dashboard/app.py', 'r') as f:
    content = f.read()

# Remove the block 'if is_demo_mode(): ... ' up to 'print(f"[seed] Safety net also failed: {_e}")'
content = re.sub(r'if is_demo_mode\(\):.*?print\(f"\[seed\] Safety net also failed: \{_e\}"\)', '# SAFETY NET REMOVED - No demo data insertion.', content, flags=re.DOTALL)

before_request = '''
@app.before_request
def check_db_availability():
    if request.endpoint == "static":
        return
    try:
        from dashboard.gateway import get_connection
        with get_connection() as conn:
            pass
    except Exception as e:
        print("[DB_ERROR]", e)
        try:
            return render_template('unavailable.html', message="Database is currently unavailable. Please try again later.", error_code="DB_CONNECTION_FAILED"), 503
        except Exception:
            abort(503, description="Database unavailable — Sovereign Alpha is offline for maintenance.")
'''

if '@app.before_request' not in content:
    content = content.replace('app = Flask(__name__)', 'app = Flask(__name__)' + before_request)

with open('dashboard/app.py', 'w') as f:
    f.write(content)
print('Updated dashboard/app.py')
