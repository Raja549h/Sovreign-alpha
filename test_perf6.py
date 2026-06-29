import sys, os
sys.path.insert(0, os.path.abspath('dashboard'))
from app import app
import app as myapp
myapp.is_authenticated = lambda: True
client = app.test_client()
client.set_cookie('session_token', 'bypass')
print(client.get('/performance').data.decode('utf-8'))
