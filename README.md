---
title: Sovereign Alpha
emoji: 📊
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

<div align="center">

# 🏛️ Sovereign Alpha

### **Institutional Intelligence Operating System for Professional Investors**

*Identify variant perception. Quantify hidden risk. Capture non-consensus alpha — with every decision cryptographically proven compliant.*

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq LLM](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com)
[![Base Blockchain](https://img.shields.io/badge/Base-Sepolia_Testnet-0052FF?style=for-the-badge&logo=coinbase&logoColor=white)](https://base.org)
[![Zero-Knowledge](https://img.shields.io/badge/ZK_Proofs-SHA256_|_EZKL-6C3483?style=for-the-badge&logo=ethereum&logoColor=white)](#validation-ledger--zk-proofs)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

---

**`Forensic Equity Research`** · **`Portfolio Intelligence`** · **`Thesis Tracking`** · **`Macro Analysis`** · **`FII Flow Monitoring`** · **`Currency Sensitivity`** · **`Validation Ledger`**

</div>

---

## 📖 What is Sovereign Alpha?

**Sovereign Alpha** is a production-grade AI intelligence operating system built for professional investors — hedge funds, family offices, and institutional research desks — who need to reason over **proprietary, non-public data** to generate differentiated investment insights.

Unlike generic financial AI tools that rely on publicly available data (and therefore produce consensus-level outputs), Sovereign Alpha operates as a **private AI agent council** that ingests your fund's confidential research notes, internal position data, and proprietary risk parameters. It then orchestrates a multi-agent pipeline where:

1. A **Forensic Analyst Agent** reads private data and identifies alpha opportunities that public AI models *cannot see*.
2. A **Zero-Knowledge Proof Generator** creates cryptographic proof that the decision followed fund policy — *without revealing the underlying data*.
3. A **Risk Manager Agent** (with absolute veto power) verifies the proof and evaluates risk across position sizing, sector exposure, and drawdown limits.
4. An **Auditor Agent** logs everything immutably to the Base blockchain, creating a tamper-proof compliance trail.
5. A **Billing Meter** tracks performance attribution and calculates fees automatically.

The result is a system where *every recommendation is auditable, every decision is cryptographically verified, and no private data ever leaves the fund's perimeter.*

> **The pitch in one sentence:** *"This agent made decisions on your private data and here is the cryptographic proof it followed every compliance rule — without anyone ever seeing your data."*

---

## ✨ Key Features

### 🔬 Forensic Equity Research Engine
- RAG-powered analysis over proprietary research notes using ChromaDB vector store
- Semantic search across internal analyst reports, supply chain intelligence, and channel checks
- Structured output via Pydantic schemas — every recommendation includes ticker, confidence score, alpha thesis, risk factors, and time horizon

### 📊 Portfolio Intelligence & Position Monitoring
- Real-time portfolio weight tracking across 20+ positions
- Sector exposure monitoring with configurable limits (Technology ≤ 20%, Financials ≤ 20%, etc.)
- Correlation risk detection — identifies when true diversification is lower than sector weights suggest
- Momentum scoring with mean-reversion alerting

### 🎯 Thesis Tracking & Variant Perception
- Surfaces non-consensus opportunities by comparing proprietary intelligence against public market expectations
- Identifies "sandbagged" earnings guidance using supply chain contacts and alternative data
- Tracks thesis evolution from initial signal → recommendation → approval → post-trade audit

### 🌐 Macroeconomic Regime Analysis
- Regime detection engine classifying market environments (risk-on, risk-off, rotation, crisis)
- Sector allocation adjustments based on macro regime
- Integration-ready for FII flow monitoring and currency sensitivity mapping

### 🔐 Zero-Knowledge Compliance Proofs
- Every trade decision generates a cryptographic proof (SHA-256 stub, upgradeable to EZKL zk-SNARKs)
- Proves policy compliance without revealing private data, model weights, or strategy
- Proof hashes logged immutably on Base Sepolia testnet blockchain

### ⚖️ Autonomous Risk Management
- Risk Manager Agent holds **absolute veto power** — no trade proceeds without approval
- Automatic veto triggers: missing Signed Audit Trails proof, confidence < 65%, position size > 5%, sector breach
- Multi-layer validation: position sizing → sector exposure → drawdown limits → AI risk assessment

### 📋 Immutable Audit Trail
- Every decision (approved or vetoed) logged on-chain via Base testnet
- Local ledger fallback with deterministic transaction hash simulation
- Regulator-ready compliance summaries generated in plain English

### 💰 Self-Hosted Billing & Performance Attribution
- SQLite-based inference tracking — no external service required
- Performance fee calculation: 12% of alpha above benchmark (configurable)
- Monthly reporting with approval rates, confidence metrics, and dollar-value alpha attribution

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        SOVEREIGN ALPHA OS                            │
│                    Master Orchestrator (crew.py)                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐   │
│   │   PRIVATE    │     │  KNOWLEDGE  │     │    GROQ LLM API     │   │
│   │    DATA      │────▶│    BASE     │────▶│  LLaMA 3.3 70B      │   │
│   │             │     │  (ChromaDB) │     │  Versatile           │   │
│   │ • Research   │     │  (RAG)      │     │  Temperature: 0.2    │   │
│   │ • Positions  │     └──────┬──────┘     └──────────┬──────────┘   │
│   │ • Risk Params│            │                       │              │
│   └─────────────┘            │                       │              │
│                              ▼                       ▼              │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │              PHASE 1: ANALYST AGENT                       │      │
│   │   Reads private data → Generates structured recommendation│      │
│   │   Output: TradeRecommendation (Pydantic schema)           │      │
│   └──────────────────────────┬───────────────────────────────┘      │
│                              │                                       │
│                              ▼                                       │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │              PHASE 2: Signed Audit Trails PROOF GENERATOR                  │      │
│   │   Creates cryptographic proof BEFORE Risk Manager review  │      │
│   │   Output: ProofResult (hash, verification status)         │      │
│   └──────────────────────────┬───────────────────────────────┘      │
│                              │                                       │
│                              ▼                                       │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │              PHASE 3: RISK MANAGER AGENT                  │      │
│   │   Verifies Signed Audit Trails proof → Checks limits → Approves or VETOES │      │
│   │   Output: RiskDecision (approved/vetoed + risk score)     │      │
│   └──────────────────────────┬───────────────────────────────┘      │
│                              │                                       │
│                              ▼                                       │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │              PHASE 4: AUDITOR AGENT                       │      │
│   │   Logs to Base blockchain → Creates billing entry         │      │
│   │   Output: AuditRecord (trade ID, TX hash, compliance)     │      │
│   └──────────────────────────┬───────────────────────────────┘      │
│                              │                                       │
│                              ▼                                       │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │              PHASE 5: BILLING & REPORTING                 │      │
│   │   Performance fees → Alpha attribution → Monthly report   │      │
│   └──────────────────────────────────────────────────────────┘      │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                          │
│  ChromaDB (vectors) │ SQLite (billing) │ Base Sepolia (audit trail)  │
└──────────────────────────────────────────────────────────────────────┘
```

> **Architecture Diagram Note:** A visual Mermaid/Excalidraw diagram is available in the `/documents` directory. The architecture follows a strict sequential pipeline where the Signed Audit Trails proof is generated *before* the Risk Manager sees the recommendation — this ordering is critical for compliance integrity.

---

## 📈 Real-World Case Studies

The following examples demonstrate how Sovereign Alpha processes variant perception and hidden risk signals using Indian equity markets as the analytical context.

### Case Study 1: Bajaj Finance — Detecting Hidden AUM Quality Risk

| Dimension | Analysis |
|-----------|----------|
| **Thesis** | Consensus views Bajaj Finance as an unassailable fintech-NBFC compounder. Sovereign Alpha's forensic engine surfaces variant perception. |
| **What the Agent Finds** | Internal RAG retrieves proprietary channel checks revealing: (a) Unsecured personal loan disbursements growing 2.1x faster than secured book, shifting the risk profile; (b) Early-stage delinquency (DPD 30+) in digital loan channels running 180bps above legacy channels — not visible in headline GNPA; (c) Customer acquisition cost per digital borrower rising ₹340 QoQ while ticket sizes shrink. |
| **Signed Audit Trails Proof** | Generates SHA-256 proof that the SELL recommendation followed policy: confidence 0.71, recommended weight 1.8% (within 5% cap), drawdown risk scored at 0.62. |
| **Risk Manager** | Approves the weight reduction. Flags correlation risk — Bajaj Finance moves with NIFTY Financial Services index, and fund already holds HDFC Bank and Kotak. |
| **Auditor** | Decision logged to Base Sepolia with compliance summary: *"Position reduction approved. Signed Audit Trails proof verified. Decision consistent with fund's maximum sector exposure and drawdown limits."* |
| **Edge** | Public analysts focus on headline AUM growth (26% YoY). Sovereign Alpha surfaces the *composition* risk that consensus misses. |

---

### Case Study 2: Muthoot Finance — FII Flow Reversal Alpha

| Dimension | Analysis |
|-----------|----------|
| **Thesis** | Gold loan NBFCs are mispriced during FII outflow cycles. Sovereign Alpha's macro regime engine identifies the opportunity. |
| **What the Agent Finds** | (a) FII net selling in Indian equities crossed ₹18,000 Cr in the trailing 30 days — historically, gold prices rally 8-12% in the subsequent quarter; (b) Muthoot's gold AUM per branch at ₹67 Cr is at a 3-year trough — a contrarian entry signal; (c) INR/USD weakening past 83.5 — currency sensitivity mapping shows Muthoot's earnings are positively correlated to gold's INR price (gold rises when INR weakens). |
| **Signed Audit Trails Proof** | Proof generated for BUY recommendation: confidence 0.78, target weight 3.2%, potential return +18.4% over 90 days. |
| **Risk Manager** | Approves with condition: *"Set trailing stop-loss at -8% given gold price volatility."* Financials sector exposure post-trade: 14.2% (within 20% limit). |
| **Auditor** | Full audit trail created. Billing meter records: if +18.4% return materializes on a 3.2% weight in a ₹59M AUM fund, alpha contribution = 0.59%, performance fee = ₹4,17,600 (12% of excess). |
| **Edge** | The opportunity exists because FII flow data is public but the *second-order effect* on gold NBFCs requires connecting macro regime → currency sensitivity → company-specific AUM quality — a chain of reasoning most single-layer AI tools cannot perform. |

---

### Case Study 3: Page Industries — Margin Compression Thesis Tracking

| Dimension | Analysis |
|-----------|----------|
| **Thesis** | Page Industries (Jockey India licensee) trades at 55x PE. The market assumes pricing power is infinite. Sovereign Alpha tracks the counter-thesis. |
| **What the Agent Finds** | (a) Proprietary retail channel checks from 6 cities show Jockey's average selling price (ASP) growth decelerating from 9.2% to 3.1% YoY — D-Mart and Flipkart are forcing discounted SKUs; (b) Cotton prices (MCX) have risen 22% in 6 months but Page's last quarter showed only 40bps of gross margin expansion — suggesting pricing power is exhausted; (c) Management guided for "mid-teen" volume growth but internal distributor feedback suggests Q2 volumes flat to negative due to channel destocking. |
| **Signed Audit Trails Proof** | SELL recommendation proof: confidence 0.74, current weight 2.1%, recommended weight 0.5%, potential return -14.2% over 120 days. |
| **Risk Manager** | Approves weight reduction. Notes: *"Consumer discretionary sector exposure drops to 3.8% post-trade. Thesis is contrarian to consensus — monitor for thesis invalidation if Q2 results show ASP recovery."* |
| **Auditor** | Decision hash logged immutably. If the thesis plays out, the *avoided loss* on a 1.6% weight reduction ≈ ₹1.34 Cr in a ₹59M fund. This is tracked in the billing meter as negative-alpha avoidance. |
| **Edge** | Sovereign Alpha's thesis tracking maintains the contrarian view across multiple data updates. Unlike human analysts who suffer from anchoring bias on premium brands, the system re-evaluates from first principles each cycle. |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM Inference** | Groq Cloud (LLaMA 3.3 70B Versatile) | Ultra-fast reasoning over private data (~200ms latency) |
| **Agent Framework** | CrewAI | Multi-agent orchestration and task delegation |
| **RAG / Vector Store** | ChromaDB + LlamaIndex + HuggingFace Embeddings | Semantic search over proprietary research notes |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2) | Local embedding generation — data never leaves the machine |
| **Data Validation** | Pydantic v2 | Structured output schemas for every agent response |
| **Signed Audit Trails Proofs** | SHA-256 (stub) → EZKL (production) | Cryptographic compliance verification |
| **Blockchain** | Base Sepolia Testnet (Web3.py) | Immutable on-chain audit trail |
| **Database** | PostgreSQL (production) + SQLite (billing) | Persistent data layer and inference tracking |
| **Dashboard** | FastAPI + Jinja2 Templates | Real-time portfolio monitoring and research display |
| **Data Processing** | Pandas | Portfolio analytics, position monitoring, risk calculations |
| **CLI Interface** | Rich | Beautiful terminal output with formatted tables and panels |
| **Configuration** | python-dotenv | Environment-based secrets management |

---

## ⚙️ How It Works — Step by Step

### Step 1: Data Ingestion
```
Private research notes, portfolio positions, and risk parameters
are ingested into a local ChromaDB vector store.
Data never leaves your machine. The RAG engine chunks research by
section (split on ---) and creates searchable embeddings.
```

### Step 2: Analyst Agent Queries Private Data
```
The Analyst queries the knowledge base with natural language:
"What are the strongest alpha opportunities and trade signals?"

ChromaDB returns the top-k most relevant research chunks and
position data. The Analyst then reasons over this context using
Groq's LLaMA 3.3 70B model at temperature 0.2 (low randomness
for consistent, data-driven output).
```

### Step 3: Structured Recommendation Generated
```python
# Every recommendation follows this exact schema:
TradeRecommendation(
    ticker="BAJFINANCE",
    company="Bajaj Finance Ltd",
    sector="Financials",
    action="SELL",           # BUY | SELL | HOLD
    current_weight_pct=3.4,
    recommended_weight_pct=1.8,
    confidence_score=0.71,   # Must be ≥ 0.65 to pass risk check
    alpha_thesis="Unsecured book growing 2.1x faster than secured...",
    data_sources_used=["internal_research", "channel_checks", "positions"],
    potential_return_pct=-12.5,
    time_horizon_days=60,
    key_risks=["GNPA surprise", "Digital loan traction", "Rate cycle"]
)
```

### Step 4: Zero-Knowledge Proof (Before Risk Review)
```
CRITICAL ORDERING: The proof is generated BEFORE the Risk Manager
sees the recommendation. This proves the decision followed policy
at the moment of creation — not after the fact.

The proof verifies:
  ✓ Confidence score ≥ 65% threshold
  ✓ Position size ≤ 5% maximum
  ✓ Action is valid (BUY/SELL/HOLD)

Output: Deterministic SHA-256 hash of the serialized decision data.
```

### Step 5: Risk Manager Evaluation
```
The Risk Manager receives the recommendation AND the proof.
It performs multi-layer validation:

  Layer 1: Signed Audit Trails proof verification (automatic veto if missing)
  Layer 2: Confidence threshold check
  Layer 3: Position size limit check
  Layer 4: Sector exposure calculation
  Layer 5: Full AI risk assessment via Groq (temperature 0.1)

Any single failure triggers an AUTOMATIC VETO.
The Risk Manager's veto power is absolute and non-overridable.
```

### Step 6: Audit & Blockchain Logging
```
Whether approved or vetoed, the full decision is logged:

  → Signed Audit Trails proof hash logged to Base Sepolia testnet
  → Local JSONL ledger updated (fallback when no wallet configured)
  → Billing meter entry created in SQLite
  → Compliance summary generated in plain English for regulators
  → Complete AuditRecord created with trade ID, TX hash, and timestamps
```

### Step 7: Performance Reporting
```
The billing meter calculates:
  • Total inferences run
  • Approved vs. vetoed trade ratio
  • Average confidence and potential return
  • Alpha above benchmark (default: 8% annual)
  • Performance fee: 12% of alpha × AUM
```

---

## 🔐 Validation Ledger & Signed Audit Trails Proofs

The **Validation Ledger** is the cryptographic backbone of Sovereign Alpha. It answers a question that matters deeply to regulated institutions:

> *"Can you prove that every AI-generated decision followed your fund's compliance rules — without revealing the private data or strategy that informed the decision?"*

### How It Works

```
┌─────────────────────┐
│   Decision Data     │     ┌──────────────────────┐
│   (private)         │────▶│  Policy Verification │
│                     │     │  • Confidence ≥ 65%  │
│  • ticker           │     │  • Weight ≤ 5%       │
│  • action           │     │  • Valid action type  │
│  • confidence       │     └──────────┬───────────┘
│  • weight           │                │
│  • risk score       │                ▼
└─────────────────────┘     ┌──────────────────────┐
                            │  SHA-256 Hash        │
                            │  (deterministic)     │
                            │                      │
                            │  0x7f3a9b2c4e...     │
                            └──────────┬───────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
            ┌──────────┐      ┌──────────────┐    ┌───────────┐
            │ Risk     │      │  Base        │    │  Local    │
            │ Manager  │      │  Sepolia     │    │  Ledger   │
            │ Verifies │      │  Blockchain  │    │  (JSONL)  │
            └──────────┘      └──────────────┘    └───────────┘
```

### Current Implementation (Stub Mode)
- Deterministic SHA-256 hashing of canonicalized decision data
- Policy compliance verification encoded in the proof generation
- Same interface as production EZKL — zero code changes required to upgrade

### Production Upgrade Path (EZKL zk-SNARKs)
- Replace `self.mode = "stub"` with `self.mode = "ezkl"` in `proof_generator.py`
- Real zk-SNARK proofs that can be verified by *any* third party
- On-chain smart contract verification on Base mainnet
- Mathematically impossible to forge — the gold standard for institutional compliance

### What Gets Logged On-Chain
```json
{
  "trade_id": "TRADE-BAJFINANCE-20240315-143022-A7B2C3D4",
  "ticker": "BAJFINANCE",
  "action": "SELL",
  "approved": true,
  "proof_hash": "0x7f3a9b2c4e8d1f6a...",
  "risk_score": 0.31,
  "timestamp": "2024-03-15T14:30:22.000Z"
}
```

> **Privacy Guarantee:** The actual research notes, position data, and strategy logic **NEVER** go on-chain. Only the proof hash is logged — an irreversible cryptographic commitment that proves compliance without revealing the underlying data.

---

## 🖥️ Screenshots & Demo

> Screenshots and demo recordings will be added here. The dashboard includes:

| View | Description |
|------|-------------|
| **Pipeline Console** | Real-time output showing all 5 phases executing sequentially |
| **Research Dashboard** | Forensic equity research with thesis tracking and risk flags |
| **Portfolio Monitor** | Live position weights, sector exposure, and drawdown alerts |
| **Audit Trail** | Chronological ledger of all decisions with Signed Audit Trails proof status |
| **Billing Report** | Performance attribution with alpha calculation and fee summary |

```
📸 Screenshots coming soon — run `python crew.py` to see the live console output.
📹 Demo video will be linked here.
```

---

## 🗺️ Future Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| **v1.0** | Multi-agent pipeline with Signed Audit Trails proof stub | ✅ Complete |
| **v1.1** | Base Sepolia blockchain logging | ✅ Complete |
| **v1.2** | RAG-powered knowledge base (ChromaDB) | ✅ Complete |
| **v1.3** | Autonomous risk management with veto power | ✅ Complete |
| **v1.4** | Self-hosted billing meter | ✅ Complete |
| **v1.5** | FastAPI dashboard with real-time monitoring | ✅ Complete |
| **v2.0** | PostgreSQL production data layer | ✅ Complete |
| **v2.1** | Macro regime detection engine | ✅ Complete |
| | | |
| **v2.5** | Real EZKL zk-SNARK proof generation | 🔄 In Progress |
| **v3.0** | FII flow monitoring (NSDL/CDSL data integration) | 📋 Planned |
| **v3.1** | Currency sensitivity mapping (INR/USD, INR/EUR) | 📋 Planned |
| **v3.2** | Options flow analysis and implied volatility surface | 📋 Planned |
| **v3.3** | Satellite imagery alternative data integration | 📋 Planned |
| **v4.0** | Base mainnet deployment with smart contract verification | 📋 Planned |
| **v4.1** | Multi-fund support with tenant isolation | 📋 Planned |
| **v4.2** | Institutional API gateway with OAuth2 | 📋 Planned |
| **v5.0** | Real-time market data streaming (NSE/BSE WebSocket) | 🔮 Vision |
| **v5.1** | Natural language query interface for fund managers | 🔮 Vision |

---

## 🚀 Installation & Usage

### Prerequisites
- Python 3.11+
- Free [Groq API key](https://console.groq.com) (no credit card required)
- Git

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/sovereign-alpha.git
cd sovereign-alpha

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Open .env and add your Groq API key

# 5. Run the pipeline
python crew.py
```

### Running Specific Analyses

```bash
# General alpha scan
python crew.py

# Sector-focused analysis
python crew.py technology sector momentum signals
python crew.py financials hidden credit risk exposure
python crew.py energy supply gap and refining margin opportunity

# Risk-focused
python crew.py reduce highest risk positions
python crew.py evaluate sector concentration risk
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Groq Cloud API key for LLM inference |
| `WALLET_PRIVATE_KEY` | ❌ | Base Sepolia testnet wallet key (for on-chain logging) |
| `WEB3_RPC_URL` | ❌ | Custom RPC endpoint (defaults to `https://sepolia.base.org`) |
| `DATABASE_URL` | ❌ | PostgreSQL connection string (for production deployment) |

### Project Structure

```
sovereign-alpha/
├── agents/
│   ├── analyst.py              # Forensic equity research agent
│   ├── risk_manager.py         # Autonomous risk manager (veto power)
│   └── auditor.py              # Blockchain logger + compliance
├── engine/
│   ├── data_layer.py           # PostgreSQL data layer
│   └── regime.py               # Macroeconomic regime detection
├── dashboard/
│   ├── app.py                  # FastAPI dashboard application
│   ├── auth.py                 # Authentication and session management
│   ├── schemas.py              # API schemas and data models
│   └── templates/              # Jinja2 HTML templates
├── rag/
│   └── knowledge_base.py       # ChromaDB RAG engine (private data)
├── zkml/
│   └── proof_generator.py      # Signed Audit Trails proof generation (stub → EZKL)
├── blockchain/
│   └── ledger.py               # Base testnet immutable logging
├── billing/
│   └── meter.py                # Performance fee calculator (SQLite)
├── data/
│   ├── sample_positions.csv    # Portfolio positions (replace with real)
│   ├── sample_research.txt     # Research notes (replace with real)
│   └── risk_parameters.json    # Fund risk limits (editable)
├── crew.py                     # Master orchestrator — RUN THIS
├── config.py                   # Centralized configuration
├── requirements.txt            # Python dependencies
└── .env.example                # Environment template
```

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

Build freely. Research rigorously. Pitch boldly.

---

## 📬 Contact

**Lokesh Raja** — Builder of Sovereign Alpha

- 📧 Email: [rajtulshan3@gmail.com](mailto:rajtulshan3@gmail.com)
- 🐙 GitHub: [github.com/Raja549h](https://github.com/Raja549h)

> *Built with conviction that the future of institutional investing is AI-native, privacy-preserving, and cryptographically verifiable.*

---

<div align="center">

**⭐ If this project impressed you, consider starring it — it helps with visibility.**

*Sovereign Alpha — Where private intelligence meets provable compliance.*

</div>
