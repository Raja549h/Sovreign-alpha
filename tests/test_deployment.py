import requests
import sys

BASE_URL = "http://127.0.0.1:7860/api/v1"

def run_tests():
    print("Starting Deployment API Tests...")
    all_passed = True

    try:
        # 1. Test Score API
        print(f"Testing {BASE_URL}/score/RELIANCE")
        resp = requests.get(f"{BASE_URL}/score/RELIANCE")
        if resp.status_code == 200:
            data = resp.json()
            if 'overall_score' in data and 'fundamental_score' in data:
                print(" [PASS] Score API returned expected data.")
            else:
                print(f" [FAIL] Score API missing keys. Data: {data}")
                all_passed = False
        else:
            print(f" [FAIL] Score API returned status {resp.status_code}. Response: {resp.text}")
            if resp.status_code != 404:
                all_passed = False

        # 2. Test Divergences API
        print(f"Testing {BASE_URL}/divergences")
        resp = requests.get(f"{BASE_URL}/divergences")
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                print(f" [PASS] Divergences API returned list of length {len(data)}.")
            else:
                print(f" [FAIL] Divergences API did not return a list. Data: {data}")
                all_passed = False
        else:
            print(f" [FAIL] Divergences API returned status {resp.status_code}. Response: {resp.text}")
            all_passed = False

        # 3. Test Validation Ledger API
        print(f"Testing {BASE_URL}/validation-ledger")
        resp = requests.get(f"{BASE_URL}/validation-ledger")
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                print(f" [PASS] Validation Ledger API returned list of length {len(data)}.")
            else:
                print(f" [FAIL] Validation Ledger API did not return a list. Data: {data}")
                all_passed = False
        else:
            print(f" [FAIL] Validation Ledger API returned status {resp.status_code}")
            all_passed = False

    except Exception as e:
        print(f" [FAIL] Exception during tests: {e}")
        all_passed = False

    if all_passed:
        print("\nALL API TESTS PASSED")
        sys.exit(0)
    else:
        print("\nAPI TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
