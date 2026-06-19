# Database Layer Report

## Abstraction Strategy
A new centralized abstraction layer `database.py` has been instantiated. This file wraps the DB-API 2.0 implementations for both SQLite (`sqlite3`) and Neon PostgreSQL (`psycopg2`).

- **Connection Interception**: All database invocations now utilize `get_db_connection(db_name)`.
- **Driver Resolution**: If the environment variable `NEON_URL` is set, the class establishes a `psycopg2` connection to the Neon pooler. Otherwise, it defaults to the legacy SQLite structure.
- **Query Interception**: The `execute()` wrapper automatically translates SQLite parameterization syntax (`?`) into PostgreSQL syntax (`%s`).
- **Data Shape Preservation**: We use `psycopg2.extras.DictCursor` to precisely emulate `sqlite3.Row` dictionary-like access logic.

All 130+ legacy calls must now be targeted to this unified router.
