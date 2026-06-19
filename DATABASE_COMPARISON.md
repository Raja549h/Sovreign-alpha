# Database Comparison

## Local Database vs. Deployed Database

- **Is HF using the same database as local?** No. 
- **Why?** `.gitignore` explicitly ignores `billing.db` (`*.db`, `billing/billing.db`). Therefore, the rich dataset present on the local machine during verification tests is never transmitted to the Hugging Face Space repository.

## State of Deployed Database
- **Mounted Storage:** `None` (Ephemeral).
- **Persistent Volume:** `None`.
- **Database Initialization:** 
  During Docker build, `seed_db.py` creates `research.db` and `fund_data.db`. However, Sovereign Alpha's latest dashboard logic relies exclusively on `billing.db`.
- **Table Counts / Evidence Counts / Predictions:** **ZERO**.

## Evidence
Because the database is re-initialized by the application and is fully empty, queries like `SELECT COUNT(*) FROM prediction_ledger` evaluate to `0`. The dashboard UI attempts to render this empty state, which to a casual observer appears as "no change" or identical to the previous broken state.
