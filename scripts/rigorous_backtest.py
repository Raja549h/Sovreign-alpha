import pandas as pd
import numpy as np
import yfinance as yf
import pandas_market_calendars as mcal
import re
import time
import os
from datetime import datetime, timedelta

# Parameters
ATR_PERIOD = 14
ATR_STOP_MULT = 1.5
ATR_TARGET_MULT = 3.0
DRAWDOWN_GATE_PCT = -5.0
FORWARD_TRADING_DAYS = 10
RSI_OVERBOUGHT = 75

# We already have 'historical_bulk_deals_12m.csv' and 'bulk_deal_universe.csv'
deals_df = pd.read_csv('historical_bulk_deals_12m.csv')
deals_df['deal_date'] = pd.to_datetime(deals_df['deal_date'])

top_tickers = pd.read_csv('bulk_deal_universe.csv')['ticker'].tolist()

def compute_atr(df, period=ATR_PERIOD):
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    tr = pd.concat([high - low, (high - close).abs(), (low - close).abs()], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def compute_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

# Pre-fetch all price data (use a generous lookback to cover everything)
print('Fetching price data...')
end = datetime.now() + timedelta(days=1)
start = end - timedelta(days=365 + 60) # 14 months

price_data = {}
for i, ticker in enumerate(top_tickers):
    try:
        df = yf.download(f"{ticker}.NS", start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), progress=False, auto_adjust=True)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df['ATR'] = compute_atr(df)
            df['RSI'] = compute_rsi(df)
            price_data[ticker] = df
    except:
        pass
print(f'Fetched {len(price_data)} tickers.')

# ---------------------------------------------------------------------------
# Logic rules (identical to previous)
# ---------------------------------------------------------------------------
def would_veto(price_df, deal_date, deal_price):
    if price_df.index.tz is not None:
        price_df = price_df.copy()
        price_df.index = price_df.index.tz_localize(None)

    # NO LOOK-AHEAD BIAS: Strict filtering up to deal_date
    historical = price_df[price_df.index <= deal_date]
    if len(historical) < ATR_PERIOD + 5:
        return False, "Insufficient history"

    latest = historical.iloc[-1]
    atr = float(latest.get('ATR', 0))
    rsi = float(latest.get('RSI', 50))
    close = float(latest['Close'])

    if atr <= 0 or np.isnan(atr):
        return False, "ATR unavailable"

    reasons = []
    if rsi > RSI_OVERBOUGHT: reasons.append(f"RSI overbought")
    if deal_price > close + atr: reasons.append(f"Deal price premium")
    atr_pct = (atr / close) * 100
    if atr_pct > 5.0: reasons.append(f"Extreme volatility")
    
    if len(historical) >= 50:
        sma50 = float(historical['Close'].tail(50).mean())
        if close < sma50 * 0.97: reasons.append(f"Downtrend")
    
    if len(historical) >= 20:
        price_20d_ago = float(historical['Close'].iloc[-20])
        pct_change = (close - price_20d_ago) / price_20d_ago * 100
        if pct_change < -10: reasons.append(f"Momentum collapse")

    return len(reasons) >= 1, "; ".join(reasons)

def compute_forward_drawdown(price_df, deal_date, deal_price):
    cal = mcal.get_calendar('NSE')
    if price_df.index.tz is not None:
        price_df = price_df.copy()
        price_df.index = price_df.index.tz_localize(None)

    schedule = cal.schedule(start_date=deal_date, end_date=deal_date + timedelta(days=25))
    if schedule.empty: return None
    trading_days = schedule.index[:FORWARD_TRADING_DAYS]
    if len(trading_days) == 0: return None
    
    end_td = trading_days[-1]
    forward = price_df[(price_df.index >= deal_date) & (price_df.index <= end_td)]
    if forward.empty: return None

    min_low = float(forward['Low'].min())
    return ((min_low - deal_price) / deal_price) * 100

