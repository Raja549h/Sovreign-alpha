#!/usr/bin/env python3
"""
Sovereign Alpha - Mistral AI Health Check
==========================================
Diagnostic script to verify the Mistral AI backend is fully operational.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent / ".env")

API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL = "mistral-large-latest"

def run_health_check():
    print("=" * 60)
    print("SOVEREIGN ALPHA - MISTRAL AI HEALTH CHECK")
    print("=" * 60)

    # ── Step 1: Verify API key is present ──
    if not API_KEY:
        print("\n[FAIL] MISTRAL_API_KEY is not set in the environment.")
        print("       Ensure your .env file contains: MISTRAL_API_KEY=<your_key>")
        return False

    print(f"\n[OK]   MISTRAL_API_KEY detected ({len(API_KEY)} chars)")
    print(f"[INFO] Model: {MODEL}")

    # ── Step 2: Initialize the Mistral client ──
    try:
        from mistralai.client import Mistral
        client = Mistral(api_key=API_KEY)
        print("[OK]   Mistral client initialized successfully")
    except ImportError:
        print("\n[FAIL] 'mistralai' package is not installed.")
        print("       Run: pip install mistralai")
        return False
    except Exception as e:
        print(f"\n[FAIL] Client initialization error: {e}")
        return False

    # ── Step 3: Execute health-check chat completion ──
    prompt = "System status check: Respond with 'ONLINE' if operational."
    print(f"\n[INFO] Sending health-check prompt to {MODEL}...")

    start = time.time()
    try:
        response = client.chat.complete(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a system health monitor. Respond concisely."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=50,
            temperature=0.0,
        )
        elapsed = time.time() - start
    except Exception as e:
        elapsed = time.time() - start
        err_str = str(e).lower()

        if "401" in err_str or "403" in err_str or "unauthorized" in err_str:
            print(f"\n[FAIL] Authentication error ({elapsed:.2f}s)")
            print("       Your MISTRAL_API_KEY is invalid or revoked.")
        elif "timeout" in err_str or "timed out" in err_str:
            print(f"\n[FAIL] Network timeout ({elapsed:.2f}s)")
            print("       Could not reach https://api.mistral.ai — check connectivity.")
        elif "404" in err_str or "not found" in err_str:
            print(f"\n[FAIL] Model not found ({elapsed:.2f}s)")
            print(f"       '{MODEL}' may not be available on your plan.")
        else:
            print(f"\n[FAIL] Unexpected error ({elapsed:.2f}s)")
            print(f"       {type(e).__name__}: {e}")
        return False

    # ── Step 4: Validate the response ──
    try:
        reply = response.choices[0].message.content.strip()
        usage = response.usage
    except (IndexError, AttributeError) as e:
        print(f"\n[FAIL] Malformed response object: {e}")
        return False

    print(f"\n[OK]   Response received in {elapsed:.2f}s")
    print(f"[OK]   Model reply: \"{reply}\"")
    print(f"[INFO] Tokens used — prompt: {usage.prompt_tokens}, "
          f"completion: {usage.completion_tokens}, total: {usage.total_tokens}")

    is_online = "online" in reply.lower()

    print("\n" + "=" * 60)
    if is_online:
        print("RESULT: [PASS] MISTRAL AI BACKEND IS FULLY OPERATIONAL")
    else:
        print("RESULT: [WARN] Response received but did not contain 'ONLINE'")
        print(f"         Raw reply: \"{reply}\"")
    print("=" * 60)

    return is_online


if __name__ == "__main__":
    success = run_health_check()
    sys.exit(0 if success else 1)
