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
import json
from database import get_connection
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

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

    def __init__(self, data_dir: Optional[Path] = None):
        self.regime_engine = MarketRegimeEngine()
        self.data_dir = data_dir or BILLING_DIR
        self.db_path = self.data_dir / "db"
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure veto archive table exists using canonical schema."""
        try:
            from dashboard.schemas import init_billing_db
            init_billing_db(self.db_path)
        except Exception as e:
            logger.warning(f"Veto table creation failed: {e}")

    def _save_veto(self, veto: VetoRecord) -> bool:
        """Persist veto to database."""
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO veto_archive
                (veto_id, prediction_id, timestamp, asset, sector, rejection_reason,
                 risk_score, expected_loss_pct, actual_outcome, actual_return_pct,
                 avoided_drawdown, veto_correct, proof_hash, notes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                veto.veto_id,
                veto.prediction_id,
                veto.timestamp,
                veto.ticker,
                "",
                veto.veto_reason,
                1.0 - getattr(veto, 'rejected_confidence', 0.5), # Add risk_score (1 - confidence)
                veto.expected_loss_pct,
                veto.actual_outcome,
                veto.actual_return_pct,
                veto.avoided_drawdown,
                veto.veto_correct,
                "",
                "",
                datetime.utcnow().isoformat() + 'Z'
            ))
            conn.commit()
            conn.close()
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

        if regime == "RISK_OFF" and signal == "BUY" and prediction.confidence < 0.80:
            passed = False
            reason = f"BUY signal in RISK_OFF regime with insufficient confidence ({prediction.confidence:.0%} < 0.80)"
        elif regime == "RISK_ON" and signal == "SELL" and prediction.confidence < 0.70:
            passed = False
            reason = f"SELL signal in RISK_ON regime with insufficient confidence ({prediction.confidence:.0%} < 0.70)"

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

        if rsi > 80:
            passed = False
            details = f"Extreme overbought (RSI {rsi}) — volatility instability risk"
        elif rsi < 15:
            passed = False
            details = f"Extreme oversold (RSI {rsi}) — potential capitulation"
        elif vol_ratio > 5.0:
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
        min_rr = 1.5

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

        all_passed = all(c.passed for c in checks)
        failed_checks = [c for c in checks if not c.passed]

        timestamp = datetime.utcnow().isoformat() + 'Z'

        if all_passed:
            approval = RiskApproval(
                prediction_id=prediction.prediction_id,
                approved=True,
                risk_checks=checks,
                reasoning="All risk checks passed",
                timestamp=timestamp
            )
            logger.info(f"RISK: {prediction.ticker} {prediction.signal} APPROVED (conf: {prediction.confidence:.0%})")
            return approval

        veto_reasons = [c.details for c in failed_checks]
        veto_reason = "; ".join(veto_reasons)

        veto = VetoRecord(
            veto_id=f"VETO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{prediction.ticker}",
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

            conn.close()

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
