#!/usr/bin/env python3
"""
SOVEREIGN ALPHA — Institutional Intelligence Pipeline
=====================================================
Master orchestrator for the Sovereign Alpha system.

Pipeline:
1. Market Regime Engine classifies current regime
2. Data Layer fetches multi-source market intelligence
3. Analyst Agent generates institutional predictions
4. Risk Manager applies dynamic veto filtering
5. Cryptographic Auditor signs and chains approved predictions
6. Results persisted to prediction ledger and veto archive

Run with: python crew.py
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from config import BASE_DIR, LLM_API_KEY, logger
from engine.regime import MarketRegimeEngine
from engine.data_layer import DataLayer
from agents.analyst import AnalystAgent, InstitutionalPrediction
from agents.risk_manager import RiskManager
from agents.auditor import CryptographicAuditor, AuditCertificate


class SovereignAlphaPipeline:
    """
    Institutional-grade intelligence pipeline.
    Coordinates all engines and agents.
    """

    def __init__(self):
        self.regime_engine = None
        self.data_layer = None
        self.analyst = None
        self.risk_manager = None
        self.auditor = None
        self._initialize()

    def _initialize(self):
        print("\n" + "=" * 70)
        print("SOVEREIGN ALPHA — Institutional Intelligence Pipeline")
        print("=" * 70)

        if not LLM_API_KEY:
            print("WARNING: LLM_API_KEY not set — using rule-based analysis only")

        self.regime_engine = MarketRegimeEngine()
        logger.info("Market Regime Engine initialized")

        self.data_layer = DataLayer()
        logger.info("Data Layer initialized")

        self.analyst = AnalystAgent()
        logger.info("Analyst Agent initialized")

        self.risk_manager = RiskManager()
        logger.info("Risk Manager initialized")

        self.auditor = CryptographicAuditor()
        logger.info("Cryptographic Auditor initialized")

        print("\n[PASS] All systems initialized")
        print("=" * 70)

    def run(self, tickers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute full intelligence pipeline.
        Returns structured results.
        """
        results = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "regime": {},
            "predictions": [],
            "approved": [],
            "vetoed": [],
            "certificates": [],
            "summary": {}
        }

        print("\n[1/5] Classifying market regime...")
        regime = self.regime_engine.classify()
        results["regime"] = {
            "regime": regime.regime,
            "confidence": regime.confidence,
            "summary": regime.summary,
            "timestamp": regime.timestamp
        }
        print(f"      Regime: {regime.regime} (confidence: {regime.confidence:.1%})")
        print(f"      Summary: {regime.summary}")

        print("\n[2/5] Fetching market intelligence...")
        macro = self.data_layer.fetch_macro_snapshot()
        print(f"      VIX: {macro.vix} | 10Y: {macro.treasury_10y}% | DXY: {macro.dxy}")

        print("\n[3/5] Generating predictions...")
        predictions = self.analyst.run_full_analysis(tickers)
        print(f"      Generated {len(predictions)} predictions")

        print("\n[4/5] Applying risk governance...")
        approved_predictions = []
        vetoed_predictions = []
        audit_batch = []

        for pred in predictions:
            approval = self.risk_manager.evaluate(pred)

            if approval.approved:
                approved_predictions.append(pred)
                audit_batch.append((pred, approval.risk_checks))
            else:
                vetoed_predictions.append({
                    "ticker": pred.ticker,
                    "signal": pred.signal,
                    "confidence": pred.confidence,
                    "veto_reason": approval.reasoning,
                    "timestamp": approval.timestamp
                })

        print(f"      Approved: {len(approved_predictions)} | Vetoed: {len(vetoed_predictions)}")

        print("\n[5/5] Generating audit certificates...")
        certificates = self.auditor.audit_batch(audit_batch)
        print(f"      Generated {len(certificates)} certificates")

        results["predictions"] = [self._serialize_prediction(p) for p in predictions]
        results["approved"] = [self._serialize_prediction(p) for p in approved_predictions]
        results["vetoed"] = vetoed_predictions
        results["certificates"] = [self._serialize_certificate(c) for c in certificates]
        results["summary"] = self._build_summary(predictions, approved_predictions, vetoed_predictions, certificates, regime)

        return results

    def _serialize_prediction(self, pred: InstitutionalPrediction) -> Dict[str, Any]:
        """Convert prediction to serializable dict."""
        return {
            "prediction_id": pred.prediction_id,
            "ticker": pred.ticker,
            "signal": pred.signal,
            "confidence": pred.confidence,
            "market_regime": pred.market_regime,
            "thesis": pred.thesis,
            "risk_factors": pred.risk_factors,
            "entry_price": pred.entry_price,
            "target_price": pred.target_price,
            "stop_loss": pred.stop_loss,
            "risk_reward_ratio": pred.risk_reward_ratio,
            "expected_timeline_days": pred.expected_timeline_days,
            "timestamp": pred.timestamp
        }

    def _serialize_certificate(self, cert: AuditCertificate) -> Dict[str, Any]:
        """Convert certificate to serializable dict."""
        return {
            "certificate_id": cert.certificate_id,
            "prediction_id": cert.prediction_id,
            "ticker": cert.ticker,
            "commitment_hash": cert.commitment_hash,
            "merkle_root": cert.merkle_root,
            "timestamp": cert.timestamp,
            "verdict": cert.verdict,
            "chain_status": cert.chain_status
        }

    def _build_summary(self, all_preds, approved, vetoed, certs, regime) -> Dict[str, Any]:
        """Build pipeline summary."""
        buy_count = sum(1 for p in all_preds if p.signal == "BUY")
        sell_count = sum(1 for p in all_preds if p.signal == "SELL")
        hold_count = sum(1 for p in all_preds if p.signal == "HOLD")

        avg_conf = sum(p.confidence for p in all_preds) / len(all_preds) if all_preds else 0

        return {
            "total_predictions": len(all_preds),
            "approved": len(approved),
            "vetoed": len(vetoed),
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "hold_signals": hold_count,
            "avg_confidence": round(avg_conf, 3),
            "regime": regime.regime,
            "certificates_generated": len(certs),
            "audit_chain_integrity": self.auditor.merkle_chain.verify_chain_integrity()
        }

    def print_report(self, results: Dict[str, Any]):
        """Print institutional report to console."""
        s = results["summary"]
        r = results["regime"]

        print("\n" + "=" * 70)
        print("SOVEREIGN ALPHA — DAILY INTELLIGENCE REPORT")
        print("=" * 70)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Market Regime: {r['regime']} (confidence: {r['confidence']:.1%})")
        print(f"Regime Context: {r['summary']}")
        print("-" * 70)

        print(f"\nPredictions Generated: {s['total_predictions']}")
        print(f"  Approved: {s['approved']}")
        print(f"  Vetoed: {s['vetoed']}")
        print(f"  BUY signals: {s['buy_signals']}")
        print(f"  SELL signals: {s['sell_signals']}")
        print(f"  HOLD signals: {s['hold_signals']}")
        print(f"  Avg Confidence: {s['avg_confidence']:.0%}")
        print(f"  Audit Certificates: {s['certificates_generated']}")
        print(f"  Chain Integrity: {'VERIFIED' if s['audit_chain_integrity'] else 'PENDING'}")

        if results["approved"]:
            print("\nAPPROVED PREDICTIONS:")
            for p in results["approved"]:
                print(f"  [+] {p['ticker']} | {p['signal']} | Conf: {p['confidence']:.0%} | Entry: ${p['entry_price']} | Target: ${p['target_price']}")
                print(f"      {p['thesis'][:100]}...")

        if results["vetoed"]:
            print("\nVETOED PREDICTIONS:")
            for v in results["vetoed"]:
                print(f"  [-] {v['ticker']} | {v['signal']} | Conf: {v['confidence']:.0%}")
                print(f"      Reason: {v['veto_reason'][:80]}...")

        print("\n" + "=" * 70)
        print("END OF REPORT")
        print("=" * 70)


