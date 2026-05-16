"""
WEEKLY REPORT — Generate institutional weekly performance report
Runs every Sunday at 9:00 AM
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "reports"
BILLING_DIR = BASE_DIR / "billing"
FUND_DATA_DB = BILLING_DIR / "fund_data.db"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(FUND_DATA_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_week_stats(week_start, week_end):
    """Get statistics for a specific week."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT COUNT(*) as total FROM prediction_ledger 
        WHERE timestamp >= ? AND timestamp < ?
    """, (week_start, week_end))
    total = c.fetchone()['total'] or 0
    
    c.execute("""
        SELECT COUNT(*) as correct FROM prediction_ledger 
        WHERE timestamp >= ? AND timestamp < ? AND actual_outcome = 'correct'
    """, (week_start, week_end))
    correct = c.fetchone()['correct'] or 0
    
    c.execute("""
        SELECT COUNT(*) as with_outcome FROM prediction_ledger 
        WHERE timestamp >= ? AND timestamp < ? AND actual_outcome IS NOT NULL AND actual_outcome != ''
    """, (week_start, week_end))
    with_outcome = c.fetchone()['with_outcome'] or 0
    
    c.execute("""
        SELECT AVG(confidence_score) as avg_conf FROM prediction_ledger 
        WHERE timestamp >= ? AND timestamp < ?
    """, (week_start, week_end))
    avg_conf = c.fetchone()['avg_conf'] or 0
    
    c.execute("""
        SELECT COUNT(*) as vetoed FROM prediction_ledger 
        WHERE timestamp >= ? AND timestamp < ? AND status = 'risk-rejected'
    """, (week_start, week_end))
    vetoed = c.fetchone()['vetoed'] or 0
    
    c.execute("""
        SELECT COALESCE(SUM(avoided_drawdown), 0) as avoided FROM veto_archive
        WHERE created_at >= ? AND created_at < ?
    """, (week_start, week_end))
    avoided = c.fetchone()['avoided'] or 0
    
    # Get top and worst predictions
    c.execute("""
        SELECT asset, actual_return_pct, confidence_score 
        FROM prediction_ledger 
        WHERE timestamp >= ? AND timestamp < ? AND actual_return_pct IS NOT NULL
        ORDER BY actual_return_pct DESC LIMIT 1
    """, (week_start, week_end))
    best = c.fetchone()
    
    c.execute("""
        SELECT asset, actual_return_pct, confidence_score 
        FROM prediction_ledger 
        WHERE timestamp >= ? AND timestamp < ? AND actual_return_pct IS NOT NULL
        ORDER BY actual_return_pct ASC LIMIT 1
    """, (week_start, week_end))
    worst = c.fetchone()
    
    conn.close()
    
    accuracy = (correct / with_outcome * 100) if with_outcome > 0 else 0
    
    return {
        'total': total,
        'correct': correct,
        'with_outcome': with_outcome,
        'accuracy': accuracy,
        'avg_conf': avg_conf * 100 if avg_conf else 0,
        'vetoed': vetoed,
        'avoided': avoided,
        'best': best,
        'worst': worst
    }


def get_cumulative_stats():
    """Get cumulative stats across all weeks."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as total FROM prediction_ledger")
    total = c.fetchone()['total'] or 0
    
    c.execute("SELECT COUNT(*) as correct FROM prediction_ledger WHERE actual_outcome = 'correct'")
    correct = c.fetchone()['correct'] or 0
    
    c.execute("SELECT COUNT(*) as with_outcome FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
    with_outcome = c.fetchone()['with_outcome'] or 0
    
    c.execute("SELECT COALESCE(SUM(avoided_drawdown), 0) as avoided FROM veto_archive")
    avoided = c.fetchone()['avoided'] or 0
    
    c.execute("SELECT COUNT(*) as veto_correct FROM veto_archive WHERE veto_correct = 1")
    veto_correct = c.fetchone()['veto_correct'] or 0
    
    c.execute("SELECT COUNT(*) as total_vetoes FROM veto_archive")
    total_vetoes = c.fetchone()['total_vetoes'] or 0
    
    conn.close()
    
    accuracy = (correct / with_outcome * 100) if with_outcome > 0 else 0
    veto_accuracy = (veto_correct / total_vetoes * 100) if total_vetoes > 0 else 0
    
    return {
        'total': total,
        'accuracy': accuracy,
        'avoided': avoided,
        'veto_accuracy': veto_accuracy,
        'live_days': (datetime.now() - datetime(2026, 1, 2)).days
    }


def generate_weekly_report():
    """Generate the weekly institutional report."""
    today = datetime.now()
    week_start = (today - timedelta(days=today.weekday() + 7)).strftime('%Y-%m-%d')
    week_end = today.strftime('%Y-%m-%d')
    
    week_stats = get_week_stats(week_start, week_end)
    cum_stats = get_cumulative_stats()
    
    week_num = (today - datetime(2026, 1, 2)).days // 7 + 1
    
    best_str = f"{week_stats['best']['asset']} (+{week_stats['best']['actual_return_pct']:.1f}%)" if week_stats['best'] else "N/A"
    worst_str = f"{week_stats['worst']['asset']} ({week_stats['worst']['actual_return_pct']:.1f}%)" if week_stats['worst'] else "N/A"
    
    lines = []
    lines.append(f"# WEEKLY INSTITUTIONAL REPORT — Week {week_num}")
    lines.append(f"**Period:** {week_start} to {week_end}")
    lines.append(f"**Generated:** {today.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## This Week's Performance")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Predictions | {week_stats['total']} |")
    lines.append(f"| Accuracy | {week_stats['accuracy']:.1f}% |")
    lines.append(f"| Avg Confidence | {week_stats['avg_conf']:.0f}% |")
    lines.append(f"| Risk-Rejections | {week_stats['vetoed']} |")
    lines.append(f"| Avoided Drawdown | ${week_stats['avoided']:,.0f} |")
    lines.append(f"| Best Prediction | {best_str} |")
    lines.append(f"| Worst Prediction | {worst_str} |")
    lines.append("")
    lines.append("## Cumulative Track Record")
    lines.append("")
    lines.append(f"- Total predictions: {cum_stats['total']}")
    lines.append(f"- Overall accuracy: {cum_stats['accuracy']:.1f}%")
    lines.append(f"- Total avoided drawdown: ${cum_stats['avoided']:,.0f}")
    lines.append(f"- Veto accuracy: {cum_stats['veto_accuracy']:.1f}%")
    lines.append(f"- Live days: {cum_stats['live_days']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Auto-generated weekly report. All data from prediction ledger.*")
    
    content = "\n".join(lines)
    
    # Save weekly report
    report_file = REPORTS_DIR / f"WEEKLY_REPORT_{today.strftime('%Y-%m-%d')}.md"
    with open(report_file, 'w') as f:
        f.write(content)
    
    print(f"[OK] Weekly report saved: {report_file}")
    
    # Update cumulative track record
    update_cumulative_record(cum_stats, week_num)
    
    return content


def update_cumulative_record(cum_stats, week_num):
    """Update the cumulative track record file."""
    cum_file = REPORTS_DIR / "CUMULATIVE_TRACK_RECORD.md"
    
    lines = []
    lines.append("# SOVEREIGN ALPHA — CUMULATIVE TRACK RECORD")
    lines.append(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Week:** {week_num}")
    lines.append("")
    lines.append("## Running Totals")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Predictions | {cum_stats['total']} |")
    lines.append(f"| Overall Accuracy | {cum_stats['accuracy']:.1f}% |")
    lines.append(f"| Total Avoided Drawdown | ${cum_stats['avoided']:,.0f} |")
    lines.append(f"| Veto Accuracy | {cum_stats['veto_accuracy']:.1f}% |")
    lines.append(f"| Live Days | {cum_stats['live_days']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Updated automatically every Sunday.*")
    
    with open(cum_file, 'w') as f:
        f.write("\n".join(lines))
    
    print(f"[OK] Cumulative record updated: {cum_file}")


if __name__ == '__main__':
    generate_weekly_report()