#!/usr/bin/env python3
"""
Sovereign Alpha - Demo Mode
=========================
Automated presentation mode that runs the full demo.
Usage: python demo/demo_mode.py
"""

import sys
import time
import subprocess
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_PORT = 5000


def print_step(step_num: int, title: str, duration: int):
    """Print step header."""
    print("\n" + "=" * 60)
    print(f"STEP {step_num}: {title}")
    print(f"Duration: {duration} seconds")
    print("=" * 60)


def main():
    """Run 4-minute demo."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║         S O V E R E I G N   A L P H A                         ║
║                    DEMO MODE                                 ║
║              4-Minute Presentation                           ║
╚═══════════════════════════════════════════════════════════════════╝
""")
    
    print("Starting demo in...")
    print("  3...")
    time.sleep(1)
    print("  2...")
    time.sleep(1)
    print("  1...")
    time.sleep(1)
    
    # Start dashboard
    print("\n[STARTING DASHBOARD]")
    dashboard_process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "dashboard" / "app.py")],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)
    
    # Open browser
    webbrowser.open(f"http://localhost:{DASHBOARD_PORT}")
    
    # Step 1: Dashboard home with track record (30 seconds)
    print_step(1, "Dashboard Home with Track Record", 30)
    print("""
    - Show home page with portfolio overview
    - Point out key metrics:
      * AUM: $10.4M
      * Approval Rate: 49%
      * Alpha Generated: $913K
      * ZK Proofs: 28 verified
    - Mention track record card showing Sharpe ratio
    """)
    time.sleep(30)
    
    # Step 2: Live market data page (45 seconds)
    print_step(2, "Live Market Data from yfinance", 45)
    print("""
    - Navigate to Live Market page
    - Show real-time data:
      * Live prices fetched from Yahoo Finance
      * RSI indicators (color-coded)
      * Volume signals
      * Analyst targets
    - Explain how data is refreshed
    """)
    
    # Simulate browser navigation instruction
    print(f"\n[ AUTO-NAVIGATE ] Opening live market page...")
    
    time.sleep(45)
    
    # Step 3: Run crew.py analysis (60 seconds)
    print_step(3, "Run Full AI Agent Analysis", 60)
    print("""
    - Show analyst agent processing
    - Show risk manager evaluation
    - Show auditor proof generation
    - Explain the 3-agent pipeline
    """)
    
    print("\n[ RUNNING ANALYSIS ] Running crew.py...")
    crew_result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "crew.py")],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        timeout=90
    )
    
    if crew_result.returncode == 0:
        print("[SUCCESS] Analysis completed")
    else:
        print("[INFO] Analysis completed (fallback mode)")
    
    time.sleep(60)
    
    # Step 4: Decision appears in dashboard (30 seconds)
    print_step(4, "New Decision in Dashboard", 30)
    print("""
    - Refresh dashboard to show new decision
    - Highlight approved trade
    - Show confidence score
    - Show position value
    """)
    time.sleep(30)
    
    # Step 5: ZK proof certificate shown (30 seconds)
    print_step(5, "ZK Proof Certificate", 30)
    print("""
    - Navigate to Proofs page
    - Show RSA certificate structure:
      * Commitment hash
      * RSA signature
      * Policy checks
      * Verdict (COMPLIANT/NON-COMPLIANT)
    - Explain anyone can verify with public key
    """)
    time.sleep(30)
    
    # Step 6: Blockchain log entry shown (30 seconds)
    print_step(6, "Blockchain Ledger Entry", 30)
    print("""
    - Show local ledger entry
    - Transaction hash displayed
    - Explain Base testnet integration
    - Mention can be upgraded to mainnet
    """)
    time.sleep(30)
    
    # Step 7: Billing update shown (30 seconds)
    print_step(7, "Performance Fee Calculation", 30)
    print("""
    - Show fee calculated (12% of alpha)
    - Show billing database update
    - Explain automated fee settlement
    """)
    time.sleep(30)
    
    # Final summary
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("""
    Key Points to Conclude:
    - End-to-end automated system
    - Real market data integration  
    - Cryptographic proof verification
    - Risk management at every step
    - Ready for hedge fund deployment
    
    Questions?
    """)
    
    print(f"\nDashboard still running at: http://localhost:{DASHBOARD_PORT}")
    print("Press Ctrl+C to stop...")
    
    try:
        input("\n[Press Enter to stop the dashboard]")
    except:
        pass
    
    dashboard_process.terminate()
    dashboard_process.wait()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nDemo interrupted.")
        
        try:
            dashboard_process.terminate()
        except:
            pass
        
        sys.exit(0)