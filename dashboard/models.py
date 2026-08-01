import yfinance as yf
from config import logger

def generate_trade_proposal(prediction_data):
    """
    Generates a specific trade proposal from prediction data.
    """
    ticker = prediction_data.get('asset') or prediction_data.get('ticker', 'UNKNOWN')
    
    # We derive a simulated 1-5 score from confidence if overall_score is missing
    conf = prediction_data.get('confidence_score') or prediction_data.get('confidence') or 0.0
    score = prediction_data.get('overall_score', conf * 5)
    
    current_price = 100.0 # Default fallback
    try:
        # Avoid hanging on yfinance call if ticker is invalid
        if ticker and ticker != 'UNKNOWN':
            # Most Indian stocks need .NS suffix for yfinance
            suffix_ticker = ticker + ".NS" if not ticker.endswith(".NS") and not ticker.endswith(".BO") else ticker
            stock = yf.Ticker(suffix_ticker)
            hist = stock.history(period='5d')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
    except Exception as e:
        logger.warning(f"Failed to fetch price for {ticker}: {e}")

    if score < 3.0:
        signal = "SHORT"
        target_price = current_price * 0.88
        stop_loss = current_price * 1.05
    elif score > 4.0:
        signal = "LONG"
        target_price = current_price * 1.12
        stop_loss = current_price * 0.95
    else:
        signal = "HOLD"
        target_price = current_price
        stop_loss = current_price
        
    if conf > 0.70:
        position_size = 5.0
    elif conf > 0.60:
        position_size = 3.0
    else:
        position_size = 1.0
        
    return {
        'signal': signal,
        'entry_price': round(current_price, 2),
        'target_price': round(target_price, 2),
        'stop_loss': round(stop_loss, 2),
        'position_size_pct': position_size,
        'score': round(score, 2),
        'rationale': f"Trade proposed based on AI overall score of {round(score, 2)}/5.0"
    }
