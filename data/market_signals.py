#!/usr/bin/env python3
"""
Sovereign Alpha - Market Signals Generator
======================================
Generates trading signals from live market data.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

DATA_DIR = Path(__file__).parent.parent / "data"
INPUT_FILE = DATA_DIR / "live_market_data.json"
OUTPUT_FILE = DATA_DIR / "live_signals.json"


def generate_signals(market_data: dict) -> dict:
    """Generate trading signals from market data."""
    signals = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "oversold": [],
        "overbought": [],
        "unusual_volume": [],
        "below_target": [],
        "near_high": [],
        "near_low": [],
        "summary": {
            "total_signals": 0,
            "buy_signals": 0,
            "sell_signals": 0
        }
    }
    
    for ticker, data in market_data.get("tickers", {}).items():
        if "error" in data:
            continue
        
        price = data.get("current_price", 0)
        rsi = data.get("rsi_14", 50)
        volume_ratio = data.get("volume_ratio", 1)
        analyst_target = data.get("analyst_target")
        pct_above_ma200 = data.get("percent_above_ma200", 0)
        high = data.get("52_week_high", price)
        low = data.get("52_week_low", price)
        
        if rsi < 30:
            signals["oversold"].append({
                "symbol": ticker,
                "rsi": rsi,
                "price": price,
                "reason": "RSI below 30 - oversold"
            })
        
        if rsi > 70:
            signals["overbought"].append({
                "symbol": ticker,
                "rsi": rsi,
                "price": price,
                "reason": "RSI above 70 - overbought"
            })
        
        if volume_ratio >= 2.0:
            signals["unusual_volume"].append({
                "symbol": ticker,
                "volume_ratio": volume_ratio,
                "price": price,
                "reason": "Volume 2x above average"
            })
        
        if analyst_target and analyst_target > 0:
            pct_below_target = ((analyst_target - price) / analyst_target) * 100
            if pct_below_target >= 15:
                signals["below_target"].append({
                    "symbol": ticker,
                    "current_price": price,
                    "analyst_target": analyst_target,
                    "pct_below": round(pct_below_target, 2),
                    "reason": f"{round(pct_below_target, 1)}% below analyst target"
                })
        
        if high > 0:
            pct_from_high = ((high - price) / high) * 100
            if pct_from_high <= 5:
                signals["near_high"].append({
                    "symbol": ticker,
                    "price": price,
                    "52_week_high": high,
                    "pct_from_high": round(pct_from_high, 2),
                    "reason": "Within 5% of 52-week high"
                })
        
        if low > 0:
            pct_from_low = ((price - low) / low) * 100
            if pct_from_low <= 5:
                signals["near_low"].append({
                    "symbol": ticker,
                    "price": price,
                    "52_week_low": low,
                    "pct_from_low": round(pct_from_low, 2),
                    "reason": "Within 5% of 52-week low"
                })
    
    signals["summary"]["total_signals"] = (
        len(signals["oversold"]) + len(signals["overbought"]) + 
        len(signals["unusual_volume"]) + len(signals["below_target"]) +
        len(signals["near_high"]) + len(signals["near_low"])
    )
    signals["summary"]["buy_signals"] = (
        len(signals["oversold"]) + len(signals["unusual_volume"]) +
        len(signals["below_target"]) + len(signals["near_low"])
    )
    signals["summary"]["sell_signals"] = (
        len(signals["overbought"]) + len(signals["near_high"])
    )
    
    return signals


def main():
    """Main entry point."""
    print("=" * 60)
    print("SOVEREIGN ALPHA - Market Signals")
    print("=" * 60)
    
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found")
        print("Run market_feed.py first to fetch market data")
        return 1
    
    with open(INPUT_FILE, "r") as f:
        market_data = json.load(f)
    
    print(f"Loaded market data for {len(market_data.get('tickers', {}))} tickers")
    
    signals = generate_signals(market_data)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=2, default=str)
    
    print(f"\nSignals saved to: {OUTPUT_FILE}")
    print(f"Generated at: {signals['generated_at']}")
    print(f"\nSignal Summary:")
    print(f"  Oversold (buy):     {len(signals['oversold'])}")
    print(f"  Overbought (sell): {len(signals['overbought'])}")
    print(f"  Unusual Volume:   {len(signals['unusual_volume'])}")
    print(f"  Below Target:     {len(signals['below_target'])}")
    print(f"  Near 52w High:    {len(signals['near_high'])}")
    print(f"  Near 52w Low:    {len(signals['near_low'])}")
    print(f"  Total Signals:    {signals['summary']['total_signals']}")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)