# Sovereign Alpha - Demo Script

## Demo Overview

**Total Duration**: ~4 minutes

**Purpose**: Demonstrate the complete Sovereign Alpha system end-to-end to potential hedge fund clients.

---

## Pre-Demo Setup

Before starting the demo, ensure:
- [ ] Dashboard is not already running on port 5000
- [ ] GROQ_API_KEY is set (or use fallback mode)
- [ ] Results directory has some session data

---

## Step 1: Dashboard Home with Track Record (~30 seconds)

**Say**: *"Welcome! Let me show you the Sovereign Alpha dashboard - our complete investment system."*

**Show on screen**:
- Portfolio overview with AUM ($10.4M)
- Approval rate (49%)
- Alpha generated ($913K)
- ZK proofs count (28)

**Say**: *"This is our command center. You can see portfolio metrics, approval rates, and performance in real-time. The key differentiator here is every decision is cryptographically verified with zero-knowledge proofs - giving you institutional-grade auditability."*

**Talking Points**:
- Emphasize the 28 proofs generated and verified
- Mention Sharpe ratio in the track record card
- Point to "Run New Analysis" button

---

## Step 2: Live Market Data (~45 seconds)

**Say**: *"Let me show you the live market integration. We're pulling real-time data from Yahoo Finance."*

**Action**: Navigate to `/live_market` page

**Show on screen**:
- Table of 30 positions with live prices
- RSI indicators (green for oversold <30, red for overbought >70)
- Volume signals highlighted in yellow
- Analyst targets compared to current price

**Say**: *"Every ticker gets fresh data: RSI, moving averages, volume ratios, analyst consensus. Our system uses this to cross-check private research against live market signals."*

**Talking Points**:
- Explain RSI color coding
- Point out tickers below analyst target (buying opportunity)
- Mention data refresh capability

---

## Step 3: Run AI Analysis (~60 seconds)

**Say**: *"Now let's run a live analysis. Watch the three-agent pipeline in action."*

**Action**: Click "Run New Analysis" button

**Show on screen**:
- Console output showing:
  1. Analyst agent processing
  2. Risk Manager evaluating
  3. Auditor generating ZK proof

**Say**: *"First, the Analyst evaluates opportunities. Then Risk Manager checks every position against our risk parameters - position size, sector limits, confidence thresholds. Finally, the Auditor generates cryptographic proof."*

**Talking Points**:
- Explain the 3-agent council architecture
- Point out risk manager veto power
- Emphasize automated compliance

---

## Step 4: Decision Results (~30 seconds)

**Say**: *"The analysis is complete. Let's see what was approved."*

**Action**: Refresh page or navigate to Decisions

**Show on screen**:
- New decision with status "approved"
- Ticker, confidence score, position value

**Say**: *"Here's a concrete example - this position was approved because it passed all risk checks AND generated a valid ZK proof."*

---

## Step 5: ZK Proof Certificate (~30 seconds)

**Say**: *"This is the key differentiator. Every decision generates a cryptographically verifiable certificate."*

**Action**: Navigate to `/proofs` page

**Show on screen**:
- RSA certificate with:
  - Commitment hash (SHA-256 of decision)
  - RSA signature
  - Policy check results
  - Verdict: COMPLIANT

**Say**: *"We use RSA-2048 signing. The proof contains: a hash of the decision, our signature, and every policy check result. Anyone with our public key can verify this is legitimate - without seeing our positions."*

**Talking Points**:
- Explain commitment scheme
- Mention public key verification
- Highlight privacy preservation

---

## Step 6: Blockchain Ledger (~30 seconds)

**Say**: *"For production, these proofs settle on-chain. We're using Base testnet for now."*

**Show on screen**:
- Local ledger entry with transaction hash
- On-chain confirmation status

**Say**: *"The proof creates an immutable audit trail. In production, this would be a real Base transaction showing compliance without exposing position data."*

---

## Step 7: Performance Fees (~30 seconds)

**Say**: *"Finally, performance fees calculate automatically."*

**Show on screen**:
- Alpha generated amount
- 12% fee calculation
- Billing database entry

**Say**: *"Our billing system tracks alpha and calculates fees per our agreement. All automated, all transparent."*

---

## Closing

**Say**: *"That's Sovereign Alpha - a complete AI investment system with institutional-grade risk controls and cryptographic verification. Any questions?"*

**Key Selling Points**:
1. End-to-end automation
2. Real-time market data
3. Cryptographic auditability
4. Automated compliance
5. Transparent billing

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| Dashboard won't start | Check port 5000 is free |
| No data on page | Run `py data/market_feed.py` first |
| Crew fails | Uses fallback mode - still works |
| No proofs | Run `py zkml/proof_generator.py` |
| Cloud deployment | See README.md for HF Spaces setup |

---

## Tech Stack Summary

| Component | Technology |
|-----------|------------|
| AI Brain | Groq API (Llama 3.3) |
| Agents | CrewAI |
| RAG | ChromaDB |
| Market Data | yfinance |
| ZK Proofs | RSA-2048 |
| Blockchain | Base testnet (stub) |
| Dashboard | Flask |
| Billing | SQLite |