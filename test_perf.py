import sys; sys.path.insert(0, '.')
from dashboard.app import app
client = app.test_client()
with app.app_context():
    response = client.get('/performance')
    print("STATUS:", response.status_code)
