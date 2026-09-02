import pandas as pd
import numpy as np
import yfinance as yf
import pandas_market_calendars as mcal
from nselib import capital_market
from datetime import datetime, timedelta
import time
from scipy.stats import chi2_contingency
import re

# Parameters
ATR_PERIOD = 14
FORWARD_TRADING_DAYS = 10
DRAWDOWN_GATE_PCT = -5.0
INSTITUTIONAL_RE = re.compile(
    r"(?:LTD|PVT\s*LTD|CAPITAL|AIF|FUND|INVESTMENTS?|HOLDINGS?|ASSET|MANAGEMENT)",
    re.IGNORECASE,
)

print("--- FETCHING VIRGIN HOLDOUT DATA (Jan 2025 - Jul 2025) ---")
# This period has NEVER been touched by the previous backtests or sweeps.

all_dfs = []
chunks = [
    ('01-01-2025', '31-03-2025'),
    ('01-04-2025', '30-06-2025')
]

for from_str, to_str in chunks:
    print(f"Fetching bulk deals from {from_str} to {to_str}...")
    for attempt in range(3):
        try:
            df = capital_market.bulk_deal_data(from_date=from_str, to_date=to_str)
            if df is not None and not df.empty:
                all_dfs.append(df)
                print(f"  OK: {len(df)} rows")
                break
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                print(f"  FAIL: {e}")
    time.sleep(1)

raw_df = pd.concat(all_dfs, ignore_index=True).drop_duplicates()
print(f"\nTotal raw rows in virgin set: {len(raw_df)}")

# Clean and filter
df = raw_df.rename(columns={
    'Date': 'deal_date', 'Symbol': 'ticker', 'ClientName': 'client_name',
    'Buy/Sell': 'action', 'QuantityTraded': 'quantity', 'TradePrice/Wght.Avg.Price': 'deal_price'
})
df['quantity'] = pd.to_numeric(df['quantity'].astype(str).str.replace(',', '', regex=False), errors='coerce')
df['deal_price'] = pd.to_numeric(df['deal_price'].astype(str).str.replace(',', '', regex=False), errors='coerce')
mask = df['client_name'].astype(str).apply(lambda x: bool(INSTITUTIONAL_RE.search(x)))
virgin_deals = df[mask].copy()

try:
    virgin_deals['deal_date'] = pd.to_datetime(virgin_deals['deal_date'], format='%d-%b-%Y')
except:
    virgin_deals['deal_date'] = pd.to_datetime(virgin_deals['deal_date'], dayfirst=True)

# We use the established screening universe
top_tickers = pd.read_csv('bulk_deal_universe.csv')['ticker'].tolist()
virgin_deals = virgin_deals[virgin_deals['ticker'].isin(top_tickers)]

# Deduplicate: 1 deal per ticker per day (largest volume)
virgin_deals = virgin_deals.sort_values('quantity', ascending=False)
virgin_deals = virgin_deals.drop_duplicates(subset=['ticker', 'deal_date'])

print(f"Institutional, universe-matched virgin deals: {len(virgin_deals)}")

def compute_atr(df, period=ATR_PERIOD):
    high, low, close = df['High'], df['Low'], df['Close'].shift(1)
    tr = pd.concat([high - low, (high - close).abs(), (low - close).abs()], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def compute_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

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

print("\nFetching historical price data for virgin period (Oct 2024 - Jul 2025)...")
price_data = {}
for i, ticker in enumerate(top_tickers):
    try:
        pdf = yf.download(f"{ticker}.NS", start='2024-10-01', end='2025-07-31', progress=False, auto_adjust=True)
        if pdf is not None and not pdf.empty:
            if isinstance(pdf.columns, pd.MultiIndex):
                pdf.columns = pdf.columns.get_level_values(0)
            pdf['ATR'] = compute_atr(pdf)
            pdf['RSI'] = compute_rsi(pdf)
            price_data[ticker] = pdf
    except:
        pass

print(f"Fetched prices for {len(price_data)} tickers.")

# ---------------------------------------------------------------------------
# EXACT VERY STRICT MODEL - NO TUNING
# ---------------------------------------------------------------------------
print("\n--- EVALUATING VERY STRICT MODEL ON VIRGIN HOLDOUT ---")
tp = fp = fn = tn = 0

for _, deal in virgin_deals.iterrows():
    ticker = deal['ticker']
    deal_date = deal['deal_date']
    deal_price = float(deal['deal_price'])
    
    if ticker not in price_data: continue
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
        
    atr_pct = (atr/close)*100
    
    # Very Strict Model Logic
    reasons = []
    if rsi > 80: reasons.append('rsi')
    if deal_price > close + atr: reasons.append('premium')
    if atr_pct > 7.0: reasons.append('atr_pct')
    
    if len(historical) >= 50:
        sma50 = float(historical['Close'].tail(50).mean())
        if close < sma50 * 0.97: reasons.append('sma50')
    if len(historical) >= 20:
        p20 = float(historical['Close'].iloc[-20])
        if (close - p20)/p20 * 100 < -10: reasons.append('mom')
        
    is_vetoed = len(reasons) >= 1
    did_crash = dd <= DRAWDOWN_GATE_PCT
    
    if is_vetoed and did_crash: tp += 1
    if is_vetoed and not did_crash: fp += 1
    if not is_vetoed and did_crash: fn += 1
    if not is_vetoed and not did_crash: tn += 1

total = tp + fp + fn + tn
if total == 0:
    print("No valid deals evaluated.")
else:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    base_rate = (tp + fn) / total
    
    obs = np.array([[tp, fp], [fn, tn]])
    chi2, p, _, _ = chi2_contingency(obs, correction=False)
    
    print(f"Total Evaluated: {total}")
    print(f"Base Crash Rate: {base_rate:.1%}")
    print(f"Veto Rate:       {(tp+fp)/total:.1%}")
    print()
    print(f"Precision:       {precision:.1%}")
    print(f"Sensitivity:     {sensitivity:.1%}")
    print(f"Specificity:     {specificity:.1%}")
    print()
    print(f"Toxicity Edge:   {precision - base_rate:+.1%}")
    print(f"Chi2 p-value:    {p:.4f}")
    if p < 0.05:
        print("RESULT: STATISTICALLY SIGNIFICANT OUT OF SAMPLE.")
    else:
        print("RESULT: NOT STATISTICALLY SIGNIFICANT. (Noise / Curve-Fit)")
