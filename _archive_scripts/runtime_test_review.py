from crew import SovereignAlphaPipeline

try:
    pipeline = SovereignAlphaPipeline()
    print("PIPELINE_INIT_OK")
except Exception as exc:
    print(f"PIPELINE_INIT_FAIL {type(exc).__name__}: {exc}")
