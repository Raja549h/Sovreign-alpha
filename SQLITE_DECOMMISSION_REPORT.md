# SQLite Decommissioning Audit Report

> [!CAUTION]
> **VERDICT: SQLITE STILL REQUIRED**
> The application cannot survive a Neon-only cold start. SQLite removal would cause immediate, total system failure.

---

## Executive Summary

This audit was conducted with zero assumptions and full forensic rigor. The results are uncomfortable but truthful.

**The `database.py` abstraction layer exists but is not connected to anything.** Zero production files import it. The entire production codebase — every route, every engine, every pipeline — still calls `sqlite3.connect()` directly.

---

## Phase 1 — Cold Start Simulation

### Can the application function with SQLite files removed?

**NO.**

If `billing.db`, `research.db`, and `fund_data.db` are removed:

| Component | Result | Reason |
|---|---|---|
| Dashboard (`app.py`) | **CRASH** | 18 direct `sqlite3.connect()` calls to missing files |
| Pipeline (`crew.py`) | **CRASH** | Direct `sqlite3.connect()` at line 259 |
| Evidence Engine (`research_db.py`) | **CRASH** | 7 direct `sqlite3.connect()` calls |
| Schemas (`schemas.py`) | **CRASH** | `init_billing_db()`, `init_research_db()`, `init_fund_data_db()` all call `sqlite3.connect()` |
| Risk Manager (`risk_manager.py`) | **CRASH** | 2 direct `sqlite3.connect()` calls |
| All Intelligence Modules | **CRASH** | 12 files with direct `sqlite3.connect()` calls |

**The application has no Neon pathway.** Every request hits SQLite directly.

---

## Phase 2 — Complete Dependency Inventory

### Direct `sqlite3.connect()` Calls in Production Files

| File | Call Count | Database Target |
|---|---|---|
| `app.py` | **18** | billing.db, research.db, fund_data.db |
| `research_db.py` | **7** | research.db |
| `schemas.py` | **3** | billing.db, research.db, fund_data.db |
| `audit_check.py` | **6** | billing.db, research.db |
| `crew.py` | **1** | billing.db |
| `risk_manager.py` | **2** | billing.db |
| `health_check.py` | **1** | billing.db |
| `health_check_full.py` | **2** | billing.db |
| `email_digest.py` | **2** | fund_data.db |
| `daily_cycle.py` | **2** | fund_data.db |
| `reanalyze_buy_metrics.py` | **2** | fund_data.db |
| `meter.py` | **2** | billing.db |
| `init_meter_db.py` | **1** | meter.db |
| `seed_db.py` | **2** | research.db, fund_data.db |
| `generate_one_pager.py` | **1** | fund_data.db |
| `generate_whitepaper.py` | **1** | fund_data.db |
| `backfill_memory.py` | **1** | research.db |
| `evolution_quality.py` | **1** | research.db |
| `fii_intelligence.py` | **1** | research.db |
| `observation_registry.py` | **1** | research.db |
| `observation_stream.py` | **1** | research.db |
| `portfolio_intelligence.py` | **1** | research.db |
| `seed_muthoot.py` | **1** | research.db |
| `seed_pageind.py` | **1** | research.db |
| `thesis_evolution_engine.py` | **1** | research.db |
| `thesis_tracker.py` | **1** | research.db |
| `fii_flow.py` | **2** | research.db |
| `import_sensitivity.py` | **2** | research.db |
| `macro_engine.py` | **1** | research.db |
| `macro_health.py` | **2** | research.db |
| `reserve_stress.py` | **2** | research.db |

**Total: 37 production files, 78+ direct `sqlite3.connect()` calls**

### Files That Import `database.py`

| File | Purpose |
|---|---|
| `run_all_tests.py` | Test script only |

**Total production files using the abstraction layer: 0**

---

## Phase 3 — Neon-Only Environment Verification

### Can a fresh Neon-only environment serve the application?

**NO.** The prerequisite for this test is that the application code routes through `database.py`. It does not.

| Subsystem | Neon-Ready | Blocking Issue |
|---|---|---|
| Dashboard | NO | `app.py` calls `sqlite3.connect()` directly 18 times |
| Pipeline | NO | `crew.py` calls `sqlite3.connect()` directly |
| Evidence Engine | NO | `research_db.py` calls `sqlite3.connect()` 7 times |
| Autopsy Engine | NO | Routed through `research_db.py` (SQLite-only) |
| Failure Ledger | NO | Routed through `research_db.py` (SQLite-only) |
| Challenge Engine | NO | Routed through `research_db.py` (SQLite-only) |
| Calibration | NO | Routed through `research_db.py` (SQLite-only) |
| Weekly IC | NO | Routed through `app.py` (SQLite-only) |
| Proof Generation | NO | Routed through `crew.py` and `meter.py` (SQLite-only) |

