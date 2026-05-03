#!/usr/bin/env python3
"""
Sovereign Alpha - Market Data Feed
==================================
Fetches real-time market data using yfinance.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "live_market_data.json"


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate RSI from price series."""
    if len(prices) < period + 1:
        return 50.0
    
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi.iloc[-1], 1) if not pd.isna(rsi.iloc[-1]) else 50.0


def calculate_moving_averages(prices: pd.Series) -> Dict[str, float]:
    """Calculate 50-day and 200-day moving averages."""
    ma50 = prices.rolling(window=50).mean().iloc[-1] if len(prices) >= 50 else None
    ma200 = prices.rolling(window=200).mean().iloc[-1] if len(prices) >= 200 else None
    
    return {
        "ma50": round(ma50, 2) if ma50 else None,
        "ma200": round(ma200, 2) if ma200 else None
    }


def calculate_percent_above_ma200(current_price: float, ma200: float) -> float:
    """Calculate % above/below 200-day MA."""
    if not ma200:
        return 0.0
    return round(((current_price - ma200) / ma200) * 100, 2)


def fetch_market_data(tickers: List[str]) -> Dict[str, Any]:
    """Fetch market data for all tickers."""
    print(f"Fetching market data for {len(tickers)} tickers...")
    
    market_data = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "tickers": {}
    }
    
    for i, ticker in enumerate(tickers):
        try:
            print(f"  [{i+1}/{len(tickers)}] {ticker}...")
            ticker_data = yf.Ticker(ticker)
            info = ticker_data.info
            
            current_price = info.get("currentPrice") or info.get("regularMarketPreviousClose") or 0
            previous_close = info.get("regularMarketPreviousClose") or current_price
            fifty_two_week_high = info.get("fiftyTwoWeekHigh") or current_price
            fifty_two_week_low = info.get("fiftyTwoWeekLow") or current_price
            volume = info.get("volume") or 0
            avg_volume = info.get("averageVolume") or 1
            
            hist = ticker_data.history(period="1y")
            
            rsi = calculate_rsi(hist["Close"]) if len(hist) > 14 else 50.0
            ma_data = calculate_moving_averages(hist["Close"])
            percent_ma200 = calculate_percent_above_ma200(current_price, ma_data.get("ma200"))
            
            earnings_date = None
            try:
                earnings = ticker_data.earnings_dates
                if earnings is not None and len(earnings) > 0:
                    next_earnings = earnings.index[0]
                    earnings_date = str(next_earnings.date())
            except:
                pass
            
            short_interest = None
            try:
                if "shortPercentOfFloat" in info:
                    short_interest = info.get("shortPercentOfFloat", 0) * 100
            except:
                pass
            
            analyst_target = info.get("targetMeanPrice") or None
            analyst_consensus = None
            if "recommendationKey" in info:
                rec = info.get("recommendationKey", "").upper()
                analyst_consensus = rec
            
            ticker_market_data = {
                "symbol": ticker,
                "current_price": current_price,
                "previous_close": previous_close,
                "52_week_high": fifty_two_week_high,
                "52_week_low": fifty_two_week_low,
                "daily_volume": volume,
                "avg_volume": avg_volume,
                "volume_ratio": round(volume / avg_volume, 2) if avg_volume > 0 else 1.0,
                "rsi_14": rsi,
                "ma50": ma_data.get("ma50"),
                "ma200": ma_data.get("ma200"),
                "percent_above_ma200": percent_ma200,
                "earnings_date": earnings_date,
                "short_interest_pct": short_interest,
                "analyst_target": analyst_target,
                "analyst_consensus": analyst_consensus
            }
            
            market_data["tickers"][ticker] = ticker_market_data
            
        except Exception as e:
            print(f"    Error fetching {ticker}: {e}")
            market_data["tickers"][ticker] = {
                "symbol": ticker,
                "error": str(e)
            }
    
    return market_data


def load_tickers_from_csv() -> List[str]:
    """Load tickers from sample_positions.csv."""
    csv_path = DATA_DIR / "sample_positions.csv"
    tickers = set()
    
    with open(csv_path, "r") as f:
        lines = f.readlines()[1:]
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                tickers.add(parts[1])
    
    return sorted(list(tickers))


def main():
    """Main entry point."""
    print("=" * 60)
    print("SOVEREIGN ALPHA - Market Data Feed")
    print("=" * 60)
    
    tickers = load_tickers_from_csv()
    print(f"Loaded {len(tickers)} tickers from CSV")
    
    market_data = fetch_market_data(tickers)
    
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(market_data, f, indent=2, default=str)
    
    print(f"\nMarket data saved to: {OUTPUT_FILE}")
    print(f"Fetched at: {market_data['fetched_at']}")
    
    valid_count = sum(1 for t, d in market_data["tickers"].items() if "error" not in d)
    print(f"Successfully fetched: {valid_count}/{len(tickers)}")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)