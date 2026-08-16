import sys
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

# Add project root to path to import engine
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.risk_and_timing import calculate_execution

# Configure logging for clear terminal output
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def fetch_screener_candidates(screener_url: str) -> list:
    """
    Scrapes the main results table from a public Screener.in URL using pandas.read_html
    with a BeautifulSoup flavor. Cleans the dataframe and returns a list of stock 
    tickers with '.NS' appended for Yahoo Finance compatibility.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(screener_url, headers=headers)
    response.raise_for_status()
    
    import io
    # Use pandas to read html tables as requested (flavor bs4)
    # This validates the table exists on the page
    try:
        tables = pd.read_html(io.StringIO(response.text), flavor='bs4')
        if not tables:
            return []
    except ValueError:
        return []
        
    # While pandas extracts the text, the actual ticker symbols on screener.in
    # are embedded in the anchor tags' href attribute. We use BeautifulSoup 
    # to extract these cleanly.
    soup = BeautifulSoup(response.text, 'html.parser')
    tickers = []
    
    table = soup.find('table')
    if not table:
        return []
        
    for a in table.find_all('a', href=True):
        href = a['href']
        if href.startswith('/company/') and href.endswith('/'):
            parts = href.split('/')
            if len(parts) >= 3:
                ticker = parts[2]
                if ticker and ticker not in tickers:
                    tickers.append(ticker)
                    
    # Append .NS to names for Yahoo Finance compatibility
    ns_tickers = [f"{t}.NS" for t in tickers]
    return ns_tickers

def main():
    screener_url = 'https://www.screener.in/screens/3879109/sovereign-4d-guidance-vs-execution/'
    portfolio_value = 1000000.0  # ₹1,000,000 as requested
    
    logger.info("=" * 60)
    logger.info("SOVEREIGN ALPHA - END-TO-END SCREENER PIPELINE")
    logger.info("=" * 60)
    logger.info(f"Fetching candidates from: {screener_url}")
    
    tickers = fetch_screener_candidates(screener_url)
    logger.info(f"Found {len(tickers)} candidates: {', '.join(tickers)}")
    logger.info("-" * 60)
    
    triggered_stocks = []
    
    for ticker in tickers:
        # Run the Risk_and_Timing module (which fetches 60-day yf data, calculates SMA/ATR, and Kelly sizing)
        result = calculate_execution(ticker, portfolio_value)
        
        # Check if the "BUY TRIGGER" gate is True
        if result.get('success') and result.get('buy_trigger_met'):
            triggered_stocks.append(result)
            
    logger.info("\n" + "=" * 60)
    logger.info("EXECUTION TARGETS (BUY TRIGGER = TRUE)")
    logger.info("=" * 60)
    
    if not triggered_stocks:
        logger.info("No stocks passed the timing criteria today.")
    else:
        for trade in triggered_stocks:
            logger.info(f"Ticker:                      {trade['ticker']}")
            logger.info(f"Entry Price:                 {trade['current_close']}")
            logger.info(f"Stop Loss Price:             {trade['stop_loss']}")
            logger.info(f"Kelly Capital Allocation %:  {trade['safe_allocation_pct']}%")
            logger.info(f"Exact Number of Shares:      {trade['shares_to_buy']}")
            logger.info("-" * 40)

if __name__ == '__main__':
    main()
