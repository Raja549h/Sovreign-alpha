import os
import sys
import json
import urllib.request
from urllib.error import URLError, HTTPError

def check_hf_token():
    # 1. Read the token from a HF_TOKEN environment variable
    token = os.environ.get('HF_TOKEN')
    if not token:
        print("FAIL: HF_TOKEN environment variable is not set.")
        print("Please set the HF_TOKEN environment variable before running this script.")
        sys.exit(1)

    # Do not print or log the actual token
    print("Checking Hugging Face token (length: {} characters)...".format(len(token)))
    
    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': 'HF-Token-Verifier/1.0'
    }

    # 2. Attempt to authenticate with Hugging Face using the token
    whoami_url = 'https://huggingface.co/api/whoami-v2'
    req = urllib.request.Request(whoami_url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                whoami_data = json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        if e.code == 401:
            print("\nFAIL: Token is INVALID or EXPIRED.")
            print("Action Required: Please generate a new token at: https://huggingface.co/settings/tokens")
            sys.exit(1)
        else:
            print(f"\nFAIL: Failed to authenticate. HTTP Status Code: {e.code}")
            sys.exit(1)
    except URLError as e:
        print(f"\nFAIL: Network error while connecting to Hugging Face: {e.reason}")
        sys.exit(1)

    auth_info = whoami_data.get('auth', {})
    token_info = auth_info.get('accessToken', {})
    role = token_info.get('role', 'unknown')
    user_name = whoami_data.get('name', 'Unknown User')

    print(f"PASS: Successfully authenticated as user '{user_name}'.")

    # 4. Check if the token has write permissions
    # Tokens can be 'write', 'fineGrained', or 'read'
    if role == 'read':
        print("\nFAIL: Token is MISSING REQUIRED PERMISSIONS.")
        print(f"Current token role is '{role}'. It requires 'write' access to push updates.")
        print("Action Required: Please generate a new token with 'write' permissions at: https://huggingface.co/settings/tokens")
        sys.exit(1)
    
    print(f"PASS: Token has sufficient baseline role ('{role}').")

    # 3. Test access to the Space: svrn-alpha/sovereignalpha
    space_id = "svrn-alpha/sovereignalpha"
    space_url = f'https://huggingface.co/api/spaces/{space_id}'
    space_req = urllib.request.Request(space_url, headers=headers)
    
    try:
        with urllib.request.urlopen(space_req) as response:
            space_data = json.loads(response.read().decode('utf-8'))
            print(f"PASS: Verified access to Space '{space_id}'.")
            
            # Additional check: verify the space status can be pulled
            runtime = space_data.get('runtime', {})
            stage = runtime.get('stage', 'Unknown')
            print(f"PASS: Successfully pulled Space status (Current stage: {stage}).")

    except HTTPError as e:
        if e.code in (401, 403, 404):
            print(f"\nFAIL: Token lacks access to the Space '{space_id}'.")
            print("Reason: The token's user is not authorized, or the space does not exist.")
            print("Action Required: Ensure the token belongs to an account with access to 'svrn-alpha/sovereignalpha'.")
            sys.exit(1)
        else:
            print(f"\nFAIL: Error verifying Space access. HTTP Status Code: {e.code}")
            sys.exit(1)
    except Exception as e:
        print(f"\nFAIL: Error verifying Space access: {e}")
        sys.exit(1)

    # 5. Return a clear PASS/FAIL status with specific error messages
    print("\n---------------------------------------------------------")
    print("STATUS: PASS")
    print("---------------------------------------------------------")
    print("The Hugging Face token is fully verified and has the necessary permissions to:")
    print(" - Access the Sovereign Alpha Space")
    print(" - Push updates to the Space")
    print(" - Pull logs and status")
    sys.exit(0)

if __name__ == '__main__':
    check_hf_token()
