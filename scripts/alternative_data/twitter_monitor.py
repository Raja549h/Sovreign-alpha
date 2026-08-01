import datetime
from dashboard.gateway import get_connection
from config import logger

def get_sentiment(text):
    text_lower = text.lower()
    if 'guidance raised' in text_lower or 'strong' in text_lower:
        return 4.5
    if 'guidance cut' in text_lower or 'weak' in text_lower:
        return 2.0
    return 3.0

def monitor():
    logger.info("Running Twitter Monitor...")
    
    simulated_tweets = [
        {"ticker": "RELIANCE", "source_name": "@MukeshAmbani", "excerpt": "We are committed to strong growth in our retail and telecom sectors."},
        {"ticker": "INFY", "source_name": "@Infosys", "excerpt": "Guidance cut for the upcoming quarter due to macro uncertainties."}
    ]
    
    try:
        with get_connection() as conn:
            c = conn.cursor()
            for t in simulated_tweets:
                sentiment = get_sentiment(t['excerpt'])
                c.execute("""
                    INSERT INTO alternative_mentions (ticker, source_type, source_name, mention_date, sentiment_score, excerpt_text)
                    VALUES (%s, 'TWITTER', %s, CURRENT_TIMESTAMP, %s, %s)
                """, (t['ticker'], t['source_name'], sentiment, t['excerpt']))
            logger.info("Twitter monitor successfully logged mentions.")
    except Exception as e:
        logger.error(f"Twitter monitor failed: {e}")

if __name__ == '__main__':
    monitor()
