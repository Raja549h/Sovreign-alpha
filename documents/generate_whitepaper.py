"""
WHITEPAPER GENERATOR
Sovereign Alpha - Institutional Intelligence System

Generates institutional whitepaper from prediction ledger data.
"""

import os
import sys
import sqlite3
import json
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
    conn = sqlite3.connect(str(FUND_DATA_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_ledger_stats():
    """Get statistics from the prediction ledger."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as total FROM prediction_ledger")
    total = c.fetchone()['total'] or 0
    
    c.execute("SELECT COUNT(*) as cleared FROM prediction_ledger WHERE status = 'cleared'")
    cleared = c.fetchone()['cleared'] or 0
    
    c.execute("SELECT COUNT(*) as rejected FROM prediction_ledger WHERE status = 'risk-rejected'")
    rejected = c.fetchone()['rejected'] or 0
    
    c.execute("SELECT COUNT(*) as with_outcome FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
    with_outcome = c.fetchone()['with_outcome'] or 0
    
    c.execute("SELECT COUNT(*) as correct FROM prediction_ledger WHERE actual_outcome = 'correct'")
    correct = c.fetchone()['correct'] or 0
    
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
        'cleared': cleared,
        'risk_rejected': rejected,
        'with_outcome': with_outcome,
        'correct': correct,
        'success_rate': success_rate,
        'veto_efficiency': veto_efficiency,
        'veto_correct': veto_correct,
        'total_vetoes': total_vetoes,
        'total_avoided_drawdown': total_avoided
    }


def get_predictions(limit=100):
    """Get recent predictions."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM prediction_ledger ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_vetoes(limit=50):
    """Get recent vetoes."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM veto_archive ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def generate_whitepaper():
    """Generate the institutional whitepaper."""
    stats = get_ledger_stats()
    predictions = get_predictions(50)
    vetoes = get_vetoes(30)
    
    success_rate = stats['success_rate']
    veto_efficiency = stats['veto_efficiency']
    
    lines = []
    lines.append("# SOVEREIGN ALPHA")
    lines.append("## Institutional Risk Governance System\n")
    lines.append(f"**Document Version:** 1.0")
    lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}")
    lines.append("**Classification:** Internal Use Only\n")
    lines.append("---\n")
    lines.append("# EXECUTIVE SUMMARY\n")
    lines.append("Sovereign Alpha is an institutional-grade risk governance system designed for")
    lines.append("private equity and alternative investment fund managers operating in the Indian market.\n")
    lines.append("The system provides immutable, verifiable audit trails for all investment recommendations")
    lines.append("and risk decisions, enabling regulatory compliance, LP transparency, and systematic")
    lines.append("governance documentation.\n")
    lines.append("**Key Metrics:**")
    lines.append(f"- Total recommendations issued: {stats['total_predictions']}")
    lines.append(f"- Risk-rejections (vetoes): {stats['risk_rejected']} ({stats['risk_rejected']/max(stats['total_predictions'],1)*100:.1f}%)")
    lines.append(f"- Verified correct predictions: {stats['correct']}/{stats['with_outcome']} ({success_rate:.1f}%)")
    lines.append(f"- Veto accuracy: {stats['veto_correct']}/{stats['total_vetoes']} ({veto_efficiency:.1f}%)\n")
    lines.append("---\n")
    lines.append("# SECTION 1: PROBLEM STATEMENT\n")
    lines.append("## 1.1 Private Data Reasoning Gap\n")
    lines.append("Alternative investment funds (Category III AIFs) in India manage sophisticated portfolios")
    lines.append("with significant exposure to private company data, early-stage investments, and complex")
    lines.append("derivative positions. This data is not publicly available, creating a 'reasoning gap'.\n")
    lines.append("This leads to inconsistent risk assessment and limited governance transparency.\n")
    lines.append("---\n")
    lines.append("# SECTION 2: SYSTEM ARCHITECTURE\n")
    lines.append("## 2.1 Three-Layer Governance\n")
    lines.append("**Layer 1: Analytical Engine** - Generates recommendations with confidence scores")
    lines.append("**Layer 2: Risk Manager** - Policy compliance and veto issuance")
    lines.append("**Layer 3: Auditor** - Cryptographic verification and merkle chain\n")
    lines.append("---\n")
    lines.append("# SECTION 3: VETO GOVERNANCE\n")
    lines.append("## 3.2 Veto Statistics\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Vetoes | {stats['total_vetoes']} |")
    lines.append(f"| Correct Vetoes | {stats['veto_correct']} |")
    lines.append(f"| Veto Efficiency | {veto_efficiency:.1f}% |")
    lines.append(f"| Total Avoided Drawdown | ${stats['total_avoided_drawdown']:,.0f} |\n")
    lines.append("---\n")
    lines.append("# SECTION 4: CRYPTOGRAPHIC AUDITABILITY\n")
    lines.append("## 4.1 Proof Certificate Architecture\n")
    lines.append("Each recommendation generates a cryptographic audit certificate containing:")
    lines.append("- Proof Hash: SHA-256 hash of recommendation data")
    lines.append("- Timestamp: Server-generated, immutable")
    lines.append("- Asset/Thesis: Plain English reasoning")
    lines.append("- Confidence Score: Quantitative assessment")
    lines.append("- Status: Cleared or Risk-Rejected\n")
    lines.append("## 4.2 Merkle Chain\n")
    lines.append("Certificates are linked in a merkle chain providing tamper evidence.\n")
    lines.append("---\n")
    lines.append("# SECTION 5: MEASURED OUTCOMES\n")
    lines.append("## 5.1 Prediction Ledger Statistics\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Predictions | {stats['total_predictions']} |")
    lines.append(f"| Cleared for Review | {stats['cleared']} |")
    lines.append(f"| Risk-Rejected | {stats['risk_rejected']} |")
    lines.append(f"| With Verified Outcomes | {stats['with_outcome']} |")
    lines.append(f"| Correct Predictions | {stats['correct']} |")
    lines.append(f"| Success Rate | {success_rate:.1f}% |\n")
    lines.append("---\n")
    lines.append("# SECTION 6: INSTITUTIONAL APPLICABILITY\n")
    lines.append("## 6.1 Indian Category III AIF Compliance\n")
    lines.append("SEBI regulations require board-approved investment policy, risk management framework,")
    lines.append("and audit trail of investment decisions. Sovereign Alpha provides all three.\n")
    lines.append("---\n")
    lines.append("**Contact:** Fund Administrator\n")
    lines.append(f"\n*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    content = "\n".join(lines)
    
    output_file = DOCS_DIR / "INSTITUTIONAL_WHITEPAPER.md"
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"Whitepaper generated: {output_file}")
    return str(output_file)


if __name__ == '__main__':
    generate_whitepaper()