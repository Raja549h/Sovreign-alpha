import os
import sys
import re
from datetime import datetime, timezone
import yfinance as yf
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.db import get_connection

def resolve_predictions():
    try:
        with get_connection() as conn:
            c = conn.cursor(cursor_factory=RealDictCursor)
            
            print("Running historical database patch...")
            c.execute("""
                UPDATE prediction_ledger
                SET status = 'active'
                WHERE status = 'cleared'
                  AND (actual_outcome IS NULL OR actual_outcome IN ('None', 'indeterminate', ''))
            """)
            patched_count = c.rowcount
            print(f"Patched {patched_count} 'cleared' rows to 'active'.")
            
            c.execute("""
                SELECT id, asset, timestamp, entry_price, target_price, stop_loss, trade_signal, thesis
                FROM prediction_ledger
                WHERE status = 'active'
            """)
            
            predictions = c.fetchall()
            print(f"Found {len(predictions)} active predictions to check.")
            
            now = datetime.now(timezone.utc)
            
            for pred in predictions:
                ticker = pred['asset']
                if not ticker:
                    continue
                
                yf_ticker = ticker if (ticker.endswith('.NS') or ticker.endswith('.BO') or '.' in ticker) else f"{ticker}.NS"
                
                pred_time = pred['timestamp']
                if 'T' in str(pred_time):
                    pred_dt = datetime.fromisoformat(str(pred_time).replace('Z', '+00:00'))
                else:
                    pred_dt = datetime.strptime(str(pred_time)[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    
                entry_date_str = pred_dt.strftime('%Y-%m-%d')
                
                try:
                    stock = yf.Ticker(yf_ticker)
                    hist = stock.history(start=entry_date_str)
                    if hist.empty:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(start=entry_date_str)
                except Exception as e:
                    print(f"[{ticker}] YFinance Error: {e}")
                    continue
                    
                if hist.empty:
                    print(f"[{ticker}] No history found starting {entry_date_str}")
                    continue
                
                thesis = str(pred['thesis'])
                entry_price = float(pred['entry_price']) if pred['entry_price'] else None
                if entry_price is None or entry_price <= 0:
                    price_patterns = [
                        r'entry.*?(\d+[,.]?\d+)',
                        r'price.*?(\d+[,.]?\d+)',
                        r'₹\s*(\d+[,.]?\d+)',
                        r'INR\s*(\d+[,.]?\d+)',
                    ]
                    for pat in price_patterns:
                        match = re.search(pat, thesis, re.IGNORECASE)
                        if match:
                            try:
                                entry_price = float(match.group(1).replace(',', ''))
                                if entry_price > 10:
                                    break
                            except ValueError:
                                entry_price = None
                
                if not entry_price:
                    # Can't calculate P/L without an entry price. Skip.
                    continue

                target = float(pred['target_price']) if pred['target_price'] else None
                stop = float(pred['stop_loss']) if pred['stop_loss'] else None
                
                signal = str(pred['trade_signal']).upper() if pred['trade_signal'] else 'BUY'
                if not signal or signal == 'NONE':
                    if 'sell' in thesis.lower() or 'short' in thesis.lower():
                        signal = 'SHORT'
                    else:
                        signal = 'BUY'
                
                outcome = None
                
                for index, row in hist.iterrows():
                    high = row['High']
                    low = row['Low']
                    
                    if target and stop:
                        if signal == 'SHORT':
                            if low <= target:
                                outcome = 'HIT'
                                break
                            elif high >= stop:
                                outcome = 'MISS'
                                break
                        else:
                            if high >= target:
                                outcome = 'HIT'
                                break
                            elif low <= stop:
                                outcome = 'MISS'
                                break
                
                days_elapsed = (now - pred_dt).days
                if outcome is None and days_elapsed >= 30:
                    outcome = 'EXPIRED'
                    
                if outcome is not None:
                    current_price = float(hist['Close'].iloc[-1])
                    if signal == 'SHORT':
                        actual_return = round(float((entry_price - current_price) / entry_price * 100), 2)
                    else:
                        actual_return = round(float((current_price - entry_price) / entry_price * 100), 2)
                        
                    c.execute("""
                        UPDATE prediction_ledger
                        SET actual_outcome = %s, status = 'resolved', actual_return_pct = %s, updated_at = %s, entry_price = %s
                        WHERE id = %s
                    """, (outcome, actual_return, now.isoformat(), entry_price, pred['id']))
                    
                    print(f"[{ticker}] Resolved as {outcome}")

            conn.commit()

            c.execute("SELECT COUNT(*) as count FROM prediction_ledger WHERE status = 'active'")
            pending_count = c.fetchone()['count']
            
            c.execute("SELECT COUNT(*) as count FROM prediction_ledger WHERE status = 'resolved'")
            resolved_count = c.fetchone()['count']
            
            print("\n--- RESOLUTION STATUS UPDATED ---")
            print(f"Total Pending (Active):   {pending_count}")
            print(f"Total Resolved (Closed):  {resolved_count}")
            print("---------------------------------")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    load_dotenv()
    resolve_predictions()
