from dashboard.app import app  
app.testing = True  
with app.test_client() as client:  
    resp = client.get('/performance')  
    print('Status:', resp.status_code)  
