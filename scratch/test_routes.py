import os, sys
import requests

routes = [
    '/system-health',
    '/evidence',
    '/audit',
    '/calibration',
    '/predictions',
    '/failure-ledger',
    '/veto-archive',
    '/proofs',
    '/performance',
    '/research',
    '/macro-health',
    '/portfolio',
    '/edge',
    '/challenge',
    '/research-quality'
]

results = []
for route in routes:
    try:
        r = requests.get(f'http://127.0.0.1:5000{route}', timeout=5)
        status = r.status_code
        content = r.text
        if status == 500:
            res = "BROKEN (500)"
        elif "No data" in content or "empty-state" in content or "0 rows" in content or len(content) < 1000:
            res = f"POSSIBLY EMPTY (Len: {len(content)})"
        else:
            res = f"OK (Len: {len(content)})"
    except Exception as e:
        res = f"ERROR: {e}"
    results.append(f"{route}: {res}")
    print(f"{route}: {res}")
