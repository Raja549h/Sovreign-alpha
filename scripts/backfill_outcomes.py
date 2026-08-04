import os
import sys
from datetime import datetime, timezone, timedelta

# Add the project root to sys.path so we can import dashboard.gateway
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.gateway import get_connection
import yfinance as yf
import re

def backfill_outcomes():
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # We need to fetch all cleared predictions that don't have an outcome
        c.execute("""
            SELECT id, prediction_id, asset, timestamp, confidence_score, thesis,
                   expected_timeline_days, status, trade_signal, entry_price, 
                   target_price, stop_loss
            FROM prediction_ledger
            WHERE status = 'cleared' AND actual_outcome IS NULL
        """)
        
        columns = [col[0] for col in c.description]
        predictions = [dict(zip(columns, row)) for row in c.fetchall()]
        
        now = datetime.now(timezone.utc)
        resolved_count = 0
        
        print(f"Found {len(predictions)} cleared predictions to backfill.")
        
        for pred in predictions:
            ticker = pred.get('asset', '')
            if not ticker or len(ticker) < 2:
                continue

            yf_ticker = ticker
            if not ticker.endswith('.NS') and not ticker.endswith('.BO') and '.' not in ticker:
                yf_ticker = f"{ticker}.NS"
                
            try:
                stock = yf.Ticker(yf_ticker)
                hist = stock.history(period='5d')
                if hist.empty:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='5d')
                if hist.empty:
                    print(f"[{ticker}] No price data found.")
                    continue
                current_price = float(hist['Close'].iloc[-1])
            except Exception as e:
                print(f"[{ticker}] YFinance Error: {e}")
                continue

            # Resolve entry price
            entry_price = pred.get('entry_price')
            target_price = pred.get('target_price')
            stop_loss = pred.get('stop_loss')
            signal = pred.get('trade_signal')
            thesis = str(pred.get('thesis', ''))
            
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

            if entry_price is None or entry_price <= 0:
                print(f"[{ticker}] Skipping. Could not determine entry_price.")
                continue

            # Decide outcome
            if signal == 'SHORT' or 'sell' in thesis.lower() or 'short' in thesis.lower():
                is_short = True
                actual_return = round((entry_price - current_price) / entry_price * 100, 2)
            else:
                is_short = False
                actual_return = round((current_price - entry_price) / entry_price * 100, 2)

            outcome = None
            if target_price and stop_loss:
                if is_short:
                    if current_price <= target_price:
                        outcome = 'HIT'
                    elif current_price >= stop_loss:
                        outcome = 'MISS'
                else:
                    if current_price >= target_price:
                        outcome = 'HIT'
                    elif current_price <= stop_loss:
                        outcome = 'MISS'

            # Calculate days elapsed to see if we should force expiration
            pred_time = pred.get('timestamp', '')
            timeline_days = pred.get('expected_timeline_days') or 30
            try:
                if 'T' in str(pred_time):
                    pred_dt = datetime.fromisoformat(str(pred_time).replace('Z', '+00:00'))
                else:
                    pred_dt = datetime.strptime(str(pred_time)[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except Exception:
                pred_dt = now - timedelta(days=60)
            
            days_elapsed = (now - pred_dt).days

            if outcome is None:
                if days_elapsed >= timeline_days:
                    outcome = 'HIT' if actual_return > 0 else 'MISS'
                else:
                    # In backfill, let's force outcome based on current return to ensure we populate stats
                    outcome = 'HIT' if actual_return > 0 else 'MISS'
                    print(f"[{ticker}] Within range but backfill forces resolution. return={actual_return}%")

            notes = f"BACKFILL - Entry: {entry_price:.2f}, Current: {current_price:.2f}, Return: {actual_return:+.2f}%"
            
            # Update prediction
            c.execute("""
                UPDATE prediction_ledger
                SET actual_outcome = %s, actual_return_pct = %s, 
                    outcome_notes = %s, resolved_at = %s, updated_at = %s
                WHERE id = %s
            """, (outcome, actual_return, notes, now.isoformat(), now.isoformat(), pred['id']))
            conn.commit()
            
            print(f"[{ticker}] Updated: {outcome} ({actual_return}%)")
            resolved_count += 1
            
        print(f"Finished backfilling {resolved_count} predictions.")
        
    except Exception as e:
        print(f"Error during backfill: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    backfill_outcomes()
