from database import get_connection
"""
EXECUTIVE ONE-PAGER GENERATOR
Sovereign Alpha - Institutional Intelligence System

Generates a one-page executive summary for CIOs.
"""

import sys

from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "documents"
BILLING_DIR = BASE_DIR / "billing"
FUND_DATA_DB = BILLING_DIR / "fund_data.db"

DOCS_DIR.mkdir(exist_ok=True)


def get_db_connection():
    """Get a database connection."""
    conn = get_connection()
    return conn


def get_ledger_stats():
    """Get statistics from the prediction ledger."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as total FROM prediction_ledger")
    total = c.fetchone()['total'] or 0
    
    c.execute("SELECT COUNT(*) as rejected FROM prediction_ledger WHERE status = 'risk-rejected'")
    rejected = c.fetchone()['rejected'] or 0
    
    c.execute("SELECT COUNT(*) as correct FROM prediction_ledger WHERE actual_outcome = 'correct'")
    correct = c.fetchone()['correct'] or 0
    
    c.execute("SELECT COUNT(*) as with_outcome FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
    with_outcome = c.fetchone()['with_outcome'] or 0
    
    c.execute("SELECT COUNT(*) as veto_correct FROM veto_archive WHERE veto_correct = 1")
    veto_correct = c.fetchone()['veto_correct'] or 0
    
    c.execute("SELECT COUNT(*) as total_vetoes FROM veto_archive")
    total_vetoes = c.fetchone()['total_vetoes'] or 0
    
    c.execute("SELECT COALESCE(SUM(avoided_drawdown), 0) as total_avoided FROM veto_archive")
    total_avoided = c.fetchone()['total_avoided'] or 0
    
    conn.close()
    
    success_rate = (correct / with_outcome * 100) if with_outcome > 0 else 0
    veto_efficiency = (veto_correct / total_vetoes * 100) if total_vetoes > 0 else 0
    
    return {
        'total_predictions': total,
        'risk_rejected': rejected,
        'correct': correct,
        'with_outcome': with_outcome,
        'success_rate': success_rate,
        'veto_efficiency': veto_efficiency,
        'veto_correct': veto_correct,
        'total_vetoes': total_vetoes,
        'total_avoided_drawdown': total_avoided
    }


def generate_one_pager():
    """Generate the executive one-pager."""
    stats = get_ledger_stats()
    
    success_rate = stats['success_rate']
    veto_efficiency = stats['veto_efficiency']
    total_avoided = stats['total_avoided_drawdown']
    
    content = f"""# SOVEREIGN ALPHA
## Executive One-Pager

**Date:** {datetime.utcnow().strftime('%Y-%m-%d')}

---

## What It Is

Institutional risk governance system for Category III AIF managers.
Provides immutable, verifiable audit trail for all investment decisions.

---

## The Problem

Private fund data cannot be analyzed systematically.
Risk decisions lack documentation for regulatory compliance.
LP transparency requires auditable governance evidence.

---

## The Capability

- **Prediction Ledger:** Write-once, immutable records of all recommendations
- **Veto Archive:** Track every risk-rejection with reasons and outcomes
- **Cryptographic Certificates:** Verifiable proof of decision integrity
- **Merkle Chain:** Tamper-resistant audit history

---

## Killer Metric

**{veto_efficiency:.0f}% veto accuracy** — {stats['veto_correct']} of {stats['total_vetoes']} risk-rejections 
correctly avoided losses, protecting ${total_avoided:,.0f} in portfolio value.

---

## Architecture

| Component | Function |
|-----------|----------|
| RAG Pipeline | Private data analysis |
| Analytical Engine | Recommendation generation |
| Risk Manager | Policy compliance |
| Cryptographic Layer | Audit certificates |
| Merkle Chain | Tamper evidence |

---

## Proof Layer

Every decision generates RSA-2048 signed certificate.
Third parties verify without accessing private data.

---

## Dashboard

Access at: https://demonsatan-soverignalpha.hf.space
Login required. All data stored locally.

---

**Contact:** Fund Administrator

*Generated from actual system data. No projections.*
"""

    output_file = DOCS_DIR / "EXECUTIVE_ONE_PAGER.md"
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"One-pager generated: {output_file}")
    return str(output_file)


if __name__ == '__main__':
    generate_one_pager()