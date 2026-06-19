# Root Cause Analysis

## Findings Classification

- **A. Git Sync Failure**: FALSE (0%)
- **B. HF Build Failure**: FALSE (0%)
- **C. HF Cache Issue**: FALSE (0%)
- **D. Runtime Loading Wrong Files**: FALSE (0%)
- **E. Wrong Database**: TRUE (100%) - It runs against an empty DB instead of a hydrated one.
- **F. Startup Overwriting Data**: TRUE (100%) - `IS_CLOUD` logic aggressively deletes the database.
- **G. Environment Variable Issue**: FALSE (0%) - The variables are correctly passed; the logic interacting with them is destructive.

## Primary Root Cause
The true root cause is **Class F: Startup Overwriting Data**.
The codebase contains a hardcoded logic bomb in `dashboard/app.py`:
```python
if IS_CLOUD and DB_PATH.exists():
    print("[seed] Cloud deploy detected - removing old DB for clean schema")
    DB_PATH.unlink()
```
Upon a successful deployment and boot in the Hugging Face environment, the backend automatically wipes the database clean. Consequently, queries meant to return the newly verified metrics, decisions, and outcomes return exactly 0 results. The dashboard seamlessly handles this empty state, giving the illusion to the user that "nothing has changed" because the UI structure persists, but the underlying verified data has been silently obliterated by the startup sequence.
