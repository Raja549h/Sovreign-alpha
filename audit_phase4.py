import os
import requests
import time
import json

BASE_URL = "https://svrn-alpha-soverignalpha.hf.space"
PASSWORD = "sovereign2024"

session = requests.Session()
resp = session.post(f"{BASE_URL}/login", data={"password": PASSWORD})
print("Login:", resp.status_code)

print("Triggering pipeline...")
run_resp = session.post(f"{BASE_URL}/api/run", json={"ticker": "MSFT"})
print("Status:", run_resp.status_code)
try:
    print("Response:", run_resp.json())
except:
    print("Response text:", run_resp.text[:500])

