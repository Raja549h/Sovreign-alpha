# SOVEREIGN ALPHA
## Trade Requirements Document & Application Flow

**Version:** 2.0  
**Date:** 2026-05-25  
**Classification:** Internal Use Only  

---

## 1. TRADE DECISION FLOW

```
                   ┌─────────────────────────────┐
                   │    FUND MANAGER UPLOADS      │
                   │  Positions CSV / Parameters  │
                   │      Research Notes          │
                   └──────────┬──────────────────┘
                              │
                              ▼
                   ┌─────────────────────────────┐
                   │     KNOWLEDGE BASE (RAG)     │
                   │  Embed positions + research  │
                   │  Build portfolio summary     │
                   └──────────┬──────────────────┘
                              │
                              ▼
                   ┌─────────────────────────────┐
                   │     ANALYTICAL ENGINE        │
                   │  Analyze positions vs data   │
                   │  Generate recommendations   │
                   │  with confidence scores      │
                   └──────────┬──────────────────┘
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
          ┌─────────────────┐   ┌─────────────────┐
          │  RISK MANAGER    │   │   REGIME ENGINE │
          │  Apply governance│   │  Classify market│
          │  Position size?  │   │  RISK_ON / OFF  │
          │  Sector limit?   │   │  NEUTRAL        │
          │  Confidence ≥    │   └────────┬────────┘
          │    threshold?    │            │
          └────────┬────────┘            │
                   │                     │
          ┌────────┴────────┐            │
          ▼                 ▼            │
    ┌──────────┐     ┌──────────┐        │
    │ APPROVED │     │  VETOED  │        │
    │  Trade   │     │  Reject  │        │
    │  passes  │     │  Signal  │        │
    └────┬─────┘     └────┬─────┘        │
         │                │              │
         ▼                ▼              │
    ┌────────────────────────────────────┐
    │     CRYPTOGRAPHIC PROOF GEN        │
    │  RSA-2048 sign decision/veto       │
    │  Write to prediction ledger        │
    │  Commit to Merkle chain            │
    └──────────┬─────────────────────────┘
               │
               ▼
    ┌────────────────────────────────────┐
    │     BLOCKCHAIN / BILLING LEDGER    │
    │  Log decision hash to chain        │
    │  Track alpha / fees                │
    │  Update dashboard stats            │
    └────────────────────────────────────┘
```

---

## 2. PREDICTION LIFECYCLE

```
Created → Pending → Cleared / Risk-Rejected → Outcome Tracked
   │          │            │                        │
   │          │            │                        └─ correct / incorrect
   │          │            │
   │          │            └─ Veto logged to veto_archive
   │          │
   │          └─ Scheduled outcome evaluation (timeline_days)
   │
   └─ Proof certificate generated immediately
```

### 2.1 States

| State | Description | Transitions |
|-------|-------------|-------------|
| `pending` | Initial state after creation | → `cleared`, `risk-rejected` |
| `cleared` | Passed risk checks, recommendation active | → `outcome_tracked` |
| `risk-rejected` | Failed risk checks, moved to veto archive | → `outcome_tracked` |
| `outcome_tracked` | Actual outcome recorded | Terminal |

### 2.2 Veto Correctness Logic

```
veto_correct = True   if actual_return < expected_loss  (correct rejection)
             = False  if actual_return > 0               (false rejection)
             = None   if outcome not yet observed        (pending)
avoided_drawdown = abs(expected_loss - actual_return) when veto_correct
```

---

## 3. DATA FLOW ARCHITECTURE

### 3.1 Upload Flow
```
Form Upload → InputValidator → pandas parse → column mapping
→ normalize → validate → store BLOB in fund_data.db
→ preview returned to UI
```

### 3.2 Analysis Run Flow
```
POST /api/run → load fund_data from DB → write temp files
→ knowledge_base.get_portfolio_summary()
→ for each position: risk check (size, sector, confidence)
→ proof_generator.generate_proof() → RSA-2048 sign
→ ledger.log_decision() → blockchain hash
→ billing.log_performance() → SQLite write
→ return {new_decisions, new_proofs, total_alpha}
```

### 3.3 Market Data Flow
```
market_feed.py (cron) → yfinance fetch → live_market_data.json
market_signals.py (cron) → RSI/volume calc → live_signals.json
Dashboard reads JSON files → normalize → render template
```

### 3.4 Research Flow
```
POST /research/analyze → validate ticker → engine.run_analysis()
→ DataLayer fetch financials → LLM generate note
→ research_db.save_note() → HTML file on disk
→ Dashboard reads from research.db → render note page
```

---

## 4. API ENDPOINT MAP

### 4.1 Protected Routes (require login)

| Method | Path | Purpose | Rate Limit |
|--------|------|---------|------------|
| GET | `/` | Dashboard home | default |
| GET | `/decisions` | Decision log | default |
| GET | `/predictions` | Prediction ledger | default |
| GET | `/veto-archive` | Veto archive | default |
| GET | `/proofs` | Crypto proofs | default |
| GET | `/performance` | Analytics page | default |
| GET | `/live_market` | Market intelligence | default |
| GET | `/upload` | Upload portal | default |
| GET | `/research` | Research home | default |
| GET | `/research/<ticker>` | Company detail | default |
| GET | `/research/note/<ref>` | Research note | default |
| POST | `/update-outcome` | Update prediction/veto outcome | 30/min |
| POST | `/api/refresh` | Partial dashboard refresh | default |
| POST | `/api/run` | Run analysis pipeline | 3/min |
| POST | `/upload/positions` | Upload positions CSV | 5/min |
| POST | `/upload/params` | Save risk parameters | 30/min |
| POST | `/upload/research` | Upload research notes | 5/min |
| POST | `/research/analyze` | Run research analysis | 10/min |
| GET | `/api/export-predictions` | CSV export | default |
| GET | `/api/proof-cert/<id>` | Download proof cert | default |
| GET | `/api/regime` | Regime JSON | default |
| GET | `/api/intelligence` | Full intelligence JSON | default |
| GET | `/api/live_data` | Market data JSON | default |
| GET | `/api/signals` | Signals JSON | default |
| GET | `/api/track_record` | Track record JSON | default |
| GET | `/api/public_key` | Public key | default |
| GET | `/debug/db` | DB debug info | default |
| GET | `/download/positions-template` | CSV template | default |
| GET | `/download/research-template` | Research template | default |

### 4.2 Public Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/login` | Login page |
| GET | `/health` | Health check |
| GET/POST | `/run` | Run analysis (HTML) |

---

## 5. EXTERNAL INTEGRATIONS

| Service | Purpose | Auth | Fallback |
|---------|---------|------|----------|
| yfinance | Market prices, macro data | None | Returns None on failure |
| FRED API | Fed funds rate, HY/IG OAS | API key (optional) | Returns 0.0 |
| SEC EDGAR | 13F filings | None | Returns hardcoded holdings |
| World Bank | India GDP, inflation, CAD | None | Returns hardcoded defaults |
| Groq API | LLM research generation | API key (required) | Prints warning if missing |
| Base Sepolia | Blockchain ledger | Private key (optional) | Falls back to local DB |

---
