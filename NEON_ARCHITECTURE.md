# Neon Database Architecture Strategy

## Unified Global Namespace
Because Neon provisions a single database environment (`neondb`), Sovereign Alpha drops the legacy multi-file separation (`billing.db`, `research.db`, `fund_data.db`, `meter.db`) and unifies all 45+ tables into the primary `public` schema.

## Migration Design Rules
- **Schema Mapping**: All tables share a namespace. Analysis confirms zero table-name collisions across the 4 legacy databases.
- **Connection Pooling**: `psycopg2.pool.SimpleConnectionPool` is initialized within `database.py`. All short-lived `get_db_connection()` requests now pull from the active pool instead of spinning up atomic file locks.
- **Transactions**: Default behavior enforces `autocommit = False`. The `commit()` and `rollback()` logic remains tightly controlled by the engine handlers (e.g., `seed_db.py`, `dashboard/app.py`).

## Conflict Strategies
To mimic SQLite's conflict management cleanly in PostgreSQL:
- `INSERT OR IGNORE` -> `INSERT INTO ... ON CONFLICT DO NOTHING`
- `INSERT OR REPLACE` -> `INSERT INTO ... ON CONFLICT (id) DO UPDATE SET ...`

## Data Migration Pathway (Dry Run Strategy)
1. **Extraction**: A Python bridging script will read directly from the live `sqlite3.Row` dictionaries.
2. **Batch Upload**: Using `psycopg2.extras.execute_values`, records will be mass-inserted into the Neon instance.
3. **Validation Checksum**: A cryptographic or strict-row-count comparison between local SQLite sizes and remote Neon sizes will mathematically prove migration fidelity.
