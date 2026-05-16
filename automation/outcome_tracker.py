"""
OUTCOME TRACKER — Automatically update prediction outcomes
Runs daily after the main cycle to check predictions from 5 days ago
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).parent.parent
BILLING_DIR = BASE_DIR / "billing"
FUND_DATA_DB = BILLING_DIR / "fund_data.db"


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(FUND_DATA_DB))
    conn.row_factory = sqlite3.Row
    return conn


def track_outcomes():
    """Check predictions from 5 days ago and update outcomes."""
    print("\n[OUTCOME TRACKER] Checking predictions from 5 days ago...")
    
    five_days_ago = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get predictions from 5 days ago that don't have outcomes yet
    c.execute("""
        SELECT * FROM prediction_ledger 
        WHERE timestamp LIKE ? AND (actual_outcome IS NULL OR actual_outcome = '')
    """, (f"{five_days_ago}%",))
    
    predictions = c.fetchall()
    
    if not predictions:
        print("  No predictions to check from 5 days ago")
        conn.close()
        return
    
    print(f"  Found {len(predictions)} predictions to check")
    
    try:
        import yfinance as yf
    except ImportError:
        print("  [ERROR] yfinance not installed")
        conn.close()
        return
    
    updated = 0
    
    for pred in predictions:
        ticker = pred['asset']
        pred_date = pred['timestamp'][:10]
        action = 'BUY' if pred['status'] == 'cleared' else 'HOLD'
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=pred_date, end=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
            
            if len(hist) < 2:
                continue
            
            entry_price = hist.iloc[0]['Close']
            current_price = hist.iloc[-1]['Close']
            return_pct = (current_price - entry_price) / entry_price * 100
            
            # Determine outcome
            if action == 'BUY':
                if return_pct > 1:
                    outcome = 'correct'
                elif return_pct < -1:
                    outcome = 'incorrect'
                else:
                    outcome = 'partial'
            elif action == 'SELL':
                if return_pct < -1:
                    outcome = 'correct'
                elif return_pct > 1:
                    outcome = 'incorrect'
                else:
                    outcome = 'partial'
            else:  # HOLD
                if abs(return_pct) < 1:
                    outcome = 'correct'
                else:
                    outcome = 'partial'
            
            c.execute("""
                UPDATE prediction_ledger SET
                actual_outcome = ?,
                actual_return_pct = ?,
                outcome_notes = ?,
                updated_at = ?
                WHERE prediction_id = ?
            """, (
                outcome,
                round(return_pct, 2),
                f"Auto-tracked: {return_pct:.1f}% return",
                datetime.now().isoformat() + 'Z',
                pred['prediction_id']
            ))
            
            updated += 1
            print(f"  {ticker}: {outcome} ({return_pct:.1f}%)")
            
        except Exception as e:
            print(f"  [ERROR] {ticker}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n  Updated {updated} predictions with outcomes")


if __name__ == '__main__':
    track_outcomes()