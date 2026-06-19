# Configuration Audit

## Execution Configuration Logic
- **`SPACE_ID`**: Detected as present in HF Space environment.
- **`IS_CLOUD` Logic**: The variable `IS_CLOUD` evaluates to `True` strictly in the Hugging Face deployed environment. Locally, `IS_CLOUD` evaluates to `False`.
- **Cloud-Specific Execution Paths**: 
  In `dashboard/app.py`, there is a critical block triggered exclusively when `IS_CLOUD` is True:
  ```python
  if IS_CLOUD and DB_PATH.exists():
      print("[seed] Cloud deploy detected - removing old DB for clean schema")
      DB_PATH.unlink()
  ```

## Determination
HF deployment absolutely follows a fundamentally different logic path than local execution. Locally, the pre-populated `billing.db` persists because `IS_CLOUD` is false. In production, this cloud-specific execution path deliberately triggers data destruction.
