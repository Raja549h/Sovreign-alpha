import os
import time
import socket
import urllib.parse
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor

# Export psycopg2 exceptions for legacy compatibility
class DatabaseError(psycopg2.Error): pass
class IntegrityError(psycopg2.IntegrityError): pass
class OperationalError(psycopg2.OperationalError): pass
class ConnectionError(psycopg2.OperationalError): pass

_PG_POOL = None

def _create_pool():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url or len(db_url) < 10:
        raise ConnectionError("CRITICAL: DATABASE_URL environment variable is not set.")
        
    parsed = urllib.parse.urlparse(db_url)
    host = parsed.hostname
    
    base = db_url.split('?')[0] if '?' in db_url else db_url
    conn_url = base + "?sslmode=require&connect_timeout=10&keepalives_idle=5&keepalives_interval=2&keepalives_count=2"
    
    retries = 5
    for attempt in range(1, retries + 1):
        try:
            return pool.ThreadedConnectionPool(1, 20, conn_url, cursor_factory=DictCursor)
        except psycopg2.OperationalError as e:
            if "could not translate host name" in str(e) and host:
                try:
                    ip = socket.gethostbyname(host)
                    conn_url = conn_url.replace(host, ip)
                except socket.gaierror:
                    pass
            
            if attempt < retries:
                time.sleep(3)
            else:
                raise ConnectionError("CRITICAL: Database unreachable after 5 attempts.") from e
    return None

def get_pool():
    global _PG_POOL
    
    # Check if pool is alive
    if _PG_POOL is not None:
        try:
            if not _PG_POOL.closed:
                return _PG_POOL
        except Exception:
            pass # Pool is dead
            
    # Create new pool immediately if dead or None
    _PG_POOL = _create_pool()
    return _PG_POOL

@contextmanager
def get_db_connection():
    """
    Yields a connection from the global pool.
    Retries internally if pool connection fails.
    """
    pool_obj = None
    conn = None
    last_err = None
    
    for attempt in range(1, 6):
        try:
            pool_obj = get_pool()
            conn = pool_obj.getconn()
            conn.autocommit = False
            break
        except Exception as e:
            print(f"[gateway] DB ERROR: {e}")
            last_err = e
            if attempt < 5:
                time.sleep(3)
                # Force pool recreation on next attempt by clearing global
                global _PG_POOL
                _PG_POOL = None
                
    if not conn:
        raise ConnectionError(f"Failed to get database connection after 5 attempts: {last_err}")
        
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if pool_obj and conn:
            try:
                pool_obj.putconn(conn)
            except Exception:
                pass

class LegacyConnectionWrapper:
    """Provides backward compatibility for scripts not using context managers."""
    def __init__(self):
        self._pool = get_pool()
        self._conn = self._pool.getconn()
        self._conn.autocommit = True

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)
        
    def execute(self, query, vars=None):
        """SQLite compatibility wrapper."""
        c = self._conn.cursor()
        c.execute(query, vars)
        return c
    
    def commit(self):
        self._conn.commit()
    
    def rollback(self):
        self._conn.rollback()
        
    def close(self):
        if hasattr(self, '_conn') and hasattr(self, '_pool') and self._conn is not None:
            try:
                self._pool.putconn(self._conn)
            except Exception:
                pass
            self._conn = None
            self._pool = None

    def __del__(self):
        self.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()

def get_connection():
    """Legacy alias to return a raw connection wrapper."""
    return LegacyConnectionWrapper()

# Aliases for compatibility
DatabaseConnection = get_connection
