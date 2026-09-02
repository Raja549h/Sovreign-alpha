"""
Sovereign Alpha: Retroactive Bulk Deal Backtest Engine
======================================================
1. Mines 12 months of NSE bulk deal history
2. Identifies the top 150 most-frequent institutional tickers
3. Fetches 6-month price data + computes 14-day ATR for each
4. Applies veto logic retroactively at each bulk deal date
5. Measures 10-trading-day forward drawdown
6. Outputs ranked autopsy matches (drawdown <= -5%)
"""

import pandas as pd
import numpy as np
import yfinance as yf
import pandas_market_calendars as mcal
import re
import time
import os
from datetime import datetime, timedelta
from nselib import capital_market


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
INSTITUTIONAL_RE = re.compile(
    r"(?:LTD|PVT\s*LTD|CAPITAL|AIF|FUND|INVESTMENTS?|HOLDINGS?|ASSET|MANAGEMENT)",
    re.IGNORECASE,
)
TOP_N_TICKERS = 150
LOOKBACK_MONTHS = 12
ATR_PERIOD = 14
ATR_STOP_MULT = 1.5
ATR_TARGET_MULT = 3.0
DRAWDOWN_GATE_PCT = -5.0
FORWARD_TRADING_DAYS = 10
RSI_OVERBOUGHT = 75
RSI_OVERSOLD = 25


# ---------------------------------------------------------------------------
# STEP 1: Mine 12 months of NSE bulk deals
# ---------------------------------------------------------------------------

def fetch_all_bulk_deals(months_back=LOOKBACK_MONTHS):
    """Fetch bulk deals in 90-day chunks going back `months_back` months."""
    all_dfs = []
    end = datetime.now()

    chunks = []
    for i in range(0, months_back * 30, 90):
        chunk_end = end - timedelta(days=i)
        chunk_start = chunk_end - timedelta(days=89)
        chunks.append((chunk_start.strftime('%d-%m-%Y'), chunk_end.strftime('%d-%m-%Y')))

    for from_str, to_str in chunks:
        print(f"  Fetching {from_str} -> {to_str} ...", end=" ", flush=True)
        for attempt in range(3):
            try:
                df = capital_market.bulk_deal_data(from_date=from_str, to_date=to_str)
                if df is not None and not df.empty:
                    all_dfs.append(df)
                    print(f"{len(df)} rows")
                    break
                else:
                    print("empty")
                    break
            except Exception as e:
                if attempt < 2:
                    time.sleep(3)
                else:
                    print(f"FAIL: {e}")
        time.sleep(1)  # rate limit courtesy

    if not all_dfs:
        raise RuntimeError("Could not fetch any bulk deal data from NSE.")

    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.drop_duplicates()
    return combined


def clean_and_filter(raw_df):
    """Rename columns, filter to institutional clients, standardize types."""
    df = raw_df.rename(columns={
        'Date': 'deal_date',
        'Symbol': 'ticker',
        'ClientName': 'client_name',
        'Buy/Sell': 'action',
        'QuantityTraded': 'quantity',
        'TradePrice/Wght.Avg.Price': 'deal_price',
    })
    df = df[['deal_date', 'ticker', 'client_name', 'action', 'quantity', 'deal_price']]

    df['quantity'] = pd.to_numeric(
        df['quantity'].astype(str).str.replace(',', '', regex=False), errors='coerce'
    )
    df['deal_price'] = pd.to_numeric(
        df['deal_price'].astype(str).str.replace(',', '', regex=False), errors='coerce'
    )

    # Institutional filter
    mask = df['client_name'].astype(str).apply(lambda x: bool(INSTITUTIONAL_RE.search(x)))
    df = df[mask].copy()

    # Parse dates
    try:
        df['deal_date'] = pd.to_datetime(df['deal_date'], format='%d-%b-%Y')
    except ValueError:
        df['deal_date'] = pd.to_datetime(df['deal_date'], dayfirst=True)

    return df


