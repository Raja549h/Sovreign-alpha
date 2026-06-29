import sys, os, traceback, re
sys.path.insert(0, os.path.abspath('dashboard'))
from app import app
import app as myapp
myapp.is_authenticated = lambda: True

with app.test_client() as client:
    client.set_cookie('session_token', 'bypass')
    resp = client.get('/performance')
    html = resp.data.decode('utf-8')
    print("LEN HTML:", len(html))
    idx = html.find('Total Predictions')
    if idx != -1:
        print(html[idx-100:idx+400])
