# Sovereign Alpha Agent System

A private AI agent council that reasons over hedge fund proprietary data to find alpha opportunities, generates Zero-Knowledge proofs for every decision, and settles performance fees autonomously on blockchain.

## Overview

The Sovereign Alpha Agent System is a complete, production-ready AI agent framework built with:

- **Python 3.11+**
- **Groq API** (llama-3.3-70b-versatile, llama-3.1-8b-instant)
- **CrewAI** for multi-agent orchestration
- **ChromaDB** for local vector storage
- **EZKL** for Zero-Knowledge proofs (stub)
- **Web3.py** for Base blockchain

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
│  │ (ChromaDB)   │    │    JSON     │    │  Generator  │  │
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

## Project Structure

```
sovereign-alpha/
├── agents/                 # Three CrewAI agents
│   ├── analyst.py         # Analyst Agent
│   ├── risk_manager.py   # Risk Manager Agent  
│   └── auditor.py       # Auditor Agent
├── data/                 # Fund data
│   ├── sample_positions.csv
│   ├── sample_research.txt
│   └── risk_parameters.json
├── rag/                  # RAG knowledge base
│   └── knowledge_base.py
├── zkml/                # ZK proof generator
│   └── proof_generator.py
├── blockchain/           # Blockchain ledger
│   └── ledger.py
├── billing/              # SQLite billing meter
│   └── meter.py
├── crew.py              # Master orchestrator
├── config.py           # Configuration
├── requirements.txt   # Dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## Quick Start

### 1. Prerequisites

- Python 3.11 or higher
- A Groq API key (free at https://console.groq.com)

### 2. Installation

```bash
# Navigate to the project directory
cd sovereign-alpha

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy the environment template
copy .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your_key_here
```

### 4. Run the System

```bash
python crew.py
```

## Sample Output

```
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║       S O V E R E I G N   A L P H A   A G E N T   S Y S T E M  ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════════╝

======================================================================
SOVEREIGN ALPHA AGENT SYSTEM - Initializing
======================================================================
✓ All systems initialized
======================================================================

======================================================================
SOVEREIGN ALPHA - Starting Analysis Cycle
======================================================================

------------------------------------------------------
STEP 1: ANALYST AGENT - Generating Recommendations
------------------------------------------------------

  Generated 3 recommendations

  Processing: DEC-001 - BUY NVDA

------------------------------------------------------
STEP 2: RISK MANAGER - Checking DEC-001
------------------------------------------------------

  Analyzing: BUY NVDA @ $892.40
  Position Value: $892,400.00
  Confidence: 95%
  Sector: Technology

  ✓ Approved (passed 2 checks)

------------------------------------------------------
STEP 3: AUDITOR - Generating ZK Proof
------------------------------------------------------

  ✓ ZK Proof: abc123...
  ✓ Blockchain: confirmed
  ✓ Fee: $5,354.40
```

## The Three Agents

### 1. Analyst Agent

- **Role**: Senior Quantitative Analyst
- **Goal**: Identify alpha opportunities with high confidence trades
- **Tools**: 
  - RAG knowledge base (positions, research notes)
  - Risk parameters
  - Portfolio summary

### 2. Risk Manager Agent

- **Role**: Chief Risk Officer  
- **Goal**: Protect fund capital by verifying all recommendations
- **Powers**: Absolute VETO over any trade
- **Checks**:
  - Position size limits
  - Sector exposure limits
  - Confidence threshold
  - Max drawdown
  - ZK proof verification

### 3. Auditor Agent

- **Role**: Chief Compliance Auditor
- **Goal**: Cryptographic verification and blockchain logging
- **Responsibilities**:
  - Generate ZK proofs for approved decisions
  - Log proof hashes to Base blockchain
  - Calculate performance fees
  - Generate invoices

## Configuration

### Risk Parameters

Edit `data/risk_parameters.json` to configure:

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

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key | Yes |
| `WEB3_RPC_URL` | Base Sepolia RPC | No |
| `PRIVATE_KEY` | Wallet private key | No |
| `WALLET_ADDRESS` | Wallet address | No |

## Understanding the Output

### Decision Flow

1. **Analyst** reads fund data and generates trade recommendations
2. **Risk Manager** checks each recommendation against risk parameters
3. If approved, **Auditor** generates ZK proof
4. Proof is logged to blockchain (or local ledger)
5. Performance fee is calculated

### ZK Proof

The ZK proof proves that:
- A valid decision was made
- All risk checks passed
- Policy was followed

Without revealing:
- Specific position data
- Confidential research notes

### Performance Fees

- 12% of alpha generated
- Calculated per approved trade
- Logged to SQLite database

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

The system will use a simple fallback search. Install ChromaDB for full functionality:

```bash
pip install chromadb
```

## License

This system is provided as-is for educational and research purposes.

## Contact

For questions, please open an issue on the project repository.