def get_top_tickers(deals_df, top_n=TOP_N_TICKERS):
    """Return the top_n most frequently appearing tickers in institutional deals."""
    counts = deals_df['ticker'].value_counts()
    top = counts.head(top_n)
    print(f"\n  Top {len(top)} tickers by bulk deal frequency:")
    for i, (ticker, cnt) in enumerate(top.items()):
        if i < 20 or i >= len(top) - 3:
            print(f"    {i+1:4d}. {ticker:20s}  {cnt:4d} deals")
        elif i == 20:
            print(f"    ... ({len(top) - 23} more) ...")
    return list(top.index)


# ---------------------------------------------------------------------------
# STEP 2: Fetch price data and compute ATR
# ---------------------------------------------------------------------------

def compute_atr(df, period=ATR_PERIOD):
    """Compute Average True Range."""
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    tr = pd.concat([
        high - low,
        (high - close).abs(),
        (low - close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def compute_rsi(df, period=14):
    """Compute RSI."""
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def fetch_price_data(tickers, months_back=8):
    """Download price data for all tickers."""
    end = datetime.now() + timedelta(days=1)
    start = end - timedelta(days=months_back * 30)

    price_data = {}
    total = len(tickers)
    failed = []

    for i, ticker in enumerate(tickers):
        ns_ticker = ticker + ".NS"
        if (i + 1) % 25 == 0 or i == 0:
            print(f"  Fetching prices: {i+1}/{total} ...", flush=True)
        try:
            df = yf.download(
                ns_ticker,
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
                progress=False,
                auto_adjust=True,
            )
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                # Add ATR and RSI
                df['ATR'] = compute_atr(df)
                df['RSI'] = compute_rsi(df)
                price_data[ticker] = df
            else:
                failed.append(ticker)
        except Exception as e:
            failed.append(ticker)

    print(f"  Fetched {len(price_data)}/{total} tickers. Failed: {len(failed)}")
    if failed and len(failed) <= 10:
        print(f"  Failed tickers: {failed}")
    return price_data


# ---------------------------------------------------------------------------
# STEP 3: Retroactive veto logic
# ---------------------------------------------------------------------------

def would_veto(price_df, deal_date, deal_price):
    """
    Apply the ATR-based veto logic at the deal date.
    Returns (should_veto: bool, reason: str, metrics: dict)
    """
    # Get price data up to deal_date
    if price_df.index.tz is not None:
        price_df = price_df.copy()
        price_df.index = price_df.index.tz_localize(None)

    historical = price_df[price_df.index <= deal_date]
    if len(historical) < ATR_PERIOD + 5:
        return False, "Insufficient history", {}

    latest = historical.iloc[-1]
    atr = float(latest.get('ATR', 0))
    rsi = float(latest.get('RSI', 50))
    close = float(latest['Close'])

    if atr <= 0 or np.isnan(atr):
        return False, "ATR unavailable", {}

    # Compute what the target/stop would have been
    target_up = close + (ATR_TARGET_MULT * atr)
    stop_down = close - (ATR_STOP_MULT * atr)
    risk_reward = abs(target_up - close) / abs(close - stop_down) if abs(close - stop_down) > 0 else 0

    reasons = []

    # Veto conditions:
    # 1. RSI extreme overbought (buying into a blow-off top)
    if rsi > RSI_OVERBOUGHT:
        reasons.append(f"RSI overbought at {rsi:.0f}")

    # 2. Deal price significantly above the ATR-implied fair band
    #    (institutional buyer paying a premium > 1 ATR above close)
    if deal_price > close + atr:
        reasons.append(f"Deal price {deal_price:.1f} > close+ATR {close+atr:.1f}")

    # 3. ATR-implied stop is too wide (volatility too high for safe entry)
    atr_pct = (atr / close) * 100
    if atr_pct > 5.0:
        reasons.append(f"ATR {atr_pct:.1f}% of price (extreme volatility)")

    # 4. Price below 50-day SMA (structural downtrend)
    if len(historical) >= 50:
        sma50 = float(historical['Close'].tail(50).mean())
        if close < sma50 * 0.97:
            reasons.append(f"Price {close:.1f} below SMA50 {sma50:.1f} (downtrend)")

    # 5. Recent sharp decline (close dropped > 10% in last 20 days)
    if len(historical) >= 20:
        price_20d_ago = float(historical['Close'].iloc[-20])
        pct_change = (close - price_20d_ago) / price_20d_ago * 100
        if pct_change < -10:
            reasons.append(f"Down {pct_change:.1f}% over 20 days (momentum collapse)")

    should_veto = len(reasons) >= 1
    reason_str = "; ".join(reasons) if reasons else "No veto triggers"

    return should_veto, reason_str, {
        'close': close, 'atr': atr, 'rsi': rsi,
        'atr_pct': atr_pct, 'target': target_up, 'stop': stop_down,
    }


# ---------------------------------------------------------------------------
# STEP 4: Forward drawdown measurement
# ---------------------------------------------------------------------------

def compute_forward_drawdown(price_df, deal_date, deal_price):
    """
    Compute max drawdown from deal_price over the next 10 trading days.
    Uses the NSE trading calendar.
    """
    cal = mcal.get_calendar('NSE')

    if price_df.index.tz is not None:
        price_df = price_df.copy()
        price_df.index = price_df.index.tz_localize(None)

    # Get the next 10 trading days
    schedule = cal.schedule(
        start_date=deal_date,
        end_date=deal_date + timedelta(days=25),
    )
    if schedule.empty:
        return None, None

    trading_days = schedule.index[:FORWARD_TRADING_DAYS]
    if len(trading_days) == 0:
        return None, None
    end_td = trading_days[-1]

    forward = price_df[(price_df.index >= deal_date) & (price_df.index <= end_td)]
    if forward.empty:
        return None, None

    min_low = float(forward['Low'].min())
    drawdown_pct = ((min_low - deal_price) / deal_price) * 100

    last_close = float(forward['Close'].iloc[-1])
    end_return = ((last_close - deal_price) / deal_price) * 100

    return drawdown_pct, end_return


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("  SOVEREIGN ALPHA -- RETROACTIVE BULK DEAL BACKTEST")
    print("=" * 70)
    print()

    # STEP 1: Mine bulk deal history
    print("[1/4] Mining 12 months of NSE bulk deal history...")
    raw = fetch_all_bulk_deals(months_back=LOOKBACK_MONTHS)
    print(f"  Total raw rows: {len(raw)}")

    deals = clean_and_filter(raw)
    print(f"  Institutional deals: {len(deals)}")
    print(f"  Date range: {deals['deal_date'].min().date()} to {deals['deal_date'].max().date()}")

    top_tickers = get_top_tickers(deals, TOP_N_TICKERS)

    # Save the universe for future use
    pd.DataFrame({'ticker': top_tickers}).to_csv('bulk_deal_universe.csv', index=False)
    deals.to_csv('historical_bulk_deals_12m.csv', index=False)

    # STEP 2: Fetch price data
    print(f"\n[2/4] Fetching price data for {len(top_tickers)} tickers...")
    price_data = fetch_price_data(top_tickers, months_back=8)

    # STEP 3: Retroactive veto backtest
    print(f"\n[3/4] Running retroactive veto backtest...")

    # Only process deals from last 6 months for the backtest
    cutoff = datetime.now() - timedelta(days=180)
    recent_deals = deals[deals['deal_date'] >= cutoff].copy()
    recent_deals = recent_deals[recent_deals['ticker'].isin(price_data.keys())]
    print(f"  Deals in backtest window (6 months): {len(recent_deals)}")

    # Deduplicate: one deal per ticker per day (keep largest by quantity)
    recent_deals = recent_deals.sort_values('quantity', ascending=False)
    recent_deals = recent_deals.drop_duplicates(subset=['ticker', 'deal_date'], keep='first')
    print(f"  After dedup (1 per ticker/day): {len(recent_deals)}")

    vetoed = []
    not_vetoed = 0
    no_data = 0

    for idx, (_, deal) in enumerate(recent_deals.iterrows()):
        ticker = deal['ticker']
        deal_date = deal['deal_date']
        deal_price = float(deal['deal_price'])

        if ticker not in price_data:
            no_data += 1
            continue

        pdf = price_data[ticker]
        should_veto, reason, metrics = would_veto(pdf, deal_date, deal_price)

        if should_veto:
            vetoed.append({
                'ticker': ticker,
                'deal_date': deal_date,
                'client_name': deal['client_name'],
                'action': deal['action'],
                'deal_price': deal_price,
                'veto_reason': reason,
                **metrics,
            })
        else:
            not_vetoed += 1

        if (idx + 1) % 200 == 0:
            print(f"    Processed {idx+1}/{len(recent_deals)} deals... ({len(vetoed)} vetoed so far)")

    print(f"  Veto results: {len(vetoed)} vetoed, {not_vetoed} passed, {no_data} no data")

    if not vetoed:
        print("\n  No vetoes generated. Adjust veto thresholds or expand deal window.")
        return

    # STEP 4: Forward drawdown for vetoed deals
    print(f"\n[4/4] Computing 10-day forward drawdown for {len(vetoed)} vetoed deals...")

    autopsy_matches = []

    for i, v in enumerate(vetoed):
        ticker = v['ticker']
        pdf = price_data[ticker]
        deal_date = v['deal_date']
        deal_price = v['deal_price']

        drawdown, end_return = compute_forward_drawdown(pdf, deal_date, deal_price)

        if drawdown is None:
            continue

        v['drawdown_pct'] = round(drawdown, 2)
        v['end_return_pct'] = round(end_return, 2) if end_return is not None else None

        if drawdown <= DRAWDOWN_GATE_PCT:
            autopsy_matches.append(v)

        if (i + 1) % 100 == 0:
            print(f"    Processed {i+1}/{len(vetoed)}... ({len(autopsy_matches)} notable so far)")

    # RESULTS
    print()
    print("=" * 70)
    print("  BACKTEST RESULTS")
    print("=" * 70)

    if not autopsy_matches:
        print(f"  Vetoed deals: {len(vetoed)}")
        print(f"  Notable matches (drawdown <= {DRAWDOWN_GATE_PCT}%): 0")

        # Show the worst drawdowns anyway
        all_with_dd = [v for v in vetoed if 'drawdown_pct' in v]
        if all_with_dd:
            all_with_dd.sort(key=lambda x: x['drawdown_pct'])
            print(f"\n  Closest misses (worst drawdowns that didn't hit -5% gate):")
            for v in all_with_dd[:10]:
                print(f"    {v['ticker']:15s}  deal {str(v['deal_date'])[:10]}  "
                      f"drawdown {v['drawdown_pct']:+.2f}%  reason: {v['veto_reason'][:60]}")
        return

    # Sort by worst drawdown
    autopsy_matches.sort(key=lambda x: x['drawdown_pct'])

    results_df = pd.DataFrame(autopsy_matches)
    results_df.to_csv('autopsy_matches.csv', index=False)

    print(f"  Total vetoed deals:    {len(vetoed)}")
    print(f"  Notable matches:       {len(autopsy_matches)}")
    print(f"  Average drawdown:      {np.mean([m['drawdown_pct'] for m in autopsy_matches]):.2f}%")
    print(f"  Worst drawdown:        {autopsy_matches[0]['drawdown_pct']:.2f}%")
    print()
    print(f"  {'Rank':<5s} {'Ticker':<15s} {'Deal Date':<12s} {'Client':<35s} {'DD%':>8s} {'Reason'}")
    print(f"  {'-'*5} {'-'*15} {'-'*12} {'-'*35} {'-'*8} {'-'*40}")

    for i, m in enumerate(autopsy_matches[:25]):
        client = str(m['client_name'])[:33]
        reason = str(m['veto_reason'])[:40]
        print(f"  {i+1:<5d} {m['ticker']:<15s} {str(m['deal_date'])[:10]:<12s} "
              f"{client:<35s} {m['drawdown_pct']:>+7.2f}% {reason}")

    print()
    print(f"  Results saved to: autopsy_matches.csv")
    print(f"  Ticker universe saved to: bulk_deal_universe.csv")
    print("=" * 70)


if __name__ == '__main__':
    main()
