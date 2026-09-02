import pandas as pd
import numpy as np
import yfinance as yf
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
from scipy.stats import chi2_contingency

# Parameters
ATR_PERIOD = 14
FORWARD_TRADING_DAYS = 10
DRAWDOWN_GATE_PCT = -5.0

print("Loading data...")
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

end = datetime.now() + timedelta(days=1)
start = end - timedelta(days=365 + 60) 

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

oos_cutoff = datetime.now() - timedelta(days=42)
filtered_deals = deals_df[deals_df['ticker'].isin(price_data.keys())].copy()
filtered_deals = filtered_deals.sort_values('quantity', ascending=False).drop_duplicates(subset=['ticker', 'deal_date'])

# Pre-compute indicators and drawdowns for all deals to make sweep fast
print("Pre-computing metrics for all deals...")
master_data = []
for _, deal in filtered_deals.iterrows():
    ticker = deal['ticker']
    deal_date = deal['deal_date']
    deal_price = float(deal['deal_price'])
    
    pdf = price_data[ticker]
    dd = compute_forward_drawdown(pdf, deal_date, deal_price)
    if dd is None: continue
        
    historical = pdf[pdf.index <= deal_date]
    if len(historical) < ATR_PERIOD + 5: continue
        
    latest = historical.iloc[-1]
    atr = float(latest.get('ATR', 0))
    rsi = float(latest.get('RSI', 50))
    close = float(latest['Close'])
    
    if atr <= 0 or np.isnan(atr): continue
        
    is_oos = deal_date >= oos_cutoff
    did_crash = dd <= DRAWDOWN_GATE_PCT
    
    # Store raw features for parameter sweep
    master_data.append({
        'ticker': ticker,
        'deal_date': deal_date,
        'deal_price': deal_price,
        'close': close,
        'atr': atr,
        'rsi': rsi,
        'atr_pct': (atr/close)*100,
        'is_oos': is_oos,
        'did_crash': did_crash,
        'historical': historical # needed for sma50 / 20d momentum
    })

def evaluate_thresholds(rsi_threshold, atr_pct_threshold, min_reasons):
    is_results = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}
    oos_results = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}
    
    for row in master_data:
        reasons = []
        if row['rsi'] > rsi_threshold: reasons.append('rsi')
        if row['deal_price'] > row['close'] + row['atr']: reasons.append('premium')
        if row['atr_pct'] > atr_pct_threshold: reasons.append('atr_pct')
        
        hist = row['historical']
        if len(hist) >= 50:
            sma50 = float(hist['Close'].tail(50).mean())
            if row['close'] < sma50 * 0.97: reasons.append('sma50')
        if len(hist) >= 20:
            p20 = float(hist['Close'].iloc[-20])
            if (row['close'] - p20)/p20 * 100 < -10: reasons.append('mom')
            
        is_vetoed = len(reasons) >= min_reasons
        c = row['did_crash']
        
        res = oos_results if row['is_oos'] else is_results
        
        if is_vetoed and c: res['tp'] += 1
        if is_vetoed and not c: res['fp'] += 1
        if not is_vetoed and c: res['fn'] += 1
        if not is_vetoed and not c: res['tn'] += 1
        
    return is_results, oos_results

def print_stats(res, label):
    tp, fp = res['tp'], res['fp']
    fn, tn = res['fn'], res['tn']
    total = tp + fp + fn + tn
    if total == 0: return
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    base_rate = (tp + fn) / total
    
    obs = np.array([[tp, fp], [fn, tn]])
    chi2, p, _, _ = chi2_contingency(obs, correction=False)
    
    print(f"{label}: Precision={precision:.1%} | Sens={sensitivity:.1%} | Spec={specificity:.1%} | Base={base_rate:.1%} | Chi2 p={p:.3f} | Vetoes={tp+fp}/{total}")

print("\n--- BASELINE THRESHOLDS (Original) ---")
is_res, oos_res = evaluate_thresholds(75, 5.0, 1)
print_stats(is_res, "IN-SAMPLE")
print_stats(oos_res, "OUT-OF-SAMPLE")

print("\n--- STRICTER THRESHOLDS (Require 2+ reasons) ---")
is_res, oos_res = evaluate_thresholds(75, 5.0, 2)
print_stats(is_res, "IN-SAMPLE")
print_stats(oos_res, "OUT-OF-SAMPLE")

print("\n--- VERY STRICT THRESHOLDS (RSI > 80, ATR% > 7.0%, 1+ reason) ---")
is_res, oos_res = evaluate_thresholds(80, 7.0, 1)
print_stats(is_res, "IN-SAMPLE")
print_stats(oos_res, "OUT-OF-SAMPLE")

