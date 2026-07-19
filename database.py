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
            _PG_POOL = pool.ThreadedConnectionPool(1, 5, conn_url, cursor_factory=DictCursor)
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

# Backward compatibility aliases
get_connection = get_db_connection
