# SOVEREIGN ALPHA
## Backend Schema & Architecture

**Version:** 2.0  
**Date:** 2026-05-25  
**Classification:** Internal Use Only  

---

## 1. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                      DASHBOARD (Flask)                       │
│  app.py - 34 routes, 20 HTML + 11 JSON + 1 CSV + 1 PDF     │
│  auth.py - session handling, password verification          │
│  security/validator.py - input sanitization, XSS/SQLi check │
├────────────────┬────────────────────┬───────────────────────┤
│  ENGINE LAYER  │  RESEARCH LAYER    │  CRYPTO LAYER         │
│  data_layer.py │  engine.py         │  proof_generator.py   │
│  regime.py     │  research_db.py    │  merkle_chain.py      │
│  risk.py       │  note_generator.py │  keys/                │
│                │  pdf_exporter.py   │                       │
├────────────────┴────────────────────┴───────────────────────┤
│                   INFRASTRUCTURE LAYER                       │
│  blockchain/ledger.py  │  billing/meter.py                   │
│  automation/           │  rag/knowledge_base.py              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. DATABASE SCHEMA

### 2.1 billing.db (Primary Operational DB)

#### prediction_ledger
```sql
CREATE TABLE prediction_ledger (
    prediction_id      TEXT PRIMARY KEY,
    timestamp          TEXT NOT NULL,
    asset              TEXT NOT NULL,
    sector             TEXT,
    thesis             TEXT,
    confidence_score   REAL,
    status             TEXT NOT NULL,       -- 'cleared' | 'risk-rejected' | 'pending'
    expected_timeline_days INTEGER,
    proof_hash         TEXT,
    created_at         TEXT NOT NULL,
    updated_at         TEXT,
    actual_outcome     TEXT,                -- 'correct' | 'incorrect' | ''
    actual_return_pct  REAL,
    outcome_notes      TEXT
);
```

#### veto_archive
```sql
CREATE TABLE veto_archive (
    veto_id            TEXT PRIMARY KEY,
    asset              TEXT NOT NULL,
    sector             TEXT,
    rejection_reason   TEXT NOT NULL,
    risk_score         REAL,
    timestamp          TEXT NOT NULL,
    actual_outcome     TEXT,                -- 'correct' | 'incorrect' | NULL
    actual_return_pct  REAL,
    expected_loss_pct  REAL,
    avoided_drawdown   REAL,
    veto_correct       INTEGER,             -- 1=True, 0=False, NULL=Pending
    notes              TEXT
);
```

#### performance_log
```sql
CREATE TABLE performance_log (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id        TEXT,
    symbol             TEXT,
    action             TEXT,
    status             TEXT,                -- 'active' | 'vetoed'
    alpha_generated    REAL,
    fee_calculated     REAL,
    timestamp          TEXT
);
```

#### inference_log
```sql
CREATE TABLE inference_log (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    model              TEXT,
    prompt_tokens      INTEGER,
    completion_tokens  INTEGER,
    total_tokens       INTEGER,
    cost               REAL,
    timestamp          TEXT
);
```

#### monthly_summary
```sql
CREATE TABLE monthly_summary (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    month              TEXT,
    total_decisions    INTEGER,
    approved           INTEGER,
    vetoed             INTEGER,
    accuracy           REAL
);
```

### 2.2 fund_data.db (Fund Manager Uploads)

#### fund_uploads
```sql
CREATE TABLE fund_uploads (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    file_type          TEXT,                -- 'positions' | 'research'
    file_content       BLOB,
    uploaded_at        TEXT
);
```

#### fund_params
```sql
CREATE TABLE fund_params (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    param_key          TEXT UNIQUE,
    param_value        TEXT,
    updated_at         TEXT
);
```

#### prediction_ledger (duplicated schema)
Same as billing.db (kept for backward compatibility with fund_data reads).

#### veto_archive (duplicated schema)
Same as billing.db with extra prediction_id column.

### 2.3 research.db (Research Engine)

#### companies
```sql
CREATE TABLE companies (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker             TEXT,
    company_name       TEXT,
    exchange           TEXT,
    sector             TEXT,
    added_at           TEXT
);
```

#### filings
```sql
CREATE TABLE filings (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id         INTEGER REFERENCES companies(id),
    filing_type        TEXT,
    period             TEXT,
    source_url         TEXT,
    local_path         TEXT,
    extracted_text     TEXT,
    extracted_tables   TEXT,
    ingested_at        TEXT,
    status             TEXT
);
```

#### financial_series
```sql
CREATE TABLE financial_series (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id         INTEGER REFERENCES companies(id),
    metric_name        TEXT,
    period             TEXT,
    value              REAL,
    unit               TEXT,
    source_filing_id   INTEGER,
    extracted_at       TEXT
);
```

