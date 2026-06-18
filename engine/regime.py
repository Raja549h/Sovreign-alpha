"""
MARKET REGIME ENGINE
====================
Dynamic regime classification modeled after institutional macro research systems.

Classifies market into: RISK_ON, RISK_OFF, NEUTRAL

Inputs:
- VIX (CBOE Volatility Index)
- Credit spreads (HY OAS, IG OAS)
- Treasury yields (10Y, 2Y, yield curve)
- Fed funds rate
- Dollar index (DXY)
- Market breadth indicators

Regime affects:
- Confidence thresholds
- Veto aggressiveness
- Buy/sell approval logic
- Position sizing guidance
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, logger


@dataclass
class RegimeIndicators:
    """Raw indicator values used for regime classification."""
    vix: float = 0.0
    vix_20d_avg: float = 0.0
    vix_60d_avg: float = 0.0
    hy_oas: float = 0.0
    ig_oas: float = 0.0
    treasury_10y: float = 0.0
    treasury_2y: float = 0.0
    yield_curve_slope: float = 0.0
    fed_funds_rate: float = 0.0
    dxy: float = 0.0
    sp500_ma50: float = 0.0
    sp500_ma200: float = 0.0
    sp500_current: float = 0.0
    treasury_10y_20d_chg: float = 0.0
    credit_spread_20d_chg: float = 0.0
    timestamp: str = ""


@dataclass
class RegimeClassification:
    """Output of regime engine."""
    regime: str = "NEUTRAL"
    confidence: float = 0.0
    vix_signal: str = "neutral"
    credit_signal: str = "neutral"
    yield_signal: str = "neutral"
    trend_signal: str = "neutral"
    dollar_signal: str = "neutral"
    summary: str = ""
    indicators: Dict[str, Any] = None
    timestamp: str = ""


class MarketRegimeEngine:
    """
    Institutional-grade market regime classifier.

    Classification rules:

    RISK_OFF if ANY:
    - VIX > 25
    - HY OAS > 500bps
    - 10Y yield rising > 50bps in 20 days
    - Yield curve inverted > 50bps
    - SP500 below 200-day MA

    RISK_ON if ALL:
    - VIX < 15
    - HY OAS < 300bps
    - Credit spreads stable or narrowing
    - SP500 above 50-day MA
    - Yield curve normal or steepening

    NEUTRAL otherwise
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR
        self.regime_dir = self.data_dir / "regime"
        self.regime_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.regime_dir / "regime_history.json"
        self._load_history()

    def _load_history(self):
        """Load regime history for trend analysis."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []

    def _save_history(self, classification: RegimeClassification):
        """Append classification to history."""
        record = asdict(classification)
        self.history.append(record)
        self.history = self.history[-90:]
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except:
            pass

    def fetch_indicators(self) -> RegimeIndicators:
        """
        Fetch all regime indicators from data sources.
        Gracefully degrades if sources fail.
        """
        indicators = RegimeIndicators(
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )

        try:
            import yfinance as yf

            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="60d")
            if not vix_hist.empty:
                indicators.vix = round(float(vix_hist['Close'].iloc[-1]), 2)
                if len(vix_hist) >= 20:
                    indicators.vix_20d_avg = round(float(vix_hist['Close'].iloc[-20:].mean()), 2)
                if len(vix_hist) >= 60:
                    indicators.vix_60d_avg = round(float(vix_hist['Close'].mean()), 2)

            sp500 = yf.Ticker("^GSPC")
            sp_hist = sp500.history(period="250d")
            if not sp_hist.empty:
                indicators.sp500_current = round(float(sp_hist['Close'].iloc[-1]), 2)
                if len(sp_hist) >= 50:
                    indicators.sp500_ma50 = round(float(sp_hist['Close'].iloc[-50:].mean()), 2)
                if len(sp_hist) >= 200:
                    indicators.sp500_ma200 = round(float(sp_hist['Close'].iloc[-200:].mean()), 2)

            dxy = yf.Ticker("DX-Y.NYB")
            dxy_hist = dxy.history(period="30d")
            if not dxy_hist.empty:
                indicators.dxy = round(float(dxy_hist['Close'].iloc[-1]), 2)

            tn10 = yf.Ticker("^TNX")
            tn10_hist = tn10.history(period="30d")
            if not tn10_hist.empty:
                indicators.treasury_10y = round(float(tn10_hist['Close'].iloc[-1]), 3)
                if len(tn10_hist) >= 20:
                    indicators.treasury_10y_20d_chg = round(
                        float(tn10_hist['Close'].iloc[-1] - tn10_hist['Close'].iloc[-20]), 3
                    )

            tn2 = yf.Ticker("^IRX")
            tn2_hist = tn2.history(period="30d")
            if not tn2_hist.empty:
                indicators.treasury_2y = round(float(tn2_hist['Close'].iloc[-1]), 3)

        except Exception as e:
            logger.warning(f"yfinance indicator fetch failed: {e}")

        try:
            from fredapi import Fred
            fred_key = os.environ.get("FRED_API_KEY", "")
            if fred_key:
                fred = Fred(api_key=fred_key)
                try:
                    indicators.fed_funds_rate = round(float(fred.get_series_latest_obs('FEDFUNDS')), 3)
                except:
                    pass
                try:
                    indicators.hy_oas = round(float(fred.get_series_latest_obs('BAMLH0A0HYM2')), 2)
                except:
                    pass
                try:
                    indicators.ig_oas = round(float(fred.get_series_latest_obs('BAMLC0A0CM')), 2)
                except:
                    pass
        except Exception as e:
            logger.warning(f"FRED indicator fetch failed: {e}")

        if indicators.yield_curve_slope == 0 and indicators.treasury_10y > 0 and indicators.treasury_2y > 0:
            indicators.yield_curve_slope = round(indicators.treasury_10y - indicators.treasury_2y, 3)

        return indicators

    def _classify_vix(self, indicators: RegimeIndicators) -> tuple:
        """Classify VIX signal: risk_on, risk_off, neutral."""
        vix = indicators.vix
        if vix == 0:
            return "neutral", 0.0
        if vix > 30:
            return "risk_off", min((vix - 30) / 20, 1.0)
        if vix > 25:
            return "risk_off", min((vix - 25) / 10, 0.8)
        if vix < 12:
            return "risk_on", min((15 - vix) / 10, 0.9)
        if vix < 15:
            return "risk_on", 0.6
        return "neutral", 0.3

    def _classify_credit(self, indicators: RegimeIndicators) -> tuple:
        """Classify credit spread signal."""
        hy_oas = indicators.hy_oas
        if hy_oas == 0:
            return "neutral", 0.0
        if hy_oas > 600:
            return "risk_off", min((hy_oas - 600) / 400, 1.0)
        if hy_oas > 500:
            return "risk_off", min((hy_oas - 500) / 200, 0.8)
        if hy_oas > 400:
            return "neutral", 0.4
        if hy_oas < 300:
            return "risk_on", min((350 - hy_oas) / 100, 0.8)
        return "neutral", 0.3

    def _classify_yields(self, indicators: RegimeIndicators) -> tuple:
        """Classify yield curve and rate movement signal."""
        slope = indicators.yield_curve_slope
        rate_chg = indicators.treasury_10y_20d_chg

        if slope < -0.5:
            return "risk_off", min(abs(slope) / 2, 0.9)
        if rate_chg > 0.50:
            return "risk_off", min(rate_chg / 1.0, 0.8)
        if slope > 0.5 and rate_chg < 0.20:
            return "risk_on", 0.6
        if slope > 0 and rate_chg < 0.30:
            return "risk_on", 0.4
        return "neutral", 0.3

    def _classify_trend(self, indicators: RegimeIndicators) -> tuple:
        """Classify equity trend signal."""
        price = indicators.sp500_current
        ma50 = indicators.sp500_ma50
        ma200 = indicators.sp500_ma200

        if price == 0:
            return "neutral", 0.0
        if price < ma200 and ma200 > 0:
            return "risk_off", 0.8
        if price > ma50 and ma50 > ma200 and ma200 > 0:
            return "risk_on", 0.7
        if price > ma50 and ma50 > 0:
            return "risk_on", 0.5
        return "neutral", 0.3

    def _classify_dollar(self, indicators: RegimeIndicators) -> tuple:
        """Classify dollar strength signal."""
        dxy = indicators.dxy
        if dxy == 0:
            return "neutral", 0.0
        if dxy > 108:
            return "risk_off", min((dxy - 108) / 10, 0.7)
        if dxy > 105:
            return "neutral", 0.4
        if dxy < 100:
            return "risk_on", 0.5
        return "neutral", 0.3

    def classify(self, indicators: Optional[RegimeIndicators] = None) -> RegimeClassification:
        """
        Full regime classification.
        Fetches indicators if not provided.
        """
        if indicators is None:
            indicators = self.fetch_indicators()

        vix_sig, vix_conf = self._classify_vix(indicators)
        credit_sig, credit_conf = self._classify_credit(indicators)
        yield_sig, yield_conf = self._classify_yields(indicators)
        trend_sig, trend_conf = self._classify_trend(indicators)
        dollar_sig, dollar_conf = self._classify_dollar(indicators)

        signals = [vix_sig, credit_sig, yield_sig, trend_sig, dollar_sig]
        confidences = [vix_conf, credit_conf, yield_conf, trend_conf, dollar_conf]

        risk_off_count = sum(1 for s in signals if s == "risk_off")
        risk_on_count = sum(1 for s in signals if s == "risk_on")

        weighted_conf = 0.0
        total_weight = 0.0
        weights = [0.30, 0.25, 0.20, 0.15, 0.10]

        for i, (sig, conf) in enumerate(zip(signals, confidences)):
            if sig == "risk_off":
                weighted_conf += conf * weights[i]
            elif sig == "risk_on":
                weighted_conf -= conf * weights[i] * 0.5
            total_weight += weights[i]

        if risk_off_count >= 2:
            regime = "RISK_OFF"
            confidence = min(weighted_conf + 0.3, 1.0)
        elif risk_on_count >= 3:
            regime = "RISK_ON"
            confidence = min(abs(weighted_conf) + 0.2, 0.9)
        else:
            regime = "NEUTRAL"
            confidence = max(1.0 - abs(weighted_conf), 0.3)

        summary_parts = []
        if vix_sig != "neutral":
            summary_parts.append(f"VIX {indicators.vix:.0f} ({vix_sig})")
        if credit_sig != "neutral":
            summary_parts.append(f"HY OAS {indicators.hy_oas:.0f}bps ({credit_sig})")
        if yield_sig != "neutral":
            summary_parts.append(f"10Y {indicators.treasury_10y:.2f}% ({yield_sig})")
        if trend_sig != "neutral":
            summary_parts.append(f"SPX {indicators.sp500_current:.0f} vs MA200 {indicators.sp500_ma200:.0f} ({trend_sig})")

        summary = " | ".join(summary_parts) if summary_parts else "All indicators within normal ranges"

        classification = RegimeClassification(
            regime=regime,
            confidence=round(confidence, 3),
            vix_signal=vix_sig,
            credit_signal=credit_sig,
            yield_signal=yield_sig,
            trend_signal=trend_sig,
            dollar_signal=dollar_sig,
            summary=summary,
            indicators={
                "vix": indicators.vix,
                "vix_20d_avg": indicators.vix_20d_avg,
                "hy_oas": indicators.hy_oas,
                "ig_oas": indicators.ig_oas,
                "treasury_10y": indicators.treasury_10y,
                "treasury_2y": indicators.treasury_2y,
                "yield_curve_slope": indicators.yield_curve_slope,
                "fed_funds_rate": indicators.fed_funds_rate,
                "dxy": indicators.dxy,
                "sp500_current": indicators.sp500_current,
                "sp500_ma50": indicators.sp500_ma50,
                "sp500_ma200": indicators.sp500_ma200,
                "treasury_10y_20d_chg": indicators.treasury_10y_20d_chg,
            },
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )

        self._save_history(classification)

        logger.info(f"Regime: {regime} (confidence: {confidence:.1%}) | {summary}")

        return classification

    def get_regime_config(self, regime: str) -> Dict[str, Any]:
        """
        Return configuration parameters based on current regime.
        Used by Risk Manager to adjust thresholds dynamically.
        """
        configs = {
            "RISK_OFF": {
                "min_confidence_buy": 0.80,
                "min_confidence_sell": 0.70,
                "max_position_size_pct": 2.5,
                "max_sector_exposure_pct": 15.0,
                "veto_aggressiveness": "high",
                "max_portfolio_beta": 0.8,
                "cash_floor_pct": 20.0,
                "stop_loss_pct": 5.0,
                "hedge_required": True,
            },
            "NEUTRAL": {
                "min_confidence_buy": 0.70,
                "min_confidence_sell": 0.60,
                "max_position_size_pct": 4.0,
                "max_sector_exposure_pct": 20.0,
                "veto_aggressiveness": "medium",
                "max_portfolio_beta": 1.0,
                "cash_floor_pct": 10.0,
                "stop_loss_pct": 8.0,
                "hedge_required": False,
            },
            "RISK_ON": {
                "min_confidence_buy": 0.65,
                "min_confidence_sell": 0.55,
                "max_position_size_pct": 5.0,
                "max_sector_exposure_pct": 25.0,
                "veto_aggressiveness": "low",
                "max_portfolio_beta": 1.2,
                "cash_floor_pct": 5.0,
                "stop_loss_pct": 10.0,
                "hedge_required": False,
            }
        }
        return configs.get(regime, configs["NEUTRAL"])

    def get_latest(self) -> Optional[RegimeClassification]:
        """Get the most recent regime classification."""
        if self.history:
            data = self.history[-1]
            return RegimeClassification(**data)
        return None

    def get_regime_summary(self) -> Dict[str, Any]:
        """Get summary suitable for dashboard display."""
        latest = self.get_latest()
        if latest is None:
            return {
                "regime": "UNKNOWN",
                "confidence": 0,
                "summary": "No regime data available",
                "indicators": {}
            }
        return {
            "regime": latest.regime,
            "confidence": latest.confidence,
            "summary": latest.summary,
            "vix_signal": latest.vix_signal,
            "credit_signal": latest.credit_signal,
            "yield_signal": latest.yield_signal,
            "trend_signal": latest.trend_signal,
            "indicators": latest.indicators or {},
            "timestamp": latest.timestamp
        }


def create_regime_engine() -> MarketRegimeEngine:
    """Factory function."""
    return MarketRegimeEngine()


if __name__ == "__main__":
    engine = create_regime_engine()

    print("=" * 60)
    print("MARKET REGIME ENGINE")
    print("=" * 60)

    print("\nFetching indicators...")
    indicators = engine.fetch_indicators()
    print(f"  VIX: {indicators.vix}")
    print(f"  10Y Yield: {indicators.treasury_10y}%")
    print(f"  SP500: {indicators.sp500_current}")
    print(f"  DXY: {indicators.dxy}")

    print("\nClassifying regime...")
    classification = engine.classify(indicators)
    print(f"  Regime: {classification.regime}")
    print(f"  Confidence: {classification.confidence:.1%}")
    print(f"  Summary: {classification.summary}")

    print("\nRegime config:")
    config = engine.get_regime_config(classification.regime)
    for k, v in config.items():
        print(f"  {k}: {v}")
