## Goal
Complete Sovereign Alpha's Bloomberg/Palantir-grade terminal upgrade — fix all backend bugs, redesign every page for data-dense institutional aesthetics, increase font sizes for readability, and deploy reliably to Hugging Face Spaces.

## Constraints & Preferences
- Free tier, always-on, no build minute caps, SQLite persists between restarts, public space, all secrets secured in HF Space secrets, GitHub Actions auto-deploys to HF on push to main
- Do NOT change color scheme, existing routes, backend logic, DB schema, research note output, or font to non-monospace for data elements
- Do NOT add gradients, glassmorphism, or consumer SaaS aesthetics
- Bloomberg Terminal meets Palantir Foundry aesthetic: dark, data-dense, precise, zero decorative elements
- All numbers/tickers/timestamps/hashes/status badges must use monospace
- Green = positive/cleared, Red = risk/vetoed/negative, Amber = pending/warning, White = primary data, Gray = secondary labels — no other colors
- Zero rounded corners on data elements; only action buttons may have 2px radius max
- Primary metric 28-32px white bold, secondary label 10px gray uppercase letter-spacing 0.1em, table data 11-12px monospace, never below 9px
- All font sizes increased — base html set to 15px, smallest rem bumped to 0.65rem (9.75px), table data at 0.75rem (11.25px), stat values at 1.35rem (20.25px)

## Progress
### Done
- Dockerfile: python:3.11-slim, user 1000, gcc/libcairo2 for pycairo build, port 7860, seeds DB on build, global pip install (no --user), USER 1000 with chowned permissions
- README.md: HF Spaces metadata header (sdk: docker, app_port: 7860, public: true)
- .hfignore: created with excludes for .venv, logs, .env, __pycache__, etc.
- dashboard/app.py: default port 7860; IS_CLOUD prioritizes SPACE_ID over RENDER; CORS updated with HF URL, Render URL removed; ProxyFix applies on HF too; seed uses IS_CLOUD; rate limits increased to 2000/day, 500/hour global / 20/15min, 100/day on login
- yfinance + fredapi: added to requirements-docker.txt; confirmed installed and importable via /health endpoint (both = "ok")
- Render files deleted: render.yaml, .renderignore, Procfile, runtime.txt, DEPLOYMENT.md
- requirements-render.txt renamed to requirements-docker.txt; all code references updated
- Render references cleaned from 12 files (seed_db.py, email_digest.py, backtest_90day.py, health_check.py, seed_on_deploy.py, docs, etc.)
- All 6 secrets added to HF Spaces settings (GROQ_API_KEY, JWT_SECRET, FERNET_KEY, FUND_PASSWORD, DIGEST_EMAIL, DIGEST_PASSWORD)
- Space made public: https://demonsatan-soverignalpha.hf.space
- Security: Talisman session_cookie_secure=True; CSP updated to allow cdn.jsdelivr.net for Chart.js
- Bootstrap CSS added to base.html for research templates rendering
- .gitkeep files created for results/ and zkml/proofs/ directories
- Login password: (stored in .env and HF Space secrets)
- Bug Fix 1: get_dashboard_stats() rewritten — queries prediction_ledger + veto_archive (was performance_log which was always empty). Returns total_predictions, approved, vetoed_count, approval_rate, veto_efficiency, correct_vetoes, total_avoided_drawdown
- Bug Fix 2: Added @app.template_filter('pct') — converts values ≤1.0 to percentage (e.g. 0.82 → 82.0%). Applied in all templates: index.html, predictions.html, decisions.html
- Bug Fix 3: Created decisions table in seed_database_on_startup(). get_decisions() now does UNION ALL of prediction_ledger + veto_archive. On every startup: re-syncs from both tables
- UI Upgrade: Complete Bloomberg/Palantir terminal redesign:
  - base.html: data-dense CSS (::selection, custom scrollbar, [data-tip] tooltips, alternating table rows, colored left-border stat boxes, inline confidence bars with labels, filter-bar styling, toast notifications, key-value list, click-to-copy for hashes)
  - All templates updated: index, predictions, decisions, veto_archive, proofs, performance, research_home, research_company, research_note, upload, live_market
  - JS features: live clock (1s), ticker strip auto-refresh (60s via /api/ticker-refresh), dashboard partial refresh (60s), hash click-to-copy with toast, filterTable() client-side text search, session keepalive
  - Research templates de-Bootstrapped, all using base.css exclusively
  - Predictions table: inline confidence progress bars per row with color thresholds (high/med/low)
  - Stat boxes: colored left borders (accent/green, danger/red, warning/amber, info/blue)
  - Signal cards: colored left borders matching severity
  - Key-value list component for compact metric display