# ---------------------------------------------------------------------------
# Split Data (In-Sample vs Out-of-Sample)
# ---------------------------------------------------------------------------
# OOS is the last 6 weeks
oos_cutoff = datetime.now() - timedelta(days=42)

# Deduplicate to one deal per ticker/day
filtered_deals = deals_df[deals_df['ticker'].isin(price_data.keys())].copy()
filtered_deals = filtered_deals.sort_values('quantity', ascending=False).drop_duplicates(subset=['ticker', 'deal_date'])

def run_evaluation(deals_subset, name="Dataset"):
    total = 0
    vetoed_count = 0
    
    tp = 0 # Vetoed & Crashed
    fp = 0 # Vetoed & Safe
    fn = 0 # Allowed & Crashed
    tn = 0 # Allowed & Safe
    
    results = []

    for _, deal in deals_subset.iterrows():
        ticker = deal['ticker']
        deal_date = deal['deal_date']
        deal_price = float(deal['deal_price'])
        
        pdf = price_data[ticker]
        dd = compute_forward_drawdown(pdf, deal_date, deal_price)
        if dd is None: continue
            
        is_vetoed, reason = would_veto(pdf, deal_date, deal_price)
        did_crash = dd <= DRAWDOWN_GATE_PCT
        
        total += 1
        if is_vetoed: vetoed_count += 1
            
        if is_vetoed and did_crash: tp += 1
        if is_vetoed and not did_crash: fp += 1
        if not is_vetoed and did_crash: fn += 1
        if not is_vetoed and not did_crash: tn += 1
            
        results.append({
            'ticker': ticker,
            'deal_date': deal_date,
            'is_vetoed': is_vetoed,
            'did_crash': did_crash,
            'drawdown': dd
        })
        
    base_rate = (tp + fn) / total if total > 0 else 0
    veto_rate = (tp + fp) / total if total > 0 else 0
    
    # Positive Predictive Value (Accuracy of a Veto)
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
    # Negative Predictive Value (Accuracy of Allowing)
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    
    # False Positive Rate (Vetoed but safe) = 1 - PPV
    fpr_veto = fp / (tp + fp) if (tp + fp) > 0 else 0
    
    print(f"=== {name} ===")
    print(f"Total Evaluated: {total}")
    print(f"Base Crash Rate (Any Deal Crashes): {base_rate:.1%}")
    print(f"Veto Rate (Deals Engine Blocks):    {veto_rate:.1%}")
    print()
    print(f"Confusion Matrix:")
    print(f"  True Positives (Vetoed & Crashed):  {tp}")
    print(f"  False Positives (Vetoed & Safe):    {fp}  <-- Blocked a good trade")
    print(f"  False Negatives (Allowed & Crashed):{fn}  <-- Missed a bad trade")
    print(f"  True Negatives (Allowed & Safe):    {tn}")
    print()
    print(f"Veto Accuracy (When we veto, it crashes): {ppv:.1%}")
    print(f"False Positive Rate of Vetoes:            {fpr_veto:.1%}")
    print(f"Edge (Veto Accuracy vs Base Rate):        {ppv - base_rate:+.1%}")
    print(f"Allowed Safety (When allowed, it's safe): {npv:.1%}")
    print(f"Edge (Allowed Safety vs (1-Base Rate)):   {npv - (1-base_rate):+.1%}")
    print()
    
    return pd.DataFrame(results)

print("\nEvaluating In-Sample (Older than 6 weeks)...")
is_deals = filtered_deals[filtered_deals['deal_date'] < oos_cutoff]
is_results = run_evaluation(is_deals, "IN-SAMPLE (Older than 6 weeks)")

print("Evaluating Out-Of-Sample (Last 6 weeks)...")
oos_deals = filtered_deals[filtered_deals['deal_date'] >= oos_cutoff]
oos_results = run_evaluation(oos_deals, "OUT-OF-SAMPLE (Last 6 weeks)")
