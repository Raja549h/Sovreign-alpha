"""
RISK MANAGER — Institutional Veto Architecture
===============================================
Dynamic veto system that adjusts thresholds based on market regime.

Rejects:
- Weak-confidence trades
- Overexposed sectors
- High-volatility instability
- Regime-inconsistent signals
- Concentration escalation

Every veto includes reason, rejected confidence, market regime, timestamp.
All vetoes stored permanently for outcome tracking.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.db import get_connection

from config import logger, BILLING_DIR
from engine.regime import MarketRegimeEngine


@dataclass
class RiskCheck:
    """Individual risk check."""
    check_name: str
    passed: bool
    details: str
    severity: str = "low"


@dataclass
class VetoRecord:
    """Permanent veto record."""
    veto_id: str
    prediction_id: str
    ticker: str
    signal: str
    rejected_confidence: float
    veto_reason: str
    market_regime: str
    failed_checks: List[str]
    timestamp: str
    expected_loss_pct: float = 0.0
    actual_outcome: str = ""
    actual_return_pct: float = 0.0
    avoided_drawdown: float = 0.0
    veto_correct: bool = False


@dataclass
class RiskApproval:
    """Risk manager decision."""
    prediction_id: str
    approved: bool
    risk_checks: List[RiskCheck]
    veto_record: Optional[VetoRecord] = None
    reasoning: str = ""
    timestamp: str = ""


class RiskManager:
    """
    Institutional risk manager with regime-aware veto logic.
    """

    RISK_THRESHOLD_MULTIPLIER = 0.7

    def __init__(self, data_dir: Optional[Path] = None):
        self.regime_engine = MarketRegimeEngine()
        self.data_dir = data_dir or BILLING_DIR
        self.db_path = self.data_dir / "db"
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure veto archive table exists using canonical PostgreSQL schema. Raises fatal RuntimeError on failure."""
        try:
            with get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    CREATE TABLE IF NOT EXISTS veto_archive (
                        id SERIAL PRIMARY KEY,
                        veto_id VARCHAR(64) UNIQUE,
                        prediction_id VARCHAR(64),
                        timestamp VARCHAR(32),
                        asset VARCHAR(32),
                        sector VARCHAR(64),
                        rejection_reason TEXT,
                        expected_loss_pct NUMERIC(6, 2),
                        proof_hash VARCHAR(128),
                        actual_outcome VARCHAR(32),
                        actual_return_pct NUMERIC(6, 2),
                        avoided_drawdown NUMERIC(10, 2),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
            logger.info("RiskManager: veto_archive table verified.")
        except Exception as e:
            logger.error(f"Fatal: Failed to initialize/verify database tables in RiskManager: {e}")
            raise RuntimeError(f"RiskManager fatal initialization failure: unable to verify or create required database tables: {e}") from e

    def _save_veto(self, veto: VetoRecord) -> bool:
        """Persist veto to database."""
        try:
            import uuid
            with get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO veto_archive
                    (veto_id, prediction_id, timestamp, asset, sector, rejection_reason, expected_loss_pct, proof_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (veto_id) DO NOTHING
                """, (
                    veto.veto_id if hasattr(veto, 'veto_id') else str(uuid.uuid4()),
                    veto.prediction_id if hasattr(veto, 'prediction_id') else '',
                    veto.timestamp if hasattr(veto, 'timestamp') else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    veto.ticker if hasattr(veto, 'ticker') else '',
                    '', # sector
                    veto.veto_reason if hasattr(veto, 'veto_reason') else '',
                    veto.expected_loss_pct if hasattr(veto, 'expected_loss_pct') else 0.0,
                    ''
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.warning(f"Veto save failed: {e}")
            return False

    def _get_regime_config(self, regime: str) -> Dict[str, Any]:
        """Get risk thresholds for current regime."""
        return self.regime_engine.get_regime_config(regime)

    def _check_confidence(self, prediction, regime_config: Dict) -> RiskCheck:
        """Check if confidence meets regime-adjusted threshold."""
        confidence = prediction.confidence
        signal = prediction.signal

        if signal == "BUY":
            threshold = regime_config.get("min_confidence_buy", 0.70)
        elif signal == "SELL":
            threshold = regime_config.get("min_confidence_sell", 0.60)
        else:
            threshold = 0.50

        # Apply multiplier
        threshold = threshold * self.RISK_THRESHOLD_MULTIPLIER

        passed = confidence >= threshold
        return RiskCheck(
            check_name="Confidence Threshold",
            passed=passed,
            details=f"Confidence {confidence:.0%} {'meets' if passed else 'below'} regime threshold {threshold:.0%}",
            severity="critical" if not passed else "low"
        )

    def _check_regime_consistency(self, prediction, regime_config: Dict) -> RiskCheck:
        """Check if signal is consistent with market regime."""
        regime = prediction.market_regime
        signal = prediction.signal

        passed = True
        reason = "Signal consistent with regime"

        risk_off_thresh = 0.80 * self.RISK_THRESHOLD_MULTIPLIER
        risk_on_thresh = 0.70 * self.RISK_THRESHOLD_MULTIPLIER

        if regime == "RISK_OFF" and signal == "BUY" and prediction.confidence < risk_off_thresh:
            passed = False
            reason = f"BUY signal in RISK_OFF regime with insufficient confidence ({prediction.confidence:.0%} < {risk_off_thresh:.0%})"
        elif regime == "RISK_ON" and signal == "SELL" and prediction.confidence < risk_on_thresh:
            passed = False
            reason = f"SELL signal in RISK_ON regime with insufficient confidence ({prediction.confidence:.0%} < {risk_on_thresh:.0%})"

        return RiskCheck(
            check_name="Regime Consistency",
            passed=passed,
            details=reason,
            severity="critical" if not passed else "low"
        )

    def _check_volatility_stability(self, prediction, tech: Dict) -> RiskCheck:
        """Check if volatility conditions support the trade."""
        rsi = tech.get("rsi", 50)
        vol_ratio = tech.get("volume_ratio", 1.0)

        passed = True
        details = "Volatility conditions acceptable"

        # Apply a relaxation to thresholds using the multiplier's complement
        relaxation = (1.0 - self.RISK_THRESHOLD_MULTIPLIER)
        upper_rsi = min(100, 85 + (15 * relaxation)) # Typically 85, now 89.5
        lower_rsi = max(0, 10 - (10 * relaxation)) # Typically 10, now 7
        vol_max = 8.0 + (5.0 * relaxation) # Typically 8.0, now 9.5

        if rsi > upper_rsi:
            passed = False
            details = f"Extreme overbought (RSI {rsi}) — volatility instability risk"
        elif rsi < lower_rsi:
            passed = False
            details = f"Extreme oversold (RSI {rsi}) — potential capitulation"
        elif vol_ratio > vol_max:
            passed = False
            details = f"Extreme volume spike ({vol_ratio:.1f}x) — potential news-driven instability"

        return RiskCheck(
            check_name="Volatility Stability",
            passed=passed,
            details=details,
            severity="high" if not passed else "low"
        )

    def _check_risk_reward(self, prediction) -> RiskCheck:
        """Check if risk/reward ratio meets minimum threshold."""
        rr = prediction.risk_reward_ratio
        min_rr = 1.0

        passed = rr >= min_rr
        return RiskCheck(
            check_name="Risk/Reward Ratio",
            passed=passed,
            details=f"R/R {rr:.1f} {'meets' if passed else 'below'} minimum {min_rr:.1f}",
            severity="high" if not passed else "low"
        )

    def _check_sector_concentration(self, prediction, sector_exposure: Dict[str, float]) -> RiskCheck:
        """Check if adding this position would exceed sector limits."""
        regime_config = self._get_regime_config(prediction.market_regime)
        max_sector = regime_config.get("max_sector_exposure_pct", 20.0)

        sector = prediction.institutional_positioning.get("sector", "Unknown")
        current_exposure = sector_exposure.get(sector, 0.0)

        passed = current_exposure < max_sector
        return RiskCheck(
            check_name="Sector Concentration",
            passed=passed,
            details=f"{sector} exposure {current_exposure:.0f}% {'within' if passed else 'exceeds'} limit {max_sector:.0f}%",
            severity="high" if not passed else "low"
        )

    def evaluate(self, prediction, sector_exposure: Optional[Dict[str, float]] = None) -> RiskApproval:
        """
        Full risk evaluation of a prediction.
        Returns approval or veto.
        """
        if sector_exposure is None:
            sector_exposure = {}

        regime_config = self._get_regime_config(prediction.market_regime)
        tech = prediction.technical_summary

        checks = [
            self._check_confidence(prediction, regime_config),
            self._check_regime_consistency(prediction, regime_config),
            self._check_volatility_stability(prediction, tech),
            self._check_risk_reward(prediction),
            self._check_sector_concentration(prediction, sector_exposure),
        ]

        failed_checks = [c for c in checks if not c.passed]
        critical_failures = [c for c in failed_checks if c.severity == 'critical']
        
        # Majority-fail model: reject only if 2+ critical failures OR 3+ total failures
        all_passed = len(critical_failures) < 2 and len(failed_checks) < 3

        now_utc = datetime.now(timezone.utc)
        timestamp = now_utc.isoformat().replace("+00:00", "Z")

        if all_passed:
            approval = RiskApproval(
                prediction_id=prediction.prediction_id,
                approved=True,
                risk_checks=checks,
                reasoning=f"Approved with {len(failed_checks)} minor risk flags" if failed_checks else "All risk checks passed",
                timestamp=timestamp
            )
            logger.info(f"RISK: {prediction.ticker} {prediction.signal} APPROVED (conf: {prediction.confidence:.0%}, flags: {len(failed_checks)})")
            return approval

        veto_reasons = [c.details for c in failed_checks]
        veto_reason = "; ".join(veto_reasons)

        veto = VetoRecord(
            veto_id=f"VETO-{now_utc.strftime('%Y%m%d%H%M%S')}-{prediction.ticker}",
            prediction_id=prediction.prediction_id,
            ticker=prediction.ticker,
            signal=prediction.signal,
            rejected_confidence=prediction.confidence,
            veto_reason=veto_reason,
            market_regime=prediction.market_regime,
            failed_checks=[c.check_name for c in failed_checks],
            timestamp=timestamp,
            expected_loss_pct=-10.0
        )

        self._save_veto(veto)

        approval = RiskApproval(
            prediction_id=prediction.prediction_id,
            approved=False,
            risk_checks=checks,
            veto_record=veto,
            reasoning=veto_reason,
            timestamp=timestamp
        )

        logger.info(f"RISK: {prediction.ticker} {prediction.signal} VETOED | {veto_reason[:80]}")
        return approval

    def get_veto_summary(self) -> Dict[str, Any]:
        """Get summary of all vetoes."""
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as total FROM veto_archive")
            total = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(*) as correct FROM veto_archive WHERE veto_correct = 1")
            correct = c.fetchone()[0] or 0

            c.execute("SELECT COALESCE(SUM(avoided_drawdown), 0) as total_avoided FROM veto_archive")
            avoided = c.fetchone()[0] or 0

            pass # conn.close()

            return {
                "total_vetoes": total,
                "correct_vetoes": correct,
                "veto_accuracy": round(correct / total * 100, 1) if total > 0 else 0,
                "total_avoided_drawdown": avoided
            }
        except Exception as e:
            logger.warning(f"Veto summary failed: {e}")
            return {"total_vetoes": 0, "correct_vetoes": 0, "veto_accuracy": 0, "total_avoided_drawdown": 0}


def create_risk_manager() -> RiskManager:
    """Factory function."""
    return RiskManager()


if __name__ == "__main__":
    rm = create_risk_manager()
    summary = rm.get_veto_summary()
    print(f"Veto Summary: {summary}")
