import datetime
from engine.db import get_connection
from config import logger

def get_sentiment(text):
    text_lower = text.lower()
    if 'upgrade' in text_lower or 'outperform' in text_lower:
        return 4.5
    if 'downgrade' in text_lower or 'underperform' in text_lower:
        return 2.0
    return 3.0

def monitor():
    logger.info("Running News Monitor...")
    
    simulated_news = [
        {"ticker": "HDFCBANK", "source_name": "Financial Times", "excerpt": "Analysts upgrade HDFC Bank on strong deposit growth."},
        {"ticker": "LT", "source_name": "Bloomberg", "excerpt": "L&T faces project delays due to supply chain issues."}
    ]
    
    try:
        with get_connection() as conn:
            c = conn.cursor()
            for n in simulated_news:
                sentiment = get_sentiment(n['excerpt'])
                c.execute("""
                    INSERT INTO alternative_mentions (ticker, source_type, source_name, mention_date, sentiment_score, excerpt_text)
                    VALUES (%s, 'NEWS', %s, CURRENT_TIMESTAMP, %s, %s)
                """, (n['ticker'], n['source_name'], sentiment, n['excerpt']))
            logger.info("News monitor successfully logged mentions.")
    except Exception as e:
        logger.error(f"News monitor failed: {e}")

if __name__ == '__main__':
    monitor()
