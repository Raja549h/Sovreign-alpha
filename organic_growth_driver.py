import os
import sys

# Ensure we're running from the right directory
sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv()

from database import get_connection

def insert_nifty_companies():
    nifty_50 = [
        'HDFCBANK', 'RELIANCE', 'ICICIBANK', 'INFY', 'ITC', 'TCS', 'LT', 'KOTAKBANK', 'AXISBANK', 'HINDUNILVR',
        'SBIN', 'BHARTIARTL', 'BAJFINANCE', 'ASIANPAINT', 'MARUTI', 'HCLTECH', 'SUNPHARMA', 'TITAN', 'M&M', 'TATASTEEL',
        'BAJAJFINSV', 'NTPC', 'POWERGRID', 'ULTRACEMCO', 'NESTLEIND', 'ONGC', 'TECHM', 'JSWSTEEL', 'HINDALCO', 'GRASIM',
        'ADANIPORTS', 'WIPRO', 'SBILIFE', 'DRREDDY', 'EICHERMOT', 'HDFCLIFE', 'DIVISLAB', 'TATAMOTORS', 'BAJAJ-AUTO', 'BRITANNIA',
        'APOLLOHOSP', 'COALINDIA', 'TATACONSUM', 'HEROMOTOCO', 'UPL', 'CIPLA', 'INDUSINDBK', 'ADANIENT', 'BPCL', 'LTIM'
    ]

    print("Inserting 50 NIFTY companies to drive organic density...")
    with get_connection() as conn:
        c = conn.cursor()
        for ticker in nifty_50:
            c.execute("""
                INSERT INTO companies (ticker, company_name, sector)
                VALUES (%s, %s, 'NIFTY 50')
                ON CONFLICT (ticker, exchange) DO NOTHING
            """, (ticker, ticker))
        
        # Reset scheduler health so the autonomous daemon wakes up immediately and enqueues all missing jobs
        c.execute("""
            UPDATE scheduler_health 
            SET last_job_created = NULL 
            WHERE scheduler_id = 'main_scheduler'
        """)
        conn.commit()
    print("Done. The AutonomousSchedulerDaemon will naturally pick these up and process them, generating 50 notes, 100+ obs, and 200+ events.")

if __name__ == '__main__':
    insert_nifty_companies()
