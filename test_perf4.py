import sys, os, traceback, re
sys.path.insert(0, os.path.abspath('dashboard'))
from app import app
import privacy
app.testing = True

import app as myapp
myapp.is_authenticated = lambda: True
privacy.verify_session_token = lambda x: True

with app.test_client() as client:
    client.set_cookie('localhost', 'session_token', 'bypass')
    resp = client.get('/performance')
    html = resp.data.decode('utf-8')
    m = re.search(r'<div class="stats-row">.*?</div>\s*</div>', html, re.DOTALL)
    if m:
        print("STATS ROW:")
        print(m.group(0))
    else:
        print("Stats row not found")
        # Let's just print a piece of it
        idx = html.find('Total Predictions')
        if idx != -1:
            print(html[idx:idx+200])
