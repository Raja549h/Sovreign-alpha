import sys
sys.path.insert(0, 'C:/Users/lokes/Downloads/project/sovereign-alpha')
from dotenv import load_dotenv
load_dotenv()
from database import get_connection, init_pool

def purge_us_tickers():
    init_pool()
    conn = get_connection()
    c = conn.cursor()
    
    tickers = ('TSM', 'AVGO', 'AMD', 'CVX', 'XOM', 'UNI', 'LLY', 'MS', 'MSFT')
    
    print("Purging US tickers from observations...")
    c.execute(f"DELETE FROM observations WHERE ticker IN {tickers}")
    print(f"Deleted {c.rowcount} rows from observations.")
            
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == '__main__':
    purge_us_tickers()
