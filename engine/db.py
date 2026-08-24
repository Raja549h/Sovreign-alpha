"""
Database Connectivity for Sovereign Alpha (Headless DaaS Architecture)
=====================================================================
Direct connection manager to Aiven Cloud PostgreSQL database.
"""

import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError, OperationalError
from dotenv import load_dotenv

load_dotenv(override=False)

def get_db_url() -> str:
    url = os.environ.get("AIVEN_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL or AIVEN_DATABASE_URL is not set.")
    return url

@contextmanager
def get_connection(cursor_factory=RealDictCursor):
    """Context manager returning an active PostgreSQL connection with RealDictCursor."""
    conn = psycopg2.connect(get_db_url(), cursor_factory=cursor_factory)
    try:
        yield conn
    finally:
        conn.close()

def get_raw_connection():
    """Return a raw psycopg2 connection."""
    return psycopg2.connect(get_db_url(), cursor_factory=RealDictCursor)
