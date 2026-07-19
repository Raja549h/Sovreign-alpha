import os
import time
import socket
import urllib.parse
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor

class DatabaseError(psycopg2.Error): pass
class IntegrityError(psycopg2.IntegrityError): pass
class OperationalError(psycopg2.OperationalError): pass
class ConnectionError(psycopg2.OperationalError): pass

_PG_POOL = None

def get_pool(force_reinit=False):
    global _PG_POOL
    
    if _PG_POOL is not None and not force_reinit:
        try:
            if not _PG_POOL.closed:
                return _PG_POOL
        except Exception:
            pass # Pool is likely closed or broken
            
    neon_url = os.environ.get("NEON_URL")
    if not neon_url or len(neon_url) < 10:
        raise ConnectionError("CRITICAL: NEON_URL environment variable is not set.")
        
    parsed = urllib.parse.urlparse(neon_url)
    host = parsed.hostname
    
    base = neon_url.split('?')[0] if '?' in neon_url else neon_url
    conn_url = base + "?sslmode=require&connect_timeout=10&keepalives_idle=5&keepalives_interval=2&keepalives_count=2"
    
    retries = 3
    for attempt in range(1, retries + 1):
        try:
            _PG_POOL = pool.ThreadedConnectionPool(1, 20, conn_url, cursor_factory=DictCursor)
            return _PG_POOL
        except psycopg2.OperationalError as e:
            if "could not translate host name" in str(e) and host:
                try:
                    ip = socket.gethostbyname(host)
                    conn_url = conn_url.replace(host, ip)
                except socket.gaierror:
                    pass
            
            if attempt < retries:
                time.sleep(2)
            else:
                raise ConnectionError("CRITICAL: Database unreachable after 3 attempts.") from e

@contextmanager
def get_db_connection():
    pool_obj = None
    conn = None
    last_err = None
    
    for attempt in range(1, 4):
        try:
            pool_obj = get_pool(force_reinit=(attempt > 1))
            conn = pool_obj.getconn()
            conn.autocommit = False
            break
        except Exception as e:
            print(f"DB ERROR: {e}")
            last_err = e
            if attempt < 3:
                time.sleep(2)
                
    if not conn:
        raise ConnectionError(f"Failed to get database connection: {last_err}")
        
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
    def __init__(self):
        self._pool = get_pool()
        self._conn = self._pool.getconn()
        self._conn.autocommit = True

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)
    
    def commit(self):
        self._conn.commit()
    
    def rollback(self):
        self._conn.rollback()

    def execute(self, *args, **kwargs):
        with self._conn.cursor() as c:
            c.execute(*args, **kwargs)
            
    def close(self):
        try:
            if getattr(self, '_closed', False):
                return
            self._pool.putconn(self._conn)
            self._closed = True
        except Exception:
            pass
            
    def __del__(self):
        self.close()
            
    def __enter__(self):
        self._conn.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._conn.__exit__(exc_type, exc_val, exc_tb)

def get_legacy_connection():
    return LegacyConnectionWrapper()

# Backward compatibility aliases
get_connection = get_legacy_connection
