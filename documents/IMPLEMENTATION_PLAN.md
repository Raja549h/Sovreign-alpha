# SOVEREIGN ALPHA
## Implementation Plan

**Version:** 2.0  
**Date:** 2026-05-25  
**Classification:** Internal Use Only  
**Status:** Core implemented — see milestones for roadmap

---

## 1. DEVELOPMENT PHASES

### PHASE 0: Foundation (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| Flask app scaffolding | ✓ | 34 routes, Jinja2 templates |
| SQLite database schema | ✓ | 4 DBs: billing, fund_data, research, meter |
| Authentication system | ✓ | JWT session tokens, login/logout |
| Rate limiting | ✓ | flask-limiter, per-route limits |
| CSRF protection | ✓ | flask-wtf, all POST endpoints |
| CSP / Security headers | ✓ | Talisman, frame-ancestors none, HSTS |
| File upload handling | ✓ | CSV/Excel parse, column auto-detection |
| Input validation | ✓ | XSS/SQLi sanitization, ticker validation |

### PHASE 1: Data Persistence & Reliability (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| Seed data on first startup | ✓ | 5 predictions + 3 vetoes in billing.db |
| Demo mode fallback for empty DB | ✓ | SAMPLE_* data on all routes |
| Market data structure normalization | ✓ | Flat/nested JSON handled |
| Macro ticker injection | ✓ | Context processor → all templates |
| Partial dashboard refresh | ✓ | No full reload, DOM update only |
| Error boundary: graceful 4xx/5xx | ✓ | 404, 500, 429, 413 handlers |
| Retry logic on API fetch failures | ✓ | Console.warn, no UI breakage |
| Skeleton loading states | ✓ | CSS shimmer animation |

### PHASE 2: Institutional UX (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| Dark institutional palette | ✓ | #0a0b0e base, semantic colors |
| Typography system | ✓ | System sans + monospace for data |
| Stat boxes with hover effects | ✓ | 170px min, border-light transition |
| Intelligence panels (VIX/10Y/DXY) | ✓ | 4-column grid on dashboard |
| Confidence bars | ✓ | 4px height, semantic fill color |
| Severity tags | ✓ | critical/high/medium/low |
| Signal cards (compact) | ✓ | Used in market signal panels |
| Fade-in page transitions | ✓ | 0.3s ease on all templates |
| Responsive breakpoints | ✓ | 1024/768/480px |
| Ticker strip with live data | ✓ | SPX/VIX/DXY/10Y/GOLD/WTI/NSEI |

### PHASE 3: Security Hardening (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| Auth on all API endpoints | ✓ | /api/live_data, /api/signals, etc. |
| XSS sanitization (research notes) | ✓ | Script/event handler stripping |
| CSRF on upload endpoints | ✓ | Token in FormData fetch requests |
| Failed login tracking | ✓ | 5 attempts → 15-min IP lockout |
| Timing-safe password compare | ✓ | hmac.compare_digest() |
| Session cookie hardening | ✓ | httponly, samesite=Lax, secure on cloud |
| Debug mode disabled | ✓ | app.run(debug=False) |

### PHASE 4: Enhancement Pipeline (NEXT)

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Websocket push for real-time market data | P2 | Medium | WebSocket library |
| Redis rate-limit storage (persistent) | P2 | Low | Upgraded cloud plan |
| Research note edit history | P2 | Medium | research_db migration |
| Multi-user support (role-based) | P2 | High | Auth system rewrite |
| PDF report generation (dashboard) | P2 | Medium | WeasyPrint |
| API key auth for external consumers | P2 | Medium | API gateway pattern |
| Dark/light theme toggle | P3 | Low | CSS variable swap |
| Export to PowerPoint/PDF (monthly) | P3 | High | python-pptx |
| Automated test suite (pytest) | P3 | High | CI/CD setup |
| Docker containerization | P3 | Medium | Dockerfile |

---

## 2. CURRENT ARCHITECTURE MAP

