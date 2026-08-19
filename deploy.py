from huggingface_hub import HfApi
import os, sys
token = os.environ.get('HF_TOKEN')
if not token:
    print("::error::HF_TOKEN secret not set")
    sys.exit(1)
api = HfApi(token=token)
repo_id = "svrn-alpha/sovereignalpha"
print(f"Uploading to {repo_id}...")
try:
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        ignore_patterns=[
            ".git*", ".venv/", "venv/", "__pycache__/", "*.pyc",
            "research/data/filings/", "research/data/transcripts/",
            "logs/", "*.log", "exports/", ".env", "SUMMARY.md",
            "backtesting/", "documents/", "demo/", "security/",
            "requirements-pipeline.txt", "scratch/"
        ]
    )
    print("Deployed to HF Spaces successfully")
except Exception as e:
    print(f"::error::HF upload failed: {e}")
    sys.exit(1)
