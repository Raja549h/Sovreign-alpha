import os
import time
import threading
import yfinance as yf
from config import logger

class StockPriceCache:
    def __init__(self, ttl=300):
        """Initialize cache with default 5-minute TTL."""
        self.cache = {}
        self.ttl = int(os.environ.get('CACHE_TTL', ttl))
        self.lock = threading.Lock()
        
    def get_price(self, symbol):
        """Get price from cache or fetch if missing/staled."""
        now = time.time()
        
        # Fast path reading
        with self.lock:
            if symbol in self.cache:
                cached_time, price = self.cache[symbol]
                if now - cached_time < self.ttl:
                    return price
                    
        # Cache miss or stale - fetch price
        price = self._fetch_price(symbol)
        
        # Store back in cache
        with self.lock:
            self.cache[symbol] = (time.time(), price)
            
        return price
        
    def _fetch_price(self, symbol):
        """Internal method to fetch price via yfinance with fallback logic."""
        try:
            logger.info(f"Fetching fresh price for {symbol} via yfinance API")
            stock = yf.Ticker(symbol)
            info = stock.fast_info
            price = info.get('last_price')
            
            if not price:
                # Fallback to history if fast_info fails
                hist = stock.history(period="1d")
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
            
            if price:
                return round(price, 2)
            else:
                raise ValueError("No price data available")
                
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {e}. Retrying with fallback...")
            return self._get_fallback_price(symbol)
            
    def _get_fallback_price(self, symbol):
        """Fallback when API limit is reached. Returns the last known price."""
        with self.lock:
            if symbol in self.cache:
                logger.info(f"Using stale cached price for {symbol} due to API error")
                return self.cache[symbol][1]
        
        logger.error(f"No price or fallback available for {symbol}")
        return 0.0

# Singleton instance for the application
price_cache = StockPriceCache()
