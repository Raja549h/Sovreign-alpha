import os
import requests
import time
import json
import uuid

BASE_URL = "https://svrn-alpha-soverignalpha.hf.space"
PASSWORD = "sovereign2024"

# Phase 1: Routes
ROUTES = [
    ("/", "GET"),
    ("/decisions", "GET"),
    ("/predictions", "GET"),
    ("/veto-archive", "GET"),
    ("/proofs", "GET"),
    ("/performance", "GET"),
    ("/live_market", "GET"),
    ("/upload", "GET"),
    ("/run", "GET"),
    ("/health", "GET"),
    ("/autopsy", "GET"),
    ("/challenge", "GET"),
    ("/edge-discovery", "GET"),
    ("/research-quality", "GET"),
    ("/evidence", "GET"),
    ("/system-health", "GET"),
    ("/failure-ledger", "GET"),
    ("/calibration", "GET"),
    ("/audit", "GET"),
    ("/edge", "GET"),
    ("/research", "GET"),
    ("/portfolio", "GET"),
    ("/watchlist", "GET"),
    ("/macro", "GET"),
    ("/runs", "GET"),
]

API_ROUTES = [
    ("/api/runs", "GET"),
    ("/api/track_record", "GET"),
    ("/api/system-health", "GET"),
    ("/api/evidence/timeline", "GET"),
    ("/api/evidence/memos", "GET"),
    ("/api/evidence/calibration-dashboard", "GET"),
    ("/api/evidence/institutional-credibility", "GET"),
    ("/api/institutional-credibility", "GET"),
    ("/api/shadow-portfolio", "GET"),
]

session = requests.Session()

def login():
    print("Logging in...")
    resp = session.post(f"{BASE_URL}/login", data={"password": PASSWORD})
    print("Login status:", resp.status_code)
    
def test_routes():
    print("Testing routes...")
    results = []
    for route, method in ROUTES + API_ROUTES:
        start = time.time()
        try:
            if method == "GET":
                r = session.get(f"{BASE_URL}{route}", timeout=10)
            status = r.status_code
            text_len = len(r.text)
        except Exception as e:
            status = str(e)
            text_len = 0
        latency = round(time.time() - start, 3)
        print(f"{method} {route} - {status} ({latency}s)")
        results.append({
            "route": route,
            "status": status,
            "latency": latency,
            "size": text_len
        })
    return results

if __name__ == "__main__":
    login()
    res = test_routes()
    with open("audit_results.json", "w") as f:
        json.dump(res, f, indent=2)
