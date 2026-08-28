import os
import sys
from datetime import datetime, timezone, timedelta
import yfinance as yf
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.db import get_connection

def rescue_null_bounds():
    try:
        with get_connection() as conn:
            c = conn.cursor(cursor_factory=RealDictCursor)
            
            c.execute("""
                SELECT id, asset, timestamp, trade_signal 
                FROM prediction_ledger 
                WHERE status = 'active' AND entry_price IS NULL
            """)
            
            rows = c.fetchall()
            print(f"Found {len(rows)} active predictions with NULL entry_price to rescue.")
            
            rescued_count = 0
            
            for row in rows:
                ticker = row['asset']
                if not ticker:
                    continue
                    
                yf_ticker = ticker if (ticker.endswith('.NS') or ticker.endswith('.BO') or '.' in ticker) else f"{ticker}.NS"
                
                pred_time = row['timestamp']
                if 'T' in str(pred_time):
                    pred_dt = datetime.fromisoformat(str(pred_time).replace('Z', '+00:00'))
                else:
                    pred_dt = datetime.strptime(str(pred_time)[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    
                date_str = pred_dt.strftime('%Y-%m-%d')
                end_str = (pred_dt + timedelta(days=3)).strftime('%Y-%m-%d')
                
                try:
                    stock = yf.Ticker(yf_ticker)
                    hist = stock.history(start=date_str, end=end_str)
                    if hist.empty:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(start=date_str, end=end_str)
                except Exception:
                    continue
                    
                if hist.empty:
                    print(f"[{ticker}] Failed to fetch history for date {date_str}")
                    continue
                    
                entry_price = round(float(hist['Close'].iloc[0]), 2)
                
                signal = str(row['trade_signal']).upper() if row['trade_signal'] else 'BUY'
                if signal == 'NONE' or not signal:
                    signal = 'BUY'
                    
                if signal in ('SHORT', 'SELL'):
                    target_price = round(entry_price * 0.91, 2)
                    stop_loss = round(entry_price * 1.03, 2)
                else:
                    target_price = round(entry_price * 1.09, 2)
                    stop_loss = round(entry_price * 0.97, 2)
                    
                c.execute("""
                    UPDATE prediction_ledger
                    SET entry_price = %s, target_price = %s, stop_loss = %s, trade_signal = %s
                    WHERE id = %s
                """, (entry_price, target_price, stop_loss, signal, row['id']))
                
                rescued_count += 1
                print(f"[{ticker}] Rescued! Entry: {entry_price}, Target: {target_price}, Stop: {stop_loss}")
                
            conn.commit()
            print(f"\nSuccessfully rescued and backfilled {rescued_count} predictions.")
            
    except Exception as e:
        print(f"Error during rescue operation: {e}")

if __name__ == '__main__':
    load_dotenv()
    rescue_null_bounds()
