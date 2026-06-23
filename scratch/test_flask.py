import os, sys, traceback
sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv()
from dashboard.app import app, performance

app.config['TESTING'] = True

try:
    with app.test_request_context('/performance'):
        # Just call the function directly to see if it throws an exception internally
        res = performance()
        print("Performance returned.")
except Exception as e:
    traceback.print_exc()
