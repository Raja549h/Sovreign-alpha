"""
Step 2: Bulk Deal <-> Veto Matcher
Cross-references institutional bulk deals against the veto_archive,
applies a 30-day lookback window, fetches 10-trading-day forward price data
using the NSE trading calendar, and gates on a <= -5% drawdown.
"""

import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


def get_vetoes() -> pd.DataFrame:
    """Fetch all vetoes from the Aiven database."""
    load_dotenv(override=True)
    url = os.environ.get('DATABASE_URL') or os.environ.get('AIVEN_DATABASE_URL')
    if not url:
        raise RuntimeError("DATABASE_URL or AIVEN_DATABASE_URL is not set.")
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT veto_id, asset, timestamp, rejection_reason FROM veto_archive")
    vetoes = cur.fetchall()
    conn.close()
    print(f"  Loaded {len(vetoes)} vetoes from database.")
    return pd.DataFrame(vetoes)


def find_matches(deals_df: pd.DataFrame, vetoes_df: pd.DataFrame) -> list:
    """Find deals that occurred within 30 days after a veto on the same ticker."""
    # Clean veto asset names: strip .NS suffix
    vetoes_df = vetoes_df.copy()
    vetoes_df['asset_clean'] = vetoes_df['asset'].astype(str).str.replace('.NS', '', regex=False)

    # Normalize timestamps to tz-naive
    vetoes_df['timestamp'] = pd.to_datetime(vetoes_df['timestamp'], utc=True).dt.tz_localize(None)

    matches = []
    for _, deal in deals_df.iterrows():
        ticker = deal['ticker']
        deal_date = deal['deal_date']

        # Find vetoes for the same ticker
        v_match = vetoes_df[vetoes_df['asset_clean'] == ticker]

        for _, v in v_match.iterrows():
            veto_date = v['timestamp']
            days_diff = (deal_date - veto_date).days

            if 0 <= days_diff <= 30:
                matches.append({
                    'ticker': ticker,
                    'deal_date': deal_date,
                    'client_name': deal['client_name'],
                    'action': deal['action'],
                    'deal_price': deal['deal_price'],
                    'veto_date': veto_date,
                    'rejection_reason': v['rejection_reason'],
                    'veto_id': v['veto_id']
                })

    return matches


def compute_drawdowns(matches: list) -> list:
    """
    For each match, fetch the 10-trading-day forward price window
    using the NSE calendar and compute the max drawdown from deal_price.
    """
    cal = mcal.get_calendar('NSE')
    results = []

    for i, m in enumerate(matches):
        ticker_ns = m['ticker'] + ".NS"
        start = m['deal_date']

        # Get 10 actual trading days forward
        schedule = cal.schedule(start_date=start, end_date=start + timedelta(days=25))
        if schedule.empty:
            print(f"    [{i+1}] {ticker_ns}: No trading days found. Skipping.")
            continue

        trading_days = schedule.index[:10]
        if len(trading_days) == 0:
            continue
        end_date = trading_days[-1]

        # Fetch price data
        try:
            hist = yf.download(
                ticker_ns,
                start=start.strftime('%Y-%m-%d'),
                end=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                progress=False,
                auto_adjust=True
            )
        except Exception as e:
            print(f"    [{i+1}] {ticker_ns}: yfinance error: {e}")
            continue

        if hist.empty:
            print(f"    [{i+1}] {ticker_ns}: No price data returned.")
            continue

        # Handle yfinance multi-level columns (ticker in second level)
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)

        deal_price = float(m['deal_price'])
        min_low = float(hist['Low'].min())
        drawdown_pct = ((min_low - deal_price) / deal_price) * 100

        if drawdown_pct <= -5.0:
            m['drawdown_pct'] = round(drawdown_pct, 2)
            m['min_price_10d'] = round(min_low, 2)
            m['forward_end_date'] = end_date.strftime('%Y-%m-%d')
            results.append(m)
            print(f"    [{i+1}] {ticker_ns}: NOTABLE drawdown {drawdown_pct:.2f}%")
        else:
            print(f"    [{i+1}] {ticker_ns}: drawdown {drawdown_pct:.2f}% (below -5% threshold, skipped)")

    return results


def process_matches():
    """Main entry point for Step 2."""
    print("[Step 2] Matching bulk deals against veto archive...")

    csv_path = 'institutional_bulk_deals.csv'
    if not os.path.exists(csv_path):
        print(f"  ERROR: {csv_path} not found. Run Step 1 first.")
        return

    deals_df = pd.read_csv(csv_path)
    deals_df['deal_date'] = pd.to_datetime(deals_df['deal_date'])
    print(f"  Loaded {len(deals_df)} institutional deals from CSV.")

    vetoes_df = get_vetoes()
    if vetoes_df.empty:
        print("  No vetoes found in database. Nothing to match.")
        return

    matches = find_matches(deals_df, vetoes_df)
    if not matches:
        print("  No Autopsy matches found (no deal occurred within 30 days of a veto).")
        return

    print(f"  Found {len(matches)} potential matches. Computing forward drawdowns...")
    results = compute_drawdowns(matches)

    if not results:
        print("[Step 2] COMPLETE: No matches met the <= -5% drawdown gate.")
        return

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('drawdown_pct', ascending=True)
    out_path = "autopsy_matches.csv"
    results_df.to_csv(out_path, index=False)
    print(f"[Step 2] SUCCESS: {len(results_df)} notable matches saved to {out_path}")
    print(results_df[['ticker', 'client_name', 'action', 'deal_date', 'drawdown_pct']].to_string())


if __name__ == '__main__':
    process_matches()
