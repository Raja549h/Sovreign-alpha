import os
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2 import pool

class DatabaseError(psycopg2.Error): pass
class IntegrityError(psycopg2.IntegrityError): pass
class OperationalError(psycopg2.OperationalError): pass
class ConnectionError(psycopg2.OperationalError): pass

_PG_POOL = None

def init_pool():
    global _PG_POOL
    if _PG_POOL is not None:
        return
    
    neon_url = os.environ.get("NEON_URL", "")
    if not neon_url or len(neon_url) < 10:
        print("WARNING: NEON_URL missing or malformed. Running without DB.")
        return

    import time
    import socket
    import urllib.parse
    
    parsed = urllib.parse.urlparse(neon_url)
    host = parsed.hostname
    
    retries = 3
    for attempt in range(1, retries + 1):
        try:
            # Enforce max 30 connections to avoid pool exhaustion during concurrent API requests
            base = neon_url.split('?')[0] if '?' in neon_url else neon_url
            conn_url = base + "?sslmode=require&connect_timeout=10&keepalives_idle=5&keepalives_interval=2&keepalives_count=2"
                
            _PG_POOL = pool.ThreadedConnectionPool(1, 30, conn_url, cursor_factory=DictCursor)
            return # Success
            
        except psycopg2.OperationalError as e:
            if "could not translate host name" in str(e) and host:
                try:
                    # Try to resolve IP dynamically
                    ip = socket.gethostbyname(host)
                    neon_url = neon_url.replace(host, ip)
                    print(f"[DB Retry] Resolved {host} to {ip}")
                except socket.gaierror:
                    pass
            
            if attempt < retries:
                print(f"[DB Retry] Connection failed, retrying {attempt}/{retries} in 2s...")
                time.sleep(2)
            else:
                raise ConnectionError("CRITICAL: Database unreachable after 3 attempts.") from e

class NeonRow:
    def __init__(self, d):
        self._d = d
        self._keys = list(d.keys())

    def keys(self):
        return self._keys

    def values(self):
        return self._d.values()

    def items(self):
        return self._d.items()

    def get(self, key, default=None):
        return self._d.get(key, default)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._d[self._keys[key]]
        return self._d[key]

    def __iter__(self):
        return iter(self._d.values())

    def __len__(self):
        return len(self._d)

    def __contains__(self, key):
        return key in self._d

class NeonCursor:
    def __init__(self, cursor, db_conn=None):
        self.cursor = cursor
        self.db_conn = db_conn

    def execute(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
        except psycopg2.IntegrityError as e:
            self.cursor.connection.rollback()
            raise IntegrityError(str(e))
        except psycopg2.OperationalError as e:
            self.cursor.connection.rollback()
            raise OperationalError(str(e))
        except psycopg2.ProgrammingError as e:
            self.cursor.connection.rollback()
            raise OperationalError(str(e))
        except psycopg2.Error as e:
            self.cursor.connection.rollback()
            raise DatabaseError(str(e))
        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        if row:
            return NeonRow(dict(row))
        return None

    def fetchall(self):
        return [NeonRow(dict(row)) for row in self.cursor.fetchall()]
        
    @property
    def lastrowid(self):
        return 1

    @property
    def rowcount(self):
        return self.cursor.rowcount

    @property
    def description(self):
        return self.cursor.description

    def close(self):
        self.cursor.close()

class DatabaseConnection:
    def __init__(self, db_name=None):
        init_pool()
        self.pool_key = id(self)
        self.is_pooled = False
        self.conn = None
        last_err = None
        
        if _PG_POOL:
            try:
                self.conn = _PG_POOL.getconn(key=self.pool_key)
                self.is_pooled = True
            except psycopg2.Error as e:
                last_err = f"Pool getconn failed: {e}"
        else:
            last_err = "Pool not initialized."
            
        if not self.conn:
            # Hardcore fallback: direct unpooled connection
            neon_url = os.environ.get("NEON_URL", "")
            if not neon_url:
                raise ConnectionError(f"{last_err} NEON_URL missing.")
            base = neon_url.split('?')[0] if '?' in neon_url else neon_url
            conn_url = base + "?sslmode=require&connect_timeout=15"
            try:
                import psycopg2
                self.conn = psycopg2.connect(conn_url)
            except psycopg2.Error as e:
                raise ConnectionError(f"{last_err} | Direct fallback failed: {e}")
                
        self.conn.autocommit = False

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, value):
        pass

    def cursor(self):
        return NeonCursor(self.conn.cursor(), db_conn=self)

    def execute(self, query, params=None):
        cursor = self.cursor()
        cursor.execute(query, params)
        return cursor

    def executescript(self, sql_script):
        """Execute multiple SQL statements separated by semicolons"""
        cursor = self.cursor()
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
        for stmt in statements:
            cursor.execute(stmt)

    def fetch_one(self, query, params=None):
        cursor = self.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query, params=None):
        cursor = self.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if hasattr(self, 'conn') and self.conn:
            if getattr(self, 'is_pooled', False) and _PG_POOL:
                try:
                    _PG_POOL.putconn(self.conn, key=self.pool_key)
                except Exception as e:
                    print(f"Error putting connection back to pool: {e}")
                    try:
                        self.conn.close()
                    except Exception:
                        pass
            else:
                try:
                    self.conn.close()
                except Exception:
                    pass
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

def get_db_connection(*args, **kwargs):
    try:
        return DatabaseConnection()
    except Exception:
        return None

import time

def get_connection(*args, **kwargs):
    for attempt in range(5):
        try:
            return DatabaseConnection()
        except Exception as e:
            if attempt == 4:
                print(f"[database] All 5 connection attempts failed: {e}")
                return None
            time.sleep(1)
    return None

def transaction(*args, **kwargs):
    for attempt in range(5):
        try:
            return DatabaseConnection()
        except Exception as e:
            if attempt == 4:
                return None
            time.sleep(1)
    return None