```
sovereign-alpha/
├── dashboard/              # Flask web application
│   ├── app.py              # 2297 lines, 34 routes, all logic
│   ├── auth.py             # Session verification helpers
│   ├── templates/          # 14 Jinja2 templates
│   │   ├── base.html       # Master layout (redesigned v2)
│   │   ├── index.html      # Dashboard home
│   │   ├── decisions.html  # Decision log
│   │   ├── predictions.html# Prediction ledger
│   │   ├── veto_archive.html# Veto archive
│   │   ├── proofs.html     # Crypto proof certificates
│   │   ├── performance.html# Analytics + charts
│   │   ├── live_market.html# Market intelligence
│   │   ├── upload.html     # Fund manager upload portal
│   │   ├── login.html      # Authentication
│   │   ├── error.html      # Error handler
│   │   └── research_*.html # Research engine (3 files)
│   └── security/
│       └── validator.py    # Input validation module
├── engine/                 # Data + intelligence layer
│   ├── data_layer.py       # yfinance, FRED, SEC data fetch
│   ├── regime.py           # Market regime classification
│   └── risk.py             # Risk scoring
├── research/               # Research engine
│   ├── engine.py           # SovereignAlphaResearch
│   ├── storage/            # research_db.py
│   └── output/             # note_generator, pdf_exporter
├── zkml/                   # Zero-knowledge proof system
│   ├── proof_generator.py  # RSA-2048 signing
│   └── proofs/             # cert_*.json certificates
├── blockchain/             # Base Sepolia integration
│   └── ledger.py           # Blockchain decision logging
├── billing/                # Billing + performance tracking
│   ├── meter.py            # BillingMeter class
│   ├── billing.db          # Primary operational DB
│   ├── fund_data.db        # Fund uploads DB
│   └── research.db         # Research engine DB
├── data/                   # Market data + config files
│   ├── live_market_data.json
│   ├── live_signals.json
│   ├── regime/             # Regime history
│   └── data_cache/         # Cached API responses
├── documents/              # Generated documentation
│   ├── INSTITUTIONAL_WHITEPAPER.md
│   ├── EXECUTIVE_ONE_PAGER.md
│   ├── PRD.md               # ← This file
│   ├── TRD.md               # ← This file
│   ├── UI_UX_BRIEF.md       # ← This file
│   ├── BACKEND_SCHEMA.md    # ← This file
│   └── IMPLEMENTATION_PLAN.md # ← This file
└── automation/             # Scheduled tasks
    ├── master_daily.py     # Daily pipeline
    └── email_digest.py     # Email notification
```

---

## 3. KNOWN TECHNICAL DEBT

| Item | Impact | Resolution Plan |
|------|--------|----------------|
| In-memory rate limit storage | Resets on server restart | Migrate to Redis when off free tier |
| SQLite concurrent writes | May block on heavy load | Migrate to PostgreSQL when scaled |
| Single-threaded Flask | Blocks on LLM calls | Async workers or Celery for background tasks |
| All logic in app.py (2297 lines) | Hard to maintain | Split into blueprints (dashboard, api, research) |
| No automated tests | Manual verification only | pytest + Playwright for E2E |
| Inline JS/CSS in templates | Not cacheable, no minification | Build pipeline (webpack/vite) |
| Sample data fallback | Shows institutional data even when empty | Replace with true seed after first analysis run |
| No WebSocket | 60s poll latency for dashboard refresh | SSE or WebSocket for sub-second updates |

---

## 4. DEPLOYMENT CHECKLIST

### Pre-Deploy
- [x] `.env` configured with `FUND_PASSWORD`, `JWT_SECRET`, `GROQ_API_KEY`
- [x] `requirements-docker.txt` includes all 5 security packages
- [x] `Dockerfile` / HF Spaces configured
- [x] CSP allows `cdnjs.cloudflare.com`, `fonts.googleapis.com`
- [x] `IS_CLOUD` set in environment

### Post-Deploy Verification
- [ ] Dashboard returns 200 at `https://demonsatan-soverignalpha.hf.space`
- [ ] Login with correct `FUND_PASSWORD` works
- [ ] All 8 nav pages return 200 after login
- [ ] Health check returns `{"status": "healthy"}`
- [ ] Rate limiting responds with 429 on excessive requests
- [ ] Security headers present: CSP, X-Frame-Options, HSTS
- [ ] Research engine generates notes via Groq API
- [ ] Live market data loads from yfinance cache
- [ ] Upload portal accepts CSV and saves to fund_data.db

### Monitor
- [ ] HF Spaces build logs for package install errors
- [ ] Flask error logs for unhandled exceptions
- [ ] Rate limit hit counts (track via failed_attempts dict)
- [ ] Database file growth (billing.db, fund_data.db, research.db)

---

## 5. MILESTONE SUMMARY

| Milestone | Target | Status | Deliverables |
|-----------|--------|--------|-------------|
| v1.0 — Core Dashboard | — | ✓ COMPLETE | All routes, auth, DB, upload |
| v1.1 — Security Audit | — | ✓ COMPLETE | Rate limiting, CSP, CSRF, input validation |
| v1.2 — Data Persistence | — | ✓ COMPLETE | Demo fallback, partial refresh, market normalize |
| v1.3 — UX Redesign | — | ✓ COMPLETE | Institutional theme, intel panels, signals |
| v2.0 — Full Hardening | 2026-05-25 | ✓ COMPLETE | Auth on APIs, XSS fix, CSRF cleanup |
| v2.1 — Real-time Market | 2026-06 | ⬜ PENDING | WebSocket push, live price updates |
| v2.2 — Test Suite | 2026-06 | ⬜ PENDING | pytest + Playwright E2E |
| v2.3 — Multi-User | 2026-07 | ⬜ PENDING | Roles, permissions, shared dashboard |
| v3.0 — Production Ready | 2026-Q3 | ⬜ PENDING | PostgreSQL, Redis, Docker, CI/CD |

---