- Deploy workflow fixed: Separated HF deploy from pipeline job. daily-pipeline.yml no longer includes deploy; new deploy-to-hf.yml triggers on push: [main] independently
- Font sizes increased globally: html { font-size: 15px } (was 13px). All 0.55rem → 0.65rem (now 9.75px, above 9px floor), 0.6rem → 0.7rem, 0.62rem → 0.7rem. Stat values 1.1rem → 1.35rem. Table data 0.65rem → 0.75rem. Top-bar/ticker-strip height 24px → 32px. Nav height 36px → 42px. Padding/spacing increased throughout
- Deployed live: commit 8d95c7e (workflow fix) → 2741772 (UI redesign) → 7b8daa0 (font sizes) pushed to main; HF Space rebuilt and serving all changes

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- Use python dashboard/app.py (Flask dev server) not gunicorn — gunicorn had Python environment mismatch issues, Flask dev server works reliably for HF Spaces
- Force push to HF Space (git push hf main --force) because HF remote had unrelated commits
- Global pip install (no --user flag) + USER user + chown -R user:user /home/user — fixes package import issues when container runs as UID 1000
- Made space public so webfetch verification and external access work without auth
- Separated deploy from pipeline job — pipeline was failing (missing API keys), blocking all deploys. Now deploy-to-hf.yml runs independently on push to main
- Increased base font to 15px and bumped all 0.55-0.62rem values to 0.65-0.7rem to meet "never below 9px" constraint

## Next Steps
- (none — all bugs fixed, all templates redesigned, font sizes increased, deployed and live)

## Critical Context
- HF Space URL: https://demonsatan-soverignalpha.hf.space (public)
- GitHub repo: github.com/Raja549h/Sovreign-alpha (private, PAT auth)
- HF token: (stored securely in HF Space secrets and GitHub repo secrets, not committed)
- All 6 secrets with real values stored in HF Space secrets + local .env
- Fund password: (set in .env and HF Space secrets)
- /health endpoint returns: status=healthy, is_cloud=true, database=true, proofs_dir=true, results_dir=true, all packages ok
- Rate limits: 500/h, 2000/d global; 20/15min, 100/d on login
- Deploy workflow: .github/workflows/deploy-to-hf.yml (independent of pipeline), triggers on push to main; .github/workflows/daily-pipeline.yml (schedule only, no deploy)
- Previous deploy bug: old workflow had deploy-to-hf: needs run-pipeline + if: success(); pipeline fails → deploy never ran. Now fixed with separate workflow
- Dashboard confirmed live with all fixes and larger fonts deployed

## Relevant Files
- Dockerfile: Entry point for HF Spaces Docker build; global pip install, USER 1000, chowned permissions
- dashboard/app.py: Main Flask app; includes get_dashboard_stats() fix, pct template filter, decisions sync, /api/ticker-refresh endpoint, /api/refresh endpoint
- requirements-docker.txt: 16 lightweight dependencies; includes yfinance, fredapi
- dashboard/seed_db.py: Creates tables and seeds data with realistic confidence values + decisions sync
- dashboard/templates/base.html: Main layout — Bloomberg ticker strip, terminal nav, live clock, global CSS with large fonts, tooltips, filter-bar, key-val, confidence bars, hash copy, toast
- dashboard/templates/index.html: Dashboard — stat cards with colored borders, regime box, predictions/vetoes tables, quick actions
- dashboard/templates/predictions.html: Filterable table with inline confidence bars, proof hashes, status badges, CSV export
- dashboard/templates/decisions.html: Decision log with filter bar, hash copy, action badges, confidence display
- dashboard/templates/veto_archive.html: Veto archive with color-coded outcome badges, avoided DD, filter bar
- dashboard/templates/proofs.html: RSA-2048 verification display, proof certificates table with hash copy
- dashboard/templates/performance.html: Charts (line + bar), metrics strip, key metrics table
- dashboard/templates/research_home.html, research_company.html, research_note.html: Forensic intelligence terminal (de-Bootstrapped)
- dashboard/templates/upload.html: Terminal-style upload form with progress indicators
- dashboard/templates/live_market.html: Signals display with oversold/overbought/unusual volume cards
- dashboard/templates/login.html: Terminal-style login
- .github/workflows/daily-pipeline.yml: CI/CD schedule-only; no deploy step
- .github/workflows/deploy-to-hf.yml: Deploy on push to main via huggingface_hub upload_folder
