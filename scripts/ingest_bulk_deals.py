"""
Step 1: NSE Bulk Deal Ingestion
Fetches institutional bulk deals from NSE via nselib, filters retail noise,
and outputs a clean CSV for downstream matching.
"""

import pandas as pd
import re
import time
from datetime import datetime, timedelta
from nselib import capital_market


INSTITUTIONAL_PATTERN = re.compile(
    r"(?:LTD|PVT\s*LTD|CAPITAL|AIF|FUND|INVESTMENTS?|HOLDINGS?|ASSET|MANAGEMENT)",
    re.IGNORECASE
)

COLUMN_MAP = {
    'Date': 'deal_date',
    'Symbol': 'ticker',
    'ClientName': 'client_name',
    'Buy/Sell': 'action',
    'QuantityTraded': 'quantity',
    'TradePrice/Wght.Avg.Price': 'deal_price'
}

OUTPUT_COLUMNS = ['deal_date', 'ticker', 'client_name', 'action', 'quantity', 'deal_price']


def fetch_bulk_deals_with_retry(from_str: str, to_str: str, retries: int = 5) -> pd.DataFrame:
    """Fetch bulk deals from NSE with exponential backoff retry."""
    for attempt in range(1, retries + 1):
        print(f"  Attempt {attempt}/{retries}: fetching bulk deals {from_str} -> {to_str} ...")
        try:
            df = capital_market.bulk_deal_data(from_date=from_str, to_date=to_str)
            if df is not None and not df.empty:
                print(f"  Fetched {len(df)} raw rows.")
                return df
            print("  Empty response from NSE. Retrying...")
        except Exception as e:
            print(f"  nselib error: {e}")
        time.sleep(2 * attempt)

    print("  All retry attempts exhausted.")
    return pd.DataFrame()


def ingest_bulk_deals(days_back: int = 30) -> pd.DataFrame:
    """
    Ingest NSE bulk deals for the last `days_back` days,
    filter to institutional-only clients, and return a clean DataFrame.
    """
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)

    to_str = to_date.strftime("%d-%m-%Y")
    from_str = from_date.strftime("%d-%m-%Y")

    print(f"[Step 1] Ingesting NSE bulk deals ({from_str} to {to_str})...")
    raw_df = fetch_bulk_deals_with_retry(from_str, to_str)

    if raw_df.empty:
        print("[Step 1] FAILED: No bulk deals fetched.")
        return raw_df

    # Rename columns to clean schema
    df = raw_df.rename(columns=COLUMN_MAP)
    df = df[OUTPUT_COLUMNS]

    # Clean numeric columns
    df['quantity'] = pd.to_numeric(
        df['quantity'].astype(str).str.replace(',', '', regex=False),
        errors='coerce'
    )
    df['deal_price'] = pd.to_numeric(
        df['deal_price'].astype(str).str.replace(',', '', regex=False),
        errors='coerce'
    )

    # Filter: institutional clients only
    total_before = len(df)
    mask = df['client_name'].astype(str).apply(lambda x: bool(INSTITUTIONAL_PATTERN.search(x)))
    df = df[mask].copy()
    print(f"  Filtered {total_before} total deals -> {len(df)} institutional deals.")

    if df.empty:
        print("[Step 1] No institutional deals found after filtering.")
        return df

    # Standardize dates — nselib returns dates like "21-AUG-2026"
    try:
        df['deal_date'] = pd.to_datetime(df['deal_date'], format='%d-%b-%Y').dt.strftime('%Y-%m-%d')
    except ValueError:
        # Fallback: let pandas infer the format
        df['deal_date'] = pd.to_datetime(df['deal_date'], dayfirst=True).dt.strftime('%Y-%m-%d')

    print(f"[Step 1] SUCCESS: {len(df)} institutional deals ready.")
    return df


if __name__ == "__main__":
    result = ingest_bulk_deals(days_back=30)
    if not result.empty:
        out_path = "institutional_bulk_deals.csv"
        result.to_csv(out_path, index=False)
        print(f"  Saved to {out_path}")
        print(result.head(10).to_string())
    else:
        print("  No output generated.")
