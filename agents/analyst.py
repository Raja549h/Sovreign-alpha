"""
ANALYST AGENT — Institutional Market Intelligence
==================================================
Generates high-confidence predictions using:
1. Technical market structure
2. Institutional positioning
3. Macro regime analysis
4. Risk governance context

Output format matches Goldman Sachs research / Bloomberg intelligence notes.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, logger
from engine.regime import MarketRegimeEngine
from engine.data_layer import DataLayer

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class InstitutionalPrediction:
    """Single institutional-grade prediction."""
    prediction_id: str
    ticker: str
    signal: str
    confidence: float
    market_regime: str
    thesis: str
    risk_factors: List[str]
    institutional_positioning: Dict[str, Any]
    macro_context: Dict[str, Any]
    technical_summary: Dict[str, Any]
    data_sources_used: List[str]
    timestamp: str
    expected_timeline_days: int
    entry_price: float
    target_price: float
    stop_loss: float
    risk_reward_ratio: float


class AnalystAgent:
    """
    Institutional analyst agent.
    Generates predictions that read like Bloomberg intelligence notes.
    """

    INSTITUTIONAL_TICKERS = [
        'NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'JPM', 'GS', 'MS',
        'LLY', 'UNH',
        'XOM', 'CVX',
        'AMD', 'AVGO', 'TSM'
    ]

    def __init__(self):
        self.data_layer = DataLayer()
        self.regime_engine = MarketRegimeEngine()
        self.cerebras_client = None
        if OPENAI_AVAILABLE and LLM_API_KEY:
            self.cerebras_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    def _build_technical_summary(self, profile) -> Dict[str, Any]:
        """Build technical structure summary from asset profile."""
        if profile is None:
            return {}

        trend = "neutral"
        if profile.sma_50 > 0 and profile.sma_200 > 0:
            if profile.price > profile.sma_50 > profile.sma_200:
                trend = "bullish"
            elif profile.price < profile.sma_50 < profile.sma_200:
                trend = "bearish"

        momentum = "neutral"
        if profile.rsi_14 < 30:
            momentum = "oversold"
        elif profile.rsi_14 > 70:
            momentum = "overbought"
        elif profile.rsi_14 > 50:
            momentum = "positive"
        elif profile.rsi_14 < 50:
            momentum = "negative"

        vol_context = "normal"
        if profile.volume_ratio > 2.0:
            vol_context = "elevated"
        elif profile.volume_ratio < 0.5:
            vol_context = "light"

        return {
            "trend": trend,
            "momentum": momentum,
            "rsi": profile.rsi_14,
            "macd": profile.macd,
            "sma_20": profile.sma_20,
            "sma_50": profile.sma_50,
            "sma_200": profile.sma_200,
            "volume_context": vol_context,
            "volume_ratio": profile.volume_ratio,
            "atr_14": profile.atr_14,
            "price_vs_52w_high": round(((profile.price - profile.high_52w) / profile.high_52w) * 100, 1) if profile.high_52w > 0 else 0,
            "price_vs_52w_low": round(((profile.price - profile.low_52w) / profile.low_52w) * 100, 1) if profile.low_52w > 0 else 0,
        }

    def _generate_thesis(self, ticker: str, profile, regime: str, macro: Dict, tech: Dict, sec_data: Dict) -> str:
        """Generate institutional thesis using Cerebras LLM."""
        if not self.cerebras_client:
            return self._generate_simple_thesis(ticker, profile, regime, macro, tech)

        signal = self._determine_signal(profile, regime, tech)

        regime_context = {
            "RISK_ON": "risk-on environment characterized by falling volatility, stable credit conditions, and positive liquidity",
            "RISK_OFF": "risk-off environment with elevated volatility, widening credit spreads, and deteriorating liquidity conditions",
            "NEUTRAL": "neutral regime with mixed signals across volatility, credit, and rate indicators"
        }

        prompt = f"""You are a senior institutional analyst at a macro hedge fund. Write a concise, evidence-driven thesis for a {signal} signal on {ticker}.

TECHNICAL STRUCTURE:
- Trend: {tech.get('trend', 'neutral')}
- RSI(14): {tech.get('rsi', 50)}
- MACD: {tech.get('macd', 0)}
- Price vs SMA50: {profile.price if profile else 0} vs {tech.get('sma_50', 0)}
- Price vs SMA200: {profile.price if profile else 0} vs {tech.get('sma_200', 0)}
- Volume: {tech.get('volume_context', 'normal')} ({tech.get('volume_ratio', 1)}x average)
- 52-week range: {profile.low_52w if profile else 0} - {profile.high_52w if profile else 0}

