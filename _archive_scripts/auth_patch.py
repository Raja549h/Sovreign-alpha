import re

with open('verify_live_deployment_automated.py', 'r') as f:
    content = f.read()

# Replace requests.get with session.get
task_b_replacement = '''def task_b_ui_walkthrough():
    print_header("Task B - UI Route & Content Walkthrough (Authenticated)")
    failed = False
    
    session = requests.Session()
    login_url = f"{LIVE_URL}/login"
    print(f"Logging into {login_url}...")
    try:
        resp = session.post(login_url, data={"password": "sovereign2024"}, timeout=10)
        if "session_token" not in session.cookies:
            print("[!] VIOLATION: Failed to authenticate. No session cookie received.")
            sys.exit(1)
        else:
            print("[PASS] Successfully logged in.")
    except Exception as e:
        print(f"[FAIL] Login Request failed: {e}")
        sys.exit(1)
        
    for route in ROUTES_TO_CHECK:
        url = f"{LIVE_URL}{route}"
        print(f"Checking {url} ...")
        try:
            resp = session.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"  [!] VIOLATION: Expected 200, got {resp.status_code}")
                failed = True
                continue
                
            html = resp.text.lower()
            
            found_forbidden = []
            for forbidden in FORBIDDEN_UI_STRINGS:
                if forbidden in html:
                    found_forbidden.append(forbidden)
                    
            if found_forbidden:
                print(f"  [!] VIOLATION: Forbidden strings found: {', '.join(found_forbidden)}")
                failed = True
                
            has_ticker = False
            for ticker in INDIAN_TICKERS:
                if ticker.lower() in html:
                    has_ticker = True
                    break
                    
            if not has_ticker:
                print(f"  [!] VIOLATION: No Indian tickers found on this route")
                failed = True
                
            if not failed:
                print("  [PASS] Route clean and populated.")
                
        except Exception as e:
            print(f"  [FAIL] Request failed: {e}")
            failed = True
            
    if failed:
        print("\\n[FAIL] Task B: UI Walkthrough failed.")
        sys.exit(1)
    else:
        print("\\n[PASS] Task B: All UI routes clean and active.")
'''

content = re.sub(r'def task_b_ui_walkthrough\(\):.*?def task_c', task_b_replacement + '\ndef task_c', content, flags=re.DOTALL)

with open('verify_live_deployment_automated.py', 'w') as f:
    f.write(content)
print('Updated script for login auth')
