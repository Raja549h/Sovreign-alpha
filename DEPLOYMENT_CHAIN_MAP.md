# Deployment Chain Map

## End-to-End Architecture Flow

1. **Local Repository** (`c:\Users\lokes\Downloads\project\sovereign-alpha`)
   - Developer commits code to `main` branch.
   
2. **Git Commit**
   - Head is advanced to latest hash (`5978ba9e2ea731dc62e1c926971e78cbe1d53466`).

3. **GitHub Repository** (`https://github.com/Raja549h/Sovreign-alpha.git`)
   - Receives the push. Triggers `.github/workflows/deploy-to-hf.yml`.
   
4. **Build Process (GitHub Actions)**
   - The workflow executes.
   - Bypasses `whoami()` check.
   - Uploads folder to Hugging Face Spaces using `huggingface_hub` SDK.

5. **Hugging Face Space Repository** (`https://huggingface.co/spaces/svrn-alpha/soverignalpha`)
   - Receives the uploaded files.
   - Generates a new synthetic HF Git commit (`b0e022c01bc2fd28aaf4dfa81bec5ea220fcd95a`).

6. **Build Process (Hugging Face)**
   - Detects file changes.
   - Builds Dockerfile.
   - Installs dependencies from `requirements-docker.txt`.
   - Runs `python dashboard/seed_db.py`.

7. **Runtime Container**
   - Container enters `RUNNING` stage.
   
8. **Application Startup**
   - Executes `python dashboard/app.py`.
   - Flask initializes.
   - Encounters `IS_CLOUD` specific startup block.

9. **Database Loading**
   - `IS_CLOUD` block deletes existing `billing.db`.
   - `init_billing_db()` initializes an empty schema.
   
10. **Dashboard**
    - Application serves web traffic on `https://svrn-alpha-soverignalpha.hf.space`.
    - Queries the empty `billing.db`.
    - Returns 0 predictions, 0 vetoes, empty data.