def main():
    """Main entry point."""
    pipeline = SovereignAlphaPipeline()

    tickers = None
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]

    results = pipeline.run(tickers)
    pipeline.print_report(results)

    results_file = BASE_DIR / "results" / f"pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(exist_ok=True)
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved: {results_file}")
    except Exception as e:
        print(f"\nWarning: Could not save results: {e}")

    try:
        from database import get_connection
        db_path = None
        conn = get_connection()
        c = conn.cursor()
        for p in results.get("approved", []):
            proof_hash = ""
            for cert in results.get("certificates", []):
                if cert.get("prediction_id") == p.get("prediction_id"):
                    proof_hash = cert.get("commitment_hash", "")
                    break
            
            c.execute("""
                INSERT INTO prediction_ledger 
                (prediction_id, timestamp, asset, sector, thesis, confidence_score, 
                 status, expected_timeline_days, proof_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                p.get("prediction_id"),
                p.get("timestamp"),
                p.get("ticker"),
                "Unknown",
                p.get("thesis"),
                p.get("confidence", 0.0),
                "cleared",
                p.get("expected_timeline_days", 30),
                proof_hash,
                datetime.utcnow().isoformat() + 'Z',
                datetime.utcnow().isoformat() + 'Z'
            ))
        conn.commit()
        conn.close()
        print(f"Persisted predictions to {db_path}")
    except Exception as e:
        print(f"Warning: Could not persist to billing DB: {e}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
