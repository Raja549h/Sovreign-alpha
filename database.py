import os
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2 import pool

class DatabaseError(psycopg2.Error): pass
class IntegrityError(psycopg2.IntegrityError): pass
class OperationalError(psycopg2.OperationalError): pass
class ConnectionError(psycopg2.OperationalError): pass

NEON_URL = os.environ.get("NEON_URL", "")

_PG_POOL = None
if NEON_URL:
    try:
        _PG_POOL = pool.SimpleConnectionPool(1, 100, NEON_URL, cursor_factory=DictCursor)
    except psycopg2.Error as e:
        print(f"Failed to initialize Neon connection pool: {e}")

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
    def __init__(self, cursor):
        self.cursor = cursor

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
        if not _PG_POOL:
            raise ConnectionError("Neon connection pool not initialized. Is NEON_URL set?")
        
        try:
            self.conn = _PG_POOL.getconn()
            self.conn.autocommit = False
        except psycopg2.Error as e:
            raise ConnectionError(f"Failed to get connection from pool: {e}")

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, value):
        pass

    def cursor(self):
        return NeonCursor(self.conn.cursor())

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
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query, params=None):
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self.conn and _PG_POOL:
            _PG_POOL.putconn(self.conn)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()

def get_db_connection(*args, **kwargs):
    return DatabaseConnection()

def get_connection(*args, **kwargs):
    return DatabaseConnection()

def transaction(*args, **kwargs):
    return DatabaseConnection()
