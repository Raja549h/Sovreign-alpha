"""
Step 3: Autopsy Report Generator
Produces HTML one-pager briefs for the top-3 worst drawdowns
and a markdown public ledger for the remaining matches.
"""

import pandas as pd
from datetime import datetime
import os


def generate_one_pager_html(match: dict) -> str:
    """Generate a styled HTML one-pager for a single Autopsy match."""
    ticker = match['ticker']
    # If this is from retroactive backtest, deal_date IS the veto_date and veto_reason is used
    deal_date = str(match.get('deal_date', ''))[:10]
    veto_date = str(match.get('veto_date', deal_date))[:10]
    client_name = match.get('client_name', 'Unknown')
    action = match.get('action', 'N/A')
    deal_price = match.get('deal_price', 0)
    drawdown_pct = match.get('drawdown_pct', 0)
    
    # Retroactive backtest doesn't save min_price_10d, it can be computed from drawdown and deal_price
    min_price = match.get('min_price_10d')
    if min_price is None and deal_price and drawdown_pct:
        min_price = round(deal_price * (1 + (drawdown_pct/100)), 2)
    min_price_str = f"{min_price}" if min_price else "N/A"
    
    rejection_reason = match.get('rejection_reason') or match.get('veto_reason', 'N/A')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Autopsy Report: {ticker}</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 40px; color: #333; max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }}
        .metric-box {{ background: #f8f9fa; padding: 15px 20px; border-radius: 5px; margin: 15px 0; border-left: 5px solid #e74c3c; }}
        .metric-box.blue {{ border-left-color: #3498db; }}
        .metric-box.red {{ border-left-color: #e74c3c; }}
        .label {{ font-weight: bold; color: #7f8c8d; font-size: 0.9em; }}
        .val {{ font-size: 1.15em; color: #2c3e50; }}
        .summary {{ line-height: 1.7; font-size: 1.05em; }}
        .footer {{ margin-top: 30px; font-size: 0.85em; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
    </style>
</head>
<body>
    <h1>AUTOPSY REPORT: {ticker}</h1>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M IST')}</p>

    <div class="metric-box">
        <span class="label">Veto Date:</span> <span class="val">{veto_date}</span><br/>
        <span class="label">Rejection Reason:</span> <span class="val">{rejection_reason}</span>
    </div>

    <div class="metric-box blue">
        <span class="label">Institutional Deal Date:</span> <span class="val">{deal_date}</span><br/>
        <span class="label">Client:</span> <span class="val">{client_name}</span><br/>
        <span class="label">Action:</span> <span class="val">{action}</span><br/>
        <span class="label">Deal Price:</span> <span class="val">₹{deal_price}</span>
    </div>

    <div class="metric-box red">
        <span class="label">10-Trading-Day Drawdown:</span> <span class="val">{drawdown_pct}%</span><br/>
        <span class="label">Lowest Price in Window:</span> <span class="val">₹{min_price_str}</span>
    </div>

    <h3>Analysis Summary</h3>
    <p class="summary">
        Sovereign Alpha's quantitative engine identified structural weakness in
        <strong>{ticker}</strong> on <strong>{veto_date}</strong> and correctly vetoed the trade.
        Within 30 days, <strong>{client_name}</strong> executed a bulk {action} at ₹{deal_price}
        on <strong>{deal_date}</strong>. The stock subsequently dropped
        <strong>{drawdown_pct}%</strong> within the next 10 trading days, validating the veto.
    </p>

    <div class="footer">
        Sovereign Alpha — Autonomous Institutional Research Agent<br/>
        This report is auto-generated and does not constitute investment advice.
    </div>
</body>
</html>"""

    safe_date = deal_date.replace('-', '')
    filename = f"reports/autopsy_{ticker}_{safe_date}.html"
    os.makedirs('reports', exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"    Generated: {filename}")
    return filename


def generate_public_ledger(matches_df: pd.DataFrame) -> str:
    """Generate a sanitized markdown public ledger of all autopsy matches."""
    lines = [
        "# SOVEREIGN ALPHA: INSTITUTIONAL TRAP AVOIDANCE LEDGER",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M IST')}",
        "",
        "The following trades were successfully vetoed by our quantitative engine "
        "prior to significant institutional drawdowns:",
        "",
        "| Ticker | Veto Date | Client | Action | Deal Price | Deal Date | Drawdown |",
        "|--------|-----------|--------|--------|------------|-----------|----------|",
    ]

    for _, m in matches_df.iterrows():
        lines.append(
            f"| {m['ticker']} "
            f"| {str(m.get('veto_date',''))[:10]} "
            f"| {m['client_name']} "
            f"| {m['action']} "
            f"| ₹{m['deal_price']} "
            f"| {str(m.get('deal_date',''))[:10]} "
            f"| {m['drawdown_pct']}% |"
        )

    lines.extend([
        "",
        "---",
        "*Sovereign Alpha is an autonomous institutional research agent. "
        "This ledger is auto-generated and does not constitute investment advice.*"
    ])

    content = "\n".join(lines)
    os.makedirs('reports', exist_ok=True)
    filename = "reports/public_ledger_batch.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"    Generated: {filename}")
    return filename


def run_reports():
    """Main entry point for Step 3."""
    print("[Step 3] Generating Autopsy Reports...")

    csv_path = "autopsy_matches.csv"
    if not os.path.exists(csv_path):
        print("  No autopsy_matches.csv found. Nothing to report (this is normal if Step 2 found 0 notable matches).")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        print("  autopsy_matches.csv is empty. Nothing to report.")
        return

    # Top 3 worst drawdowns get individual HTML one-pagers
    top_n = min(3, len(df))
    print(f"  Generating {top_n} HTML one-pager(s) for worst drawdowns...")
    for _, match in df.head(top_n).iterrows():
        generate_one_pager_html(match.to_dict())

    # All matches go to the public ledger
    print(f"  Generating public ledger with all {len(df)} matches...")
    generate_public_ledger(df)

    print(f"[Step 3] SUCCESS: {top_n} one-pager(s) + public ledger written to reports/")


if __name__ == '__main__':
    run_reports()
