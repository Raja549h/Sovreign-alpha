import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd

load_dotenv()

def main():
    url = os.environ.get('DATABASE_URL') or os.environ.get('AIVEN_DATABASE_URL')
    if not url:
        print("Error: Database URL not found.")
        return
        
    conn = psycopg2.connect(url)
    c = conn.cursor(cursor_factory=RealDictCursor)
    
    # Query active trades
    c.execute("""
        SELECT asset, timestamp, trade_signal, entry_price, target_price
        FROM prediction_ledger
        WHERE status = 'active' AND entry_price IS NOT NULL AND entry_price > 0
    """)
    active_trades = c.fetchall()
    conn.close()

    if not active_trades:
        print("No active trades found.")
        return

    unique_assets = list(set([t['asset'] for t in active_trades]))
    
    # Batch fetch prices for speed
    try:
        df = yf.download(unique_assets, period="5d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            close_prices = df['Close'].iloc[-1].to_dict()
        else:
            close_prices = {unique_assets[0]: df['Close'].iloc[-1]} if len(unique_assets) == 1 else df['Close'].iloc[-1].to_dict()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
        
    results = []
    for row in active_trades:
        asset = row['asset']
        current_price = close_prices.get(asset)
        if current_price is None or pd.isna(current_price):
            continue
        
        entry = float(row['entry_price'])
        target = float(row['target_price']) if row.get('target_price') else 0.0
        signal = str(row.get('trade_signal', 'BUY')).upper()
        if signal == 'NONE' or not signal:
            signal = 'BUY'
            
        if signal in ('SHORT', 'SELL'):
            ret = (entry - current_price) / entry * 100
        else:
            ret = (current_price - entry) / entry * 100
            
        entry_date = str(row['timestamp'])[:10]
        
        results.append({
            'Ticker': asset,
            'Entry Date': entry_date,
            'Entry Price': entry,
            'Current Price': float(current_price),
            'Floating Return (%)': ret,
            'Target Price': target
        })
        
    # Sort by floating return desc
    results.sort(key=lambda x: x['Floating Return (%)'], reverse=True)
    
    # Print top 15
    print("\nTOP 15 MOST PROFITABLE ACTIVE TRADES")
    print("-" * 103)
    print(f"{'Ticker':<15} | {'Entry Date':<12} | {'Entry Price':<12} | {'Current Price':<14} | {'Floating Return (%)':<20} | {'Target Price':<12}")
    print("-" * 103)
    
    for r in results[:15]:
        print(f"{r['Ticker']:<15} | {r['Entry Date']:<12} | {r['Entry Price']:<12.2f} | {r['Current Price']:<14.2f} | {r['Floating Return (%)']:>7.2f}%              | {r['Target Price']:<12.2f}")
    print("-" * 103)

if __name__ == "__main__":
    main()
