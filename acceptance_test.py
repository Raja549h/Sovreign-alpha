import os
import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://svrn-alpha-soverignalpha.hf.space"
PASSWORD = "sovereign2024"

session = requests.Session()

# 1. Get login page to extract CSRF token
r = session.get(BASE_URL + "/login")
soup = BeautifulSoup(r.text, 'html.parser')
# wait, the login page might not have a CSRF token input if it's custom. Let's just login
r = session.post(BASE_URL + "/login", data={"password": PASSWORD})
print("Login status:", r.status_code)

# 2. Get the /runs page to get CSRF token
r = session.get(BASE_URL + "/runs")
soup = BeautifulSoup(r.text, 'html.parser')
csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']
print("CSRF Token:", csrf_token)

# 3. Trigger run
headers = {
    'X-CSRFToken': csrf_token,
    'Content-Type': 'application/json'
}
run_resp = session.post(f"{BASE_URL}/api/runs/submit", json={"ticker": "HDFCBANK", "run_type": "ORGANIC_VERIFICATION"}, headers=headers)
print("Run trigger status:", run_resp.status_code)
print("Run response:", run_resp.text)