#### forensic_flags
```sql
CREATE TABLE forensic_flags (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id         INTEGER REFERENCES companies(id),
    flag_type          TEXT,
    severity           TEXT,                -- 'critical' | 'high' | 'medium' | 'low'
    description        TEXT,
    supporting_data    TEXT,                -- JSON
    period             TEXT,
    detected_at        TEXT,
    analyst_note       TEXT
);
```

#### research_notes
```sql
CREATE TABLE research_notes (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id         INTEGER REFERENCES companies(id),
    note_reference     TEXT UNIQUE,         -- e.g., 'SR-2026-BAJ-004'
    title              TEXT,
    summary            TEXT,
    full_content       TEXT,                -- HTML (sanitized server-side)
    risk_intensity_score    REAL,
    confidence_score        REAL,
    regime_sensitivity_score REAL,
    structural_quality_score REAL,
    forensic_flags_count    INTEGER,
    generated_at       TEXT,
    pdf_path           TEXT,
    status             TEXT
);
```

#### institutional_scores
```sql
CREATE TABLE institutional_scores (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id         INTEGER REFERENCES companies(id),
    period             TEXT,
    risk_intensity     REAL,
    confidence         REAL,
    regime_sensitivity REAL,
    structural_quality REAL,
    composite_score    REAL,
    scoring_rationale  TEXT,
    scored_at          TEXT
);
```

### 2.4 meter.db (Legacy Billing)

```sql
CREATE TABLE decisions (
    decision_id  TEXT, symbol TEXT, action TEXT,
    confidence REAL, alpha_generated REAL,
    status TEXT, created_at TEXT
);
CREATE TABLE proofs (
    decision_id TEXT, proof_hash TEXT,
    verified INTEGER, created_at TEXT
);
CREATE TABLE performance (
    date TEXT, portfolio_value REAL,
    benchmark_value REAL, alpha REAL
);
```

---

## 3. ROUTE HANDLER PATTERN

All protected routes follow this pattern:

```python
@app.route('/path')
@login_required
def handler():
    try:
        data = get_data()               # Real DB query
        demo = is_demo_mode()
        if not data and demo:
            data = SAMPLE_DATA           # Fallback to institutional sample
        return render_template('template.html', data=data, is_demo=demo)
    except Exception:
        return render_template('template.html',
                               data=SAMPLE_DATA, is_demo=True)
```

---

## 4. AUTHENTICATION SYSTEM

### 4.1 Session Token Format
```
{fund_id}:{unix_timestamp}:{sha256_hmac}
```
- Base64-encoded
- HMAC-SHA256 signed with APP_SECRET
- 7-day expiry (cookie: 1 day)

### 4.2 Verification Flow
```
Cookie → extract fund_id:timestamp:signature
→ verify HMAC against APP_SECRET
→ check timestamp not expired
→ return fund_id or None
```

### 4.3 Rate Limiting
```
Login:        5 per 15 minutes, 20 per day
POST routes:  30 per minute
Upload:       5 per minute
/api/run:     3 per minute
Research:     10 per minute
Default:      200 per day, 50 per hour
```
Storage: `memory://` (lost on server restart)

---

## 5. MARKET DATA FORMAT

### live_market_data.json
```json
{
    "^NSEI": {"price": 23759.75, "change_pct": 0.30, "volume": 0,
              "market_cap": 0, "pe_ratio": 0},
    "RELIANCE.NS": {"price": 1335.9, "change_pct": -1.90, "volume": 7980049,
                    "market_cap": 18078031151104, "pe_ratio": 22.40},
    "fetched_at": "2026-05-15T06:41:07.300934Z"
}
```
Normalized server-side to: `{'tickers': {...}, 'fetched_at': '...'}`

### live_signals.json
```json
{
    "oversold": [{"symbol": "INTC", "reason": "RSI 28 — oversold..."}],
    "overbought": [],
    "unusual_volume": [{"symbol": "NVDA", "reason": "Volume 2.8x avg..."}]
}
```

---

## 6. ENVIRONMENT VARIABLES

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `FUND_PASSWORD` | Yes | `""` | Login authentication |
| `JWT_SECRET` | Yes | `"change-this-secret-in-production"` | Session signing, CSP secret |
| `GROQ_API_KEY` | Yes | `""` | LLM research generation |
| `FRED_API_KEY` | No | `""` | Macro data |
| `WEB3_RPC_URL` | No | `"https://sepolia.base.org"` | Blockchain |
| `RENDER` | No | `"false"` | Cloud mode detection |
| `PORT` | No | `5000` | Server port |

---