MACRO ENVIRONMENT:
- Regime: {regime} — {regime_context.get(regime, '')}
- VIX: {macro.get('vix', 0)}
- 10Y Treasury: {macro.get('treasury_10y', 0)}%
- DXY: {macro.get('dxy', 0)}
- Gold: ${macro.get('gold', 0)}
- Oil WTI: ${macro.get('oil_wti', 0)}

INSTITUTIONAL POSITIONING:
- Sector: {profile.sector if profile else 'Unknown'}
- Recent 13F activity: {len(sec_data.get('recent_filings', []))} filings tracked

Write a single paragraph thesis (2-3 sentences) that:
1. References the technical structure
2. References the macro environment
3. References institutional positioning context
4. Uses professional, analytical language
5. Is evidence-driven and concise

Do NOT use retail trading language, emoji, or hype. Write like a Goldman Sachs research note."""

        try:
            response = self.cerebras_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a senior institutional analyst. Write concise, evidence-driven market analysis in the style of Goldman Sachs research notes. No hype, no emoji, no retail language."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            thesis = response.choices[0].message.content
            if thesis:
                return thesis.strip()
            return self._generate_simple_thesis(ticker, profile, regime, macro, tech)
        except Exception as e:
            logger.warning(f"LLM thesis generation failed: {e}")
            return self._generate_simple_thesis(ticker, profile, regime, macro, tech)

    def _generate_simple_thesis(self, ticker: str, profile, regime: str, macro: Dict, tech: Dict) -> str:
        """Generate thesis without LLM — rule-based institutional language."""
        signal = self._determine_signal(profile, regime, tech)
        trend = tech.get('trend', 'neutral')
        momentum = tech.get('momentum', 'neutral')
        vol = tech.get('volume_context', 'normal')
        rsi = tech.get('rsi', 50)
        vix = macro.get('vix', 0)
        t10y = macro.get('treasury_10y', 0)
        dxy = macro.get('dxy', 0)
        sector = profile.sector if profile else "Unknown"

        parts = []

        if signal == "BUY":
            parts.append(f"{signal} signal supported by")
            if trend == "bullish":
                parts.append("improving momentum structure with price above key moving averages")
            elif trend == "neutral":
                parts.append("consolidating price action near equilibrium levels")
            else:
                parts.append("oversold conditions presenting tactical entry opportunity")

            if vol == "elevated":
                parts.append("elevated volume suggesting institutional accumulation")

            if regime == "RISK_ON":
                parts.append(f"risk-on macro regime (VIX {vix}, 10Y {t10y}%) providing favorable backdrop")
            elif regime == "NEUTRAL":
                parts.append(f"neutral macro regime (VIX {vix}) with selective opportunity in {sector}")
            else:
                parts.append(f"despite risk-off conditions (VIX {vix}), {sector} sector showing relative strength")

        elif signal == "SELL":
            parts.append(f"{signal} signal driven by")
            if trend == "bearish":
                parts.append("deteriorating technical structure with price below key moving averages")
            elif momentum == "overbought":
                parts.append(f"overbought conditions (RSI {rsi}) suggesting near-term correction risk")
            else:
                parts.append("weakening momentum and distribution patterns")

            if regime == "RISK_OFF":
                parts.append(f"risk-off macro regime (VIX {vix}) amplifying downside risk")

        else:
            parts.append(f"HOLD — {ticker} showing mixed signals")
            parts.append(f"technical structure neutral (RSI {rsi}, {trend} trend)")
            parts.append(f"macro regime ({regime}) does not provide clear directional bias")

        thesis = ", ".join(parts) + "."
        return thesis

    def _determine_signal(self, profile, regime: str, tech: Dict) -> str:
        """Determine BUY/SELL/HOLD signal based on technicals and regime."""
        if profile is None:
            return "HOLD"

        score = 0

        if tech.get('trend') == 'bullish':
            score += 2
        elif tech.get('trend') == 'bearish':
            score -= 2

        rsi = tech.get('rsi', 50)
        if rsi < 30:
            score += 2
        elif rsi < 40:
            score += 1
        elif rsi > 70:
            score -= 2
        elif rsi > 60:
            score -= 1

        if tech.get('volume_context') == 'elevated' and tech.get('trend') == 'bullish':
            score += 1

        macd = tech.get('macd', 0)
        if macd > 0:
            score += 1
        elif macd < 0:
            score -= 1

        if regime == "RISK_OFF":
            score -= 1
        elif regime == "RISK_ON":
            score += 1

        if score >= 3:
            return "BUY"
        elif score <= -3:
            return "SELL"
        return "HOLD"

    def _calculate_confidence(self, profile, signal: str, regime: str, tech: Dict) -> float:
        """Calculate confidence score 0.0-1.0."""
        if profile is None:
            return 0.5

        confidence = 0.5

        if tech.get('trend') in ('bullish', 'bearish'):
            confidence += 0.1

        rsi = tech.get('rsi', 50)
        if (signal == "BUY" and rsi < 40) or (signal == "SELL" and rsi > 60):
            confidence += 0.1

        if tech.get('volume_context') == 'elevated':
            confidence += 0.05

        if regime == "NEUTRAL":
            confidence -= 0.05
        elif regime == "RISK_OFF" and signal == "BUY":
            confidence -= 0.1
        elif regime == "RISK_ON" and signal == "BUY":
            confidence += 0.05

        if profile.beta > 0 and profile.beta < 1.5:
            confidence += 0.05

        return round(min(max(confidence, 0.3), 0.95), 2)

    def _identify_risk_factors(self, ticker: str, profile, regime: str, tech: Dict, macro: Dict) -> List[str]:
        """Identify institutional risk factors."""
        risks = []

        if regime == "RISK_OFF":
            risks.append("Elevated market volatility may amplify downside")
        if tech.get('rsi', 50) > 70:
            risks.append("Overbought technical conditions suggest near-term pullback risk")
        if tech.get('rsi', 50) < 30:
            risks.append("Oversold conditions may indicate fundamental deterioration")
        if profile and profile.beta > 1.3:
            risks.append(f"High beta ({profile.beta}) increases portfolio sensitivity")
        if macro.get('treasury_10y', 0) > 4.5:
            risks.append("Elevated treasury yields pressuring equity valuations")
        if macro.get('vix', 0) > 25:
            risks.append("VIX above 25 indicates heightened uncertainty")
        if tech.get('volume_context') == 'light':
            risks.append("Light volume reduces conviction in price movement")
        if profile and profile.price > profile.high_52w * 0.95:
            risks.append("Trading near 52-week high — limited upside without catalyst")

        if not risks:
            risks.append("Standard market risk — monitor regime shifts")

        return risks

    def _build_institutional_positioning(self, profile, sec_data: Dict) -> Dict[str, Any]:
        """Build institutional positioning context."""
        return {
            "sector": profile.sector if profile else "Unknown",
            "recent_13f_filings": len(sec_data.get("recent_filings", [])),
            "notable_filers": [f.get("filer", "") for f in sec_data.get("recent_filings", [])[:3]],
            "sector_context": f"{profile.sector} sector positioning tracked via latest 13F filings" if profile else "Sector positioning data pending"
        }

    def _build_macro_context(self, regime: str, macro: Dict) -> Dict[str, Any]:
        """Build macro context for prediction."""
        return {
            "regime": regime,
            "vix": macro.get("vix", 0),
            "treasury_10y": macro.get("treasury_10y", 0),
            "dxy": macro.get("dxy", 0),
            "gold": macro.get("gold", 0),
            "oil_wti": macro.get("oil_wti", 0),
            "fed_funds": macro.get("fed_funds", 0),
            "hy_oas": macro.get("hy_oas", 0),
        }

    def analyze(self, ticker: str) -> Optional[InstitutionalPrediction]:
        """
        Full analysis pipeline for a single ticker.
        Returns institutional prediction or None if data unavailable.
        """
        try:
            logger.info(f"Analyst: analyzing {ticker}")

            profile = self.data_layer.fetch_technicals(ticker)
            if profile is None:
                logger.warning(f"No technical data for {ticker}")
                return None

            regime = self.regime_engine.classify()
            macro = self.data_layer.fetch_macro_snapshot()
            sec_data = self.data_layer.fetch_sec_13f_summary()

            tech = self._build_technical_summary(profile)
            signal = self._determine_signal(profile, regime.regime, tech)
            confidence = self._calculate_confidence(profile, signal, regime.regime, tech)
            thesis = self._generate_thesis(ticker, profile, regime.regime, asdict(macro), tech, sec_data)
            risks = self._identify_risk_factors(ticker, profile, regime.regime, tech, asdict(macro))

            entry = profile.price
            atr = profile.atr_14 if profile.atr_14 > 0 else entry * 0.03

            if signal == "BUY":
                target = round(entry * 1.08, 2)
                stop = round(entry - atr * 2, 2)
            elif signal == "SELL":
                target = round(entry * 0.92, 2)
                stop = round(entry + atr * 2, 2)
            else:
                target = round(entry * 1.02, 2)
                stop = round(entry * 0.98, 2)

            risk_reward = round(abs(target - entry) / abs(entry - stop), 2) if abs(entry - stop) > 0 else 0

            prediction = InstitutionalPrediction(
                prediction_id=f"PRED-{datetime.utcnow().strftime('%Y%m%d%H%M')}-{ticker}",
                ticker=ticker,
                signal=signal,
                confidence=confidence,
                market_regime=regime.regime,
                thesis=thesis,
                risk_factors=risks,
                institutional_positioning=self._build_institutional_positioning(profile, sec_data),
                macro_context=self._build_macro_context(regime.regime, asdict(macro)),
                technical_summary=tech,
                data_sources_used=["yfinance", "regime_engine", "sec_edgar"],
                timestamp=datetime.utcnow().isoformat() + 'Z',
                expected_timeline_days=30,
                entry_price=entry,
                target_price=target,
                stop_loss=stop,
                risk_reward_ratio=risk_reward
            )

            logger.info(f"  {ticker}: {signal} (confidence: {confidence:.0%}) | Regime: {regime.regime}")
            return prediction

        except Exception as e:
            logger.warning(f"Analysis failed for {ticker}: {e}")
            return None

    def run_full_analysis(self, tickers: Optional[List[str]] = None) -> List[InstitutionalPrediction]:
        """
        Run analysis across full watchlist.
        Returns list of predictions.
        """
        if tickers is None:
            tickers = self.INSTITUTIONAL_TICKERS

        logger.info(f"Running full analysis: {len(tickers)} tickers")

        predictions = []
        for ticker in tickers:
            try:
                pred = self.analyze(ticker)
                if pred:
                    predictions.append(pred)
            except Exception as e:
                logger.warning(f"Ticker {ticker} failed: {e}")

        logger.info(f"Analysis complete: {len(predictions)} predictions generated")
        return predictions

    def get_analysis_summary(self, predictions: List[InstitutionalPrediction]) -> Dict[str, Any]:
        """Generate summary statistics for analysis results."""
        if not predictions:
            return {"total": 0, "buy": 0, "sell": 0, "hold": 0, "avg_confidence": 0}

        signals = [p.signal for p in predictions]
        confidences = [p.confidence for p in predictions]

        return {
            "total": len(predictions),
            "buy": signals.count("BUY"),
            "sell": signals.count("SELL"),
            "hold": signals.count("HOLD"),
            "avg_confidence": round(sum(confidences) / len(confidences), 3),
            "max_confidence": round(max(confidences), 3),
            "min_confidence": round(min(confidences), 3),
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }


def create_analyst() -> AnalystAgent:
    """Factory function."""
    return AnalystAgent()


if __name__ == "__main__":
    agent = create_analyst()

    print("=" * 60)
    print("ANALYST AGENT — Institutional Market Intelligence")
    print("=" * 60)

    predictions = agent.run_full_analysis(['NVDA', 'JPM', 'XOM'])

    print("\n" + "=" * 60)
    print("PREDICTIONS")
    print("=" * 60)

    for p in predictions:
        print(f"\n{p.ticker} | {p.signal} | Confidence: {p.confidence:.0%} | Regime: {p.market_regime}")
        print(f"  Entry: ${p.entry_price} | Target: ${p.target_price} | Stop: ${p.stop_loss}")
        print(f"  R/R: {p.risk_reward_ratio}")
        print(f"  Thesis: {p.thesis[:120]}...")
        print(f"  Risks: {', '.join(p.risk_factors[:2])}")

    summary = agent.get_analysis_summary(predictions)
    print(f"\nSummary: {summary['buy']} BUY, {summary['sell']} SELL, {summary['hold']} HOLD | Avg confidence: {summary['avg_confidence']:.0%}")
