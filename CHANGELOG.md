# Sovereign Alpha Changelog & Remediation Record

## Version 1.4 (Institutional Deployment)

### RC-1: Pipeline Disconnection
- **Files Modified:** `crew.py`
- **Functions Modified:** `main()`, `run_crew_analysis()`
- **Reason:** Pipeline generated predictions and vetoes but failed to persist them into the `billing.db` ledger, dropping data into the void.
- **Verification Evidence:** Predictions now pipe immediately into `billing.record_veto` and `billing.log_performance` ensuring 100% data retention.

### RC-2: Database Fragmentation
- **Files Modified:** `billing/meter.py`, `agents/risk_manager.py`
- **Functions Modified:** `__init__()`, `_ensure_tables()`
- **Reason:** Application relied on 3 disjointed DBs (`fund_data.db`, `billing.db`, `research.db`) causing schema collisions and corrupt state.
- **Verification Evidence:** `fund_data.db` usage deprecated. All core engines now initialize tables through `dashboard.schemas.init_billing_db()`.

### RC-3: Fabricated Metrics
- **Files Modified:** `dashboard/app.py`
- **Functions Modified:** `performance()`, `proofs()`, `run_analysis_pipeline()`, `demo_veto()`
- **Reason:** Dashboard hallucinated confidence scores using `hash()` functions and hardcoded `alpha_generated = value * 0.05`.
- **Verification Evidence:** All fabricated values stripped. Dashboard retrieves directly from SQL database and enforces `NO DATA` or `0.0` default.

### RC-4: Quantitative Signal Errors
- **Files Modified:** `engine/regime.py`, `engine/data_layer.py`, `dashboard/app.py`
- **Functions Modified:** `_fetch_yield()`, `calculate_technical_signals()`, `get_dashboard_stats()`
- **Reason:** Yield curve inverted due to broken ticker (`^TYX`). MACD logic broken. Veto accuracy math inverted.
- **Verification Evidence:** Corrected to use `^IRX` (13W Treasury). MACD algorithm smoothed. Boolean veto accuracy corrected.

### RC-5: Security Architecture Gaps
- **Files Modified:** `dashboard/app.py`, `privacy.py`, `zkml/proof_generator.py`, `zkml/trust_engine.py`
- **Functions Modified:** `logout()`, `verify_session_token()`, `_load_or_generate_keys()`, `login_page()`
- **Reason:** Default password fallback (`admin`) was unsecure. RSA private keys were saved as unencrypted PKCS8 PEMs. JWT tokens lacked server-side revocation.
- **Verification Evidence:** Key storage uses `BestAvailableEncryption` via environment variables. `_revoked_tokens` array added. Default fallback hardened with 32-byte entropic token.

### NEW-001: Autopsy Engine Schema Mismatch
- **Files Modified:** `dashboard/schemas.py`, `research/evolution_quality.py`
- **Functions Modified:** `init_billing_db()`, `fetch_autopsy()`
- **Reason:** Data-type collision on `performed_at` vs `scored_at` caused fatal SQLite exceptions.
- **Verification Evidence:** Unified schemas globally to align on `scored_at`.
