"""
Step 4: Autopsy Pipeline Runner
Orchestrates the full nightly pipeline: Ingest -> Match -> Report.
Uses subprocess with error propagation -- never swallows failures.
"""

import subprocess
import sys
from datetime import datetime


SCRIPTS = [
    ("1. Ingesting NSE Bulk Deals",    "scripts/ingest_bulk_deals.py"),
    ("2. Matching against Veto Archive", "scripts/bulk_deal_matcher.py"),
    ("3. Generating Autopsy Reports",   "scripts/autopsy_report_generator.py"),
]


def run_nightly():
    print("=" * 60)
    print("  SOVEREIGN ALPHA — NIGHTLY AUTOPSY PIPELINE")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("=" * 60)
    print()

    for label, script in SCRIPTS:
        print(f"{'-' * 60}")
        print(f"  {label}")
        print(f"{'-' * 60}")
        result = subprocess.run(
            [sys.executable, script],
            capture_output=False,  # let output flow to terminal
        )
        if result.returncode != 0:
            print(f"\n  WARNING: PIPELINE HALTED: {script} exited with code {result.returncode}")
            sys.exit(result.returncode)
        print()

    print("=" * 60)
    print("  PIPELINE COMPLETE")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("  Check reports/ directory for your drafts to review.")
    print("=" * 60)


if __name__ == '__main__':
    run_nightly()
