"""
run_system_test.py
==================
Live integration test runner for Sovereign Alpha.

Flow:
  1. Scrape the public Screener.in screen to get candidate tickers.
  2. Take the top 5 candidates.
  3. For each, run calculate_execution(ticker, 1_000_000).
  4. Display all results (pass or fail) in a clean console table.
"""

import sys
import io
import logging
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.risk_and_timing import calculate_execution, MAX_POSITION_PCT

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-5s | %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCREENER_URL = (
    'https://www.screener.in/screens/3879109/'
    'sovereign-4d-guidance-vs-execution/'
)
PORTFOLIO_VALUE = 1_000_000.0   # INR 10 Lakh
TOP_N = 5                       # Only process first N candidates


# ============================================================================
# Part 1 – Screener ingestion
# ============================================================================

def fetch_screener_candidates(screener_url: str) -> list[str]:
    """
    Scrape the results table from a public Screener.in URL.

    Uses pandas.read_html (flavor='bs4') to validate the table,
    then BeautifulSoup to extract ticker symbols from the anchor hrefs
    (Screener embeds tickers in /company/<TICKER>/ links).

    Returns a list of tickers with '.NS' appended for Yahoo Finance.
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/126.0 Safari/537.36'
        )
    }

    logger.info('Requesting Screener page ...')
    resp = requests.get(screener_url, headers=headers, timeout=15)
    resp.raise_for_status()

    # Validate that the page contains at least one HTML table
    try:
        tables = pd.read_html(io.StringIO(resp.text), flavor='bs4')
        logger.info(f'pandas.read_html found {len(tables)} table(s)')
    except ValueError:
        logger.error('No tables found on the page.')
        return []

    # Extract ticker symbols from anchor tags inside the first <table>
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table')
    if table is None:
        logger.error('BeautifulSoup could not locate a <table> element.')
        return []

    tickers: list[str] = []
    for anchor in table.find_all('a', href=True):
        href = anchor['href']
        if href.startswith('/company/') and href.endswith('/'):
            symbol = href.split('/')[2]
            if symbol and symbol not in tickers:
                tickers.append(symbol)

    ns_tickers = [f'{t}.NS' for t in tickers]
    logger.info(f'Extracted {len(ns_tickers)} unique tickers')
    return ns_tickers


# ============================================================================
# Part 2 – Execution loop
# ============================================================================

def run_integration(tickers: list[str], portfolio: float) -> list[dict]:
    """
    Run calculate_execution on each ticker and collect the results.
    """
    results: list[dict] = []
    for i, ticker in enumerate(tickers, 1):
        logger.info(f'[{i}/{len(tickers)}] Processing {ticker} ...')
        t0 = time.perf_counter()
        result = calculate_execution(ticker, portfolio)
        elapsed = time.perf_counter() - t0
        result['_elapsed_s'] = round(elapsed, 2)
        results.append(result)
    return results


# ============================================================================
# Part 3 – Pretty table output
# ============================================================================

def print_table(results: list[dict]) -> None:
    """
    Format and print a clean console table of all processed tickers,
    regardless of whether the buy trigger fired.
    """
    # Column specs: (header, key, width, fmt)
    columns = [
        ('Ticker',           'ticker',              14, 's'),
        ('Close (INR)',      'current_close',       13, '.2f'),
        ('SMA 20 (INR)',     'sma_20',              13, '.2f'),
        ('ATR 14 (INR)',     'atr_14',              13, '.2f'),
        ('Breakout Tgt',     'buy_threshold',       13, '.2f'),
        ('Buy Trigger',      'buy_trigger_met',     12, 's'),
        ('Stop Loss (INR)',  'stop_loss',           15, '.2f'),
        ('Alloc Capital',    'capital_allocated',   15, '.2f'),
        ('Shares',           'shares_to_buy',        8, 'd'),
    ]

    header = ' | '.join(h.center(w) for h, _, w, _ in columns)
    sep    = '-+-'.join('-' * w for _, _, w, _ in columns)

    print()
    print('=' * len(sep))
    print('SOVEREIGN ALPHA  -  LIVE INTEGRATION TEST')
    print('=' * len(sep))
    print(header)
    print(sep)

    for r in results:
        if not r.get('success'):
            # Print a short error row for failed tickers
            ticker = r.get('ticker', '???')
            err    = r.get('error', 'unknown error')
            print(f' {ticker:<14}| ** SKIPPED: {err}')
            continue

        cells: list[str] = []
        for _, key, width, fmt in columns:
            val = r[key]
            if key == 'buy_trigger_met':
                val = 'TRUE' if val else 'FALSE'
                fmt = 's'
            cells.append(f'{val:{fmt}}'.center(width))
        print(' | '.join(cells))

    print(sep)
    print()


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    logger.info('=' * 60)
    logger.info('SOVEREIGN ALPHA  -  SYSTEM INTEGRATION TEST')
    logger.info('=' * 60)

    # Step 1 – Scrape
    all_tickers = fetch_screener_candidates(SCREENER_URL)
    if not all_tickers:
        logger.error('No tickers scraped. Aborting.')
        sys.exit(1)

    # Step 2 – Take top N
    tickers = all_tickers[:TOP_N]
    logger.info(f'Processing top {TOP_N}: {", ".join(tickers)}')

    # Step 3 – Execute
    results = run_integration(tickers, PORTFOLIO_VALUE)

    # Step 4 – Display
    print_table(results)

    # Summary stats
    ok    = [r for r in results if r.get('success')]
    buys  = [r for r in ok if r.get('buy_trigger_met')]
    fails = [r for r in results if not r.get('success')]

    logger.info(f'Processed: {len(ok)}/{len(results)} succeeded, '
                f'{len(buys)} buy triggers, {len(fails)} failures')

    # Assertions (will cause a non-zero exit if violated)
    for r in ok:
        assert isinstance(r['shares_to_buy'], int), \
            f"{r['ticker']}: shares_to_buy is not int"
        assert r['safe_allocation_pct'] <= MAX_POSITION_PCT * 100 + 0.01, \
            f"{r['ticker']}: allocation {r['safe_allocation_pct']}% exceeds cap"
        assert r['stop_loss'] < r['current_close'], \
            f"{r['ticker']}: stop_loss >= entry price"

    logger.info('All assertions passed.')


if __name__ == '__main__':
    main()
