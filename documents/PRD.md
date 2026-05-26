# SOVEREIGN ALPHA
## Product Requirements Document

**Version:** 2.0  
**Date:** 2026-05-25  
**Classification:** Internal Use Only  
**System:** Sovereign Alpha — Institutional Risk Governance & Intelligence Platform

---

## 1. PRODUCT OVERVIEW

### 1.1 Vision
An institutional-grade analytical intelligence platform for Category III AIF managers that provides immutable decision audit trails, cryptographic verification, and systematic risk governance — transforming opaque fund management into verifiable, transparent intelligence.

### 1.2 Mission
Replace retail-grade dashboards and generic AI wrappers with a calm, expensive, operationally real institutional terminal that fund managers trust with capital allocation decisions.

### 1.3 Core Value Proposition
- **Immutable Audit Trail:** Every prediction, veto, and decision is write-once and cryptographically signed
- **Risk Governance:** Systematic veto filtering with tracked outcomes and avoided-drawdown quantification
- **Verifiable Intelligence:** Zero-knowledge proofs and Merkle-chain integrity for LP/regulator audit
- **Private Data Pipeline:** RAG-based analysis of proprietary fund data without exposing it to public LLM training

---

## 2. TARGET USERS

| Persona | Needs | Pain Points |
|---------|-------|-------------|
| Fund Manager (PM) | Real-time dashboard, risk visibility, decision confidence | Information overload, no audit trail, opaque AI |
| Risk Officer | Veto tracking, regime monitoring, compliance evidence | No systematic risk logging, manual reporting |
| LP / Auditor | Verifiable decision integrity, proof of governance | Trust gap in AI-driven decisions |
| Analyst | Research generation, forensic flag detection, note creation | Manual research, no institutional memory |

---

## 3. FUNCTIONAL REQUIREMENTS

### 3.1 Dashboard (P0)

| ID | Requirement | Priority |
|----|------------|----------|
| D-01 | Display live market regime classification (RISK_ON / NEUTRAL / RISK_OFF) with confidence score | P0 |
| D-02 | Show real-time stats: approval rate, total predictions, veto efficiency, avoided drawdown | P0 |
| D-03 | Render intelligence panels with VIX, 10Y Treasury, DXY, HY OAS indicators | P0 |
| D-04 | Display recent predictions and vetoes in sortable tables with auto-refresh | P0 |
| D-05 | Show macro ticker strip with live SPX, VIX, DXY, GOLD, WTI, NSEI prices | P0 |
| D-06 | Never show zeros, NaN, undefined, broken charts, or empty analytics | P0 |
| D-07 | All data must persist across page refreshes | P0 |
| D-08 | All widgets must fail gracefully with skeleton loaders and fallback values | P1 |

### 3.2 Prediction Ledger (P0)

| ID | Requirement | Priority |
|----|------------|----------|
| PL-01 | Write-once immutable record of all investment predictions | P0 |
| PL-02 | Fields: prediction_id, asset, sector, thesis, confidence_score, status, timeline, proof_hash | P0 |
| PL-03 | Status lifecycle: pending → cleared | risk-rejected | P0 |
| PL-04 | Outcome tracking: actual_outcome, actual_return_pct, outcome_notes | P0 |
| PL-05 | CSV export for external audit | P1 |

### 3.3 Veto Archive (P0)

| ID | Requirement | Priority |
|----|------------|----------|
| VA-01 | Permanent record of all risk-rejected signals | P0 |
| VA-02 | Fields: veto_id, asset, sector, rejection_reason, expected_loss_pct | P0 |
| VA-03 | Outcome tracking: actual_return vs expected_loss, avoided_drawdown, veto_correct | P0 |
| VA-04 | Enable retrospective accuracy analysis of veto decisions | P1 |

### 3.4 Cryptographic Proofs (P0)

| ID | Requirement | Priority |
|----|------------|----------|
| CP-01 | RSA-2048 signed proof certificates for every decision | P0 |
| CP-02 | Merkle chain linking all certificates for tamper evidence | P0 |
| CP-03 | Downloadable JSON proof packages for external verification | P1 |
| CP-04 | Public-key based verification without system access | P1 |

### 3.5 Performance Analytics (P1)

| ID | Requirement | Priority |
|----|------------|----------|
| PA-01 | Confidence trend chart (line, 12-week rolling) | P1 |
| PA-02 | Sector breakdown chart (approved vs vetoed) | P1 |
| PA-03 | Return distribution histogram | P1 |
| PA-04 | Key metrics table: sessions, alpha, fees, hit rate, veto accuracy | P1 |

### 3.6 Live Market Intelligence (P1)

| ID | Requirement | Priority |
|----|------------|----------|
| LM-01 | Real-time price watchlist with change % | P1 |
| LM-02 | Technical signals: oversold, overbought, unusual volume | P1 |
| LM-03 | Regime intelligence summary with VIX, HY OAS context | P2 |

### 3.7 Research Engine (P1)

| ID | Requirement | Priority |
|----|------------|----------|
| RE-01 | Company registry with financial metrics | P1 |
| RE-02 | Forensic flag detection with severity scoring | P1 |
| RE-03 | Institutional research note generation via LLM | P1 |
| RE-04 | PDF export of research notes | P2 |

### 3.8 Upload Portal (P1)

| ID | Requirement | Priority |
|----|------------|----------|
| UP-01 | Fund positions CSV/Excel upload with column auto-detection | P1 |
| UP-02 | Risk parameter configuration (position size, sector limit, drawdown, confidence) | P1 |
| UP-03 | Research notes upload | P2 |
| UP-04 | Setup progress tracker | P2 |

### 3.9 Authentication & Security (P0)

| ID | Requirement | Priority |
|----|------------|----------|
| AS-01 | Password-based login with timing-safe comparison | P0 |
| AS-02 | Session token (JWT-based) with 24h expiry, httponly, samesite | P0 |
| AS-03 | Rate limiting: login 5/15min, 20/day; API 30/min; upload 5/min | P0 |
| AS-04 | CSRF protection on all POST endpoints | P0 |
| AS-05 | CSP headers, X-Frame-Options DENY, HSTS, XSS protection | P0 |
| AS-06 | Failed login tracking with 15-min IP lockout after 5 attempts | P0 |
| AS-07 | All API endpoints require authentication | P1 |

---

## 4. NON-FUNCTIONAL REQUIREMENTS

| ID | Requirement | Target |
|----|------------|--------|
| NF-01 | Page load time (initial) | < 2s |
| NF-02 | Page load time (subsequent) | < 500ms |
| NF-03 | Dashboard auto-refresh interval | 60s |
| NF-04 | Concurrent users | 50 |
| NF-05 | Uptime | 99.9% |
| NF-06 | Database backup | Daily |
| NF-07 | Audit log retention | Indefinite |
| NF-08 | CSP compliance | All pages |
| NF-09 | Accessible without JavaScript | Login only |

---

## 5. SYSTEM CONSTRAINTS

- **Hosting:** Hugging Face Spaces (Docker, always-on)
- **Database:** SQLite (single-file, no external DB service)
- **LLM:** Groq API (llama-3.1-8b-instant), requires API key
- **Market Data:** yfinance (free, no API key)
- **Storage:** Local filesystem (~100MB for proofs + research)
- **Cache:** In-memory TTL 300s (lost on restart)

---
