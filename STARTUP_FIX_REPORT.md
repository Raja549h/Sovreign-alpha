# Startup Fix Report

## Issue Addressed
The application was aggressively deleting its entire production schema during startup whenever `IS_CLOUD` resolved to true.

## Code Modified
- **File:** `dashboard/app.py`
- **Line Block Removed:** `DB_PATH.unlink()` inside `seed_database_on_startup()`.
- **Logic Replaced With:**
  ```python
  if DB_PATH.exists():
      print("[seed] Database exists - preserving production data")
  else:
      print("[seed] Database missing - initializing new schema")
  ```

## Verification
The startup sequence now safely checks for the database's existence. If `billing.db` exists, it preserves the data entirely. The application subsequently initializes any missing schema changes dynamically using SQLite's `CREATE TABLE IF NOT EXISTS` natively without triggering arbitrary data destruction.
