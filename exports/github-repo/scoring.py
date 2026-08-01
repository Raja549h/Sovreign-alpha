"""
Sovereign Alpha - 4D Scorer
This module calculates the 4-Dimensional Institutional Score for a given asset.
"""
from typing import Dict, Any

class FourDScorer:
    """
    Implements the Sovereign Alpha 4D scoring logic.
    Dimensions:
    1. Fundamental Score (Weight: 30%)
    2. Technical Score (Weight: 30%)
    3. Sentiment Score (Weight: 20%)
    4. Macro Score (Weight: 20%)
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            'fundamental': 0.30,
            'technical': 0.30,
            'sentiment': 0.20,
            'macro': 0.20
        }

    def score(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculates the 4D score based on input data metrics.
        Returns a dictionary with the individual scores and the overall composite score.
        """
        fund_score = self._calc_fundamental(data.get('fundamental', {}))
        tech_score = self._calc_technical(data.get('technical', {}))
        sent_score = self._calc_sentiment(data.get('sentiment', {}))
        macro_score = self._calc_macro(data.get('macro', {}))
        
        composite = (
            fund_score * self.weights['fundamental'] +
            tech_score * self.weights['technical'] +
            sent_score * self.weights['sentiment'] +
            macro_score * self.weights['macro']
        )
        
        return {
            'fundamental_score': round(fund_score, 2),
            'technical_score': round(tech_score, 2),
            'sentiment_score': round(sent_score, 2),
            'macro_score': round(macro_score, 2),
            'overall_score': round(composite, 2)
        }

    def _calc_fundamental(self, data: Dict[str, Any]) -> float:
        # Example logic mapping PE ratio, earnings growth to 1-5 scale
        growth = data.get('earnings_growth', 0)
        if growth > 20: return 5.0
        if growth > 10: return 4.0
        if growth > 0: return 3.0
        if growth > -10: return 2.0
        return 1.0

    def _calc_technical(self, data: Dict[str, Any]) -> float:
        # RSI mapping logic
        rsi = data.get('rsi', 50)
        if 30 <= rsi <= 70: return 4.0
        if rsi < 30: return 5.0 # Oversold (opportunity)
        return 2.0

    def _calc_sentiment(self, data: Dict[str, Any]) -> float:
        return data.get('sentiment_index', 3.0)

    def _calc_macro(self, data: Dict[str, Any]) -> float:
        regime = data.get('regime', 'NEUTRAL')
        if regime == 'RISK_ON': return 5.0
        if regime == 'NEUTRAL': return 3.0
        return 1.0
