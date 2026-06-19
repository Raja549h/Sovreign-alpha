# Startup Audit

## Startup Trace
1. **Docker Container Launch**: Hugging Face executes the container via `CMD ["python", "dashboard/app.py"]`.
2. **File Invocation**: `dashboard/app.py` launches first.
3. **Variable Assignment**: `IS_CLOUD` detects the Hugging Face `SPACE_ID` variable and resolves to `True`.
4. **Main Block Execution**: The `__main__` block begins execution.
5. **Database Interception**: 
   Because `IS_CLOUD` is True, `app.py` triggers an aggressive intercept:
   ```python
   if IS_CLOUD and DB_PATH.exists():
       DB_PATH.unlink()
   ```
6. **Initialization**: `app.py` invokes `init_billing_db()`, which generates a 100% empty `billing.db`.
7. **Application Loop**: Flask begins serving traffic using the now-empty database.

## Findings
- **Does startup overwrite data?** YES.
- **Does startup recreate databases?** YES. It literally deletes and recreates an empty shell.
- **Does startup load stale files?** No. It loads the exact, freshly committed files, but effectively bricks its own dataset by wiping it.
