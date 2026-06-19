# SQLite Runtime Dependency Classification Report

## Findings

### import sqlite3 in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 5
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 12
**3. Exact Code Snippet:** RESEARCH_DB = BILLING / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 13
**3. Exact Code Snippet:** FUND_DB = BILLING / "fund_data.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 52
**3. Exact Code Snippet:** check("research.db exists", RESEARCH_DB.exists(), "critical")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 53
**3. Exact Code Snippet:** check("fund_data.db exists", FUND_DB.exists(), "critical")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 56
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 60
**3. Exact Code Snippet:** check("research.db has tables", len(tables) > 0, "critical")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 100
**3. Exact Code Snippet:** check("research.db required for audit", False, "critical")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 103
**3. Exact Code Snippet:** conn2 = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 107
**3. Exact Code Snippet:** # prediction_ledger and veto_archive are created at Flask runtime (in billing.db)
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 110
**3. Exact Code Snippet:** # Also check billing.db (fund_data.db) where these tables are created at runtime
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 112
**3. Exact Code Snippet:** conn_fund = get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 127
**3. Exact Code Snippet:** conn_p = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 136
**3. Exact Code Snippet:** rec("prediction_ledger table is created by Flask at runtime in billing.db. Start the app to create it.", "low")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 142
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 143
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 266
**3. Exact Code Snippet:** conn3 = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in audit_check.py
**1. File Path:** .\audit_check.py
**2. Line Number:** 267
**3. Exact Code Snippet:** conn3.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in crew.py
**1. File Path:** .\crew.py
**2. Line Number:** 258
**3. Exact Code Snippet:** db_path = BILLING_DIR / "billing.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in crew.py
**1. File Path:** .\crew.py
**2. Line Number:** 259
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in database.py
**1. File Path:** .\database.py
**2. Line Number:** 1
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.IntegrityError in database.py
**1. File Path:** .\database.py
**2. Line Number:** 53
**3. Exact Code Snippet:** raise sqlite3.IntegrityError(str(e))
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.OperationalError in database.py
**1. File Path:** .\database.py
**2. Line Number:** 56
**3. Exact Code Snippet:** raise sqlite3.OperationalError(str(e))
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.OperationalError in database.py
**1. File Path:** .\database.py
**2. Line Number:** 59
**3. Exact Code Snippet:** raise sqlite3.OperationalError(str(e))
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 123
**3. Exact Code Snippet:** if db_name == "billing.db":
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 124
**3. Exact Code Snippet:** path = BILLING_DIR / "billing.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 125
**3. Exact Code Snippet:** elif db_name == "research.db":
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 126
**3. Exact Code Snippet:** path = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 127
**3. Exact Code Snippet:** elif db_name == "fund_data.db":
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 128
**3. Exact Code Snippet:** path = BILLING_DIR / "fund_data.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 129
**3. Exact Code Snippet:** elif db_name == "meter.db":
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 130
**3. Exact Code Snippet:** path = BILLING_DIR / "meter.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.connect in database.py
**1. File Path:** .\database.py
**2. Line Number:** 134
**3. Exact Code Snippet:** self.conn = sqlite3.connect(str(path))
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in database.py
**1. File Path:** .\database.py
**2. Line Number:** 135
**3. Exact Code Snippet:** self.conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 193
**3. Exact Code Snippet:** def get_db_connection(db_name="billing.db"):
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 196
**3. Exact Code Snippet:** def get_connection(db_name="billing.db"):
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in database.py
**1. File Path:** .\database.py
**2. Line Number:** 199
**3. Exact Code Snippet:** def transaction(db_name="billing.db"):
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in dependency_scan.py
**1. File Path:** .\dependency_scan.py
**2. Line Number:** 5
**3. Exact Code Snippet:** "import sqlite3",
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.connect in dependency_scan.py
**1. File Path:** .\dependency_scan.py
**2. Line Number:** 6
**3. Exact Code Snippet:** "sqlite3.connect",
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in dependency_scan.py
**1. File Path:** .\dependency_scan.py
**2. Line Number:** 7
**3. Exact Code Snippet:** "sqlite3.Row",
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.IntegrityError in dependency_scan.py
**1. File Path:** .\dependency_scan.py
**2. Line Number:** 8
**3. Exact Code Snippet:** "sqlite3.IntegrityError",
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.OperationalError in dependency_scan.py
**1. File Path:** .\dependency_scan.py
**2. Line Number:** 9
**3. Exact Code Snippet:** "sqlite3.OperationalError",
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in dependency_scan.py
**1. File Path:** .\dependency_scan.py
**2. Line Number:** 10
**3. Exact Code Snippet:** "billing.db",
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in dependency_scan.py
**1. File Path:** .\dependency_scan.py
**2. Line Number:** 11
**3. Exact Code Snippet:** "research.db",
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in dependency_scan.py
**1. File Path:** .\dependency_scan.py
**2. Line Number:** 12
**3. Exact Code Snippet:** "fund_data.db",
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in dependency_scan.py
**1. File Path:** .\dependency_scan.py
**2. Line Number:** 13
**3. Exact Code Snippet:** "meter.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.IntegrityError in dependency_scan.py
**1. File Path:** .\dependency_scan.py
**2. Line Number:** 82
**3. Exact Code Snippet:** report.append("**Evidence:** There are still RUNTIME_PRODUCTION dependencies listed above. Specifically, database.py heavily relies on sqlite3.IntegrityError and sqlite3.OperationalError for translating psycopg2 exceptions, which causes transitive dependencies throughout the application. Removing SQLite from runtime today would crash engines whenever a unique constraint violation or operational error occurs.")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in dry_run_migration.py
**1. File Path:** .\dry_run_migration.py
**2. Line Number:** 1
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in dry_run_migration.py
**1. File Path:** .\dry_run_migration.py
**2. Line Number:** 41
**3. Exact Code Snippet:** db_paths = [Path('billing/billing.db'), Path('billing/research.db'), Path('billing/fund_data.db'), Path('billing/meter.db')]
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in dry_run_migration.py
**1. File Path:** .\dry_run_migration.py
**2. Line Number:** 53
**3. Exact Code Snippet:** sqlite_conn = sqlite3.connect(db_path)
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in extract_inventory.py
**1. File Path:** .\extract_inventory.py
**2. Line Number:** 1
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in extract_inventory.py
**1. File Path:** .\extract_inventory.py
**2. Line Number:** 5
**3. Exact Code Snippet:** db_paths = [Path('billing/billing.db'), Path('billing/research.db'), Path('billing/fund_data.db'), Path('billing/meter.db')]
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in extract_inventory.py
**1. File Path:** .\extract_inventory.py
**2. Line Number:** 11
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in fix_parens.py
**1. File Path:** .\fix_parens.py
**2. Line Number:** 12
**3. Exact Code Snippet:** if 'get_connection("research.db")' in content or 'get_connection("billing.db")' in content or 'get_connection("fund_data.db")' in content:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in fix_parens.py
**1. File Path:** .\fix_parens.py
**2. Line Number:** 13
**3. Exact Code Snippet:** content = content.replace('get_connection("research.db")', 'get_connection("research.db")')
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in fix_parens.py
**1. File Path:** .\fix_parens.py
**2. Line Number:** 14
**3. Exact Code Snippet:** content = content.replace('get_connection("billing.db")', 'get_connection("billing.db")')
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in fix_parens.py
**1. File Path:** .\fix_parens.py
**2. Line Number:** 15
**3. Exact Code Snippet:** content = content.replace('get_connection("fund_data.db")', 'get_connection("fund_data.db")')
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in fix_sequences.py
**1. File Path:** .\fix_sequences.py
**2. Line Number:** 6
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in forensic_backup.py
**1. File Path:** .\forensic_backup.py
**2. Line Number:** 4
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in forensic_backup.py
**1. File Path:** .\forensic_backup.py
**2. Line Number:** 10
**3. Exact Code Snippet:** ('billing/billing.db.bak', 'sqlite_archive/billing_final_backup.db'),
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in forensic_backup.py
**1. File Path:** .\forensic_backup.py
**2. Line Number:** 11
**3. Exact Code Snippet:** ('billing/research.db.bak', 'sqlite_archive/research_final_backup.db'),
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in forensic_backup.py
**1. File Path:** .\forensic_backup.py
**2. Line Number:** 12
**3. Exact Code Snippet:** ('billing/fund_data.db.bak', 'sqlite_archive/fund_data_final_backup.db')
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.connect in forensic_backup.py
**1. File Path:** .\forensic_backup.py
**2. Line Number:** 30
**3. Exact Code Snippet:** conn = sqlite3.connect(dest)
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in generate_pg_schema.py
**1. File Path:** .\generate_pg_schema.py
**2. Line Number:** 1
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in generate_pg_schema.py
**1. File Path:** .\generate_pg_schema.py
**2. Line Number:** 6
**3. Exact Code Snippet:** db_paths = [Path('billing/billing.db'), Path('billing/research.db'), Path('billing/fund_data.db'), Path('billing/meter.db')]
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.connect in generate_pg_schema.py
**1. File Path:** .\generate_pg_schema.py
**2. Line Number:** 14
**3. Exact Code Snippet:** conn = sqlite3.connect(db_path)
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in generate_pg_schema_actual.py
**1. File Path:** .\generate_pg_schema_actual.py
**2. Line Number:** 1
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in generate_pg_schema_actual.py
**1. File Path:** .\generate_pg_schema_actual.py
**2. Line Number:** 6
**3. Exact Code Snippet:** db_paths = [Path('billing/billing.db'), Path('billing/research.db'), Path('billing/fund_data.db'), Path('billing/meter.db')]
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.connect in generate_pg_schema_actual.py
**1. File Path:** .\generate_pg_schema_actual.py
**2. Line Number:** 17
**3. Exact Code Snippet:** conn = sqlite3.connect(db_path)
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in generate_sqlite_audit.py
**1. File Path:** .\generate_sqlite_audit.py
**2. Line Number:** 29
**3. Exact Code Snippet:** if 'import sqlite3' in content or 'from sqlite3' in content:
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in health_check.py
**1. File Path:** .\health_check.py
**2. Line Number:** 13
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in health_check.py
**1. File Path:** .\health_check.py
**2. Line Number:** 128
**3. Exact Code Snippet:** db_path = BASE_DIR / 'billing' / 'billing.db'
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in health_check.py
**1. File Path:** .\health_check.py
**2. Line Number:** 134
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in health_check_full.py
**1. File Path:** .\health_check_full.py
**2. Line Number:** 9
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in health_check_full.py
**1. File Path:** .\health_check_full.py
**2. Line Number:** 55
**3. Exact Code Snippet:** "billing/meter.db",
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in health_check_full.py
**1. File Path:** .\health_check_full.py
**2. Line Number:** 263
**3. Exact Code Snippet:** db_path = PROJECT_DIR / "billing" / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in health_check_full.py
**1. File Path:** .\health_check_full.py
**2. Line Number:** 265
**3. Exact Code Snippet:** db_path = PROJECT_DIR / "billing" / "meter.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in health_check_full.py
**1. File Path:** .\health_check_full.py
**2. Line Number:** 273
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in health_check_full.py
**1. File Path:** .\health_check_full.py
**2. Line Number:** 502
**3. Exact Code Snippet:** # Check billing/meter.db
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in health_check_full.py
**1. File Path:** .\health_check_full.py
**2. Line Number:** 503
**3. Exact Code Snippet:** meter_db = PROJECT_DIR / "billing" / "meter.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in health_check_full.py
**1. File Path:** .\health_check_full.py
**2. Line Number:** 505
**3. Exact Code Snippet:** print("OK: billing/meter.db exists")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in health_check_full.py
**1. File Path:** .\health_check_full.py
**2. Line Number:** 507
**3. Exact Code Snippet:** print("MISSING: billing/meter.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in health_check_full.py
**1. File Path:** .\health_check_full.py
**2. Line Number:** 523
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.connect in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 15
**3. Exact Code Snippet:** # Skip if no sqlite3.connect
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 16
**3. Exact Code Snippet:** if 'sqlite3.connect' not in content:
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 23
**3. Exact Code Snippet:** # Add after import sqlite3
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 24
**3. Exact Code Snippet:** content = re.sub(r'import sqlite3', 'import sqlite3\nfrom database import get_connection', content, count=1)
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 25
**3. Exact Code Snippet:** if 'import sqlite3' not in content:
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 26
**3. Exact Code Snippet:** # If no import sqlite3, just add it at the top
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 32
**3. Exact Code Snippet:** # Most of these are billing.db, or handled by the fallback in get_connection if they pass a Path
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 33
**3. Exact Code Snippet:** # Wait, get_connection expects a string: 'billing.db', 'research.db', 'fund_data.db'
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 35
**3. Exact Code Snippet:** # We will use regex to find get_connection("billing.db") and replace intelligently
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 38
**3. Exact Code Snippet:** if 'sqlite3.connect' in line:
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 40
**3. Exact Code Snippet:** if 'research.db' in line or 'RESEARCH_DB' in line or '_RDB' in line or 'research' in line.lower():
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 41
**3. Exact Code Snippet:** lines[i] = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection("research.db")', line)
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### fund_data.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 42
**3. Exact Code Snippet:** elif 'fund_data.db' in line or 'FUND_DATA_DB' in line or 'fund_db' in line.lower():
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### fund_data.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 43
**3. Exact Code Snippet:** lines[i] = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection("fund_data.db")', line)
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### meter.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 44
**3. Exact Code Snippet:** elif 'meter.db' in line or 'init_meter_db' in filepath.name or 'meter.py' in filepath.name:
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 45
**3. Exact Code Snippet:** # meter.py uses self.db_path which points to billing.db actually!
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 46
**3. Exact Code Snippet:** # Wait, meter.py lines 22-25: `self.db_path = self.data_dir / "billing.db"`
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### meter.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 47
**3. Exact Code Snippet:** if 'meter.db' in line:
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### meter.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 48
**3. Exact Code Snippet:** lines[i] = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection("meter.db")', line)
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 50
**3. Exact Code Snippet:** lines[i] = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection("billing.db")', line)
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in migrate_all_sqlite.py
**1. File Path:** .\migrate_all_sqlite.py
**2. Line Number:** 52
**3. Exact Code Snippet:** lines[i] = re.sub(r'sqlite3\.connect\([^)]+\)', 'get_connection("billing.db")', line)
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in run_all_tests.py
**1. File Path:** .\run_all_tests.py
**2. Line Number:** 1
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in test_persistence.py
**1. File Path:** .\test_persistence.py
**2. Line Number:** 2
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in test_persistence.py
**1. File Path:** .\test_persistence.py
**2. Line Number:** 9
**3. Exact Code Snippet:** conn = sqlite3.connect(DB_PATH)
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in test_persistence.py
**1. File Path:** .\test_persistence.py
**2. Line Number:** 18
**3. Exact Code Snippet:** conn = sqlite3.connect(DB_PATH)
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in test_phases_1_to_3.py
**1. File Path:** .\test_phases_1_to_3.py
**2. Line Number:** 2
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in test_phases_1_to_3.py
**1. File Path:** .\test_phases_1_to_3.py
**2. Line Number:** 21
**3. Exact Code Snippet:** db_paths = [Path('billing/billing.db'), Path('billing/research.db'), Path('billing/fund_data.db'), Path('billing/meter.db')]
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in test_phases_1_to_3.py
**1. File Path:** .\test_phases_1_to_3.py
**2. Line Number:** 31
**3. Exact Code Snippet:** s_conn = sqlite3.connect(path)
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in test_wrapper.py
**1. File Path:** .\test_wrapper.py
**2. Line Number:** 4
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in test_wrapper.py
**1. File Path:** .\test_wrapper.py
**2. Line Number:** 7
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in test_wrapper.py
**1. File Path:** .\test_wrapper.py
**2. Line Number:** 21
**3. Exact Code Snippet:** with get_connection("billing.db") as ctx_conn:
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.IntegrityError in test_wrapper.py
**1. File Path:** .\test_wrapper.py
**2. Line Number:** 30
**3. Exact Code Snippet:** except sqlite3.IntegrityError:
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in verify_neon.py
**1. File Path:** .\verify_neon.py
**2. Line Number:** 6
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in verify_neon.py
**1. File Path:** .\verify_neon.py
**2. Line Number:** 39
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in verify_neon2.py
**1. File Path:** .\verify_neon2.py
**2. Line Number:** 6
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in verify_neon2.py
**1. File Path:** .\verify_neon2.py
**2. Line Number:** 13
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in risk_manager.py
**1. File Path:** .\agents\risk_manager.py
**2. Line Number:** 20
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in risk_manager.py
**1. File Path:** .\agents\risk_manager.py
**2. Line Number:** 80
**3. Exact Code Snippet:** self.db_path = self.data_dir / "billing.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in risk_manager.py
**1. File Path:** .\agents\risk_manager.py
**2. Line Number:** 94
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in risk_manager.py
**1. File Path:** .\agents\risk_manager.py
**2. Line Number:** 294
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in email_digest.py
**1. File Path:** .\automation\email_digest.py
**2. Line Number:** 11
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in email_digest.py
**1. File Path:** .\automation\email_digest.py
**2. Line Number:** 23
**3. Exact Code Snippet:** FUND_DATA_DB = BILLING_DIR / "fund_data.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in email_digest.py
**1. File Path:** .\automation\email_digest.py
**2. Line Number:** 56
**3. Exact Code Snippet:** conn = get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in email_digest.py
**1. File Path:** .\automation\email_digest.py
**2. Line Number:** 101
**3. Exact Code Snippet:** conn = get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in email_digest.py
**1. File Path:** .\automation\email_digest.py
**2. Line Number:** 102
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.IntegrityError in email_digest.py
**1. File Path:** .\automation\email_digest.py
**2. Line Number:** 164
**3. Exact Code Snippet:** except sqlite3.IntegrityError:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.IntegrityError in email_digest.py
**1. File Path:** .\automation\email_digest.py
**2. Line Number:** 190
**3. Exact Code Snippet:** except sqlite3.IntegrityError:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in email_digest.py
**1. File Path:** .\automation\email_digest.py
**2. Line Number:** 449
**3. Exact Code Snippet:** """Ensure research.db tables exist and backfill observation memory."""
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in master_daily.py
**1. File Path:** .\automation\master_daily.py
**2. Line Number:** 25
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in backtest_90day.py
**1. File Path:** .\backtesting\backtest_90day.py
**2. Line Number:** 24
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### fund_data.db in backtest_90day.py
**1. File Path:** .\backtesting\backtest_90day.py
**2. Line Number:** 39
**3. Exact Code Snippet:** FUND_DATA_DB = BILLING_DIR / "fund_data.db"
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in backtest_90day.py
**1. File Path:** .\backtesting\backtest_90day.py
**2. Line Number:** 83
**3. Exact Code Snippet:** conn = sqlite3.connect(str(FUND_DATA_DB))
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.Row in backtest_90day.py
**1. File Path:** .\backtesting\backtest_90day.py
**2. Line Number:** 84
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in reanalyze_buy_metrics.py
**1. File Path:** .\backtesting\reanalyze_buy_metrics.py
**2. Line Number:** 12
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### fund_data.db in reanalyze_buy_metrics.py
**1. File Path:** .\backtesting\reanalyze_buy_metrics.py
**2. Line Number:** 23
**3. Exact Code Snippet:** FUND_DATA_DB = BILLING_DIR / "fund_data.db"
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### fund_data.db in reanalyze_buy_metrics.py
**1. File Path:** .\backtesting\reanalyze_buy_metrics.py
**2. Line Number:** 38
**3. Exact Code Snippet:** conn = get_connection("fund_data.db")
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### fund_data.db in reanalyze_buy_metrics.py
**1. File Path:** .\backtesting\reanalyze_buy_metrics.py
**2. Line Number:** 224
**3. Exact Code Snippet:** conn = get_connection("fund_data.db")
**4. Classification:** TEST_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### meter.db in init_meter_db.py
**1. File Path:** .\billing\init_meter_db.py
**2. Line Number:** 3
**3. Exact Code Snippet:** Initialize billing/meter.db — Legacy billing meter database
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in init_meter_db.py
**1. File Path:** .\billing\init_meter_db.py
**2. Line Number:** 9
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in init_meter_db.py
**1. File Path:** .\billing\init_meter_db.py
**2. Line Number:** 14
**3. Exact Code Snippet:** DB_PATH = BASE_DIR / "billing" / "meter.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### meter.db in init_meter_db.py
**1. File Path:** .\billing\init_meter_db.py
**2. Line Number:** 18
**3. Exact Code Snippet:** """Create meter.db with required tables if it doesn't exist."""
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in init_meter_db.py
**1. File Path:** .\billing\init_meter_db.py
**2. Line Number:** 22
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in meter.py
**1. File Path:** .\billing\meter.py
**2. Line Number:** 3
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in meter.py
**1. File Path:** .\billing\meter.py
**2. Line Number:** 23
**3. Exact Code Snippet:** self.db_path = self.data_dir / "billing.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in meter.py
**1. File Path:** .\billing\meter.py
**2. Line Number:** 35
**3. Exact Code Snippet:** self.conn = get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in meter.py
**1. File Path:** .\billing\meter.py
**2. Line Number:** 36
**3. Exact Code Snippet:** self.conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in meter.py
**1. File Path:** .\billing\meter.py
**2. Line Number:** 42
**3. Exact Code Snippet:** self.conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 23
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 217
**3. Exact Code Snippet:** DB_PATH = BILLING_DIR / "billing.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 218
**3. Exact Code Snippet:** FUND_DATA_DB = BILLING_DIR / "fund_data.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 246
**3. Exact Code Snippet:** """Get database connection to billing.db (prediction_ledger, veto_archive)."""
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 247
**3. Exact Code Snippet:** conn = db_get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 248
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 486
**3. Exact Code Snippet:** conn = db_get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 495
**3. Exact Code Snippet:** conn = db_get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 503
**3. Exact Code Snippet:** conn = db_get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 511
**3. Exact Code Snippet:** conn = db_get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 550
**3. Exact Code Snippet:** conn = db_get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 551
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 763
**3. Exact Code Snippet:** """Get evidence-based trust metrics from research.db (no vanity metrics)."""
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 1950
**3. Exact Code Snippet:** conn = db_get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 2298
**3. Exact Code Snippet:** research_db_path = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 2305
**3. Exact Code Snippet:** conn = db_get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 2325
**3. Exact Code Snippet:** conn2 = db_get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 2337
**3. Exact Code Snippet:** conn3 = db_get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3282
**3. Exact Code Snippet:** import sqlite3, json
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3284
**3. Exact Code Snippet:** conn = db_get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3285
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3300
**3. Exact Code Snippet:** import sqlite3, json
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3310
**3. Exact Code Snippet:** conn = db_get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3332
**3. Exact Code Snippet:** import sqlite3, json
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3339
**3. Exact Code Snippet:** conn = db_get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3836
**3. Exact Code Snippet:** conn = db_get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3908
**3. Exact Code Snippet:** _conn = db_get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3953
**3. Exact Code Snippet:** _fconn = db_get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3977
**3. Exact Code Snippet:** _vconn = db_get_connection("billing.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3982
**3. Exact Code Snippet:** print(f"  [billing.db] {_tbl}: {_cnt} rows")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3985
**3. Exact Code Snippet:** print(f"  [billing.db] verification failed: {_ve}")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 3989
**3. Exact Code Snippet:** _vconn2 = db_get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 4007
**3. Exact Code Snippet:** print(f"  [research.db] {_tbl}: {_cnt} rows")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 4009
**3. Exact Code Snippet:** print(f"  [research.db] {_tbl}: MISSING")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in app.py
**1. File Path:** .\dashboard\app.py
**2. Line Number:** 4012
**3. Exact Code Snippet:** print(f"  [research.db] verification failed: {_ve}")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 8
**3. Exact Code Snippet:** billing.db:   prediction_ledger, veto_archive, decisions, performance_log,
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 10
**3. Exact Code Snippet:** research.db:  companies, filings, financial_series, forensic_flags,
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 15
**3. Exact Code Snippet:** fund_data.db: fund_params, fund_uploads
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 18
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 24
**3. Exact Code Snippet:** # billing.db
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 125
**3. Exact Code Snippet:** # research.db — core tables
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 269
**3. Exact Code Snippet:** # research.db — observation / validation tables
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 363
**3. Exact Code Snippet:** # research.db — evolution / quality tables (from evolution_quality.py)
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 476
**3. Exact Code Snippet:** # fund_data.db
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.OperationalError in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 525
**3. Exact Code Snippet:** except sqlite3.OperationalError:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### billing.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 530
**3. Exact Code Snippet:** """Create/verify billing.db tables."""
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 539
**3. Exact Code Snippet:** """Create/verify research.db tables + run migrations."""
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in schemas.py
**1. File Path:** .\dashboard\schemas.py
**2. Line Number:** 551
**3. Exact Code Snippet:** """Create/verify fund_data.db tables."""
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in seed_db.py
**1. File Path:** .\dashboard\seed_db.py
**2. Line Number:** 14
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in seed_db.py
**1. File Path:** .\dashboard\seed_db.py
**2. Line Number:** 25
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### fund_data.db in seed_db.py
**1. File Path:** .\dashboard\seed_db.py
**2. Line Number:** 26
**3. Exact Code Snippet:** FUND_DB = BILLING_DIR / "fund_data.db"
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in seed_db.py
**1. File Path:** .\dashboard\seed_db.py
**2. Line Number:** 31
**3. Exact Code Snippet:** print("[seed] Initializing research.db...")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in seed_db.py
**1. File Path:** .\dashboard\seed_db.py
**2. Line Number:** 40
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in seed_db.py
**1. File Path:** .\dashboard\seed_db.py
**2. Line Number:** 273
**3. Exact Code Snippet:** print("  [done] research.db seeded")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### fund_data.db in seed_db.py
**1. File Path:** .\dashboard\seed_db.py
**2. Line Number:** 278
**3. Exact Code Snippet:** print("[seed] Initializing fund_data.db...")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### fund_data.db in seed_db.py
**1. File Path:** .\dashboard\seed_db.py
**2. Line Number:** 279
**3. Exact Code Snippet:** conn = get_connection("fund_data.db")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### fund_data.db in seed_db.py
**1. File Path:** .\dashboard\seed_db.py
**2. Line Number:** 317
**3. Exact Code Snippet:** print("  [done] fund_data.db seeded")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in generate_one_pager.py
**1. File Path:** .\documents\generate_one_pager.py
**2. Line Number:** 10
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in generate_one_pager.py
**1. File Path:** .\documents\generate_one_pager.py
**2. Line Number:** 20
**3. Exact Code Snippet:** FUND_DATA_DB = BILLING_DIR / "fund_data.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in generate_one_pager.py
**1. File Path:** .\documents\generate_one_pager.py
**2. Line Number:** 27
**3. Exact Code Snippet:** conn = get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in generate_one_pager.py
**1. File Path:** .\documents\generate_one_pager.py
**2. Line Number:** 28
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in generate_whitepaper.py
**1. File Path:** .\documents\generate_whitepaper.py
**2. Line Number:** 10
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in generate_whitepaper.py
**1. File Path:** .\documents\generate_whitepaper.py
**2. Line Number:** 21
**3. Exact Code Snippet:** FUND_DATA_DB = BILLING_DIR / "fund_data.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in generate_whitepaper.py
**1. File Path:** .\documents\generate_whitepaper.py
**2. Line Number:** 28
**3. Exact Code Snippet:** conn = get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in generate_whitepaper.py
**1. File Path:** .\documents\generate_whitepaper.py
**2. Line Number:** 29
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in daily_cycle.py
**1. File Path:** .\operations\daily_cycle.py
**2. Line Number:** 20
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in daily_cycle.py
**1. File Path:** .\operations\daily_cycle.py
**2. Line Number:** 38
**3. Exact Code Snippet:** FUND_DATA_DB = BILLING_DIR / "fund_data.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in daily_cycle.py
**1. File Path:** .\operations\daily_cycle.py
**2. Line Number:** 43
**3. Exact Code Snippet:** conn = get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### fund_data.db in daily_cycle.py
**1. File Path:** .\operations\daily_cycle.py
**2. Line Number:** 92
**3. Exact Code Snippet:** conn = get_connection("fund_data.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in daily_cycle.py
**1. File Path:** .\operations\daily_cycle.py
**2. Line Number:** 93
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in backfill_memory.py
**1. File Path:** .\research\backfill_memory.py
**2. Line Number:** 10
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in backfill_memory.py
**1. File Path:** .\research\backfill_memory.py
**2. Line Number:** 18
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in backfill_memory.py
**1. File Path:** .\research\backfill_memory.py
**2. Line Number:** 78
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in backfill_memory.py
**1. File Path:** .\research\backfill_memory.py
**2. Line Number:** 79
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in evolution_quality.py
**1. File Path:** .\research\evolution_quality.py
**2. Line Number:** 11
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in evolution_quality.py
**1. File Path:** .\research\evolution_quality.py
**2. Line Number:** 19
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in evolution_quality.py
**1. File Path:** .\research\evolution_quality.py
**2. Line Number:** 39
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in evolution_quality.py
**1. File Path:** .\research\evolution_quality.py
**2. Line Number:** 40
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in fii_intelligence.py
**1. File Path:** .\research\fii_intelligence.py
**2. Line Number:** 9
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in fii_intelligence.py
**1. File Path:** .\research\fii_intelligence.py
**2. Line Number:** 17
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in fii_intelligence.py
**1. File Path:** .\research\fii_intelligence.py
**2. Line Number:** 43
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in fii_intelligence.py
**1. File Path:** .\research\fii_intelligence.py
**2. Line Number:** 44
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in observation_registry.py
**1. File Path:** .\research\observation_registry.py
**2. Line Number:** 9
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in observation_registry.py
**1. File Path:** .\research\observation_registry.py
**2. Line Number:** 17
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in observation_registry.py
**1. File Path:** .\research\observation_registry.py
**2. Line Number:** 24
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in observation_registry.py
**1. File Path:** .\research\observation_registry.py
**2. Line Number:** 25
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in observation_stream.py
**1. File Path:** .\research\observation_stream.py
**2. Line Number:** 6
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in observation_stream.py
**1. File Path:** .\research\observation_stream.py
**2. Line Number:** 14
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in observation_stream.py
**1. File Path:** .\research\observation_stream.py
**2. Line Number:** 17
**3. Exact Code Snippet:** conn = db_get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in observation_stream.py
**1. File Path:** .\research\observation_stream.py
**2. Line Number:** 18
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in portfolio_intelligence.py
**1. File Path:** .\research\portfolio_intelligence.py
**2. Line Number:** 7
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in portfolio_intelligence.py
**1. File Path:** .\research\portfolio_intelligence.py
**2. Line Number:** 16
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in portfolio_intelligence.py
**1. File Path:** .\research\portfolio_intelligence.py
**2. Line Number:** 19
**3. Exact Code Snippet:** conn = db_get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in portfolio_intelligence.py
**1. File Path:** .\research\portfolio_intelligence.py
**2. Line Number:** 20
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in seed_muthoot.py
**1. File Path:** .\research\seed_muthoot.py
**2. Line Number:** 3
**3. Exact Code Snippet:** Seed Muthoot Finance (MUTHOOTFIN) data into research.db.
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in seed_muthoot.py
**1. File Path:** .\research\seed_muthoot.py
**2. Line Number:** 10
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in seed_muthoot.py
**1. File Path:** .\research\seed_muthoot.py
**2. Line Number:** 18
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in seed_muthoot.py
**1. File Path:** .\research\seed_muthoot.py
**2. Line Number:** 45
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in seed_pageind.py
**1. File Path:** .\research\seed_pageind.py
**2. Line Number:** 3
**3. Exact Code Snippet:** Seed Page Industries (PAGEIND) data into research.db.
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in seed_pageind.py
**1. File Path:** .\research\seed_pageind.py
**2. Line Number:** 10
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in seed_pageind.py
**1. File Path:** .\research\seed_pageind.py
**2. Line Number:** 18
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in seed_pageind.py
**1. File Path:** .\research\seed_pageind.py
**2. Line Number:** 48
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in thesis_evolution_engine.py
**1. File Path:** .\research\thesis_evolution_engine.py
**2. Line Number:** 10
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in thesis_evolution_engine.py
**1. File Path:** .\research\thesis_evolution_engine.py
**2. Line Number:** 18
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in thesis_evolution_engine.py
**1. File Path:** .\research\thesis_evolution_engine.py
**2. Line Number:** 48
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in thesis_evolution_engine.py
**1. File Path:** .\research\thesis_evolution_engine.py
**2. Line Number:** 49
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in thesis_tracker.py
**1. File Path:** .\research\thesis_tracker.py
**2. Line Number:** 7
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in thesis_tracker.py
**1. File Path:** .\research\thesis_tracker.py
**2. Line Number:** 15
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in thesis_tracker.py
**1. File Path:** .\research\thesis_tracker.py
**2. Line Number:** 18
**3. Exact Code Snippet:** conn = db_get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in thesis_tracker.py
**1. File Path:** .\research\thesis_tracker.py
**2. Line Number:** 19
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in fii_flow.py
**1. File Path:** .\research\macro\fii_flow.py
**2. Line Number:** 13
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in fii_flow.py
**1. File Path:** .\research\macro\fii_flow.py
**2. Line Number:** 22
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in fii_flow.py
**1. File Path:** .\research\macro\fii_flow.py
**2. Line Number:** 74
**3. Exact Code Snippet:** with get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in fii_flow.py
**1. File Path:** .\research\macro\fii_flow.py
**2. Line Number:** 79
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in fii_flow.py
**1. File Path:** .\research\macro\fii_flow.py
**2. Line Number:** 80
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in import_sensitivity.py
**1. File Path:** .\research\macro\import_sensitivity.py
**2. Line Number:** 11
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in import_sensitivity.py
**1. File Path:** .\research\macro\import_sensitivity.py
**2. Line Number:** 20
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in import_sensitivity.py
**1. File Path:** .\research\macro\import_sensitivity.py
**2. Line Number:** 177
**3. Exact Code Snippet:** with get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in import_sensitivity.py
**1. File Path:** .\research\macro\import_sensitivity.py
**2. Line Number:** 182
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in import_sensitivity.py
**1. File Path:** .\research\macro\import_sensitivity.py
**2. Line Number:** 183
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in macro_engine.py
**1. File Path:** .\research\macro\macro_engine.py
**2. Line Number:** 8
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in macro_engine.py
**1. File Path:** .\research\macro\macro_engine.py
**2. Line Number:** 22
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in macro_engine.py
**1. File Path:** .\research\macro\macro_engine.py
**2. Line Number:** 35
**3. Exact Code Snippet:** with get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in macro_health.py
**1. File Path:** .\research\macro\macro_health.py
**2. Line Number:** 22
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in macro_health.py
**1. File Path:** .\research\macro\macro_health.py
**2. Line Number:** 32
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in macro_health.py
**1. File Path:** .\research\macro\macro_health.py
**2. Line Number:** 81
**3. Exact Code Snippet:** with get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in macro_health.py
**1. File Path:** .\research\macro\macro_health.py
**2. Line Number:** 86
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in macro_health.py
**1. File Path:** .\research\macro\macro_health.py
**2. Line Number:** 87
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in reserve_stress.py
**1. File Path:** .\research\macro\reserve_stress.py
**2. Line Number:** 15
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in reserve_stress.py
**1. File Path:** .\research\macro\reserve_stress.py
**2. Line Number:** 25
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in reserve_stress.py
**1. File Path:** .\research\macro\reserve_stress.py
**2. Line Number:** 70
**3. Exact Code Snippet:** with get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in reserve_stress.py
**1. File Path:** .\research\macro\reserve_stress.py
**2. Line Number:** 75
**3. Exact Code Snippet:** conn = get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in reserve_stress.py
**1. File Path:** .\research\macro\reserve_stress.py
**2. Line Number:** 76
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 9
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 18
**3. Exact Code Snippet:** RESEARCH_DB = BILLING_DIR / "research.db"
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 129
**3. Exact Code Snippet:** with db_get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 136
**3. Exact Code Snippet:** with db_get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 143
**3. Exact Code Snippet:** conn = db_get_connection("research.db")
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.Row in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 144
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.IntegrityError in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 168
**3. Exact Code Snippet:** except sqlite3.IntegrityError:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 439
**3. Exact Code Snippet:** with db_get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 649
**3. Exact Code Snippet:** with db_get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 711
**3. Exact Code Snippet:** with db_get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 826
**3. Exact Code Snippet:** with db_get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.OperationalError in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 831
**3. Exact Code Snippet:** except sqlite3.OperationalError:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 838
**3. Exact Code Snippet:** with db_get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### research.db in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 845
**3. Exact Code Snippet:** with db_get_connection("research.db") as conn:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.OperationalError in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 850
**3. Exact Code Snippet:** except sqlite3.OperationalError:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### sqlite3.OperationalError in research_db.py
**1. File Path:** .\research\storage\research_db.py
**2. Line Number:** 855
**3. Exact Code Snippet:** except sqlite3.OperationalError:
**4. Classification:** RUNTIME_PRODUCTION
**5. Risk If Removed:** HIGH
**6. Recommendation:** REFACTOR

### import sqlite3 in list_tables.py
**1. File Path:** .\scripts\list_tables.py
**2. Line Number:** 1
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in list_tables.py
**1. File Path:** .\scripts\list_tables.py
**2. Line Number:** 2
**3. Exact Code Snippet:** conn = sqlite3.connect('c:/Users/lokes/Downloads/project/sovereign-alpha/data/research.db')
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in list_tables.py
**1. File Path:** .\scripts\list_tables.py
**2. Line Number:** 6
**3. Exact Code Snippet:** print("Tables in research.db:")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in list_tables_billing.py
**1. File Path:** .\scripts\list_tables_billing.py
**2. Line Number:** 1
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in list_tables_billing.py
**1. File Path:** .\scripts\list_tables_billing.py
**2. Line Number:** 3
**3. Exact Code Snippet:** conn = get_connection("billing.db")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in list_tables_billing.py
**1. File Path:** .\scripts\list_tables_billing.py
**2. Line Number:** 7
**3. Exact Code Snippet:** print("Tables in billing.db:")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in red_team_attack.py
**1. File Path:** .\scripts\red_team_attack.py
**2. Line Number:** 1
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in red_team_attack.py
**1. File Path:** .\scripts\red_team_attack.py
**2. Line Number:** 19
**3. Exact Code Snippet:** conn = sqlite3.connect(str(BILLING_DIR / "billing.db"))
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in red_team_attack.py
**1. File Path:** .\scripts\red_team_attack.py
**2. Line Number:** 63
**3. Exact Code Snippet:** conn = sqlite3.connect(str(BILLING_DIR / "billing.db"))
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in seed_all_empty_tables.py
**1. File Path:** .\scripts\seed_all_empty_tables.py
**2. Line Number:** 1
**3. Exact Code Snippet:** """Seed all 15 tables currently empty in research.db."""
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in seed_all_empty_tables.py
**1. File Path:** .\scripts\seed_all_empty_tables.py
**2. Line Number:** 3
**3. Exact Code Snippet:** import sqlite3, json
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in seed_all_empty_tables.py
**1. File Path:** .\scripts\seed_all_empty_tables.py
**2. Line Number:** 8
**3. Exact Code Snippet:** DB = BASE / "billing" / "research.db"
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in seed_all_empty_tables.py
**1. File Path:** .\scripts\seed_all_empty_tables.py
**2. Line Number:** 16
**3. Exact Code Snippet:** conn = sqlite3.connect(str(db))
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.Row in seed_all_empty_tables.py
**1. File Path:** .\scripts\seed_all_empty_tables.py
**2. Line Number:** 17
**3. Exact Code Snippet:** conn.row_factory = sqlite3.Row
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### import sqlite3 in verify_db.py
**1. File Path:** .\scripts\verify_db.py
**2. Line Number:** 1
**3. Exact Code Snippet:** import sqlite3
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in verify_db.py
**1. File Path:** .\scripts\verify_db.py
**2. Line Number:** 5
**3. Exact Code Snippet:** db_path = Path('c:/Users/lokes/Downloads/project/sovereign-alpha/billing/billing.db')
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in verify_db.py
**1. File Path:** .\scripts\verify_db.py
**2. Line Number:** 6
**3. Exact Code Snippet:** research_db = Path('c:/Users/lokes/Downloads/project/sovereign-alpha/data/research.db')
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in verify_db.py
**1. File Path:** .\scripts\verify_db.py
**2. Line Number:** 8
**3. Exact Code Snippet:** conn1 = sqlite3.connect(db_path)
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in verify_db.py
**1. File Path:** .\scripts\verify_db.py
**2. Line Number:** 20
**3. Exact Code Snippet:** print(f"Predictions (billing.db): {predictions}")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### billing.db in verify_db.py
**1. File Path:** .\scripts\verify_db.py
**2. Line Number:** 21
**3. Exact Code Snippet:** print(f"Vetoes (billing.db): {vetoes}")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### sqlite3.connect in verify_db.py
**1. File Path:** .\scripts\verify_db.py
**2. Line Number:** 26
**3. Exact Code Snippet:** conn2 = sqlite3.connect(research_db)
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in verify_db.py
**1. File Path:** .\scripts\verify_db.py
**2. Line Number:** 30
**3. Exact Code Snippet:** print(f"Observations (research.db): {obs}")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in verify_db.py
**1. File Path:** .\scripts\verify_db.py
**2. Line Number:** 35
**3. Exact Code Snippet:** print(f"Autopsies (research.db): {auto}")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

### research.db in verify_db.py
**1. File Path:** .\scripts\verify_db.py
**2. Line Number:** 42
**3. Exact Code Snippet:** print(f"Failures (research.db): {fail}")
**4. Classification:** ARCHIVE_ONLY
**5. Risk If Removed:** LOW
**6. Recommendation:** KEEP

## Summary

- **Total Runtime Production Dependencies:** 246
- **Total Runtime Optional Dependencies:** 0
- **Total Test Dependencies:** 19
- **Total Archive Dependencies:** 58
- **Total Dead Code Dependencies:** 0

## Final Question

**Can SQLite be removed from runtime TODAY?**

**NO**

**Evidence:** There are still RUNTIME_PRODUCTION dependencies listed above. Specifically, database.py heavily relies on sqlite3.IntegrityError and sqlite3.OperationalError for translating psycopg2 exceptions, which causes transitive dependencies throughout the application. Removing SQLite from runtime today would crash engines whenever a unique constraint violation or operational error occurs.