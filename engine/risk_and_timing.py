import math
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants based on the Sovereign Alpha model performance
WIN_RATE = 0.719           # 71.9% historical hit rate
REWARD_RISK = 1.5          # Average reward/risk ratio
MAX_POSITION_PCT = 0.15    # Capital ceiling: Max 15% allocation per single trade

def calculate_execution(ticker: str, portfolio_value: float) -> dict:
    """
    Calculates the execution parameters (timing trigger, stop loss, sizing) for a given ticker.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'RELIANCE.NS').
        portfolio_value (float): The total capital in the portfolio.

    Returns:
        dict: Contains execution logic including entry, stop loss, and position sizing.
    """
    try:
        # 1. Data Fetch Window (60 Calendar Days to ensure enough trading days for 20-day SMA)
        end_date = datetime.today()
        start_date = end_date - timedelta(days=60)
        
        logger.info(f"Fetching data for {ticker} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        df = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
        
        if df.empty or len(df) < 20:
            logger.error(f"Not enough historical data for {ticker}. Required: 20, Got: {len(df)}")
            return {"success": False, "error": "Insufficient historical data"}

        # Flatten multi-level columns if present (yfinance sometimes returns multi-index columns)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # 2. Calculate Indicators (14-day ATR & 20-day SMA)
        # Calculate True Range (TR)
        # TR = Max of (High - Low), abs(High - Prev Close), abs(Low - Prev Close)
        df['Prev_Close'] = df['Close'].shift(1)
        df['High-Low'] = df['High'] - df['Low']
        df['High-PrevClose'] = abs(df['High'] - df['Prev_Close'])
        df['Low-PrevClose'] = abs(df['Low'] - df['Prev_Close'])
        
        df['TR'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)

        # Calculate 14-day ATR using Wilder's Smoothing (alpha = 1/14)
        df['ATR_14'] = df['TR'].ewm(alpha=1/14, adjust=False).mean()

        # Calculate 20-day Simple Moving Average (SMA)
        df['SMA_20'] = df['Close'].rolling(window=20).mean()

        # Extract the latest values
        latest = df.iloc[-1]
        current_close = float(latest['Close'])
        sma_20 = float(latest['SMA_20'])
        atr_14 = float(latest['ATR_14'])

        # 3. Execution Logic
        # The Trigger: Current close > 20-day SMA + (0.5 * 14-day ATR)
        buy_threshold = sma_20 + (0.5 * atr_14)
        buy_trigger_met = current_close > buy_threshold

        # The Stop Loss: 1.5 * ATR below the entry price
        stop_loss = current_close - (1.5 * atr_14)

        # The Position Sizing Factor: Volatility-Adjusted Fractional Kelly
        # Full Kelly = W - ((1 - W) / R)
        kelly_pct = WIN_RATE - ((1 - WIN_RATE) / REWARD_RISK)
        
        # Fractional Application: Half-Kelly
        half_kelly_pct = kelly_pct / 2.0
        
        # Apply the safety cap (MAX_POSITION_PCT)
        safe_allocation_pct = min(half_kelly_pct, MAX_POSITION_PCT)

        # Final Output Calculation
        capital_allocated = portfolio_value * safe_allocation_pct
        shares_to_buy = math.floor(capital_allocated / current_close)

        return {
            "success": True,
            "ticker": ticker,
            "portfolio_value": portfolio_value,
            "current_close": round(current_close, 2),
            "sma_20": round(sma_20, 2),
            "atr_14": round(atr_14, 2),
            "buy_threshold": round(buy_threshold, 2),
            "buy_trigger_met": bool(buy_trigger_met),
            "stop_loss": round(stop_loss, 2),
            "full_kelly_pct": round(kelly_pct * 100, 2),
            "half_kelly_pct": round(half_kelly_pct * 100, 2),
            "safe_allocation_pct": round(safe_allocation_pct * 100, 2),
            "capital_allocated": round(capital_allocated, 2),
            "shares_to_buy": int(shares_to_buy)
        }

    except Exception as e:
        logger.error(f"Error calculating execution for {ticker}: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Test execution
    test_ticker = "RELIANCE.NS"
    test_portfolio = 1000000.0  # ₹1,000,000
    
    print(f"Testing calculate_execution for {test_ticker} with portfolio INR {test_portfolio:,.2f}")
    result = calculate_execution(test_ticker, test_portfolio)
    import json
    print(json.dumps(result, indent=4))