### Data Migration Discrepancies

| Table | SQLite | Neon | Difference | Status |
|---|---|---|---|---|
| `decisions` (billing.db) | 11 | 0 | **11** | FAILED |
| `decisions` (meter.db) | 0 | 0 | 0 | Schema collision: 8 cols vs 9 cols |

> [!WARNING]
> The `decisions` table exists in **both** `billing.db` (9 columns, 11 rows) and `meter.db` (8 columns, 0 rows). During Neon migration, the billing.db version was created first, and meter.db's version was skipped as a duplicate. However, the dry run migration ordered billing.db's `decisions` table data insertion **before** the schema existed for it (due to table ordering), causing 0 rows to be migrated.

---

## Phase 4 — File Classification

### Safe to Archive
These files served their diagnostic purpose and can be archived:

| File | Reason |
|---|---|
| `list_tables.py` | Diagnostic utility |
| `list_tables_billing.py` | Diagnostic utility |
| `verify_db.py` | Diagnostic utility |
| `red_team_attack.py` | Security testing |
| `seed_all_empty_tables.py` | One-time seeding |
| `test_persistence.py` | Test utility |
| `test_phases_1_to_3.py` | Migration test |
| `run_all_tests.py` | Migration test |
| `kill_pg_connections.py` | Migration utility |
| `dry_run_migration.py` | Migration dry run |
| `generate_pg_schema.py` | Schema generation |
| `generate_pg_schema_actual.py` | Schema generation |

### Still Required — Cannot Be Removed

| File | Reason |
|---|---|
| `billing.db` | **18 production files depend on it directly** |
| `research.db` | **20+ production files depend on it directly** |
| `fund_data.db` | **7 production files depend on it directly** |
| `meter.db` | **2 production files depend on it directly** |
| `schemas.py` | **Creates and initializes all SQLite databases** |
| All 37 production `.py` files | **Hardcoded `sqlite3.connect()` calls** |

### Safe to Delete
Nothing. No production SQLite dependency can be safely deleted.

---

## Phase 5 — Honest Assessment

### What Was Actually Built

1. `database.py` — A database abstraction layer that CAN route to Neon
2. `POSTGRES_SCHEMA.sql` — A valid PostgreSQL schema for all tables
3. Neon data import — 48/49 tables with matching row counts
4. Connection verification — Neon is reachable and accepting queries

### What Was NOT Built

1. **Production integration** — Zero production files import `database.py`
2. **SQLite-to-Neon routing** — No `import sqlite3` was replaced anywhere
3. **Cold start test** — Never performed without SQLite files present
4. **`row_factory = sqlite3.Row` compatibility** — `database.py` uses `DictCursor` but 20+ files set `conn.row_factory = sqlite3.Row` after connecting. These files expect `row[column_name]` access via SQLite Row interface, not psycopg2 DictRow.
5. **`with sqlite3.connect(...) as conn:` pattern** — 12 call sites use the context manager pattern. `database.py` supports `__enter__/__exit__` but returns itself, not the raw connection.
6. **`decisions` table collision** — Two different schemas exist across `billing.db` and `meter.db`

### Work Remaining Before SQLite Can Be Decommissioned

| Task | Scope | Risk |
|---|---|---|
| Replace all 78+ `sqlite3.connect()` calls with `database.py` | 37 files | HIGH |
| Handle `row_factory = sqlite3.Row` compatibility | 20+ call sites | MEDIUM |
| Resolve `decisions` table name collision | 2 databases | HIGH |
| Fix 11-row data discrepancy | 1 table | LOW |
| Handle `with sqlite3.connect() as conn:` pattern | 12 call sites | MEDIUM |
| Handle `sqlite3.IntegrityError` exception catches | 2 call sites | LOW |
| Handle `sqlite3.OperationalError` exception catches | 3 call sites | LOW |
| Full E2E cold start test with no SQLite | 1 test | CRITICAL |

---

## Final Verdict

> [!CAUTION]
> ## SQLITE STILL REQUIRED
>
> The `database.py` abstraction layer was correctly designed but **never integrated** into the production codebase. Zero production files import it. All 37 production files with 78+ call sites still use `sqlite3.connect()` directly.
>
> Removing SQLite files would cause **immediate, total application failure** — every route, every engine, every pipeline would crash on the first database call.
>
> **SQLite remains the sole operational database backend for Sovereign Alpha.**
