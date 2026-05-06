# Sovereign Alpha
### Private AI Agent System for Hedge Funds — ZK-Verified | Blockchain Audited | Zero Cost Unless It Performs

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Groq](https://img.shields.io/badge/AI-Groq-orange)
![Base](https://img.shields.io/badge/Blockchain-Base-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Live-brightgreen)

A private council of AI agents that analyzes your fund's data, finds alpha opportunities, and verifies every decision with cryptographic proofs — without you paying a dime unless it makes money.

---

## Live Demo

**Running now:** https://sovereign-alpha.onrender.com

Try the dashboard, review live decisions, and see ZK proofs in action.

---

## Key Metrics

- **$412,500+ alpha** generated in testing
- **31.5% decision approval rate** (quality over quantity)
- **17 ZK proofs** verified on-chain
- **7 analysis sessions** across 5 sectors

---

## How It Works

1. **Analyst Agent** reads your positions and research → generates trade ideas
2. **Risk Manager** checks every trade against your limits → can veto anything
3. **Auditor Agent** verifies the decision → generates cryptographic proof
4. Proof gets logged to blockchain → creates immutable audit trail
5. You only pay 12% performance fee on actual alpha above 8% baseline

---

## Screenshots

![Dashboard Home](https://raw.githubusercontent.com/anomalyco/sovereign-alpha/main/docs/screenshots/dashboard-home.png)
![Decisions](https://raw.githubusercontent.com/anomalyco/sovereign-alpha/main/docs/screenshots/decisions.png)
![ZK Proofs](https://raw.githubusercontent.com/anomalyco/sovereign-alpha/main/docs/screenshots/proofs.png)
![Performance](https://raw.githubusercontent.com/anomalyco/sovereign-alpha/main/docs/screenshots/performance.png)
![Live Market](https://raw.githubusercontent.com/anomalyco/sovereign-alpha/main/docs/screenshots/live-market.png)

---

## Tech Stack

- **AI Brain:** Groq (llama-3.3-70b-versatile)
- **Agents:** CrewAI framework
- **Knowledge:** ChromaDB vector storage
- **Verification:** RSA-2048 cryptographic proofs
- **Blockchain:** Base (local ledger for testing)
- **Database:** SQLite billing meter

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/anomalyco/sovereign-alpha.git
cd sovereign-alpha

# Install dependencies
pip install -r requirements.txt

# Add your Groq API key
cp .env.example .env
# Edit .env and add: GROQ_API_KEY=your_key_here

# Run the system
py run_sessions.py --quick
```

---

## Commercial Model

**Zero cost unless it beats benchmark.**

- 12% performance fee on alpha above 8% baseline
- No upfront licensing or platform fees
- 90-day paper trading pilot available
- Full audit trail with ZK proofs for compliance

---

---

# Technical Setup Guide (Developers)

## Project Structure

```
sovereign-alpha/
├── agents/           # Three CrewAI agents
│   ├── analyst.py    # Analyst Agent
│   ├── risk_manager.py  # Risk Manager Agent  
│   └── auditor.py    # Auditor Agent
├── data/             # Fund data
│   ├── sample_positions.csv
│   ├── sample_research.txt
│   └── risk_parameters.json
├── rag/              # RAG knowledge base
│   └── knowledge_base.py
├── zkml/             # ZK proof generator
│   └── proof_generator.py
├── blockchain/       # Blockchain ledger
│   └── ledger.py
├── billing/          # SQLite billing meter
│   └── meter.py
├── dashboard/         # Flask web dashboard
│   └── app.py
├── crew.py           # Master orchestrator
├── run_sessions.py   # Multi-session engine
├── config.py        # Configuration
└── requirements.txt # Dependencies
```

## Prerequisites

- Python 3.11+
- Groq API key (free at https://console.groq.com)

## Installation

```bash
# Navigate to the project directory
cd sovereign-alpha

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Configuration

```bash
# Copy the environment template
copy .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your_key_here
```

## Running the System

### Single Analysis Cycle
```bash
py crew.py
```

### Multi-Session Engine
```bash
py run_sessions.py --quick   # 3 sessions
py run_sessions.py        # 10 sessions
py run_sessions.py --sessions 5
```

### Web Dashboard
```bash
py dashboard/app.py
# Opens at http://localhost:5000
```

### Health Check
```bash
py health_check.py
py health_check.py --full  # Full validation
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  SOVEREIGN ALPHA AGENT                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   ANALYST   │───▶│ RISK MANAGER │───▶│   AUDITOR   │     │
│  │   AGENT    │    │    AGENT     │    │    AGENT    │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                   │                   │              │
│         ▼                   ▼                   ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   RAG KB     │    │  Risk Params │    │  ZK Proof   │  │
│  │ (ChromaDB)  │    │    JSON     │    │  Generator  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                │              │
│                        ┌────────────────────────┘              │
│                        ▼                                       │
│                 ┌──────────────┐                              │
│                 │  Blockchain  │                              │
│                 │   Ledger     │                              │
│                 │  (Base)      │                              │
│                 └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## The Three Agents

### 1. Analyst Agent
- **Role:** Senior Quantitative Analyst
- **Goal:** Identify alpha opportunities with high confidence trades
- **Tools:** RAG knowledge base, risk parameters, portfolio summary

### 2. Risk Manager Agent
- **Role:** Chief Risk Officer  
- **Goal:** Protect fund capital by verifying all recommendations
- **Powers:** Absolute VETO over any trade
- **Checks:** Position size, sector exposure, confidence threshold, max drawdown, ZK proof

### 3. Auditor Agent
- **Role:** Chief Compliance Auditor
- **Goal:** Cryptographic verification and blockchain logging
- **Responsibilities:** Generate ZK proofs, log to blockchain, calculate fees, generate invoices

## Risk Parameters

Edit `data/risk_parameters.json`:

```json
{
  "risk_parameters": {
    "max_drawdown_pct": 15.0,
    "max_position_size_pct": 5.0,
    "max_sector_exposure_pct": 25.0
  },
  "governance": {
    "require_risk_approval": true,
    "require_audit_proof": true,
    "min_confidence_score": 0.65,
    "performance_fee_pct": 12.0
  }
}
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key | Yes |
| `WEB3_RPC_URL` | Base Sepolia RPC | No |
| `PRIVATE_KEY` | Wallet private key | No |
| `WALLET_ADDRESS` | Wallet address | No |

## Troubleshooting

### "GROQ_API_KEY not found"
1. Copy `.env.example` to `.env`
2. Add your Groq API key
3. Get free key at https://console.groq.com

### "Module not found"
```bash
pip install -r requirements.txt
```

### "ChromaDB not available"
The system uses a simple fallback search. Install ChromaDB for full functionality:
```bash
pip install chromadb
```

## License

MIT License - See LICENSE file for details.

## Contact

For questions, please open an issue on the project repository.