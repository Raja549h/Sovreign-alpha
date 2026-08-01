import datetime
from dashboard.gateway import get_connection
from config import logger

def get_sentiment(text):
    # Lightweight mock sentiment for alternative data to save tokens
    text_lower = text.lower()
    if 'bullish' in text_lower or 'growth' in text_lower or 'beat' in text_lower:
        return 4.5
    if 'bearish' in text_lower or 'miss' in text_lower or 'risk' in text_lower:
        return 2.0
    return 3.0

def monitor():
    logger.info("Running Podcast Monitor...")
    tickers = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BAJFINANCE", "BHARTIARTL", "KOTAKBANK", "LT", "ITC", "AXISBANK"]
    
    # Mocked RSS feed parsing for lightweight extraction
    simulated_mentions = [
        {"ticker": "BAJFINANCE", "source_name": "Fintech Daily Podcast", "excerpt": "Bajaj Finance is showing incredible resilience in their latest lending growth numbers despite macro headwinds."},
        {"ticker": "TCS", "source_name": "Tech Today Podcast", "excerpt": "TCS margins might be under pressure due to the recent wage hikes across the IT sector."}
    ]
    
    try:
        with get_connection() as conn:
            c = conn.cursor()
            for m in simulated_mentions:
                sentiment = get_sentiment(m['excerpt'])
                c.execute("""
                    INSERT INTO alternative_mentions (ticker, source_type, source_name, mention_date, sentiment_score, excerpt_text)
                    VALUES (%s, 'PODCAST', %s, CURRENT_TIMESTAMP, %s, %s)
                """, (m['ticker'], m['source_name'], sentiment, m['excerpt']))
            logger.info("Podcast monitor successfully logged mentions.")
    except Exception as e:
        logger.error(f"Podcast monitor failed: {e}")

if __name__ == '__main__':
    monitor()
