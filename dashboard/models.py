import yfinance as yf
from config import logger

def generate_trade_proposal(prediction_data):
    """
    Generates a specific trade proposal from prediction data.
    """
    ticker = prediction_data.get('asset', 'UNKNOWN')
    
    # We derive a simulated 1-5 score from confidence if overall_score is missing
    conf = prediction_data.get('confidence_score') or prediction_data.get('confidence') or 0.0
    score = prediction_data.get('overall_score', conf * 5)
    
    # Use DB values if present
    db_entry = prediction_data.get('entry_price')
    db_target = prediction_data.get('target_price')
    db_stop = prediction_data.get('stop_loss')
    db_pos = prediction_data.get('position_size_pct')
    db_signal = prediction_data.get('trade_signal')
    
    current_price = db_entry if db_entry is not None else 0.0
    if current_price == 0.0:
        try:
            if ticker and ticker != 'UNKNOWN':
                suffix_ticker = ticker + ".NS" if not ticker.endswith(".NS") and not ticker.endswith(".BO") else ticker
                stock = yf.Ticker(suffix_ticker)
                # Try getting price from multiple possible fields
                info = stock.info
                current_price = info.get('currentPrice')
                if current_price is None:
                    current_price = info.get('regularMarketPrice')
                if current_price is None:
                    current_price = info.get('previousClose', 0.0)
                
                # If all info fields fail, try history
                if not current_price:
                    hist = stock.history(period="1d")
                    if not hist.empty:
                        current_price = float(hist['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"Failed to fetch price for {ticker}: {e}")
            current_price = 0.0

    if db_target is not None and db_stop is not None and db_signal is not None:
        signal = db_signal
        target_price = db_target
        stop_loss = db_stop
    else:
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
        
    if db_pos is not None:
        position_size = db_pos
    else:
        if conf > 0.70:
            position_size = 5.0
        elif conf > 0.60:
            position_size = 3.0
        else:
            position_size = 1.0
        
    return {
        'signal': signal,
        'entry_price': round(current_price, 2) if current_price else 0.0,
        'target_price': round(target_price, 2) if target_price else 0.0,
        'stop_loss': round(stop_loss, 2) if stop_loss else 0.0,
        'position_size_pct': position_size,
        'score': round(score, 2),
        'rationale': prediction_data.get('reasoning', f"Trade proposed based on AI overall score of {round(score, 2)}/5.0")
    }
