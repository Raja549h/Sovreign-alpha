"""
MASTER DAILY — Sovereign Alpha Weekday Pipeline
=================================================
Runs every weekday at 08:45 IST.

Orchestrates:
1. Fetch live market data (yfinance, FRED, NSE India)
1b. Collect FII flow intelligence (flow regime, vulnerability)
2. Classify market regime
3. Run analyst predictions across watchlist
4. Apply risk governance (veto filtering)
5. Generate cryptographic audit certificates
6. Record predictions to immutable ledger
7. Archive vetoes with reasons
8. Update Merkle chain
9. Log results
10. Send email digest (if configured)

All errors handled gracefully — partial failures do not stop the pipeline.
"""

import os
import sys
import json
import traceback
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ['LOG_LEVEL'] = 'WARNING'

LOGS_DIR = BASE_DIR / "automation" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / f"master_daily_{datetime.now().strftime('%Y-%m-%d')}.log"


def log(msg: str):
    """Write to both console and log file."""
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass


def run_pipeline():
    """Execute the full daily pipeline."""
    log("=" * 70)
    log("MASTER DAILY — Starting weekday pipeline")
    log("=" * 70)

    results = {
        "date": datetime.utcnow().strftime('%Y-%m-%d'),
        "steps": {},
        "errors": [],
        "predictions": [],
        "approved": [],
        "vetoed": [],
        "summary": {}
    }

    # Step 1: Fetch market data
    log("[1/8] Fetching market data...")
    try:
        from engine.data_layer import DataLayer
        dl = DataLayer()
        macro = dl.fetch_macro_snapshot()
        india = dl.fetch_nse_india()
        commodities = dl.fetch_commodities()
        results["steps"]["market_data"] = "OK"
        log(f"      VIX: {macro.vix} | 10Y: {macro.treasury_10y}% | DXY: {macro.dxy}")
        log(f"      Gold: ${macro.gold} | Oil: ${macro.oil_wti}")
    except Exception as e:
        results["steps"]["market_data"] = f"FAIL: {str(e)}"
        results["errors"].append(f"market_data: {str(e)}")
        log(f"      ERROR: {e}")

    # Step 1b: Collect FII flow data
    log("[1b/8] Collecting FII flow intelligence...")
    try:
        from research.macro.fii_flow import build_flow_intelligence_report
        fii_report = build_flow_intelligence_report()
        results["steps"]["fii_flow"] = fii_report.get("data_quality", "NO_DATA")
        log(f"      Regime: {fii_report.get('flow_regime', {}).get('label', 'N/A')} | Net: {fii_report.get('monthly', {}).get('monthly_net_cr')}")
    except Exception as e:
        results["steps"]["fii_flow"] = f"FAIL: {str(e)}"
        results["errors"].append(f"fii_flow: {str(e)}")
        log(f"      ERROR: {e}")

    # Step 2: Classify regime
    log("[2/8] Classifying market regime...")
    try:
        from engine.regime import MarketRegimeEngine
        regime_engine = MarketRegimeEngine()
        regime = regime_engine.classify()
        results["steps"]["regime"] = regime.regime
        log(f"      Regime: {regime.regime} (confidence: {regime.confidence:.1%})")
        log(f"      Summary: {regime.summary}")
    except Exception as e:
        results["steps"]["regime"] = f"FAIL: {str(e)}"
        results["errors"].append(f"regime: {str(e)}")
        log(f"      ERROR: {e}")
        regime = None

    # Step 3: Run analyst predictions
    log("[3/8] Running analyst predictions...")
    predictions = []
    try:
        from agents.analyst import AnalystAgent
        analyst = AnalystAgent()
        predictions = analyst.run_full_analysis()
        results["steps"]["predictions"] = f"{len(predictions)} generated"
        log(f"      Generated {len(predictions)} predictions")
    except Exception as e:
        results["steps"]["predictions"] = f"FAIL: {str(e)}"
        results["errors"].append(f"predictions: {str(e)}")
        log(f"      ERROR: {e}")

    # Step 4: Apply risk governance
    log("[4/8] Applying risk governance...")
    approved = []
    vetoed = []
    audit_batch = []
    try:
        from agents.risk_manager import RiskManager
        rm = RiskManager()
        for pred in predictions:
            approval = rm.evaluate(pred)
            if approval.approved:
                approved.append(pred)
                audit_batch.append((pred, approval.risk_checks))
            else:
                vetoed.append({
                    "ticker": pred.ticker,
                    "signal": pred.signal,
                    "confidence": pred.confidence,
                    "reason": approval.reasoning,
                    "timestamp": approval.timestamp
                })
        results["steps"]["risk_governance"] = f"{len(approved)} approved, {len(vetoed)} vetoed"
        log(f"      Approved: {len(approved)} | Vetoed: {len(vetoed)}")
    except Exception as e:
        results["steps"]["risk_governance"] = f"FAIL: {str(e)}"
        results["errors"].append(f"risk_governance: {str(e)}")
        log(f"      ERROR: {e}")

    # Step 5: Generate audit certificates
    log("[5/8] Generating audit certificates...")
    certificates = []
    try:
        from agents.auditor import CryptographicAuditor
        auditor = CryptographicAuditor()
        certificates = auditor.audit_batch(audit_batch)
        results["steps"]["audit"] = f"{len(certificates)} certificates"
        log(f"      Generated {len(certificates)} certificates")
    except Exception as e:
        results["steps"]["audit"] = f"FAIL: {str(e)}"
        results["errors"].append(f"audit: {str(e)}")
        log(f"      ERROR: {e}")

    # Step 6: Record to prediction ledger
    log("[6/8] Recording to prediction ledger...")
    try:
        from dashboard.app import FUND_DATA_DB, save_prediction
        for pred in predictions:
            status = 'cleared' if any(a.ticker == pred.ticker for a in approved) else 'risk-rejected'
            pred_data = {
                'prediction_id': pred.prediction_id,
                'timestamp': pred.timestamp,
                'asset': pred.ticker,
                'sector': pred.institutional_positioning.get('sector', ''),
                'thesis': pred.thesis,
                'confidence_score': pred.confidence,
                'status': status,
                'expected_timeline_days': pred.expected_timeline_days,
                'proof_hash': certificates[0].commitment_hash if certificates else ''
            }
            save_prediction(pred_data)

        results["steps"]["ledger"] = f"{len(predictions)} recorded"
        log(f"      Recorded {len(predictions)} predictions to ledger (vetoes already saved by Risk Manager)")
    except Exception as e:
        results["steps"]["ledger"] = f"FAIL: {str(e)}"
        results["errors"].append(f"ledger: {str(e)}")
        log(f"      ERROR: {e}")

    # Step 7: Git sync (skip on GitHub Actions)
    log("[7/8] Syncing data...")
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        log("      Skipped (running on GitHub Actions)")
        results["steps"]["git_sync"] = "SKIPPED"
    else:
        try:
            import subprocess
            subprocess.run(
                ['git', 'add', 'data/regime/', 'engine/', 'agents/', 'results/'],
                cwd=str(BASE_DIR),
                capture_output=True,
                timeout=30
            )
            subprocess.run(
                ['git', 'commit', '-m', f'Daily pipeline {datetime.utcnow().strftime("%Y-%m-%d")} automated'],
                cwd=str(BASE_DIR),
                capture_output=True,
                timeout=30
            )
            results["steps"]["git_sync"] = "OK"
            log("      Git sync complete")
        except Exception as e:
            results["steps"]["git_sync"] = f"FAIL: {str(e)}"
            results["errors"].append(f"git_sync: {str(e)}")
            log(f"      ERROR: {e}")

    # Step 8: Email digest
    log("[8/8] Sending email digest...")
    try:
        subprocess_result = __import__('subprocess').run(
            [sys.executable, str(BASE_DIR / "automation" / "email_digest.py")],
            capture_output=True,
            text=True,
            timeout=60
        )
        if subprocess_result.returncode == 0:
            results["steps"]["email"] = "OK"
            log("      Email digest sent")
        else:
            results["steps"]["email"] = f"FAIL: {subprocess_result.stderr[:100]}"
            log(f"      ERROR: {subprocess_result.stderr[:100]}")
    except Exception as e:
        results["steps"]["email"] = f"FAIL: {str(e)}"
        results["errors"].append(f"email: {str(e)}")
        log(f"      ERROR: {e}")

    # Summary
    results["summary"] = {
        "total_predictions": len(predictions),
        "approved": len(approved),
        "vetoed": len(vetoed),
        "certificates": len(certificates),
        "errors": len(results["errors"])
    }

    log("\n" + "=" * 70)
    log(f"PIPELINE COMPLETE: {len(predictions)} predictions | {len(approved)} approved | {len(vetoed)} vetoed | {len(results['errors'])} errors")
    log("=" * 70)

    # Save results
    results_file = BASE_DIR / "results" / f"master_daily_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        log(f"Results saved: {results_file}")
    except:
        pass

    return results


if __name__ == '__main__':
    try:
        run_pipeline()
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        log(traceback.format_exc())
        sys.exit(1)
