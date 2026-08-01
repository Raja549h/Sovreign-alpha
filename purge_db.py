import os
from dashboard.gateway import get_db_connection

def purge_us_tickers():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM prediction_ledger WHERE asset IN ('AVGO', 'UNH', 'LLY', 'AAPL', 'AMZN', 'META', 'MSFT', 'GOOGL', 'GS', 'JPM', 'BTC-USD', 'TSLA', 'GME', 'AMC', 'MS', 'AMD', 'TSM', 'CVX', 'XOM', 'NVDA');")
            pred_count = c.rowcount
            
            c.execute("DELETE FROM observations WHERE ticker IN ('AVGO', 'UNH', 'LLY', 'AAPL', 'AMZN', 'META', 'MSFT', 'GOOGL', 'GS', 'JPM', 'BTC-USD', 'TSLA', 'GME', 'AMC', 'MS', 'AMD', 'TSM', 'CVX', 'XOM', 'NVDA');")
            obs_count = c.rowcount
            
            c.execute("DELETE FROM veto_archive WHERE asset IN ('AVGO', 'UNH', 'LLY', 'AAPL', 'AMZN', 'META', 'MSFT', 'GOOGL', 'GS', 'JPM', 'BTC-USD', 'TSLA', 'GME', 'AMC', 'MS', 'AMD', 'TSM', 'CVX', 'XOM', 'NVDA');")
            veto_count = c.rowcount
            
            conn.commit()
            print(f"Purged {pred_count} from prediction_ledger")
            print(f"Purged {obs_count} from observations")
            print(f"Purged {veto_count} from veto_archive")
            
    except Exception as e:
        print(f"Error purging: {e}")

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    purge_us_tickers()
