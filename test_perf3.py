import sys, os, traceback
sys.path.insert(0, os.path.abspath('dashboard'))
from app import app
app.testing = True
import app as myapp
myapp.is_authenticated = lambda: True

with app.test_client() as client:
    client.set_cookie('localhost', 'session_token', 'bypass_token')
    resp = client.get('/performance')
    print('Status Code:', resp.status_code)
    
    if b'PERFORMANCE_ROUTE_ERROR' in resp.data or b'0</div>' in resp.data:
        print('Route rendered successfully. Here is snippet:')
        print(resp.data[:500])
        print('Total Predictions:', b'Total Predictions' in resp.data)
        
        with open('perf_output.html', 'wb') as f:
            f.write(resp.data)
